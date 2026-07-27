cmake_minimum_required(VERSION 3.20)

project(resonith_core VERSION 0.1.0 LANGUAGES C CXX)

option(RESONITH_WARNINGS_AS_ERRORS "Treat native-core warnings as errors" ON)
option(RESONITH_BUILD_SHARED "Build the shared Resonith Core library" ON)
option(RESONITH_BUILD_FUZZERS "Build Clang libFuzzer security targets" OFF)
option(RESONITH_BUILD_TOOLS "Build native measurement tools" ON)

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
    src/multichannel.cpp
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

if(RESONITH_BUILD_TOOLS)
    add_executable(resonith_decode
        tools/decode.cpp
    )
    target_compile_features(resonith_decode PRIVATE cxx_std_23)
    target_link_libraries(resonith_decode PRIVATE Resonith::Core)
    set_target_properties(resonith_decode PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_decode)

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
endif()
