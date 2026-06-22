/**
 * @file test_health_checker.cpp
 * @brief 健康检查器单元测试
 *
 * 测试健康检查的核心逻辑：
 * - 后端状态管理
 * - 连续失败/成功计数
 * - 状态转换
 */

#include "../include/health_checker.h"
#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>

using namespace ha_server;

/**
 * 测试后端状态管理
 *
 * 验证：
 * - 初始状态为 Unknown
 * - 标记为 Healthy
 * - 标记为 Unhealthy
 */
void test_backend_status() {
    std::cout << "Testing backend status..." << std::endl;

    Backend backend("127.0.0.1", 8081);

    // 初始状态
    assert(backend.status == BackendStatus::Unknown);
    assert(!backend.is_healthy());

    // 标记为健康
    backend.mark_healthy();
    assert(backend.is_healthy());
    assert(backend.consecutive_failures == 0);
    assert(backend.consecutive_successes == 1);

    // 标记为不健康
    backend.mark_unhealthy();
    assert(!backend.is_healthy());
    assert(backend.consecutive_failures == 1);
    assert(backend.consecutive_successes == 0);

    std::cout << "  Passed: Status transitions work correctly" << std::endl;
}

/**
 * 测试连续失败计数
 *
 * 验证：
 * - 连续失败次数递增
 * - 达到阈值后标记为不健康
 */
void test_consecutive_failures() {
    std::cout << "Testing consecutive failures..." << std::endl;

    Backend backend("127.0.0.1", 8081);
    backend.mark_healthy();

    // 模拟连续失败
    for (int i = 0; i < 3; i++) {
        backend.mark_unhealthy();
    }

    assert(backend.consecutive_failures == 3);
    assert(!backend.is_healthy());

    std::cout << "  Passed: Consecutive failures tracked correctly" << std::endl;
}

/**
 * 测试连续成功计数
 *
 * 验证：
 * - 连续成功次数递增
 * - 恢复后标记为健康
 */
void test_consecutive_successes() {
    std::cout << "Testing consecutive successes..." << std::endl;

    Backend backend("127.0.0.1", 8081);
    backend.mark_unhealthy();
    backend.mark_unhealthy();
    backend.mark_unhealthy();

    // 模拟恢复
    backend.mark_healthy();

    assert(backend.is_healthy());
    assert(backend.consecutive_failures == 0);
    assert(backend.consecutive_successes == 1);

    std::cout << "  Passed: Recovery works correctly" << std::endl;
}

/**
 * 测试连接计数
 *
 * 验证：
 * - 增加连接数
 * - 减少连接数
 * - 获取活跃连接数
 */
void test_connection_counting() {
    std::cout << "Testing connection counting..." << std::endl;

    Backend backend("127.0.0.1", 8081);

    assert(backend.get_active_connections() == 0);

    backend.increment_connections();
    assert(backend.get_active_connections() == 1);

    backend.increment_connections();
    assert(backend.get_active_connections() == 2);

    backend.decrement_connections();
    assert(backend.get_active_connections() == 1);

    std::cout << "  Passed: Connection counting works correctly" << std::endl;
}

/**
 * 测试请求计数
 *
 * 验证：
 * - 总请求数递增
 * - 失败请求数递增
 */
void test_request_counting() {
    std::cout << "Testing request counting..." << std::endl;

    Backend backend("127.0.0.1", 8081);

    assert(backend.total_requests.load() == 0);
    assert(backend.failed_requests.load() == 0);

    backend.increment_connections();
    assert(backend.total_requests.load() == 1);

    backend.increment_failures();
    assert(backend.failed_requests.load() == 1);

    std::cout << "  Passed: Request counting works correctly" << std::endl;
}

/**
 * 测试健康检查配置
 */
void test_health_check_config() {
    std::cout << "Testing health check config..." << std::endl;

    HealthCheckConfig config;

    // 默认值
    assert(config.enabled == true);
    assert(config.interval.count() == 5000);
    assert(config.timeout.count() == 3000);
    assert(config.failure_threshold == 3);
    assert(config.success_threshold == 1);

    // 修改配置
    config.interval = std::chrono::milliseconds(1000);
    config.failure_threshold = 5;

    assert(config.interval.count() == 1000);
    assert(config.failure_threshold == 5);

    std::cout << "  Passed: Config works correctly" << std::endl;
}

int main() {
    std::cout << "=== Health Checker Tests ===" << std::endl;
    std::cout << std::endl;

    test_backend_status();
    std::cout << std::endl;

    test_consecutive_failures();
    std::cout << std::endl;

    test_consecutive_successes();
    std::cout << std::endl;

    test_connection_counting();
    std::cout << std::endl;

    test_request_counting();
    std::cout << std::endl;

    test_health_check_config();
    std::cout << std::endl;

    std::cout << "=== All Health Checker Tests Passed ===" << std::endl;
    return 0;
}
