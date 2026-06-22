/**
 * @file test_load_balancer.cpp
 * @brief 负载均衡器单元测试
 *
 * 测试三种负载均衡算法：
 * 1. 轮询 (Round Robin)
 * 2. 加权轮询 (Weighted Round Robin)
 * 3. 最少连接 (Least Connections)
 */

#include "../include/load_balancer.h"
#include <iostream>
#include <cassert>
#include <map>
#include <vector>

using namespace ha_server;

/**
 * 测试轮询算法
 *
 * 验证：
 * - 请求均匀分配到各后端
 * - 循环分配
 */
void test_round_robin() {
    std::cout << "Testing Round Robin..." << std::endl;

    // 创建后端列表
    Backend b1("127.0.0.1", 8081);
    Backend b2("127.0.0.1", 8082);
    Backend b3("127.0.0.1", 8083);

    b1.mark_healthy();
    b2.mark_healthy();
    b3.mark_healthy();

    std::vector<Backend*> backends = {&b1, &b2, &b3};

    // 创建轮询负载均衡器
    RoundRobinBalancer balancer;

    // 统计每个后端被选中的次数
    std::map<std::string, int> counts;
    int total = 90;

    for (int i = 0; i < total; i++) {
        Backend* selected = balancer.select_backend(backends);
        assert(selected != nullptr);
        counts[selected->id]++;
    }

    // 验证均匀分配
    assert(counts[b1.id] == 30);
    assert(counts[b2.id] == 30);
    assert(counts[b3.id] == 30);

    std::cout << "  Passed: Requests distributed evenly" << std::endl;
    std::cout << "    Backend 1: " << counts[b1.id] << std::endl;
    std::cout << "    Backend 2: " << counts[b2.id] << std::endl;
    std::cout << "    Backend 3: " << counts[b3.id] << std::endl;
}

/**
 * 测试加权轮询算法
 *
 * 验证：
 * - 请求按权重比例分配
 * - 平滑分配（避免突刺）
 */
void test_weighted_round_robin() {
    std::cout << "Testing Weighted Round Robin..." << std::endl;

    // 创建后端列表，不同权重
    Backend b1("127.0.0.1", 8081, 5);
    Backend b2("127.0.0.1", 8082, 3);
    Backend b3("127.0.0.1", 8083, 2);

    b1.mark_healthy();
    b2.mark_healthy();
    b3.mark_healthy();

    std::vector<Backend*> backends = {&b1, &b2, &b3};

    // 创建加权轮询负载均衡器
    WeightedRoundRobinBalancer balancer;

    // 统计每个后端被选中的次数
    std::map<std::string, int> counts;
    int total = 100;

    for (int i = 0; i < total; i++) {
        Backend* selected = balancer.select_backend(backends);
        assert(selected != nullptr);
        counts[selected->id]++;
    }

    // 验证按权重分配（5:3:2）
    // 期望：50:30:20
    assert(counts[b1.id] == 50);
    assert(counts[b2.id] == 30);
    assert(counts[b3.id] == 20);

    std::cout << "  Passed: Requests distributed by weight" << std::endl;
    std::cout << "    Backend 1 (weight=5): " << counts[b1.id] << std::endl;
    std::cout << "    Backend 2 (weight=3): " << counts[b2.id] << std::endl;
    std::cout << "    Backend 3 (weight=2): " << counts[b3.id] << std::endl;
}

/**
 * 测试最少连接算法
 *
 * 验证：
 * - 选择连接数最少的后端
 * - 自动平衡负载
 */
void test_least_connections() {
    std::cout << "Testing Least Connections..." << std::endl;

    // 创建后端列表
    Backend b1("127.0.0.1", 8081);
    Backend b2("127.0.0.1", 8082);
    Backend b3("127.0.0.1", 8083);

    b1.mark_healthy();
    b2.mark_healthy();
    b3.mark_healthy();

    std::vector<Backend*> backends = {&b1, &b2, &b3};

    // 创建最少连接负载均衡器
    LeastConnectionsBalancer balancer;

    // 模拟不同连接数
    b1.active_connections.store(10);
    b2.active_connections.store(5);
    b3.active_connections.store(15);

    // 应该选择 b2（连接数最少）
    Backend* selected = balancer.select_backend(backends);
    assert(selected == &b2);

    std::cout << "  Passed: Selected backend with least connections" << std::endl;
    std::cout << "    Backend 1 connections: 10" << std::endl;
    std::cout << "    Backend 2 connections: 5 (selected)" << std::endl;
    std::cout << "    Backend 3 connections: 15" << std::endl;

    // 模拟 b2 连接数增加
    b2.active_connections.store(20);

    // 现在应该选择 b1
    selected = balancer.select_backend(backends);
    assert(selected == &b1);

    std::cout << "  Passed: Adapted to changed connections" << std::endl;
}

/**
 * 测试空后端列表
 */
void test_empty_backends() {
    std::cout << "Testing empty backends..." << std::endl;

    std::vector<Backend*> backends;

    RoundRobinBalancer rr;
    assert(rr.select_backend(backends) == nullptr);

    WeightedRoundRobinBalancer wrr;
    assert(wrr.select_backend(backends) == nullptr);

    LeastConnectionsBalancer lc;
    assert(lc.select_backend(backends) == nullptr);

    std::cout << "  Passed: All balancers handle empty backends" << std::endl;
}

/**
 * 测试单个后端
 */
void test_single_backend() {
    std::cout << "Testing single backend..." << std::endl;

    Backend b1("127.0.0.1", 8081);
    b1.mark_healthy();

    std::vector<Backend*> backends = {&b1};

    RoundRobinBalancer rr;
    for (int i = 0; i < 10; i++) {
        assert(rr.select_backend(backends) == &b1);
    }

    std::cout << "  Passed: Single backend always selected" << std::endl;
}

int main() {
    std::cout << "=== Load Balancer Tests ===" << std::endl;
    std::cout << std::endl;

    test_round_robin();
    std::cout << std::endl;

    test_weighted_round_robin();
    std::cout << std::endl;

    test_least_connections();
    std::cout << std::endl;

    test_empty_backends();
    std::cout << std::endl;

    test_single_backend();
    std::cout << std::endl;

    std::cout << "=== All Load Balancer Tests Passed ===" << std::endl;
    return 0;
}
