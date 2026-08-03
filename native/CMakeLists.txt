cmake_minimum_required(VERSION 3.20)

project(resonith_core VERSION 0.1.0 LANGUAGES C CXX)

option(RESONITH_WARNINGS_AS_ERRORS "Treat native-core warnings as errors" ON)
option(RESONITH_BUILD_SHARED "Build the shared Resonith Core library" ON)
option(RESONITH_BUILD_FUZZERS "Build Clang libFuzzer security targets" OFF)
option(RESONITH_BUILD_TOOLS "Build native measurement tools" ON)
option(
    RESONITH_BUILD_CUDA_FOUNDRY
    "Build the optional exhaustive CUDA Foundry backend"
    OFF
)

set(RESONITH_CORE_SOURCES
    src/basis.cpp
    src/cibs.cpp
    src/composition.cpp
    src/container.cpp
    src/integrity.cpp
    src/lapped.cpp
    src/lapped_compact.cpp
    src/lapped_finite.cpp
    src/lapped_packet.cpp
    src/liftpack.cpp
    src/maf.cpp
    src/maf_typed.cpp
    src/multichannel.cpp
    src/partial_graph.cpp
    src/persistent_cell.cpp
    src/seek.cpp
    src/status.cpp
    src/stream.cpp
    src/trajectory.cpp
)

add_library(resonith_core STATIC
    ${RESONITH_CORE_SOURCES}
)
add_library(Resonith::Core ALIAS resonith_core)

target_compile_features(resonith_core PUBLIC cxx_std_23)
target_include_directories(resonith_core
    PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include>"
)
set_target_properties(resonith_core PROPERTIES
    CXX_EXTENSIONS OFF
    POSITION_INDEPENDENT_CODE ON
)

# Keep the public C ABI deployable on a stock Windows installation. Consumers
# of the static Core inherit the same self-contained runtime contract.
if(MINGW)
    target_link_options(resonith_core INTERFACE -static)
endif()

if(RESONITH_BUILD_SHARED)
    add_library(resonith_core_shared SHARED
        ${RESONITH_CORE_SOURCES}
    )
    add_library(Resonith::CoreShared ALIAS resonith_core_shared)
    target_compile_features(resonith_core_shared PUBLIC cxx_std_23)
    target_include_directories(resonith_core_shared
        PUBLIC
            "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
            "$<INSTALL_INTERFACE:include>"
    )
    target_compile_definitions(resonith_core_shared
        PUBLIC RESONITH_SHARED
        PRIVATE RESONITH_BUILDING_LIBRARY
    )
    set_target_properties(resonith_core_shared PROPERTIES
        CXX_EXTENSIONS OFF
        POSITION_INDEPENDENT_CODE ON
    )
    if(MINGW)
        target_link_options(resonith_core_shared PRIVATE -static)
    endif()
endif()

function(resonith_enable_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4)
        if(RESONITH_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE /WX)
        endif()
    else()
        target_compile_options(${target} PRIVATE
            -Wall
            -Wextra
            -Wconversion
            -Wpedantic
            -Wshadow
        )
        if(RESONITH_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE -Werror)
        endif()
    endif()
endfunction()

resonith_enable_warnings(resonith_core)
if(RESONITH_BUILD_SHARED)
    resonith_enable_warnings(resonith_core_shared)
endif()
if(MSVC)
    target_compile_options(resonith_core PRIVATE /permissive-)
    if(RESONITH_BUILD_SHARED)
        target_compile_options(resonith_core_shared PRIVATE /permissive-)
    endif()
endif()

