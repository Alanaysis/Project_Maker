/**
 * @file tcp_server_example.cpp
 * @brief Boost.Asio TCP 服务器示例
 * @details 展示如何使用 Boost.Asio 创建 TCP 服务器
 *          Boost.Asio 是一个异步 I/O 框架
 *          支持网络编程、定时器、信号处理等
 */

#include <iostream>
#include <string>
#include <memory>
#include <functional>
#include <boost/asio.hpp>

using boost::asio::ip::tcp;

/**
 * @brief TCP 会话类
 * @details 处理单个客户端连接
 */
class TcpSession : public std::enable_shared_from_this<TcpSession> {
public:
    TcpSession(tcp::socket socket) : socket_(std::move(socket)) {}

    void start() {
        do_read();
    }

private:
    void do_read() {
        auto self = shared_from_this();
        socket_.async_read_some(
            boost::asio::buffer(data_, max_length),
            [this, self](boost::system::error_code ec, std::size_t length) {
                if (!ec) {
                    std::cout << "Received: " << std::string(data_, length) << std::endl;
                    do_write(length);
                }
            });
    }

    void do_write(std::size_t length) {
        auto self = shared_from_this();
        boost::asio::async_write(
            socket_,
            boost::asio::buffer(data_, length),
            [this, self](boost::system::error_code ec, std::size_t /*bytes_transferred*/) {
                if (!ec) {
                    do_read();
                }
            });
    }

    tcp::socket socket_;
    enum { max_length = 1024 };
    char data_[max_length];
};

/**
 * @brief TCP 服务器类
 * @details 接受客户端连接
 */
class TcpServer {
public:
    TcpServer(boost::asio::io_context& io_context, short port)
        : acceptor_(io_context, tcp::endpoint(tcp::v4(), port)) {
        do_accept();
    }

private:
    void do_accept() {
        acceptor_.async_accept(
            [this](boost::system::error_code ec, tcp::socket socket) {
                if (!ec) {
                    std::cout << "Client connected" << std::endl;
                    std::make_shared<TcpSession>(std::move(socket))->start();
                }
                do_accept();
            });
    }

    tcp::acceptor acceptor_;
};

/**
 * @brief 基础服务器示例
 * @details 创建简单的 TCP 回显服务器
 */
void basic_server() {
    std::cout << "=== 基础 TCP 服务器 ===" << std::endl;

    try {
        boost::asio::io_context io_context;

        TcpServer server(io_context, 8080);

        std::cout << "Server listening on port 8080" << std::endl;
        std::cout << "Press Ctrl+C to stop" << std::endl;

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
    std::cout << "  - acceptor: 接受连接" << std::endl;
    std::cout << "  - async_*: 异步操作函数" << std::endl;
    std::cout << std::endl;

    std::cout << "异步模型：" << std::endl;
    std::cout << "  1. 发起异步操作" << std::endl;
    std::cout << "  2. 注册回调函数" << std::endl;
    std::cout << "  3. 运行 io_context" << std::endl;
    std::cout << "  4. 回调被调用" << std::endl;
    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Asio TCP 服务器示例 ===" << std::endl;
    std::cout << std::endl;

    asio_concepts();

    std::cout << "选择运行模式：" << std::endl;
    std::cout << "1. 运行服务器" << std::endl;
    std::cout << "2. 只显示概念" << std::endl;

    int choice;
    std::cin >> choice;

    if (choice == 1) {
        basic_server();
    }

    return 0;
}