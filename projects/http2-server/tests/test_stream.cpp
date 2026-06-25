/**
 * @file test_stream.cpp
 * @brief HTTP/2 流管理测试
 */

#include "http2_stream.h"
#include <iostream>
#include <cassert>

using namespace http2;

void test_stream_creation() {
    std::cout << "Testing stream creation..." << std::endl;

    Stream stream(1);

    assert(stream.get_id() == 1);
    assert(stream.get_state() == StreamState::IDLE);
    assert(stream.get_send_window() == 65535);
    assert(stream.get_recv_window() == 65535);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_state_transitions() {
    std::cout << "Testing stream state transitions..." << std::endl;

    // 测试客户端流（奇数 ID）
    Stream client_stream(1);

    // 发送头部（打开流）
    client_stream.send_headers(false);
    assert(client_stream.get_state() == StreamState::OPEN);

    // 发送数据（结束流）
    client_stream.send_data(true);
    assert(client_stream.get_state() == StreamState::HALF_CLOSED_LOCAL);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_state_remote_close() {
    std::cout << "Testing stream remote close..." << std::endl;

    Stream stream(2);

    // 接收头部（打开流）
    stream.recv_headers(false);
    assert(stream.get_state() == StreamState::OPEN);

    // 接收数据（结束流）
    stream.recv_data(true);
    assert(stream.get_state() == StreamState::HALF_CLOSED_REMOTE);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_flow_control() {
    std::cout << "Testing stream flow control..." << std::endl;

    Stream stream(1, 1000);  // 初始窗口大小 1000

    // 测试发送窗口
    assert(stream.get_send_window() == 1000);
    assert(stream.consume_send_window(500));
    assert(stream.get_send_window() == 500);
    assert(stream.consume_send_window(500));
    assert(stream.get_send_window() == 0);
    assert(!stream.consume_send_window(1));  // 窗口不足

    // 测试接收窗口
    assert(stream.get_recv_window() == 1000);
    assert(stream.consume_recv_window(300));
    assert(stream.get_recv_window() == 700);

    // 更新窗口
    stream.update_send_window(500);
    assert(stream.get_send_window() == 500);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_priority() {
    std::cout << "Testing stream priority..." << std::endl;

    Stream stream(1);
    StreamPriority priority;
    priority.weight = 32;
    priority.dependency = 0;
    priority.exclusive = true;

    stream.set_priority(priority);

    const auto& p = stream.get_priority();
    assert(p.weight == 32);
    assert(p.dependency == 0);
    assert(p.exclusive == true);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_data_buffer() {
    std::cout << "Testing stream data buffer..." << std::endl;

    Stream stream(1);

    // 添加数据
    std::vector<uint8_t> data1 = {0x01, 0x02, 0x03};
    std::vector<uint8_t> data2 = {0x04, 0x05, 0x06};

    stream.add_send_data(data1);
    stream.add_send_data(data2);

    // 获取数据
    auto result = stream.get_send_data(10);
    assert(result.size() == 6);
    assert(result[0] == 0x01);
    assert(result[3] == 0x04);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_manager() {
    std::cout << "Testing stream manager..." << std::endl;

    StreamManager manager;

    // 创建流
    auto stream1 = manager.create_stream(1);
    assert(stream1 != nullptr);
    assert(stream1->get_id() == 1);

    auto stream2 = manager.create_stream(3);
    assert(stream2 != nullptr);

    // 获取流
    auto retrieved = manager.get_stream(1);
    assert(retrieved == stream1);

    // 活跃流数量
    assert(manager.get_active_stream_count() == 2);

    // 关闭流
    manager.close_stream(1);
    assert(manager.get_active_stream_count() == 1);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_manager_max_concurrent() {
    std::cout << "Testing stream manager max concurrent streams..." << std::endl;

    StreamManager manager;
    manager.set_max_concurrent_streams(2);

    assert(manager.can_create_stream());
    manager.create_stream(1);
    assert(manager.can_create_stream());
    manager.create_stream(3);
    assert(!manager.can_create_stream());  // 已达到最大值

    manager.close_stream(1);
    assert(manager.can_create_stream());

    std::cout << "  PASSED" << std::endl;
}

void test_stream_manager_client_server_ids() {
    std::cout << "Testing stream manager client/server IDs..." << std::endl;

    StreamManager manager;

    // 客户端流 ID（奇数）
    uint32_t client_id1 = manager.get_next_client_stream_id();
    uint32_t client_id2 = manager.get_next_client_stream_id();
    assert(client_id1 % 2 == 1);  // 奇数
    assert(client_id2 % 2 == 1);  // 奇数
    assert(client_id2 > client_id1);

    // 服务器流 ID（偶数）
    uint32_t server_id1 = manager.get_next_server_stream_id();
    uint32_t server_id2 = manager.get_next_server_stream_id();
    assert(server_id1 % 2 == 0);  // 偶数
    assert(server_id2 % 2 == 0);  // 偶数
    assert(server_id2 > server_id1);

    std::cout << "  PASSED" << std::endl;
}

void test_stream_rst() {
    std::cout << "Testing stream RST_STREAM..." << std::endl;

    Stream stream(1);

    // 打开流
    stream.send_headers(false);
    assert(stream.get_state() == StreamState::OPEN);

    // 发送 RST_STREAM
    stream.send_rst_stream();
    assert(stream.get_state() == StreamState::CLOSED);

    std::cout << "  PASSED" << std::endl;
}

int main() {
    std::cout << "Running HTTP/2 Stream Tests..." << std::endl;
    std::cout << std::endl;

    test_stream_creation();
    test_stream_state_transitions();
    test_stream_state_remote_close();
    test_stream_flow_control();
    test_stream_priority();
    test_stream_data_buffer();
    test_stream_manager();
    test_stream_manager_max_concurrent();
    test_stream_manager_client_server_ids();
    test_stream_rst();

    std::cout << std::endl;
    std::cout << "All stream tests PASSED!" << std::endl;

    return 0;
}
