#include "resonith/cibs.h"

#include "integrity.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

constexpr std::uint32_t kMaximumLatentElements = 128;
constexpr std::uint32_t kMaximumBasisChannels = 8;
constexpr std::uint32_t kMaximumBasisElements = 8U * 2048U;
constexpr std::uint32_t kMaximumTypedBasisLength = 2048U;
constexpr std::uint8_t kMaximumAdapterRank = 4;
constexpr std::uint8_t kMaximumRefinementStages = 4;
constexpr std::uint8_t kMaximumShift = 30;
constexpr std::size_t kTypedBasisHeaderBytes = 48U;
constexpr std::size_t kMaximumRegistryModels = 256U;

std::uint16_t read_u16(const std::uint8_t* data) noexcept {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(data[0])
        | (static_cast<std::uint16_t>(data[1]) << 8U)
    );
}

std::uint32_t read_u32(const std::uint8_t* data) noexcept {
    return static_cast<std::uint32_t>(data[0])
        | (static_cast<std::uint32_t>(data[1]) << 8U)
        | (static_cast<std::uint32_t>(data[2]) << 16U)
        | (static_cast<std::uint32_t>(data[3]) << 24U);
}

bool is_continuation(std::uint8_t value) noexcept {
    return (value & 0xc0U) == 0x80U;
}

bool valid_utf8(const std::uint8_t* data, std::size_t size) noexcept {
    std::size_t cursor = 0U;
    while (cursor < size) {
        const std::uint8_t first = data[cursor];
        if (first <= 0x7fU) {
            ++cursor;
            continue;
        }
        if (
            first >= 0xc2U
            && first <= 0xdfU
            && cursor + 1U < size
            && is_continuation(data[cursor + 1U])
        ) {
            cursor += 2U;
            continue;
        }
        if (first >= 0xe0U && first <= 0xefU && cursor + 2U < size) {
            const std::uint8_t second = data[cursor + 1U];
            const bool second_valid = (
                    first == 0xe0U
                    && second >= 0xa0U
                    && second <= 0xbfU
                )
                || (
                    first == 0xedU
                    && second >= 0x80U
                    && second <= 0x9fU
                )
                || (
                    first != 0xe0U
                    && first != 0xedU
                    && is_continuation(second)
                );
            if (second_valid && is_continuation(data[cursor + 2U])) {
                cursor += 3U;
                continue;
            }
        }
        if (first >= 0xf0U && first <= 0xf4U && cursor + 3U < size) {
            const std::uint8_t second = data[cursor + 1U];
            const bool second_valid = (
                    first == 0xf0U
                    && second >= 0x90U
                    && second <= 0xbfU
                )
                || (
                    first == 0xf4U
                    && second >= 0x80U
                    && second <= 0x8fU
                )
                || (
                    first >= 0xf1U
                    && first <= 0xf3U
                    && is_continuation(second)
                );
            if (
                second_valid
                && is_continuation(data[cursor + 2U])
                && is_continuation(data[cursor + 3U])
            ) {
                cursor += 4U;
                continue;
            }
        }
        return false;
    }
    return true;
}

std::int64_t round_shift_ties_away(
    std::int64_t value,
    std::uint8_t shift
) noexcept {
    if (shift == 0U) {
        return value;
    }
    const bool negative = value < 0;
    const std::uint64_t magnitude = negative
        ? static_cast<std::uint64_t>(-(value + 1)) + 1U
        : static_cast<std::uint64_t>(value);
    const std::uint64_t rounded = (
        magnitude + (1ULL << (shift - 1U))
    ) >> shift;
    return negative
        ? -static_cast<std::int64_t>(rounded)
        : static_cast<std::int64_t>(rounded);
}

std::int64_t activate(std::int64_t value) noexcept {
    return value < 0 ? round_shift_ties_away(value, 3U) : value;
}

std::int16_t saturate_int16(std::int64_t value) noexcept {
    return static_cast<std::int16_t>(
        std::clamp<std::int64_t>(value, -32768, 32767)
    );
}

