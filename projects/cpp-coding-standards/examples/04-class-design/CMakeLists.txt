add_executable(class_design_demo
    class_design_demo.cpp
    good_class_design.cpp
    bad_class_design.cpp
)

target_link_libraries(class_design_demo PRIVATE
    cpp_standards_common
)

target_include_directories(class_design_demo PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)
