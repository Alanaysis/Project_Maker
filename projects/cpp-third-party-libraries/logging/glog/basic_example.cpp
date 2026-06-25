/**
 * @file basic_example.cpp
 * @brief glog 日志库基础示例
 * @details 展示 glog 的基本用法
 *          glog 是 Google 开发的 C++ 日志库
 *          功能丰富，广泛用于大型项目
 */

#include <iostream>
#include <string>
#include <glog/logging.h>

/**
 * @brief 基础日志示例
 * @details 展示 glog 的基本日志功能
 */
void basic_logging() {
    std::cout << "=== 基础日志 ===" << std::endl;

    // 不同级别的日志
    LOG(INFO) << "This is an info message";
    LOG(WARNING) << "This is a warning message";
    LOG(ERROR) << "This is an error message";

    // 条件日志
    int value = 42;
    LOG_IF(INFO, value > 40) << "Value is greater than 40: " << value;
    LOG_IF(WARNING, value < 0) << "Value is negative";

    // 每 N 次记录一次
    for (int i = 0; i < 100; ++i) {
        LOG_EVERY_N(INFO, 10) << "This appears every 10 iterations, count=" << google::COUNTER;
    }

    std::cout << std::endl;
}

/**
 * @brief 详细日志示例
 * @details 展示详细日志级别
 */
void verbose_logging() {
    std::cout << "=== 详细日志 ===" << std::endl;

    // VLOG 级别
    VLOG(1) << "Verbose level 1";
    VLOG(2) << "Verbose level 2";
    VLOG(3) << "Verbose level 3";

    // 条件详细日志
    VLOG_IF(1, true) << "This is verbose level 1";

    std::cout << std::endl;
}

/**
 * @brief 检查宏示例
 * @details 展示 glog 的检查宏
 */
void check_macros() {
    std::cout << "=== 检查宏 ===" << std::endl;

    int x = 42;
    int y = 42;

    // CHECK 宏
    CHECK_EQ(x, y) << "x should equal y";
    CHECK_NE(x, 0) << "x should not be 0";
    CHECK_GT(x, 0) << "x should be positive";
    CHECK_GE(x, 42) << "x should be >= 42";
    CHECK_LT(x, 100) << "x should be < 100";
    CHECK_LE(x, 42) << "x should be <= 42";

    // CHECK_NOTNULL
    int* ptr = &x;
    CHECK_NOTNULL(ptr);

    std::cout << "All checks passed" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 字符串日志示例
 * @details 展示字符串相关的日志
 */
void string_logging() {
    std::cout << "=== 字符串日志 ===" << std::endl;

    std::string name = "Alice";
    int age = 30;

    // 使用流式 API
    LOG(INFO) << "User: " << name << ", Age: " << age;

    // 使用 printf 风格
    LOG(INFO) << "User: " << name.c_str() << ", Age: " << age;

    std::cout << std::endl;
}

/**
 * @brief 性能日志示例
 * @details 展示性能相关的日志
 */
void performance_logging() {
    std::cout << "=== 性能日志 ===" << std::endl;

    // 计时日志
    {
        LOG(INFO) << "Starting operation...";
        // 模拟一些工作
        for (volatile int i = 0; i < 1000000; ++i) {}
        LOG(INFO) << "Operation completed";
    }

    // 条件性能日志
    bool slow_operation = true;
    LOG_IF(WARNING, slow_operation) << "This operation is slow";

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 glog 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：服务器启动
    LOG(INFO) << "Server starting...";

    // 模拟配置加载
    LOG(INFO) << "Loading configuration...";
    int port = 8080;
    LOG(INFO) << "Configuration loaded: port=" << port;

    // 模拟数据库连接
    LOG(INFO) << "Connecting to database...";
    bool db_connected = true;
    LOG_IF(ERROR, !db_connected) << "Failed to connect to database";
    LOG_IF(INFO, db_connected) << "Database connected successfully";

    // 模拟请求处理
    for (int i = 0; i < 5; ++i) {
        LOG(INFO) << "Processing request " << i;
        VLOG(1) << "Request details...";
    }

    LOG(INFO) << "Server shutdown";

    std::cout << std::endl;
}

int main(int argc, char* argv[]) {
    // 初始化 glog
    google::InitGoogleLogging(argv[0]);

    // 设置日志级别
    FLAGS_stderrthreshold = 0;  // 输出所有级别到 stderr
    FLAGS_v = 1;  // 设置 VLOG 级别

    std::cout << "=== glog 日志库示例 ===" << std::endl;
    std::cout << std::endl;

    basic_logging();
    verbose_logging();
    check_macros();
    string_logging();
    performance_logging();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;

    // 关闭 glog
    google::ShutdownGoogleLogging();

    return 0;
}