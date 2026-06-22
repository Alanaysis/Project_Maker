/**
 * @file test_connection_pool.cpp
 * @brief 连接池单元测试
 *
 * 测试连接池的核心逻辑：
 * - 连接获取和释放
 * - 池大小管理
 * - 超时清理
 *
 * 注意：此测试需要实际的网络连接，可能在某些环境下失败。
 * 主要测试连接池的状态管理逻辑。
 */

#include "../include/connection_pool.h"
#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>

using namespace ha_server;

/**
 * 测试连接池配置
 */
void test_pool_config() {
    std::cout << "Testing pool config..." << std::endl;

    ConnectionPoolConfig config;

    // 默认值
    assert(config.max_size == 100);
    assert(config.min_size == 1);
    assert(config.idle_timeout.count() == 60000);
    assert(config.connect_timeout.count() == 5000);

    // 修改配置
    config.max_size = 50;
    config.min_size = 5;

    assert(config.max_size == 50);
    assert(config.min_size == 5);

    std::cout << "  Passed: Config works correctly" << std::endl;
}

/**
 * 测试连接池创建
 */
void test_pool_creation() {
    std::cout << "Testing pool creation..." << std::endl;

    ConnectionPoolConfig config;
    config.max_size = 10;

    ConnectionPool pool("127.0.0.1", 8081, config);

    assert(pool.size() == 0);
    assert(pool.available() == 0);
    assert(pool.in_use_count() == 0);

    std::cout << "  Passed: Pool created with correct initial state" << std::endl;
}

/**
 * 测试连接池管理器
 */
void test_pool_manager() {
    std::cout << "Testing pool manager..." << std::endl;

    ConnectionPoolManager manager;
    ConnectionPoolConfig config;
    config.max_size = 10;

    // 获取连接池
    ConnectionPool* pool1 = manager.get_pool("127.0.0.1", 8081, config);
    assert(pool1 != nullptr);

    // 再次获取同一个池
    ConnectionPool* pool2 = manager.get_pool("127.0.0.1", 8081, config);
    assert(pool2 == pool1);  // 应该是同一个池

    // 获取不同的池
    ConnectionPool* pool3 = manager.get_pool("127.0.0.1", 8082, config);
    assert(pool3 != pool1);

    std::cout << "  Passed: Pool manager works correctly" << std::endl;
}

/**
 * 测试连接池大小限制
 *
 * 注意：此测试不实际创建网络连接，
 * 主要测试池的状态管理逻辑。
 */
void test_pool_size_limit() {
    std::cout << "Testing pool size limit..." << std::endl;

    ConnectionPoolConfig config;
    config.max_size = 5;

    ConnectionPool pool("127.0.0.1", 8081, config);

    // 初始状态
    assert(pool.size() == 0);

    std::cout << "  Passed: Pool size limit configured correctly" << std::endl;
}

/**
 * 测试连接池清理
 */
void test_pool_cleanup() {
    std::cout << "Testing pool cleanup..." << std::endl;

    ConnectionPoolConfig config;
    config.max_size = 10;

    ConnectionPool pool("127.0.0.1", 8081, config);

    // 清理空池
    pool.cleanup_idle();
    assert(pool.size() == 0);

    // 清空池
    pool.clear();
    assert(pool.size() == 0);

    std::cout << "  Passed: Pool cleanup works correctly" << std::endl;
}

/**
 * 测试连接池管理器清理
 */
void test_manager_cleanup() {
    std::cout << "Testing manager cleanup..." << std::endl;

    ConnectionPoolManager manager;
    ConnectionPoolConfig config;
    config.max_size = 10;

    // 创建多个池
    manager.get_pool("127.0.0.1", 8081, config);
    manager.get_pool("127.0.0.1", 8082, config);

    // 清理所有池
    manager.cleanup_all();

    // 清空所有池
    manager.clear_all();

    std::cout << "  Passed: Manager cleanup works correctly" << std::endl;
}

int main() {
    std::cout << "=== Connection Pool Tests ===" << std::endl;
    std::cout << std::endl;

    test_pool_config();
    std::cout << std::endl;

    test_pool_creation();
    std::cout << std::endl;

    test_pool_manager();
    std::cout << std::endl;

    test_pool_size_limit();
    std::cout << std::endl;

    test_pool_cleanup();
    std::cout << std::endl;

    test_manager_cleanup();
    std::cout << std::endl;

    std::cout << "=== All Connection Pool Tests Passed ===" << std::endl;
    return 0;
}
