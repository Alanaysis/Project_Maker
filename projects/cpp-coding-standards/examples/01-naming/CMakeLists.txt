add_executable(naming_demo
    naming_demo.cpp
    good_naming.cpp
    bad_naming.cpp
)

target_link_libraries(naming_demo PRIVATE
    cpp_standards_common
)

target_include_directories(naming_demo PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)