resonith_status inspect(
    const resonith_cibs_model* model,
    const resonith_cibs_adapter* adapter,
    resonith_cibs_info& info
) noexcept {
    info = {};
    if (
        model == nullptr
        || model->model_id == nullptr
        || model->projection == nullptr
        || model->projection_bias == nullptr
        || model->model_id_bytes == 0U
        || model->model_id_bytes > 255U
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (
        model->basis_channels == 0U
        || model->basis_channels > kMaximumBasisChannels
        || model->coarse_length == 0U
        || model->latent_elements == 0U
        || model->latent_elements > kMaximumLatentElements
        || model->projection_shift > kMaximumShift
        || model->refinement_stage_count > kMaximumRefinementStages
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    if (
        model->refinement_stage_count != 0U
        && model->refinement_stages == nullptr
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    std::uint64_t output_length = model->coarse_length;
    for (
        std::uint8_t index = 0;
        index < model->refinement_stage_count;
        ++index
    ) {
        const resonith_cibs_refinement_stage& stage =
            model->refinement_stages[index];
        if (
            stage.kernels == nullptr
            || stage.kernel_width == 0U
            || stage.kernel_width > 7U
            || stage.kernel_width % 2U == 0U
            || stage.shift > kMaximumShift
            || stage.reserved != 0U
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        output_length *= 2U;
    }
    const std::uint64_t output_elements =
        output_length * model->basis_channels;
    if (
        output_elements == 0U
        || output_elements > kMaximumBasisElements
        || output_length > std::numeric_limits<std::uint32_t>::max()
        || model->reserved != 0U
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }

    std::uint32_t adapter_rank = 0U;
    if (adapter != nullptr) {
        if (
            adapter->u == nullptr
            || adapter->v == nullptr
            || adapter->rank == 0U
            || adapter->rank > kMaximumAdapterRank
            || adapter->inner_shift > kMaximumShift
            || adapter->output_shift > kMaximumShift
            || adapter->reserved != 0U
        ) {
            return RESONITH_STATUS_PROFILE_BOUND;
        }
        adapter_rank = adapter->rank;
    }

    info.basis_channels = model->basis_channels;
    info.output_length = static_cast<std::uint32_t>(output_length);
    info.output_elements = static_cast<std::uint32_t>(output_elements);
    info.scratch_elements = 2U * info.output_elements + adapter_rank;
    return RESONITH_STATUS_OK;
}

resonith_status inspect_typed_basis(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_cibs_registry* registry,
    resonith_cibs_basis_info& info
) noexcept {
    info = {};
    if (data == nullptr || registry == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (data_size < kTypedBasisHeaderBytes) {
        return RESONITH_STATUS_TRUNCATED;
    }

    const std::uint8_t model_id_bytes = data[0];
    const std::uint8_t flags = data[1];
    const std::uint16_t latent_elements = read_u16(data + 2U);
    const std::uint16_t channels = read_u16(data + 4U);
    const std::uint16_t reserved = read_u16(data + 6U);
    const std::uint32_t output_length = read_u32(data + 8U);
    const std::uint32_t reserved2 = read_u32(data + 12U);
    if (flags != 0U) {
        return RESONITH_STATUS_UNSUPPORTED_FEATURE;
    }
    if (reserved != 0U || reserved2 != 0U) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        model_id_bytes == 0U
        || latent_elements == 0U
        || latent_elements > kMaximumLatentElements
        || channels == 0U
        || channels > kMaximumBasisChannels
        || output_length < 2U
        || output_length > kMaximumTypedBasisLength
        || static_cast<std::uint64_t>(channels) * output_length
            > kMaximumBasisElements
    ) {
        return RESONITH_STATUS_PROFILE_BOUND;
    }
    const std::size_t expected_size = kTypedBasisHeaderBytes
        + model_id_bytes
        + latent_elements;
    if (data_size != expected_size) {
        return data_size < expected_size
            ? RESONITH_STATUS_TRUNCATED
            : RESONITH_STATUS_MALFORMED;
    }
    const std::uint8_t* model_id = data + kTypedBasisHeaderBytes;
    if (!valid_utf8(model_id, model_id_bytes)) {
        return RESONITH_STATUS_MALFORMED;
    }
    if (
        registry->model_count > kMaximumRegistryModels
        || (
            registry->model_count != 0U
            && registry->models == nullptr
        )
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }

    const resonith_cibs_model* matched = nullptr;
    for (std::size_t index = 0U; index < registry->model_count; ++index) {
        const resonith_cibs_model& candidate = registry->models[index];
        if (
            candidate.model_id != nullptr
            && candidate.model_id_bytes == model_id_bytes
            && std::memcmp(
                candidate.model_id,
                model_id,
                model_id_bytes
            ) == 0
        ) {
            if (matched != nullptr) {
                return RESONITH_STATUS_INVALID_ARGUMENT;
            }
            matched = &candidate;
        }
    }
    if (matched == nullptr) {
        return RESONITH_STATUS_NOT_FOUND;
    }

    resonith_cibs_info model_info{};
    const resonith_status model_status = inspect(
        matched,
        nullptr,
        model_info
    );
    if (model_status != RESONITH_STATUS_OK) {
        return model_status;
    }
    if (
        matched->latent_elements != latent_elements
        || model_info.basis_channels != channels
        || model_info.output_length != output_length
    ) {
        return RESONITH_STATUS_MALFORMED;
    }

    info.model = matched;
    info.latent = reinterpret_cast<const std::int8_t*>(
        model_id + model_id_bytes
    );
    info.expected_sha256 = data + 16U;
    info.output_length = model_info.output_length;
    info.output_elements = model_info.output_elements;
    info.scratch_elements = model_info.scratch_elements;
    info.channels = static_cast<std::uint16_t>(model_info.basis_channels);
    info.latent_elements = latent_elements;
    return RESONITH_STATUS_OK;
}

void update_u32_le(
    resonith::internal::Sha256Context& context,
    std::uint32_t value
) noexcept {
    const std::array<std::uint8_t, 4> bytes = {
        static_cast<std::uint8_t>(value),
        static_cast<std::uint8_t>(value >> 8U),
        static_cast<std::uint8_t>(value >> 16U),
        static_cast<std::uint8_t>(value >> 24U),
    };
    resonith::internal::sha256_update(context, bytes.data(), bytes.size());
}

void basis_digest(
    const resonith_cibs_model& model,
    const resonith_cibs_info& info,
    const std::int64_t* samples,
    std::uint8_t digest[32]
) noexcept {
    resonith::internal::Sha256Context context{};
    resonith::internal::sha256_init(context);
    const std::uint8_t model_id_size =
        static_cast<std::uint8_t>(model.model_id_bytes);
    resonith::internal::sha256_update(context, &model_id_size, 1U);
    update_u32_le(context, info.basis_channels);
    update_u32_le(context, info.output_length);
    resonith::internal::sha256_update(
        context,
        model.model_id,
        model.model_id_bytes
    );

    std::array<std::uint8_t, 256> encoded{};
    std::size_t used = 0U;
    for (std::uint32_t index = 0; index < info.output_elements; ++index) {
        const std::uint16_t value = static_cast<std::uint16_t>(
            saturate_int16(samples[index])
        );
        encoded[used] = static_cast<std::uint8_t>(value);
        encoded[used + 1U] = static_cast<std::uint8_t>(value >> 8U);
        used += 2U;
        if (used == encoded.size()) {
            resonith::internal::sha256_update(
                context,
                encoded.data(),
                encoded.size()
            );
            used = 0U;
        }
    }
    if (used != 0U) {
        resonith::internal::sha256_update(context, encoded.data(), used);
    }
    resonith::internal::sha256_final(context, digest);
}

}  // namespace

extern "C" resonith_status resonith_cibs_inspect_model(
    const resonith_cibs_model* model,
    const resonith_cibs_adapter* adapter,
    resonith_cibs_info* info
) {
    if (info == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    return inspect(model, adapter, *info);
}

extern "C" resonith_status resonith_cibs_materialize(
    const resonith_cibs_model* model,
    const std::int8_t* latent,
    std::size_t latent_count,
    const resonith_cibs_adapter* adapter,
    const std::int32_t* correction,
    std::size_t correction_count,
    const std::uint8_t* expected_sha256,
    std::uint8_t* actual_sha256,
    std::int16_t* output,
    std::size_t output_capacity,
    std::int64_t* scratch,
    std::size_t scratch_count,
    std::uint64_t* integer_macs
) {
    resonith_cibs_info info{};
    const resonith_status inspect_status = inspect(model, adapter, info);
    if (inspect_status != RESONITH_STATUS_OK) {
        return inspect_status;
    }
    if (
        latent == nullptr
        || latent_count != model->latent_elements
        || output == nullptr
        || scratch == nullptr
        || (correction == nullptr && correction_count != 0U)
        || (correction != nullptr && correction_count != info.output_elements)
    ) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    if (output_capacity < info.output_elements) {
        return RESONITH_STATUS_OUTPUT_TOO_SMALL;
    }
    if (scratch_count < info.scratch_elements) {
        return RESONITH_STATUS_SCRATCH_TOO_SMALL;
    }
    if (integer_macs != nullptr) {
        *integer_macs = 0U;
    }

    std::int64_t* current = scratch;
    std::int64_t* next = scratch + info.output_elements;
    std::int64_t* adapter_inner = scratch + 2U * info.output_elements;
    const std::uint32_t coarse_elements =
        model->basis_channels * model->coarse_length;
    std::uint64_t macs = 0U;

    // 1. Project the latent and apply the optional bounded low-rank delta.
    if (adapter != nullptr) {
        for (std::uint8_t rank = 0; rank < adapter->rank; ++rank) {
            std::int64_t accumulator = 0;
            for (
                std::uint32_t latent_index = 0;
                latent_index < model->latent_elements;
                ++latent_index
            ) {
                accumulator += static_cast<std::int64_t>(
                    adapter->v[
                        static_cast<std::size_t>(rank)
                            * model->latent_elements
                            + latent_index
                    ]
                ) * latent[latent_index];
            }
            adapter_inner[rank] = round_shift_ties_away(
                accumulator,
                adapter->inner_shift
            );
        }
        macs += static_cast<std::uint64_t>(adapter->rank)
            * model->latent_elements;
    }

    for (std::uint32_t row = 0; row < coarse_elements; ++row) {
        std::int64_t accumulator = model->projection_bias[row];
        for (
            std::uint32_t latent_index = 0;
            latent_index < model->latent_elements;
            ++latent_index
        ) {
            accumulator += static_cast<std::int64_t>(
                model->projection[
                    static_cast<std::size_t>(row) * model->latent_elements
                        + latent_index
                ]
            ) * latent[latent_index];
        }
        std::int64_t projected = round_shift_ties_away(
            accumulator,
            model->projection_shift
        );
        if (adapter != nullptr) {
            std::int64_t delta = 0;
            for (std::uint8_t rank = 0; rank < adapter->rank; ++rank) {
                delta += static_cast<std::int64_t>(
                    adapter->u[
                        static_cast<std::size_t>(row) * adapter->rank + rank
                    ]
                ) * adapter_inner[rank];
            }
            projected += round_shift_ties_away(
                delta,
                adapter->output_shift
            );
        }
        current[row] = saturate_int16(activate(projected));
    }
    macs += static_cast<std::uint64_t>(coarse_elements)
        * model->latent_elements;
    if (adapter != nullptr) {
        macs += static_cast<std::uint64_t>(coarse_elements) * adapter->rank;
    }

    // 2. Refine with periodic channel-local kernels, saturating every stage.
    std::uint32_t current_length = model->coarse_length;
    for (
        std::uint8_t stage_index = 0;
        stage_index < model->refinement_stage_count;
        ++stage_index
    ) {
        const resonith_cibs_refinement_stage& stage =
            model->refinement_stages[stage_index];
        const std::uint32_t output_length = current_length * 2U;
        const std::int32_t center = static_cast<std::int32_t>(
            stage.kernel_width / 2U
        );
        for (
            std::uint32_t channel = 0;
            channel < model->basis_channels;
            ++channel
        ) {
            for (
                std::uint32_t position = 0;
                position < output_length;
                ++position
            ) {
                std::int64_t accumulator = 0;
                for (
                    std::uint8_t tap = 0;
                    tap < stage.kernel_width;
                    ++tap
                ) {
                    const std::int64_t offset =
                        static_cast<std::int64_t>(tap) - center;
                    std::int64_t wrapped = (
                        static_cast<std::int64_t>(position)
                        - offset
                    ) % output_length;
                    if (wrapped < 0) {
                        wrapped += output_length;
                    }
                    const std::uint32_t source_position =
                        static_cast<std::uint32_t>(wrapped) / 2U;
                    accumulator += static_cast<std::int64_t>(
                        stage.kernels[
                            static_cast<std::size_t>(channel)
                                * stage.kernel_width
                                + tap
                        ]
                    ) * current[
                        static_cast<std::size_t>(channel) * current_length
                            + source_position
                    ];
                }
                next[
                    static_cast<std::size_t>(channel) * output_length
                        + position
                ] = saturate_int16(
                    activate(round_shift_ties_away(accumulator, stage.shift))
                );
            }
        }
        macs += static_cast<std::uint64_t>(model->basis_channels)
            * output_length
            * stage.kernel_width;
        std::swap(current, next);
        current_length = output_length;
    }

    // 3. Apply objective correction in staging and hash before atomic commit.
    if (correction != nullptr) {
        for (
            std::uint32_t index = 0;
            index < info.output_elements;
            ++index
        ) {
            current[index] = saturate_int16(
                current[index] + correction[index]
            );
        }
    }
    std::uint8_t digest[32]{};
    basis_digest(*model, info, current, digest);
    if (actual_sha256 != nullptr) {
        std::memcpy(actual_sha256, digest, 32U);
    }
    if (
        expected_sha256 != nullptr
        && std::memcmp(expected_sha256, digest, 32U) != 0
    ) {
        return RESONITH_STATUS_HASH_MISMATCH;
    }

    for (std::uint32_t index = 0; index < info.output_elements; ++index) {
        output[index] = saturate_int16(current[index]);
    }
    if (integer_macs != nullptr) {
        *integer_macs = macs;
    }
    return RESONITH_STATUS_OK;
}

extern "C" resonith_status resonith_cibs_basis_inspect(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_cibs_registry* registry,
    resonith_cibs_basis_info* info
) {
    if (info == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    return inspect_typed_basis(data, data_size, registry, *info);
}

extern "C" resonith_status resonith_cibs_basis_materialize(
    const std::uint8_t* data,
    std::size_t data_size,
    const resonith_cibs_registry* registry,
    std::int16_t* output,
    std::size_t output_capacity,
    std::int64_t* scratch,
    std::size_t scratch_count,
    std::uint8_t* actual_sha256,
    std::uint64_t* integer_macs,
    std::size_t* elements_written
) {
    if (elements_written == nullptr) {
        return RESONITH_STATUS_INVALID_ARGUMENT;
    }
    *elements_written = 0U;
    resonith_cibs_basis_info info{};
    const resonith_status inspect_status = inspect_typed_basis(
        data,
        data_size,
        registry,
        info
    );
    if (inspect_status != RESONITH_STATUS_OK) {
        return inspect_status;
    }
    const resonith_status materialize_status = resonith_cibs_materialize(
        info.model,
        info.latent,
        info.latent_elements,
        nullptr,
        nullptr,
        0U,
        info.expected_sha256,
        actual_sha256,
        output,
        output_capacity,
        scratch,
        scratch_count,
        integer_macs
    );
    if (materialize_status != RESONITH_STATUS_OK) {
        return materialize_status;
    }
    *elements_written = info.output_elements;
    return RESONITH_STATUS_OK;
}
