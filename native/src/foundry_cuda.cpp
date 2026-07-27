#include "resonith/foundry_cuda.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <vector>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace {

constexpr std::uint64_t q15_scale = 32768U;
constexpr std::int64_t gain_neighbour_radius = 8;
constexpr std::uint64_t direction_count = 2U;

bool multiply_fits(
    std::uint64_t left,
    std::uint64_t right,
    std::uint64_t* product
) noexcept {
    if (
        right != 0U
        && left > std::numeric_limits<std::uint64_t>::max() / right
    ) {
        return false;
    }
    *product = left * right;
    return true;
}

resonith_foundry_status validate_range(
    std::size_t block_element_count,
    const resonith_foundry_gain_phase_range& range,
    std::size_t output_capacity,
    std::uint64_t* total_candidates
) noexcept {
    if (range.block_count < 2U || range.block_samples == 0U) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t required_elements = 0U;
    if (
        !multiply_fits(
            range.block_count,
            range.block_samples,
            &required_elements
        )
        || required_elements != block_element_count
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t pair_count = 0U;
    if (
        !multiply_fits(
            range.block_count,
            range.block_count - 1U,
            &pair_count
        )
        || !multiply_fits(pair_count, range.block_samples, total_candidates)
        || !multiply_fits(
            *total_candidates,
            direction_count,
            total_candidates
        )
    ) {
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    if (
        range.first_candidate > *total_candidates
        || range.candidate_count == 0U
        || range.candidate_count
            > *total_candidates - range.first_candidate
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    if (range.candidate_count > output_capacity) {
        return RESONITH_FOUNDRY_OUTPUT_TOO_SMALL;
    }
    return RESONITH_FOUNDRY_OK;
}

std::int64_t round_divide_away(
    std::int64_t numerator,
    std::int64_t denominator
) noexcept {
    if (numerator >= 0) {
        return (numerator + denominator / 2) / denominator;
    }
    return -((-numerator + denominator / 2) / denominator);
}

std::int64_t round_q15(std::int64_t product) noexcept {
    return round_divide_away(product, static_cast<std::int64_t>(q15_scale));
}

std::int64_t interpolated_gain(
    std::int64_t start,
    std::int64_t end,
    std::uint64_t sample,
    std::uint64_t count
) noexcept {
    if (count <= 1U) {
        return start;
    }
    return start + round_divide_away(
        (end - start) * static_cast<std::int64_t>(sample),
        static_cast<std::int64_t>(count - 1U)
    );
}

resonith_foundry_gain_phase_result evaluate_candidate(
    const std::int16_t* blocks,
    const resonith_foundry_gain_phase_range& range,
    std::uint64_t candidate_id
) noexcept {
    const bool reverse = candidate_id % direction_count != 0U;
    const std::uint64_t direction_id = candidate_id / direction_count;
    const std::uint64_t offset =
        direction_id % range.block_samples;
    const std::uint64_t pair_id =
        direction_id / range.block_samples;
    const std::uint64_t basis_index =
        pair_id / (range.block_count - 1U);
    const std::uint64_t target_slot =
        pair_id % (range.block_count - 1U);
    const std::uint64_t target_index =
        target_slot >= basis_index ? target_slot + 1U : target_slot;
    const std::int16_t* const basis =
        blocks + basis_index * range.block_samples;
    const std::int16_t* const target =
        blocks + target_index * range.block_samples;

    std::int64_t basis_energy = 0;
    std::int64_t target_energy = 0;
    std::int64_t correlation = 0;
    for (
        std::uint64_t sample = 0U;
        sample < range.block_samples;
        ++sample
    ) {
        const std::uint64_t source_index = reverse
            ? (
                offset + range.block_samples
                - sample % range.block_samples
            ) % range.block_samples
            : (sample + offset) % range.block_samples;
        const std::int64_t left = basis[source_index];
        const std::int64_t right = target[sample];
        basis_energy += left * left;
        target_energy += right * right;
        correlation += left * right;
    }

    std::int64_t fitted_gain = 0;
    if (basis_energy != 0) {
        fitted_gain = round_divide_away(
            correlation * static_cast<std::int64_t>(q15_scale),
            basis_energy
        );
        fitted_gain = std::clamp<std::int64_t>(
            fitted_gain,
            -static_cast<std::int64_t>(q15_scale),
            static_cast<std::int64_t>(q15_scale)
        );
    }

    std::int64_t gain = fitted_gain;
    std::int64_t end_gain = 0;
    std::uint32_t transform_flags = reverse
        ? static_cast<std::uint32_t>(RESONITH_FOUNDRY_TRANSFORM_REVERSE)
        : 0U;
    std::uint64_t squared_error = std::numeric_limits<std::uint64_t>::max();
    const std::int64_t first_gain = std::max<std::int64_t>(
        -static_cast<std::int64_t>(q15_scale),
        fitted_gain - gain_neighbour_radius
    );
    const std::int64_t final_gain = std::min<std::int64_t>(
        static_cast<std::int64_t>(q15_scale),
        fitted_gain + gain_neighbour_radius
    );
    for (
        std::int64_t candidate_gain = first_gain;
        candidate_gain <= final_gain;
        ++candidate_gain
    ) {
        std::uint64_t candidate_error = 0U;
        for (
            std::uint64_t sample = 0U;
            sample < range.block_samples;
            ++sample
        ) {
            const std::uint64_t source_index = reverse
                ? (
                    offset + range.block_samples
                    - sample % range.block_samples
                ) % range.block_samples
                : (sample + offset) % range.block_samples;
            const std::int64_t predicted = round_q15(
                static_cast<std::int64_t>(basis[source_index])
                    * candidate_gain
            );
            const std::int64_t difference =
                static_cast<std::int64_t>(target[sample]) - predicted;
            candidate_error += static_cast<std::uint64_t>(
                difference * difference
            );
        }
        if (
            candidate_error < squared_error
            || (
                candidate_error == squared_error
                && (
                    std::abs(candidate_gain) < std::abs(gain)
                    || (
                        std::abs(candidate_gain) == std::abs(gain)
                        && candidate_gain < gain
                    )
                )
            )
        ) {
            gain = candidate_gain;
            end_gain = 0;
            transform_flags = reverse
                ? static_cast<std::uint32_t>(
                      RESONITH_FOUNDRY_TRANSFORM_REVERSE
                  )
                : 0U;
            squared_error = candidate_error;
        }
    }

    if (range.block_samples > 1U) {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double ay = 0.0;
        double by = 0.0;
        const double denominator =
            static_cast<double>(range.block_samples - 1U);
        for (
            std::uint64_t sample = 0U;
            sample < range.block_samples;
            ++sample
        ) {
            const double position =
                static_cast<double>(sample) / denominator;
            const std::uint64_t source_index = reverse
                ? (
                    offset + range.block_samples
                    - sample % range.block_samples
                ) % range.block_samples
                : (sample + offset) % range.block_samples;
            const double aligned =
                static_cast<double>(basis[source_index]);
            const double first = aligned * (1.0 - position);
            const double second = aligned * position;
            const double scaled_target =
                static_cast<double>(target[sample])
                * static_cast<double>(q15_scale);
            aa += first * first;
            ab += first * second;
            bb += second * second;
            ay += first * scaled_target;
            by += second * scaled_target;
        }
        const double determinant = aa * bb - ab * ab;
        if (determinant > std::max(1.0, aa * bb) * 1.0e-12) {
            const auto fitted_start = std::clamp<std::int64_t>(
                static_cast<std::int64_t>(
                    (ay * bb - by * ab) / determinant
                    + ((ay * bb - by * ab) >= 0.0 ? 0.5 : -0.5)
                ),
                -static_cast<std::int64_t>(q15_scale),
                static_cast<std::int64_t>(q15_scale)
            );
            const auto fitted_end = std::clamp<std::int64_t>(
                static_cast<std::int64_t>(
                    (by * aa - ay * ab) / determinant
                    + ((by * aa - ay * ab) >= 0.0 ? 0.5 : -0.5)
                ),
                -static_cast<std::int64_t>(q15_scale),
                static_cast<std::int64_t>(q15_scale)
            );
            const std::int64_t first_start = std::max<std::int64_t>(
                -static_cast<std::int64_t>(q15_scale),
                fitted_start - gain_neighbour_radius
            );
            const std::int64_t final_start = std::min<std::int64_t>(
                static_cast<std::int64_t>(q15_scale),
                fitted_start + gain_neighbour_radius
            );
            const std::int64_t first_end = std::max<std::int64_t>(
                -static_cast<std::int64_t>(q15_scale),
                fitted_end - gain_neighbour_radius
            );
            const std::int64_t final_end = std::min<std::int64_t>(
                static_cast<std::int64_t>(q15_scale),
                fitted_end + gain_neighbour_radius
            );
            for (
                std::int64_t candidate_start = first_start;
                candidate_start <= final_start;
                ++candidate_start
            ) {
                for (
                    std::int64_t candidate_end = first_end;
                    candidate_end <= final_end;
                    ++candidate_end
                ) {
                    std::uint64_t candidate_error = 0U;
                    for (
                        std::uint64_t sample = 0U;
                        sample < range.block_samples;
                        ++sample
                    ) {
                        const std::int64_t current_gain =
                            interpolated_gain(
                                candidate_start,
                                candidate_end,
                                sample,
                                range.block_samples
                            );
                        const std::uint64_t source_index = reverse
                            ? (
                                offset + range.block_samples
                                - sample % range.block_samples
                            ) % range.block_samples
                            : (sample + offset) % range.block_samples;
                        const std::int64_t predicted = round_q15(
                            static_cast<std::int64_t>(
                                basis[source_index]
                            ) * current_gain
                        );
                        const std::int64_t difference =
                            static_cast<std::int64_t>(target[sample])
                            - predicted;
                        candidate_error += static_cast<std::uint64_t>(
                            difference * difference
                        );
                    }
                    if (candidate_error < squared_error) {
                        gain = candidate_start;
                        end_gain = candidate_end;
                        transform_flags =
                            RESONITH_FOUNDRY_TRANSFORM_LINEAR_GAIN
                            | (
                                reverse
                                    ? static_cast<std::uint32_t>(
                                          RESONITH_FOUNDRY_TRANSFORM_REVERSE
                                      )
                                    : 0U
                            );
                        squared_error = candidate_error;
                    }
                }
            }
        }
    }
    return {
        static_cast<std::uint32_t>(basis_index),
        static_cast<std::uint32_t>(target_index),
        static_cast<std::uint32_t>(offset),
        static_cast<std::int32_t>(gain),
        static_cast<std::int32_t>(end_gain),
        transform_flags,
        squared_error,
        static_cast<std::uint64_t>(target_energy),
    };
}

void copy_error(
    const std::string& message,
    char* error,
    std::size_t error_capacity
) noexcept {
    if (error == nullptr || error_capacity == 0U) {
        return;
    }
    const std::size_t count = std::min(
        message.size(),
        error_capacity - 1U
    );
    std::memcpy(error, message.data(), count);
    error[count] = '\0';
}

#if defined(_WIN32)

using nvrtc_program = void*;
using nvrtc_result = int;
using cuda_result = int;
using cuda_device = int;
using cuda_context = void*;
using cuda_module = void*;
using cuda_function = void*;
using cuda_stream = void*;
using cuda_device_ptr = std::uint64_t;

constexpr nvrtc_result nvrtc_success = 0;
constexpr cuda_result cuda_success = 0;

struct nvrtc_api {
    HMODULE library = nullptr;
    HMODULE builtins = nullptr;
    nvrtc_result (*version)(int*, int*) = nullptr;
    nvrtc_result (*create_program)(
        nvrtc_program*,
        const char*,
        const char*,
        int,
        const char* const*,
        const char* const*
    ) = nullptr;
    nvrtc_result (*compile_program)(
        nvrtc_program,
        int,
        const char* const*
    ) = nullptr;
    nvrtc_result (*log_size)(nvrtc_program, std::size_t*) = nullptr;
    nvrtc_result (*get_log)(nvrtc_program, char*) = nullptr;
    nvrtc_result (*cubin_size)(nvrtc_program, std::size_t*) = nullptr;
    nvrtc_result (*get_cubin)(nvrtc_program, char*) = nullptr;
    nvrtc_result (*destroy_program)(nvrtc_program*) = nullptr;

    ~nvrtc_api() {
        if (library != nullptr) {
            FreeLibrary(library);
        }
        if (builtins != nullptr) {
            FreeLibrary(builtins);
        }
    }
};

struct cuda_api {
    HMODULE library = nullptr;
    cuda_result (__stdcall *init)(unsigned int) = nullptr;
    cuda_result (__stdcall *device_get)(cuda_device*, int) = nullptr;
    cuda_result (__stdcall *device_name)(char*, int, cuda_device) = nullptr;
    cuda_result (__stdcall *device_compute_capability)(
        int*,
        int*,
        cuda_device
    ) = nullptr;
    cuda_result (__stdcall *device_total_memory)(
        std::size_t*,
        cuda_device
    ) = nullptr;
    cuda_result (__stdcall *primary_context_retain)(
        cuda_context*,
        cuda_device
    ) = nullptr;
    cuda_result (__stdcall *primary_context_release)(cuda_device) = nullptr;
    cuda_result (__stdcall *context_set_current)(cuda_context) = nullptr;
    cuda_result (__stdcall *memory_allocate)(
        cuda_device_ptr*,
        std::size_t
    ) = nullptr;
    cuda_result (__stdcall *memory_free)(cuda_device_ptr) = nullptr;
    cuda_result (__stdcall *copy_host_to_device)(
        cuda_device_ptr,
        const void*,
        std::size_t
    ) = nullptr;
    cuda_result (__stdcall *copy_device_to_host)(
        void*,
        cuda_device_ptr,
        std::size_t
    ) = nullptr;
    cuda_result (__stdcall *module_load_data)(
        cuda_module*,
        const void*
    ) = nullptr;
    cuda_result (__stdcall *module_get_function)(
        cuda_function*,
        cuda_module,
        const char*
    ) = nullptr;
    cuda_result (__stdcall *launch_kernel)(
        cuda_function,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        unsigned int,
        cuda_stream,
        void**,
        void**
    ) = nullptr;
    cuda_result (__stdcall *context_synchronize)() = nullptr;
    cuda_result (__stdcall *module_unload)(cuda_module) = nullptr;

    ~cuda_api() {
        if (library != nullptr) {
            FreeLibrary(library);
        }
    }
};

template <typename function_type>
bool load_symbol(
    HMODULE library,
    const char* name,
    function_type* function
) noexcept {
    const FARPROC address = GetProcAddress(library, name);
    if (address == nullptr) {
        *function = nullptr;
        return false;
    }
    static_assert(sizeof(address) == sizeof(*function));
    std::memcpy(function, &address, sizeof(address));
    return true;
}

std::wstring widen_ascii(const std::string& text) {
    return std::wstring(text.begin(), text.end());
}

std::wstring library_path(
    const char* directory,
    const wchar_t* library_name
) {
    if (directory == nullptr || directory[0] == '\0') {
        return library_name;
    }
    std::wstring result = widen_ascii(directory);
    if (!result.empty() && result.back() != L'\\' && result.back() != L'/') {
        result.push_back(L'\\');
    }
    result.append(library_name);
    return result;
}

bool load_nvrtc(
    const char* directory,
    nvrtc_api* api,
    std::string* error
) {
    std::vector<wchar_t> previous_directory;
    if (directory != nullptr && directory[0] != '\0') {
        const DWORD previous_length = GetDllDirectoryW(0U, nullptr);
        previous_directory.resize(
            std::max<DWORD>(1U, previous_length + 1U),
            L'\0'
        );
        if (previous_length != 0U) {
            GetDllDirectoryW(
                static_cast<DWORD>(previous_directory.size()),
                previous_directory.data()
            );
        }
        const std::wstring wide_directory = widen_ascii(directory);
        SetDllDirectoryW(wide_directory.c_str());
    }
    api->builtins = LoadLibraryW(
        library_path(
            directory,
            L"nvrtc-builtins64_133.dll"
        ).c_str()
    );
    api->library = LoadLibraryW(
        library_path(directory, L"nvrtc64_130_0.dll").c_str()
    );
    if (directory != nullptr && directory[0] != '\0') {
        SetDllDirectoryW(
            previous_directory.empty() || previous_directory[0] == L'\0'
                ? nullptr
                : previous_directory.data()
        );
    }
    if (api->library == nullptr || api->builtins == nullptr) {
        *error = "cannot load NVIDIA NVRTC 13 and its builtins";
        return false;
    }
    const bool complete =
        load_symbol(api->library, "nvrtcVersion", &api->version)
        && load_symbol(
            api->library,
            "nvrtcCreateProgram",
            &api->create_program
        )
        && load_symbol(
            api->library,
            "nvrtcCompileProgram",
            &api->compile_program
        )
        && load_symbol(
            api->library,
            "nvrtcGetProgramLogSize",
            &api->log_size
        )
        && load_symbol(
            api->library,
            "nvrtcGetProgramLog",
            &api->get_log
        )
        && load_symbol(
            api->library,
            "nvrtcGetCUBINSize",
            &api->cubin_size
        )
        && load_symbol(api->library, "nvrtcGetCUBIN", &api->get_cubin)
        && load_symbol(
            api->library,
            "nvrtcDestroyProgram",
            &api->destroy_program
        );
    if (!complete) {
        *error = "NVRTC library is missing a required symbol";
    }
    return complete;
}

bool load_cuda(cuda_api* api, std::string* error) {
    api->library = LoadLibraryW(L"nvcuda.dll");
    if (api->library == nullptr) {
        *error = "cannot load the NVIDIA CUDA driver";
        return false;
    }
    const bool complete =
        load_symbol(api->library, "cuInit", &api->init)
        && load_symbol(api->library, "cuDeviceGet", &api->device_get)
        && load_symbol(
            api->library,
            "cuDeviceGetName",
            &api->device_name
        )
        && load_symbol(
            api->library,
            "cuDeviceComputeCapability",
            &api->device_compute_capability
        )
        && load_symbol(
            api->library,
            "cuDeviceTotalMem_v2",
            &api->device_total_memory
        )
        && load_symbol(
            api->library,
            "cuDevicePrimaryCtxRetain",
            &api->primary_context_retain
        )
        && load_symbol(
            api->library,
            "cuDevicePrimaryCtxRelease_v2",
            &api->primary_context_release
        )
        && load_symbol(
            api->library,
            "cuCtxSetCurrent",
            &api->context_set_current
        )
        && load_symbol(
            api->library,
            "cuMemAlloc_v2",
            &api->memory_allocate
        )
        && load_symbol(
            api->library,
            "cuMemFree_v2",
            &api->memory_free
        )
        && load_symbol(
            api->library,
            "cuMemcpyHtoD_v2",
            &api->copy_host_to_device
        )
        && load_symbol(
            api->library,
            "cuMemcpyDtoH_v2",
            &api->copy_device_to_host
        )
        && load_symbol(
            api->library,
            "cuModuleLoadData",
            &api->module_load_data
        )
        && load_symbol(
            api->library,
            "cuModuleGetFunction",
            &api->module_get_function
        )
        && load_symbol(
            api->library,
            "cuLaunchKernel",
            &api->launch_kernel
        )
        && load_symbol(
            api->library,
            "cuCtxSynchronize",
            &api->context_synchronize
        )
        && load_symbol(
            api->library,
            "cuModuleUnload",
            &api->module_unload
        );
    if (!complete) {
        *error = "CUDA driver is missing a required symbol";
    }
    return complete;
}

constexpr char gain_phase_kernel[] = R"cuda(
struct Result {
    unsigned int basis_index;
    unsigned int target_index;
    unsigned int source_offset;
    int gain_q15;
    int end_gain_q15;
    unsigned int transform_flags;
    unsigned long long squared_error;
    unsigned long long target_energy;
};

__device__ long long round_divide_away(
    long long numerator,
    long long denominator
) {
    if (numerator >= 0) {
        return (numerator + denominator / 2) / denominator;
    }
    return -((-numerator + denominator / 2) / denominator);
}

__device__ long long interpolated_gain(
    long long start,
    long long end,
    unsigned int sample,
    unsigned int count
) {
    if (count <= 1U) {
        return start;
    }
    return start + round_divide_away(
        (end - start) * (long long)sample,
        (long long)(count - 1U)
    );
}

extern "C" __global__ void exhaustive_gain_phase(
    const short* blocks,
    unsigned int block_count,
    unsigned int block_samples,
    unsigned long long first_candidate,
    unsigned long long candidate_count,
    Result* output
) {
    const unsigned long long local =
        (unsigned long long)blockIdx.x * blockDim.x + threadIdx.x;
    if (local >= candidate_count) {
        return;
    }
    const unsigned long long candidate = first_candidate + local;
    const bool reverse = candidate % 2ULL != 0ULL;
    const unsigned long long direction = candidate / 2ULL;
    const unsigned long long offset = direction % block_samples;
    const unsigned long long pair = direction / block_samples;
    const unsigned long long basis_index = pair / (block_count - 1U);
    const unsigned long long target_slot = pair % (block_count - 1U);
    const unsigned long long target_index =
        target_slot >= basis_index ? target_slot + 1U : target_slot;
    const short* basis = blocks + basis_index * block_samples;
    const short* target = blocks + target_index * block_samples;

    long long basis_energy = 0;
    long long target_energy = 0;
    long long correlation = 0;
    for (unsigned int sample = 0; sample < block_samples; ++sample) {
        const unsigned long long source_index = reverse
            ? (
                offset + block_samples
                - sample % block_samples
            ) % block_samples
            : (sample + offset) % block_samples;
        const long long left = basis[source_index];
        const long long right = target[sample];
        basis_energy += left * left;
        target_energy += right * right;
        correlation += left * right;
    }

    long long fitted_gain = 0;
    if (basis_energy != 0) {
        fitted_gain = round_divide_away(
            correlation * 32768LL,
            basis_energy
        );
        fitted_gain = fitted_gain < -32768LL ? -32768LL : fitted_gain;
        fitted_gain = fitted_gain > 32768LL ? 32768LL : fitted_gain;
    }

    long long gain = fitted_gain;
    long long end_gain = 0;
    unsigned int transform_flags = reverse ? 2U : 0U;
    unsigned long long squared_error = ~0ULL;
    long long first_gain = fitted_gain - 8LL;
    long long final_gain = fitted_gain + 8LL;
    first_gain = first_gain < -32768LL ? -32768LL : first_gain;
    final_gain = final_gain > 32768LL ? 32768LL : final_gain;
    for (
        long long candidate_gain = first_gain;
        candidate_gain <= final_gain;
        ++candidate_gain
    ) {
        unsigned long long candidate_error = 0;
        for (unsigned int sample = 0; sample < block_samples; ++sample) {
            const unsigned long long source_index = reverse
                ? (
                    offset + block_samples
                    - sample % block_samples
                ) % block_samples
                : (sample + offset) % block_samples;
            const long long product =
                (long long)basis[source_index] * candidate_gain;
            const long long predicted =
                round_divide_away(product, 32768LL);
            const long long difference =
                (long long)target[sample] - predicted;
            candidate_error +=
                (unsigned long long)(difference * difference);
        }
        const long long candidate_abs =
            candidate_gain < 0 ? -candidate_gain : candidate_gain;
        const long long best_abs = gain < 0 ? -gain : gain;
        if (
            candidate_error < squared_error
            || (
                candidate_error == squared_error
                && (
                    candidate_abs < best_abs
                    || (
                        candidate_abs == best_abs
                        && candidate_gain < gain
                    )
                )
            )
        ) {
            gain = candidate_gain;
            end_gain = 0;
            transform_flags = reverse ? 2U : 0U;
            squared_error = candidate_error;
        }
    }

    if (block_samples > 1U) {
        double aa = 0.0;
        double ab = 0.0;
        double bb = 0.0;
        double ay = 0.0;
        double by = 0.0;
        const double denominator = (double)(block_samples - 1U);
        for (unsigned int sample = 0; sample < block_samples; ++sample) {
            const double position = (double)sample / denominator;
            const unsigned long long source_index = reverse
                ? (
                    offset + block_samples
                    - sample % block_samples
                ) % block_samples
                : (sample + offset) % block_samples;
            const double aligned = (double)basis[source_index];
            const double first = aligned * (1.0 - position);
            const double second = aligned * position;
            const double scaled_target = (double)target[sample] * 32768.0;
            aa += first * first;
            ab += first * second;
            bb += second * second;
            ay += first * scaled_target;
            by += second * scaled_target;
        }
        const double determinant = aa * bb - ab * ab;
        const double determinant_floor =
            (aa * bb > 1.0 ? aa * bb : 1.0) * 1.0e-12;
        if (determinant > determinant_floor) {
            const double raw_start = (ay * bb - by * ab) / determinant;
            const double raw_end = (by * aa - ay * ab) / determinant;
            long long fitted_start = (long long)(
                raw_start + (raw_start >= 0.0 ? 0.5 : -0.5)
            );
            long long fitted_end = (long long)(
                raw_end + (raw_end >= 0.0 ? 0.5 : -0.5)
            );
            fitted_start =
                fitted_start < -32768LL ? -32768LL : fitted_start;
            fitted_start =
                fitted_start > 32768LL ? 32768LL : fitted_start;
            fitted_end = fitted_end < -32768LL ? -32768LL : fitted_end;
            fitted_end = fitted_end > 32768LL ? 32768LL : fitted_end;
            long long first_start = fitted_start - 8LL;
            long long final_start = fitted_start + 8LL;
            long long first_end = fitted_end - 8LL;
            long long final_end = fitted_end + 8LL;
            first_start = first_start < -32768LL ? -32768LL : first_start;
            final_start = final_start > 32768LL ? 32768LL : final_start;
            first_end = first_end < -32768LL ? -32768LL : first_end;
            final_end = final_end > 32768LL ? 32768LL : final_end;
            for (
                long long candidate_start = first_start;
                candidate_start <= final_start;
                ++candidate_start
            ) {
                for (
                    long long candidate_end = first_end;
                    candidate_end <= final_end;
                    ++candidate_end
                ) {
                    unsigned long long candidate_error = 0;
                    for (
                        unsigned int sample = 0;
                        sample < block_samples;
                        ++sample
                    ) {
                        const long long current_gain = interpolated_gain(
                            candidate_start,
                            candidate_end,
                            sample,
                            block_samples
                        );
                        const unsigned long long source_index = reverse
                            ? (
                                offset + block_samples
                                - sample % block_samples
                            ) % block_samples
                            : (sample + offset) % block_samples;
                        const long long product =
                            (long long)basis[source_index] * current_gain;
                        const long long predicted =
                            round_divide_away(product, 32768LL);
                        const long long difference =
                            (long long)target[sample] - predicted;
                        candidate_error +=
                            (unsigned long long)(difference * difference);
                    }
                    if (candidate_error < squared_error) {
                        gain = candidate_start;
                        end_gain = candidate_end;
                        transform_flags = 1U | (reverse ? 2U : 0U);
                        squared_error = candidate_error;
                    }
                }
            }
        }
    }
    output[local] = {
        (unsigned int)basis_index,
        (unsigned int)target_index,
        (unsigned int)offset,
        (int)gain,
        (int)end_gain,
        transform_flags,
        squared_error,
        (unsigned long long)target_energy
    };
}
)cuda";

struct cuda_resources {
    cuda_api* api = nullptr;
    cuda_device device = 0;
    bool retained = false;
    cuda_module module = nullptr;
    cuda_device_ptr input = 0U;
    cuda_device_ptr output = 0U;

    ~cuda_resources() {
        if (api == nullptr) {
            return;
        }
        if (output != 0U) {
            api->memory_free(output);
        }
        if (input != 0U) {
            api->memory_free(input);
        }
        if (module != nullptr) {
            api->module_unload(module);
        }
        if (retained) {
            api->primary_context_release(device);
        }
    }
};

resonith_foundry_status compile_kernel(
    nvrtc_api& api,
    int compute_major,
    int compute_minor,
    std::vector<char>* image,
    std::string* error
) {
    nvrtc_program program = nullptr;
    nvrtc_result status = api.create_program(
        &program,
        gain_phase_kernel,
        "resonith_foundry_gain_phase.cu",
        0,
        nullptr,
        nullptr
    );
    if (status != nvrtc_success) {
        *error = "NVRTC could not create the Foundry program";
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    const std::string architecture =
        "--gpu-architecture=sm_"
        + std::to_string(compute_major)
        + std::to_string(compute_minor);
    const std::array<const char*, 3> options{
        "--std=c++23",
        architecture.c_str(),
        "--fmad=false",
    };
    status = api.compile_program(
        program,
        static_cast<int>(options.size()),
        options.data()
    );
    std::size_t log_size = 0U;
    api.log_size(program, &log_size);
    std::vector<char> log(std::max<std::size_t>(1U, log_size), '\0');
    if (log_size != 0U) {
        api.get_log(program, log.data());
    }
    if (status != nvrtc_success) {
        *error = "NVRTC compilation failed: ";
        error->append(log.data());
        api.destroy_program(&program);
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    std::size_t image_size = 0U;
    if (
        api.cubin_size(program, &image_size) != nvrtc_success
        || image_size == 0U
    ) {
        *error = "NVRTC produced no device binary";
        api.destroy_program(&program);
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    image->resize(image_size);
    if (api.get_cubin(program, image->data()) != nvrtc_success) {
        *error = "NVRTC could not return the device binary";
        api.destroy_program(&program);
        return RESONITH_FOUNDRY_COMPILATION_FAILED;
    }
    api.destroy_program(&program);
    return RESONITH_FOUNDRY_OK;
}

#endif

}  // namespace

extern "C" resonith_foundry_status
resonith_foundry_gain_phase_candidate_count(
    std::uint32_t block_count,
    std::uint32_t block_samples,
    std::uint64_t* candidate_count
) {
    if (
        candidate_count == nullptr
        || block_count < 2U
        || block_samples == 0U
    ) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t pair_count = 0U;
    if (
        !multiply_fits(block_count, block_count - 1U, &pair_count)
        || !multiply_fits(pair_count, block_samples, candidate_count)
        || !multiply_fits(
            *candidate_count,
            direction_count,
            candidate_count
        )
    ) {
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    return RESONITH_FOUNDRY_OK;
}

extern "C" resonith_foundry_status resonith_foundry_gain_phase_cpu(
    const std::int16_t* blocks,
    std::size_t block_element_count,
    const resonith_foundry_gain_phase_range* range,
    resonith_foundry_gain_phase_result* output,
    std::size_t output_capacity
) {
    if (blocks == nullptr || range == nullptr || output == nullptr) {
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t total_candidates = 0U;
    const resonith_foundry_status status = validate_range(
        block_element_count,
        *range,
        output_capacity,
        &total_candidates
    );
    if (status != RESONITH_FOUNDRY_OK) {
        return status;
    }
    for (
        std::uint64_t local = 0U;
        local < range->candidate_count;
        ++local
    ) {
        output[local] = evaluate_candidate(
            blocks,
            *range,
            range->first_candidate + local
        );
    }
    return RESONITH_FOUNDRY_OK;
}

extern "C" resonith_foundry_status resonith_foundry_gain_phase_cuda(
    const std::int16_t* blocks,
    std::size_t block_element_count,
    const resonith_foundry_gain_phase_range* range,
    resonith_foundry_gain_phase_result* output,
    std::size_t output_capacity,
    const char* nvrtc_library_directory,
    resonith_foundry_cuda_evidence* evidence,
    char* error,
    std::size_t error_capacity
) {
    if (error != nullptr && error_capacity != 0U) {
        error[0] = '\0';
    }
    if (
        blocks == nullptr
        || range == nullptr
        || output == nullptr
        || evidence == nullptr
    ) {
        copy_error("invalid Foundry argument", error, error_capacity);
        return RESONITH_FOUNDRY_INVALID_ARGUMENT;
    }
    std::uint64_t total_candidates = 0U;
    const resonith_foundry_status range_status = validate_range(
        block_element_count,
        *range,
        output_capacity,
        &total_candidates
    );
    if (range_status != RESONITH_FOUNDRY_OK) {
        copy_error("invalid Foundry candidate range", error, error_capacity);
        return range_status;
    }
    std::memset(evidence, 0, sizeof(*evidence));
#if !defined(_WIN32)
    (void)nvrtc_library_directory;
    copy_error(
        "this build has no CUDA dynamic-loader implementation",
        error,
        error_capacity
    );
    return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
#else
    nvrtc_api nvrtc{};
    cuda_api cuda{};
    std::string detail;
    if (!load_nvrtc(nvrtc_library_directory, &nvrtc, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    if (!load_cuda(&cuda, &detail)) {
        copy_error(detail, error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    int compiler_major = 0;
    int compiler_minor = 0;
    if (
        nvrtc.version(&compiler_major, &compiler_minor) != nvrtc_success
        || cuda.init(0U) != cuda_success
    ) {
        copy_error("cannot initialize NVRTC/CUDA", error, error_capacity);
        return RESONITH_FOUNDRY_BACKEND_UNAVAILABLE;
    }
    cuda_resources resources{};
    resources.api = &cuda;
    int compute_major = 0;
    int compute_minor = 0;
    if (
        cuda.device_get(&resources.device, 0) != cuda_success
        || cuda.device_compute_capability(
            &compute_major,
            &compute_minor,
            resources.device
        ) != cuda_success
    ) {
        copy_error("cannot query CUDA device 0", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    evidence->nvrtc_major = static_cast<std::uint32_t>(compiler_major);
    evidence->nvrtc_minor = static_cast<std::uint32_t>(compiler_minor);
    evidence->compute_major = static_cast<std::uint32_t>(compute_major);
    evidence->compute_minor = static_cast<std::uint32_t>(compute_minor);
    std::size_t device_memory = 0U;
    cuda.device_total_memory(&device_memory, resources.device);
    evidence->device_memory_bytes = device_memory;
    cuda.device_name(
        evidence->device_name,
        static_cast<int>(sizeof(evidence->device_name)),
        resources.device
    );
    evidence->device_name[sizeof(evidence->device_name) - 1U] = '\0';
    evidence->first_candidate = range->first_candidate;
    evidence->candidate_count = range->candidate_count;
    evidence->input_bytes =
        block_element_count * sizeof(std::int16_t);
    evidence->output_bytes =
        range->candidate_count
        * sizeof(resonith_foundry_gain_phase_result);

    std::vector<char> device_image;
    const resonith_foundry_status compile_status = compile_kernel(
        nvrtc,
        compute_major,
        compute_minor,
        &device_image,
        &detail
    );
    if (compile_status != RESONITH_FOUNDRY_OK) {
        copy_error(detail, error, error_capacity);
        return compile_status;
    }
    cuda_context context = nullptr;
    if (
        cuda.primary_context_retain(&context, resources.device)
        != cuda_success
    ) {
        copy_error("cannot retain the CUDA primary context", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    resources.retained = true;
    if (cuda.context_set_current(context) != cuda_success) {
        copy_error("cannot activate the CUDA primary context", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    cuda_function function = nullptr;
    if (
        cuda.module_load_data(
            &resources.module,
            device_image.data()
        ) != cuda_success
        || cuda.module_get_function(
            &function,
            resources.module,
            "exhaustive_gain_phase"
        ) != cuda_success
    ) {
        copy_error("cannot load the Foundry CUDA kernel", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    const std::size_t input_bytes =
        block_element_count * sizeof(std::int16_t);
    const std::size_t output_bytes =
        static_cast<std::size_t>(range->candidate_count)
        * sizeof(resonith_foundry_gain_phase_result);
    if (
        cuda.memory_allocate(&resources.input, input_bytes) != cuda_success
        || cuda.memory_allocate(&resources.output, output_bytes)
            != cuda_success
        || cuda.copy_host_to_device(
            resources.input,
            blocks,
            input_bytes
        ) != cuda_success
    ) {
        copy_error("cannot allocate/copy Foundry CUDA buffers", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }

    const unsigned int threads = 128U;
    const std::uint64_t grid64 =
        (range->candidate_count + threads - 1U) / threads;
    if (grid64 > std::numeric_limits<unsigned int>::max()) {
        copy_error("CUDA tile exceeds the one-dimensional grid", error, error_capacity);
        return RESONITH_FOUNDRY_RANGE_OVERFLOW;
    }
    std::uint32_t block_count = range->block_count;
    std::uint32_t block_samples = range->block_samples;
    std::uint64_t first_candidate = range->first_candidate;
    std::uint64_t candidate_count = range->candidate_count;
    void* arguments[] = {
        &resources.input,
        &block_count,
        &block_samples,
        &first_candidate,
        &candidate_count,
        &resources.output,
    };
    if (
        cuda.launch_kernel(
            function,
            static_cast<unsigned int>(grid64),
            1U,
            1U,
            threads,
            1U,
            1U,
            0U,
            nullptr,
            arguments,
            nullptr
        ) != cuda_success
        || cuda.context_synchronize() != cuda_success
        || cuda.copy_device_to_host(
            output,
            resources.output,
            output_bytes
        ) != cuda_success
    ) {
        copy_error("Foundry CUDA kernel execution failed", error, error_capacity);
        return RESONITH_FOUNDRY_DEVICE_FAILED;
    }
    return RESONITH_FOUNDRY_OK;
#endif
}

extern "C" const char* resonith_foundry_status_string(
    resonith_foundry_status status
) {
    switch (status) {
        case RESONITH_FOUNDRY_OK:
            return "ok";
        case RESONITH_FOUNDRY_INVALID_ARGUMENT:
            return "invalid argument";
        case RESONITH_FOUNDRY_OUTPUT_TOO_SMALL:
            return "output too small";
        case RESONITH_FOUNDRY_BACKEND_UNAVAILABLE:
            return "backend unavailable";
        case RESONITH_FOUNDRY_COMPILATION_FAILED:
            return "compilation failed";
        case RESONITH_FOUNDRY_DEVICE_FAILED:
            return "device failed";
        case RESONITH_FOUNDRY_RANGE_OVERFLOW:
            return "range overflow";
    }
    return "unknown";
}
