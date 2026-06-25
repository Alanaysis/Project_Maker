# Boost.Asio 网络库示例
find_package(Boost REQUIRED COMPONENTS system)
find_package(Threads REQUIRED)

# TCP 服务器示例
add_executable(boost_asio_tcp_server tcp_server_example.cpp)
target_link_libraries(boost_asio_tcp_server PRIVATE Boost::system Threads::Threads)

# TCP 客户端示例
add_executable(boost_asio_tcp_client tcp_client_example.cpp)
target_link_libraries(boost_asio_tcp_client PRIVATE Boost::system Threads::Threads)