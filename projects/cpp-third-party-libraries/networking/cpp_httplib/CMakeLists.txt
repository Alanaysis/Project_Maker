# cpp-httplib 示例
find_package(httplib REQUIRED)

# 服务器示例
add_executable(httplib_server server_example.cpp)
target_link_libraries(httplib_server PRIVATE httplib::httplib)

# 客户端示例
add_executable(httplib_client client_example.cpp)
target_link_libraries(httplib_client PRIVATE httplib::httplib)