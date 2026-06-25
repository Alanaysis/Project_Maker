add_executable(formatting_demo
    formatting_demo.cpp
    good_formatting.cpp
    bad_formatting.cpp
)

target_link_libraries(formatting_demo PRIVATE
    cpp_standards_common
)

target_include_directories(formatting_demo PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)
