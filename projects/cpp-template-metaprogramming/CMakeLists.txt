cmake_minimum_required(VERSION 3.16)
project(cpp-template-metaprogramming LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/include)

# Helper function to add demo executable
function(add_demo name source)
    add_executable(${name} ${source})
    target_compile_features(${name} PRIVATE cxx_std_20)
endfunction()

# 01 - Template Basics
add_demo(function_templates      src/01_template_basics/function_templates.cpp)
add_demo(class_templates         src/01_template_basics/class_templates.cpp)
add_demo(specialization          src/01_template_basics/specialization.cpp)
add_demo(non_type_params         src/01_template_basics/non_type_params.cpp)
add_demo(template_template_params src/01_template_basics/template_template_params.cpp)

# 02 - Type Traits
add_demo(basic_traits_demo       src/02_type_traits/basic_traits_demo.cpp)
add_demo(type_transform_demo     src/02_type_traits/type_transform_demo.cpp)
add_demo(type_relations_demo     src/02_type_traits/type_relations_demo.cpp)

# 03 - SFINAE
add_demo(enable_if_demo          src/03_sfinae/enable_if_demo.cpp)
add_demo(void_t_demo            src/03_sfinae/void_t_demo.cpp)
add_demo(expression_detector_demo src/03_sfinae/expression_detector_demo.cpp)

# 04 - Parameter Pack
add_demo(parameter_pack_demo     src/04_parameter_pack/parameter_pack_demo.cpp)
add_demo(fold_expressions_demo   src/04_parameter_pack/fold_expressions_demo.cpp)

# 05 - Compile Time Data
add_demo(type_list_demo          src/05_compile_time_data/type_list_demo.cpp)
add_demo(integer_sequence_demo   src/05_compile_time_data/integer_sequence_demo.cpp)
add_demo(compile_time_string_demo src/05_compile_time_data/compile_time_string_demo.cpp)

# 06 - Practical Cases
add_demo(factorial_fib_demo      src/06_practical_cases/factorial_fibonacci.cpp)
add_demo(type_erasure_demo       src/06_practical_cases/type_erasure.cpp)
add_demo(visitor_demo            src/06_practical_cases/visitor_pattern.cpp)
add_demo(dependency_injection_demo src/06_practical_cases/dependency_injection.cpp)
