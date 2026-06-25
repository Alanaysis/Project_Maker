# Boost 工具库示例
find_package(Boost REQUIRED COMPONENTS filesystem regex)

# 字符串算法示例
add_executable(boost_string_algo string_algo_example.cpp)
target_link_libraries(boost_string_algo PRIVATE Boost::boost)

# 文件系统示例
add_executable(boost_filesystem filesystem_example.cpp)
target_link_libraries(boost_filesystem PRIVATE Boost::filesystem)