/**
 * @file views_cache_latest_example.cpp
 * @brief C++23 std::views::cache_latest 示例
 *
 * std::views::cache_latest 是 C++23 引入的缓存最新视图。
 * 它缓存范围的最后一个元素，便于重复访问。
 *
 * 主要特点：
 * - 缓存范围的最后一个元素
 * - 支持重复访问
 * - 适用于需要记住状态的场景
 * - 支持惰性求值
 *
 * 编译命令：
 * g++ -std=c++23 -o views_cache_latest_example views_cache_latest_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5};

    // 创建缓存最新视图
    auto cached = data | std::views::cache_latest;

    // 遍历并访问最后一个元素
    std::cout << "Data: ";
    for (int n : cached) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 2. 实际应用：状态跟踪 ==========

void state_tracking() {
    std::cout << "\n=== 实际应用：状态跟踪 ===" << std::endl;

    // 模拟状态序列
    std::vector<std::string> states = {"Idle", "Running", "Paused", "Stopped"};

    // 跟踪最后一个状态
    auto cached_states = states | std::views::cache_latest;

    std::cout << "State sequence:" << std::endl;
    for (const auto& state : cached_states) {
        std::cout << "  State: " << state << std::endl;
    }
}

// ========== 3. 实际应用：数据处理 ==========

void data_processing() {
    std::cout << "\n=== 实际应用：数据处理 ===" << std::endl;

    // 处理数据并缓存结果
    std::vector<int> data = {10, 20, 30, 40, 50};

    auto processed = data
        | std::views::transform([](int x) { return x * 2; })
        | std::views::cache_latest;

    std::cout << "Processed data:" << std::endl;
    for (int n : processed) {
        std::cout << "  " << n << std::endl;
    }
}

// ========== 4. 实际应用：日志系统 ==========

void logging_system() {
    std::cout << "\n=== 实际应用：日志系统 ===" << std::endl;

    // 日志消息
    std::vector<std::string> logs = {
        "Application started",
        "Loading configuration",
        "Connecting to database",
        "Ready to serve requests"
    };

    // 缓存最新日志
    auto cached_logs = logs | std::views::cache_latest;

    std::cout << "Log messages:" << std::endl;
    for (const auto& log : cached_logs) {
        std::cout << "  [LOG] " << log << std::endl;
    }
}

// ========== 5. 实际应用：性能监控 ==========

void performance_monitoring() {
    std::cout << "\n=== 实际应用：性能监控 ===" << std::endl;

    // 性能指标
    std::vector<double> metrics = {95.5, 96.2, 97.1, 98.0, 99.5};

    // 缓存最新指标
    auto cached_metrics = metrics | std::views::cache_latest;

    std::cout << "Performance metrics:" << std::endl;
    for (double m : cached_metrics) {
        std::cout << "  CPU Usage: " << m << "%" << std::endl;
    }
}

// ========== 6. 实际应用：配置更新 ==========

void config_update() {
    std::cout << "\n=== 实际应用：配置更新 ===" << std::endl;

    // 配置版本
    std::vector<std::string> configs = {
        "v1.0: default",
        "v1.1: updated timeout",
        "v1.2: added new feature",
        "v1.3: performance improvements"
    };

    // 缓存最新配置
    auto cached_configs = configs | std::views::cache_latest;

    std::cout << "Configuration history:" << std::endl;
    for (const auto& config : cached_configs) {
        std::cout << "  " << config << std::endl;
    }
}

// ========== 7. 实际应用：数据流处理 ==========

void data_stream_processing() {
    std::cout << "\n=== 实际应用：数据流处理 ===" << std::endl;

    // 数据流
    std::vector<int> stream = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 处理并缓存最新结果
    auto processed = stream
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::views::transform([](int x) { return x * x; })
        | std::views::cache_latest;

    std::cout << "Processed stream:" << std::endl;
    for (int n : processed) {
        std::cout << "  " << n << std::endl;
    }
}

// ========== 8. 实际应用：错误处理 ==========

void error_handling() {
    std::cout << "\n=== 实际应用：错误处理 ===" << std::endl;

    // 模拟操作序列
    std::vector<std::string> operations = {
        "Step 1: Initialize",
        "Step 2: Load data",
        "Step 3: Process",
        "Step 4: Save results"
    };

    // 缓存最新操作
    auto cached_ops = operations | std::views::cache_latest;

    std::cout << "Operations:" << std::endl;
    for (const auto& op : cached_ops) {
        std::cout << "  " << op << std::endl;
    }
}

// ========== 9. 实际应用：数据验证 ==========

void data_validation() {
    std::cout << "\n=== 实际应用：数据验证 ===" << std::endl;

    // 验证结果
    std::vector<std::pair<std::string, bool>> results = {
        {"Name", true},
        {"Email", true},
        {"Age", false},
        {"Phone", true}
    };

    // 缓存最新验证结果
    auto cached_results = results | std::views::cache_latest;

    std::cout << "Validation results:" << std::endl;
    for (const auto& [field, valid] : cached_results) {
        std::cout << "  " << field << ": " << (valid ? "PASS" : "FAIL") << std::endl;
    }
}

// ========== 10. 实际应用：测试执行 ==========

void test_execution() {
    std::cout << "\n=== 实际应用：测试执行 ===" << std::endl;

    // 测试用例
    std::vector<std::string> tests = {
        "Test 1: Unit test",
        "Test 2: Integration test",
        "Test 3: Performance test"
    };

    // 缓存最新测试
    auto cached_tests = tests | std::views::cache_latest;

    std::cout << "Running tests:" << std::endl;
    for (const auto& test : cached_tests) {
        std::cout << "  Running: " << test << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::views::cache_latest 示例\n" << std::endl;

    basic_usage();
    state_tracking();
    data_processing();
    logging_system();
    performance_monitoring();
    config_update();
    data_stream_processing();
    error_handling();
    data_validation();
    test_execution();

    return 0;
}