if(RESONITH_BUILD_CUDA_FOUNDRY)
    add_library(resonith_foundry_cuda SHARED
        src/foundry_cuda.cpp
    )
    add_library(Resonith::FoundryCuda ALIAS resonith_foundry_cuda)
    target_compile_features(resonith_foundry_cuda PUBLIC cxx_std_23)
    target_include_directories(resonith_foundry_cuda
        PUBLIC
            "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
            "$<INSTALL_INTERFACE:include>"
    )
    target_compile_definitions(resonith_foundry_cuda
        PUBLIC RESONITH_FOUNDRY_SHARED
        PRIVATE RESONITH_BUILDING_FOUNDRY
    )
    set_target_properties(resonith_foundry_cuda PROPERTIES
        CXX_EXTENSIONS OFF
        POSITION_INDEPENDENT_CODE ON
    )
    if(MINGW)
        target_link_options(resonith_foundry_cuda PRIVATE -static)
    endif()
    resonith_enable_warnings(resonith_foundry_cuda)
endif()

if(RESONITH_BUILD_TOOLS)
    add_executable(resonith_decode
        tools/decode.cpp
    )
    target_compile_features(resonith_decode PRIVATE cxx_std_23)
    target_link_libraries(resonith_decode PRIVATE Resonith::Core)
    set_target_properties(resonith_decode PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_decode)

    if(RESONITH_BUILD_CUDA_FOUNDRY)
        add_executable(resonith_foundry_cuda_test
            tests/foundry_cuda_test.cpp
        )
        target_compile_features(
            resonith_foundry_cuda_test
            PRIVATE cxx_std_23
        )
        target_link_libraries(
            resonith_foundry_cuda_test
            PRIVATE Resonith::FoundryCuda Resonith::Core
        )
        if(MINGW)
            target_link_options(
                resonith_foundry_cuda_test
                PRIVATE -static
            )
        endif()
        set_target_properties(
            resonith_foundry_cuda_test
            PROPERTIES CXX_EXTENSIONS OFF
        )
        resonith_enable_warnings(resonith_foundry_cuda_test)

        add_executable(resonith_foundry_c_header_test
            tests/foundry_c_header_test.c
        )
        target_compile_features(
            resonith_foundry_c_header_test
            PRIVATE c_std_99
        )
        target_link_libraries(
            resonith_foundry_c_header_test
            PRIVATE Resonith::FoundryCuda
        )
        if(MINGW)
            target_link_options(
                resonith_foundry_c_header_test
                PRIVATE -static
            )
        endif()
        add_test(
            NAME foundry_c_header_compatibility
            COMMAND resonith_foundry_c_header_test
        )
    endif()

    add_executable(resonith_lapped_device_bench
        tools/lapped_device_bench.cpp
    )
    target_compile_features(
        resonith_lapped_device_bench
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_lapped_device_bench
        PRIVATE Resonith::Core
    )
    set_target_properties(
        resonith_lapped_device_bench
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_lapped_device_bench)

    add_executable(resonith_lapped_finite_bench
        tools/lapped_finite_bench.cpp
    )
    target_compile_features(
        resonith_lapped_finite_bench
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_lapped_finite_bench
        PRIVATE Resonith::Core
    )
    set_target_properties(
        resonith_lapped_finite_bench
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_lapped_finite_bench)
endif()

