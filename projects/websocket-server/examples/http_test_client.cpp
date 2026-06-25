/**
 * @file http_test_client.cpp
 * @brief HTTP 测试客户端
 *
 * 用于测试 WebSocket 服务器的握手过程。
 * 发送 HTTP Upgrade 请求并验证响应。
 *
 * 使用方式：
 *   编译: g++ -std=c++17 -I../include http_test_client.cpp ../src/common.cpp -o http_test_client
 *   运行: ./http_test_client localhost 8080
 */

#include "websocket/common.h"
#include "websocket/frame.h"
#include <iostream>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>
#include <cstring>

/**
 * @brief 发送 HTTP Upgrade 请求
 */
bool test_handshake(const std::string& host, uint16_t port) {
    std::cout << "Connecting to " << host << ":" << port << "..." << std::endl;

    // 创建套接字
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        std::cerr << "Failed to create socket" << std::endl;
        return false;
    }

    // 解析地址
    struct hostent* server = gethostbyname(host.c_str());
    if (!server) {
        std::cerr << "Failed to resolve host: " << host << std::endl;
        ::close(sockfd);
        return false;
    }

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    memcpy(&addr.sin_addr.s_addr, server->h_addr, server->h_length);
    addr.sin_port = htons(port);

    // 连接服务器
    if (connect(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << "Failed to connect" << std::endl;
        ::close(sockfd);
        return false;
    }

    std::cout << "Connected!" << std::endl;

    // 生成 Sec-WebSocket-Key
    auto key_bytes = ws::utils::random_bytes(16);
    std::string ws_key = ws::utils::base64_encode(key_bytes.data(), key_bytes.size());

    // 构建 HTTP Upgrade 请求
    std::string request = "GET / HTTP/1.1\r\n"
                         "Host: " + host + ":" + std::to_string(port) + "\r\n"
                         "Upgrade: websocket\r\n"
                         "Connection: Upgrade\r\n"
                         "Sec-WebSocket-Key: " + ws_key + "\r\n"
                         "Sec-WebSocket-Version: 13\r\n"
                         "\r\n";

    std::cout << "\n=== Sending HTTP Upgrade Request ===" << std::endl;
    std::cout << request << std::endl;

    // 发送请求
    ssize_t sent = send(sockfd, request.c_str(), request.size(), 0);
    if (sent != static_cast<ssize_t>(request.size())) {
        std::cerr << "Failed to send request" << std::endl;
        ::close(sockfd);
        return false;
    }

    // 接收响应
    char buffer[4096];
    ssize_t received = recv(sockfd, buffer, sizeof(buffer) - 1, 0);
    if (received <= 0) {
        std::cerr << "Failed to receive response" << std::endl;
        ::close(sockfd);
        return false;
    }

    buffer[received] = '\0';
    std::string response(buffer);

    std::cout << "=== Received Response ===" << std::endl;
    std::cout << response << std::endl;

    // 验证响应
    if (response.find("101 Switching Protocols") == std::string::npos) {
        std::cerr << "ERROR: Expected 101 Switching Protocols" << std::endl;
        ::close(sockfd);
        return false;
    }

    if (response.find("Upgrade: websocket") == std::string::npos) {
        std::cerr << "ERROR: Missing Upgrade header" << std::endl;
        ::close(sockfd);
        return false;
    }

    // 验证 Sec-WebSocket-Accept
    const std::string magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
    std::string accept_input = ws_key + magic;
    auto sha1_hash = ws::utils::sha1(accept_input);
    std::string expected_accept = ws::utils::base64_encode(sha1_hash.data(), sha1_hash.size());

    if (response.find(expected_accept) == std::string::npos) {
        std::cerr << "ERROR: Invalid Sec-WebSocket-Accept" << std::endl;
        std::cerr << "Expected: " << expected_accept << std::endl;
        ::close(sockfd);
        return false;
    }

    std::cout << "\n=== Handshake Successful! ===" << std::endl;
    std::cout << "Sec-WebSocket-Key: " << ws_key << std::endl;
    std::cout << "Sec-WebSocket-Accept: " << expected_accept << std::endl;

    // 发送一个 WebSocket 文本帧
    std::string message = "Hello, WebSocket!";
    auto frame = ws::FrameCodec::encode_text(message);

    std::cout << "\n=== Sending WebSocket Frame ===" << std::endl;
    std::cout << "Message: " << message << std::endl;
    std::cout << "Frame size: " << frame.size() << " bytes" << std::endl;

    sent = send(sockfd, frame.data(), frame.size(), 0);
    if (sent != static_cast<ssize_t>(frame.size())) {
        std::cerr << "Failed to send frame" << std::endl;
        ::close(sockfd);
        return false;
    }

    // 接收响应帧
    received = recv(sockfd, buffer, sizeof(buffer), 0);
    if (received > 0) {
        std::cout << "\n=== Received Response Frame ===" << std::endl;
        std::cout << "Frame size: " << received << " bytes" << std::endl;

        // 解析响应帧
        size_t consumed = 0;
        auto response_frame = ws::FrameCodec::decode_frame(
            reinterpret_cast<uint8_t*>(buffer), received, consumed);

        if (response_frame) {
            std::string response_text(response_frame->payload.begin(),
                                      response_frame->payload.end());
            std::cout << "Response: " << response_text << std::endl;
        }
    }

    // 发送关闭帧
    std::cout << "\n=== Sending Close Frame ===" << std::endl;
    auto close_frame = ws::FrameCodec::create_close_frame(ws::CloseCode::Normal, "Test complete");
    send(sockfd, close_frame.data(), close_frame.size(), 0);

    ::close(sockfd);
    std::cout << "\n=== Test Complete ===" << std::endl;

    return true;
}

/**
 * @brief 主函数
 */
int main(int argc, char* argv[]) {
    std::string host = "localhost";
    uint16_t port = 8080;

    if (argc >= 2) {
        host = argv[1];
    }
    if (argc >= 3) {
        port = static_cast<uint16_t>(std::stoi(argv[2]));
    }

    std::cout << "=== WebSocket Handshake Test Client ===" << std::endl;
    std::cout << "Target: " << host << ":" << port << std::endl << std::endl;

    if (test_handshake(host, port)) {
        std::cout << "\nAll tests passed!" << std::endl;
        return 0;
    } else {
        std::cout << "\nTest failed!" << std::endl;
        return 1;
    }
}
