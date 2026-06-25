cmake_minimum_required(VERSION 3.16)
project(cpp_template_metaprogramming_advanced
    VERSION 1.0.0
    LANGUAGES CXX
    DESCRIPTION "C++ Template Metaprogramming Advanced - 高级模板元编程项目"
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ============================================================================
# Compiler flags
# ============================================================================
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror=return-type)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        add_compile_options(-fconcepts-diagnostics-depth=3)
    endif()
elseif(MSVC)
    add_compile_options(/W4 /permissive-)
endif()

# ============================================================================
# Header-only library (interface)
# ============================================================================
add_library(template_meta INTERFACE)
target_include_directories(template_meta INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_features(template_meta INTERFACE cxx_std_20)

# ============================================================================
# Helper function to add example targets
# ============================================================================
function(add_example name)
    set(target_name "example_${name}")
    add_executable(${target_name} examples/${name}.cpp)
    target_link_libraries(${target_name} PRIVATE template_meta)
    set_target_properties(${target_name} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/examples"
    )
endfunction()

function(add_test_exec name)
    set(target_name "test_${name}")
    add_executable(${target_name} tests/${name}.cpp)
    target_link_libraries(${target_name} PRIVATE template_meta)
    set_target_properties(${target_name} PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/tests"
    )
endfunction()

# ============================================================================
# Advanced Template Techniques
# ============================================================================
add_example(expression_templates)
add_example(crtp)
add_example(mixin)
add_example(policy_classes)
add_example(tag_dispatching)

# ============================================================================
# Compile-time Algorithms
# ============================================================================
add_example(compile_time_sort)
add_example(compile_time_search)
add_example(compile_time_map_filter_reduce)

# ============================================================================
# Type Computation
# ============================================================================
add_example(type_list_ops)
add_example(type_computation)

# ============================================================================
# Advanced SFINAE
# ============================================================================
add_example(sfinae_detection)
add_example(requires_expressions)

# ============================================================================
# Template Design Patterns
# ============================================================================
add_example(policy_design)
add_example(compile_time_state_machine)
add_example(compile_time_visitor)
add_example(dependency_injection)

# ============================================================================
# Applications
# ============================================================================
add_example(units_system)
add_example(matrix_operations)
add_example(serialization)
add_example(orm_basic)
add_example(compile_time_regex)

# ============================================================================
# Tests
# ============================================================================
add_test_exec(type_list)
add_test_exec(compile_time_algorithms)
add_test_exec(sfinae)
add_test_exec(applications)

# ============================================================================
# "build all" target
# ============================================================================
macro(get_all_targets var)
    set(${var})
    macro(_collect_targets dir)
        get_property(subdirs DIRECTORY ${dir} PROPERTY SUBDIRECTORIES)
        foreach(subdir ${subdirs})
            _collect_targets(${subdir})
        endforeach()
        get_property(targets DIRECTORY ${dir} PROPERTY BUILDSYSTEM_TARGETS)
        list(APPEND ${var} ${targets})
    endmacro()
    _collect_targets(${CMAKE_CURRENT_SOURCE_DIR})
endmacro()

add_custom_target(build_all_examples
    COMMENT "Building all examples..."
)

get_all_targets(all_targets)
foreach(t ${all_targets})
    if(t MATCHES "^example_")
        add_dependencies(build_all_examples ${t})
    endif()
endforeach()

# ============================================================================
# Print summary
# ============================================================================
message(STATUS "")
message(STATUS "=== C++ Template Metaprogramming Advanced ===")
message(STATUS "C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "=============================================")
message(STATUS "")