if(RESONITH_BUILD_FUZZERS)
    if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        message(FATAL_ERROR "RESONITH_BUILD_FUZZERS requires Clang")
    endif()
    add_executable(resonith_liftpack_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/liftpack_fuzz.cpp
    )
    target_compile_features(resonith_liftpack_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_liftpack_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_liftpack_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_liftpack_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_liftpack_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_liftpack_fuzz)

    add_executable(resonith_main0_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/main0_fuzz.cpp
    )
    target_compile_features(resonith_main0_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_main0_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_main0_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_main0_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_main0_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_main0_fuzz)

    add_executable(resonith_maf_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/maf_fuzz.cpp
    )
    target_compile_features(resonith_maf_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_maf_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_maf_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_maf_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_maf_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_maf_fuzz)

    add_executable(resonith_maf_typed_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/maf_typed_fuzz.cpp
    )
    target_compile_features(resonith_maf_typed_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_maf_typed_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_maf_typed_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_maf_typed_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_maf_typed_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_maf_typed_fuzz)

    add_executable(resonith_seek_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/seek_fuzz.cpp
    )
    target_compile_features(resonith_seek_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_seek_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_seek_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_seek_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_seek_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_seek_fuzz)

    add_executable(resonith_lapped_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/lapped_fuzz.cpp
    )
    target_compile_features(resonith_lapped_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_lapped_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_lapped_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_lapped_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_lapped_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_lapped_fuzz)

    add_executable(resonith_lapped_packet_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/lapped_packet_fuzz.cpp
    )
    target_compile_features(resonith_lapped_packet_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_lapped_packet_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_lapped_packet_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_lapped_packet_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_lapped_packet_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_lapped_packet_fuzz)

    add_executable(resonith_lapped_compact_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/lapped_compact_fuzz.cpp
    )
    target_compile_features(resonith_lapped_compact_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_lapped_compact_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_lapped_compact_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_lapped_compact_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_lapped_compact_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_lapped_compact_fuzz)

    add_executable(resonith_lapped_finite_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/lapped_finite_fuzz.cpp
    )
    target_compile_features(resonith_lapped_finite_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_lapped_finite_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_lapped_finite_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    target_link_options(resonith_lapped_finite_fuzz
        PRIVATE -fsanitize=fuzzer,address,undefined
    )
    set_target_properties(
        resonith_lapped_finite_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_lapped_finite_fuzz)

    add_executable(resonith_partial_graph_fuzz
        ${RESONITH_CORE_SOURCES}
        fuzz/partial_graph_fuzz.cpp
    )
    target_compile_features(resonith_partial_graph_fuzz PRIVATE cxx_std_23)
    target_include_directories(resonith_partial_graph_fuzz
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include"
    )
    target_compile_options(resonith_partial_graph_fuzz
        PRIVATE
            -fsanitize=fuzzer,address,undefined
            -fno-sanitize=vptr
    )
    target_link_options(resonith_partial_graph_fuzz
        PRIVATE
            -fsanitize=fuzzer,address,undefined
            -fno-sanitize=vptr
    )
    set_target_properties(
        resonith_partial_graph_fuzz
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_partial_graph_fuzz)
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(resonith_liftpack_test
        tests/liftpack_test.cpp
    )
    target_compile_features(resonith_liftpack_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_liftpack_test PRIVATE Resonith::Core)
    set_target_properties(resonith_liftpack_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_liftpack_test)
    add_test(NAME liftpack_conformance COMMAND resonith_liftpack_test)

    add_executable(resonith_c_header_test
        tests/c_header_test.c
    )
    target_compile_features(resonith_c_header_test PRIVATE c_std_99)
    target_link_libraries(resonith_c_header_test PRIVATE Resonith::Core)
    set_target_properties(resonith_c_header_test PROPERTIES C_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_c_header_test)
    add_test(NAME c_header_compatibility COMMAND resonith_c_header_test)

    if(RESONITH_BUILD_SHARED)
        # This target is intentionally separate from the static C-header gate.
        # Mobile CI executes it with the packaged shared library, proving that
        # the public C ABI is exported and dynamically loadable.
        add_executable(resonith_c_header_shared_test
            tests/c_header_test.c
        )
        target_compile_features(
            resonith_c_header_shared_test
            PRIVATE c_std_99
        )
        target_link_libraries(
            resonith_c_header_shared_test
            PRIVATE Resonith::CoreShared
        )
        set_target_properties(
            resonith_c_header_shared_test
            PROPERTIES
                C_EXTENSIONS OFF
                LINKER_LANGUAGE CXX
        )
        resonith_enable_warnings(resonith_c_header_shared_test)
        add_test(
            NAME c_header_shared_compatibility
            COMMAND resonith_c_header_shared_test
        )
    endif()

    add_executable(resonith_cibs_test
        tests/cibs_test.cpp
    )
    target_compile_features(resonith_cibs_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_cibs_test PRIVATE Resonith::Core)
    set_target_properties(resonith_cibs_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_cibs_test)
    add_test(NAME cibs_conformance COMMAND resonith_cibs_test)

    add_executable(resonith_trajectory_test
        tests/trajectory_test.cpp
    )
    target_compile_features(resonith_trajectory_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_trajectory_test PRIVATE Resonith::Core)
    set_target_properties(
        resonith_trajectory_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_trajectory_test)
    add_test(NAME trajectory_conformance COMMAND resonith_trajectory_test)

    add_executable(resonith_composition_test
        tests/composition_test.cpp
    )
    target_compile_features(resonith_composition_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_composition_test PRIVATE Resonith::Core)
    set_target_properties(
        resonith_composition_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_composition_test)
    add_test(NAME composition_conformance COMMAND resonith_composition_test)

    add_executable(resonith_basis_test
        tests/basis_test.cpp
    )
    target_compile_features(resonith_basis_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_basis_test PRIVATE Resonith::Core)
    set_target_properties(resonith_basis_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_basis_test)
    add_test(NAME basis_conformance COMMAND resonith_basis_test)

    add_executable(resonith_pipeline_test
        tests/pipeline_test.cpp
    )
    target_compile_features(resonith_pipeline_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_pipeline_test PRIVATE Resonith::Core)
    set_target_properties(resonith_pipeline_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_pipeline_test)
    add_test(NAME causal_pipeline_conformance COMMAND resonith_pipeline_test)

    add_executable(resonith_player_test
        tests/player_test.cpp
    )
    target_compile_features(resonith_player_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_player_test PRIVATE Resonith::Core)
    set_target_properties(resonith_player_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_player_test)
    add_test(NAME block_player_conformance COMMAND resonith_player_test)

    add_executable(resonith_seek_test
        tests/seek_test.cpp
    )
    target_compile_features(resonith_seek_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_seek_test PRIVATE Resonith::Core)
    set_target_properties(resonith_seek_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_seek_test)
    add_test(NAME seek_sidecar_conformance COMMAND resonith_seek_test)

    add_executable(resonith_lapped_test
        tests/lapped_test.cpp
    )
    target_compile_features(resonith_lapped_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_lapped_test PRIVATE Resonith::Core)
    set_target_properties(resonith_lapped_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_lapped_test)
    add_test(NAME lapped_conformance COMMAND resonith_lapped_test)

    add_executable(resonith_maf_test
        tests/maf_test.cpp
    )
    target_compile_features(resonith_maf_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_maf_test PRIVATE Resonith::Core)
    set_target_properties(resonith_maf_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_maf_test)
    add_test(NAME maf_dsp_conformance COMMAND resonith_maf_test)

    add_executable(resonith_persistent_cell_test
        tests/persistent_cell_test.cpp
    )
    target_compile_features(resonith_persistent_cell_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_persistent_cell_test PRIVATE Resonith::Core)
    set_target_properties(
        resonith_persistent_cell_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_persistent_cell_test)
    add_test(NAME persistent_cell_conformance COMMAND resonith_persistent_cell_test)

    add_executable(resonith_maf_typed_test
        tests/maf_typed_test.cpp
    )
    target_compile_features(resonith_maf_typed_test PRIVATE cxx_std_23)
    target_link_libraries(resonith_maf_typed_test PRIVATE Resonith::Core)
    set_target_properties(
        resonith_maf_typed_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_maf_typed_test)
    add_test(NAME maf_typed_conformance COMMAND resonith_maf_typed_test)

    add_executable(resonith_partial_graph_test
        tests/partial_graph_test.cpp
    )
    target_compile_features(
        resonith_partial_graph_test
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_partial_graph_test
        PRIVATE Resonith::Core
    )
    target_include_directories(
        resonith_partial_graph_test
        PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src"
    )
    set_target_properties(
        resonith_partial_graph_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_partial_graph_test)
    add_test(
        NAME partial_graph_conformance
        COMMAND resonith_partial_graph_test
    )

    add_executable(resonith_partial_graph_allocation_tripwire_test
        tests/partial_graph_allocation_tripwire_test.cpp
    )
    target_compile_features(
        resonith_partial_graph_allocation_tripwire_test
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_partial_graph_allocation_tripwire_test
        PRIVATE Resonith::Core
    )
    set_target_properties(
        resonith_partial_graph_allocation_tripwire_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(
        resonith_partial_graph_allocation_tripwire_test
    )
    add_test(
        NAME partial_graph_allocation_tripwire
        COMMAND resonith_partial_graph_allocation_tripwire_test
    )

    add_executable(resonith_partial_graph_allocation_ordinal_test
        tests/partial_graph_allocation_ordinal_test.cpp
    )
    target_compile_features(
        resonith_partial_graph_allocation_ordinal_test
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_partial_graph_allocation_ordinal_test
        PRIVATE Resonith::Core
    )
    set_target_properties(
        resonith_partial_graph_allocation_ordinal_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(
        resonith_partial_graph_allocation_ordinal_test
    )
    add_test(
        NAME partial_graph_allocation_ordinal
        COMMAND resonith_partial_graph_allocation_ordinal_test
    )

    add_executable(resonith_r203_state_arena_hostile_witness
        tests/r203_state_arena_hostile_witness.cpp
    )
    target_compile_features(
        resonith_r203_state_arena_hostile_witness
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_r203_state_arena_hostile_witness
        PRIVATE Resonith::Core
    )
    set_target_properties(
        resonith_r203_state_arena_hostile_witness
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(
        resonith_r203_state_arena_hostile_witness
    )
    add_test(
        NAME r203_state_arena_hostile
        COMMAND resonith_r203_state_arena_hostile_witness
    )

    find_package(Threads REQUIRED)
    add_executable(resonith_partial_graph_concurrency_test
        tests/partial_graph_concurrency_test.cpp
    )
    target_compile_features(
        resonith_partial_graph_concurrency_test
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_partial_graph_concurrency_test
        PRIVATE Resonith::Core Threads::Threads
    )
    set_target_properties(
        resonith_partial_graph_concurrency_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(
        resonith_partial_graph_concurrency_test
    )
    add_test(
        NAME partial_graph_concurrency
        COMMAND resonith_partial_graph_concurrency_test
    )

    add_executable(resonith_partial_graph_fuzz_smoke
        fuzz/partial_graph_fuzz.cpp
        tests/partial_graph_fuzz_smoke.cpp
    )
    target_compile_features(
        resonith_partial_graph_fuzz_smoke
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_partial_graph_fuzz_smoke
        PRIVATE Resonith::Core
    )
    set_target_properties(
        resonith_partial_graph_fuzz_smoke
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_partial_graph_fuzz_smoke)
    add_test(
        NAME partial_graph_adversarial_smoke
        COMMAND resonith_partial_graph_fuzz_smoke
    )

    add_executable(resonith_maf_fuzz_smoke
        fuzz/maf_fuzz.cpp
        tests/maf_fuzz_smoke.cpp
    )
    target_compile_features(resonith_maf_fuzz_smoke PRIVATE cxx_std_23)
    target_link_libraries(resonith_maf_fuzz_smoke PRIVATE Resonith::Core)
    set_target_properties(
        resonith_maf_fuzz_smoke
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_maf_fuzz_smoke)
    add_test(NAME maf_adversarial_smoke COMMAND resonith_maf_fuzz_smoke)

    add_executable(resonith_maf_typed_fuzz_smoke
        fuzz/maf_typed_fuzz.cpp
        tests/maf_typed_fuzz_smoke.cpp
    )
    target_compile_features(
        resonith_maf_typed_fuzz_smoke
        PRIVATE cxx_std_23
    )
    target_link_libraries(
        resonith_maf_typed_fuzz_smoke
        PRIVATE Resonith::Core
    )
    set_target_properties(
        resonith_maf_typed_fuzz_smoke
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_maf_typed_fuzz_smoke)
    add_test(
        NAME maf_typed_adversarial_smoke
        COMMAND resonith_maf_typed_fuzz_smoke
    )
endif()
