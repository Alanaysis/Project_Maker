add_executable(header_files_demo
    header_files_demo.cpp
    good_header.h
    good_header.cpp
    bad_header.h
)

target_link_libraries(header_files_demo PRIVATE
    cpp_standards_common
)

target_include_directories(header_files_demo PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)
