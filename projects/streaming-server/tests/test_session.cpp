/**
 * @file test_session.cpp
 * @brief 会话测试
 */

#include "streaming/session/session_manager.hpp"
#include "streaming/session/load_balancer.hpp"
#include "streaming/monitor/logger.hpp"

#include <iostream>
#include <cassert>

using namespace streaming;

void test_session_lifecycle() {
    std::cout << "Testing session lifecycle..." << std::endl;

    SessionManager manager;
    manager.initialize(10, std::chrono::seconds(60));

    // 创建会话
    auto session = manager.create_session(SessionType::Publisher, ProtocolType::RTMP);
    assert(session != nullptr);
    assert(session->get_state() == SessionState::Created);

    // 更新状态
    session->set_state(SessionState::Connected);
    assert(session->get_state() == SessionState::Connected);

    // 设置客户端信息
    session->set_client_info("192.168.1.100", 12345);
    session->set_stream_name("test_stream");
    session->set_app_name("live");

    // 更新统计
    session->update_bytes_sent(1024);
    session->update_bytes_received(512);
    session->update_frames_sent(30);

    auto info = session->get_info();
    assert(info->bytes_sent == 1024);
    assert(info->bytes_received == 512);
    assert(info->frames_sent == 30);

    // 移除会话
    manager.remove_session(session->get_id());
    assert(manager.get_session_count() == 0);

    std::cout << "  Session lifecycle tests passed!" << std::endl;
}

void test_load_balancer() {
    std::cout << "Testing load balancer..." << std::endl;

    LoadBalancer lb;
    lb.initialize(LoadBalanceAlgorithm::RoundRobin);

    // 添加节点
    auto node1 = std::make_shared<ClusterNode>();
    node1->node_id = "node1";
    node1->host = "192.168.1.1";
    node1->port = 1935;
    node1->state = NodeState::Healthy;
    node1->weight = 1;

    auto node2 = std::make_shared<ClusterNode>();
    node2->node_id = "node2";
    node2->host = "192.168.1.2";
    node2->port = 1935;
    node2->state = NodeState::Healthy;
    node2->weight = 2;

    auto node3 = std::make_shared<ClusterNode>();
    node3->node_id = "node3";
    node3->host = "192.168.1.3";
    node3->port = 1935;
    node3->state = NodeState::Unhealthy;
    node3->weight = 1;

    lb.add_node(node1);
    lb.add_node(node2);
    lb.add_node(node3);

    assert(lb.get_all_nodes().size() == 3);

    // 选择节点（轮询）
    auto selected1 = lb.select_node();
    auto selected2 = lb.select_node();
    auto selected3 = lb.select_node();

    assert(selected1 != nullptr);
    assert(selected2 != nullptr);
    assert(selected3 != nullptr);

    // 测试最少连接算法
    lb.initialize(LoadBalanceAlgorithm::LeastConnections);

    node1->current_connections = 10;
    node2->current_connections = 5;
    node3->current_connections = 15;

    auto least = lb.select_node();
    assert(least == node2);

    std::cout << "  Load balancer tests passed!" << std::endl;
}

int main() {
    LogManager::instance().initialize(LogLevel::Error, "", false);

    std::cout << "Running session tests..." << std::endl;

    test_session_lifecycle();
    test_load_balancer();

    std::cout << "\nAll session tests passed!" << std::endl;
    return 0;
}
