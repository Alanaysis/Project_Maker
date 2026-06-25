add_executable(function_design_demo
    function_design_demo.cpp
    good_function_design.cpp
    bad_function_design.cpp
)

target_link_libraries(function_design_demo PRIVATE
    cpp_standards_common
)

target_include_directories(function_design_demo PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)
