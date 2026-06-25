/**
 * @file tcp_client_example.cpp
 * @brief Boost.Asio TCP 客户端示例
 * @details 展示如何使用 Boost.Asio 创建 TCP 客户端
 */

#include <iostream>
#include <string>
#include <boost/asio.hpp>

using boost::asio::ip::tcp;

/**
 * @brief 基础 TCP 客户端示例
 * @details 创建简单的 TCP 客户端
 */
void basic_client() {
    std::cout << "=== 基础 TCP 客户端 ===" << std::endl;

    try {
        boost::asio::io_context io_context;

        // 创建端点
        tcp::endpoint endpoint(boost::asio::ip::address::from_string("127.0.0.1"), 8080);

        // 创建套接字
        tcp::socket socket(io_context);

        // 连接到服务器
        socket.connect(endpoint);

        std::cout << "Connected to server" << std::endl;

        // 发送数据
        std::string message = "Hello, Server!";
        boost::asio::write(socket, boost::asio::buffer(message));

        std::cout << "Sent: " << message << std::endl;

        // 接收响应
        char reply[1024];
        size_t reply_length = socket.read_some(boost::asio::buffer(reply));

        std::cout << "Received: " << std::string(reply, reply_length) << std::endl;

        // 关闭连接
        socket.close();

    } catch (std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
    }
}

/**
 * @brief 异步 TCP 客户端示例
 * @details 展示异步 TCP 客户端的使用
 */
void async_client() {
    std::cout << "=== 异步 TCP 客户端 ===" << std::endl;

    try {
        boost::asio::io_context io_context;

        // 创建端点
        tcp::endpoint endpoint(boost::asio::ip::address::from_string("127.0.0.1"), 8080);

        // 创建套接字
        tcp::socket socket(io_context);

        // 异步连接
        socket.async_connect(endpoint,
            [&socket](const boost::system::error_code& error) {
                if (!error) {
                    std::cout << "Connected to server" << std::endl;

                    // 发送数据
                    std::string message = "Hello, Server!";
                    boost::asio::write(socket, boost::asio::buffer(message));

                    std::cout << "Sent: " << message << std::endl;
                } else {
                    std::cerr << "Connection failed: " << error.message() << std::endl;
                }
            });

        // 运行 io_context
        io_context.run();

    } catch (std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
    }
}

/**
 * @brief Boost.Asio 概念说明
 * @details 介绍 Boost.Asio 的核心概念
 */
void asio_concepts() {
    std::cout << "=== Boost.Asio 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "核心概念：" << std::endl;
    std::cout << "  - io_context: I/O 上下文，管理异步操作" << std::endl;
    std::cout << "  - socket: 网络套接字" << std::endl;
    std::cout << "  - endpoint: 网络端点（IP + 端口）" << std::endl;
    std::cout << "  - async_*: 异步操作函数" << std::endl;
    std::cout << std::endl;

    std::cout << "同步 vs 异步：" << std::endl;
    std::cout << "  - 同步: 阻塞等待操作完成" << std::endl;
    std::cout << "  - 异步: 非阻塞，通过回调通知" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Asio TCP 客户端示例 ===" << std::endl;
    std::cout << std::endl;

    asio_concepts();

    std::cout << "选择运行模式：" << std::endl;
    std::cout << "1. 同步客户端" << std::endl;
    std::cout << "2. 异步客户端" << std::endl;
    std::cout << "3. 只显示概念" << std::endl;

    int choice;
    std::cin >> choice;

    switch (choice) {
        case 1:
            basic_client();
            break;
        case 2:
            async_client();
            break;
        default:
            break;
    }

    return 0;
}