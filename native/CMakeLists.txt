cmake_minimum_required(VERSION 3.20)

project(resonith_core VERSION 0.1.0 LANGUAGES C CXX)

option(RESONITH_WARNINGS_AS_ERRORS "Treat native-core warnings as errors" ON)

add_library(resonith_core STATIC
    src/cibs.cpp
    src/container.cpp
    src/integrity.cpp
    src/liftpack.cpp
    src/status.cpp
    src/trajectory.cpp
)
add_library(Resonith::Core ALIAS resonith_core)

target_compile_features(resonith_core PUBLIC cxx_std_20)
target_include_directories(resonith_core
    PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<INSTALL_INTERFACE:include>"
)
set_target_properties(resonith_core PROPERTIES
    CXX_EXTENSIONS OFF
    POSITION_INDEPENDENT_CODE ON
)

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
if(MSVC)
    target_compile_options(resonith_core PRIVATE /permissive-)
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(resonith_liftpack_test
        tests/liftpack_test.cpp
    )
    target_compile_features(resonith_liftpack_test PRIVATE cxx_std_20)
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
    target_compile_features(resonith_cibs_test PRIVATE cxx_std_20)
    target_link_libraries(resonith_cibs_test PRIVATE Resonith::Core)
    set_target_properties(resonith_cibs_test PROPERTIES CXX_EXTENSIONS OFF)
    resonith_enable_warnings(resonith_cibs_test)
    add_test(NAME cibs_conformance COMMAND resonith_cibs_test)

    add_executable(resonith_trajectory_test
        tests/trajectory_test.cpp
    )
    target_compile_features(resonith_trajectory_test PRIVATE cxx_std_20)
    target_link_libraries(resonith_trajectory_test PRIVATE Resonith::Core)
    set_target_properties(
        resonith_trajectory_test
        PROPERTIES CXX_EXTENSIONS OFF
    )
    resonith_enable_warnings(resonith_trajectory_test)
    add_test(NAME trajectory_conformance COMMAND resonith_trajectory_test)
endif()
