/**
 * @file basic_example.cpp
 * @brief Boost.Log 日志库基础示例
 * @details 展示 Boost.Log 的基本用法
 *          Boost.Log 是 Boost 库中的日志组件
 *          功能丰富，灵活可配置
 */

#include <iostream>
#include <string>
#include <boost/log/core.hpp>
#include <boost/log/trivial.hpp>
#include <boost/log/expressions.hpp>
#include <boost/log/sinks/text_file_backend.hpp>
#include <boost/log/utility/setup/file.hpp>
#include <boost/log/utility/setup/console.hpp>
#include <boost/log/utility/setup/common_attributes.hpp>

/**
 * @brief 基础日志示例
 * @details 展示 Boost.Log 的基本日志功能
 */
void basic_logging() {
    std::cout << "=== 基础日志 ===" << std::endl;

    // 使用 trivial 日志
    BOOST_LOG_TRIVIAL(trace) << "This is a trace message";
    BOOST_LOG_TRIVIAL(debug) << "This is a debug message";
    BOOST_LOG_TRIVIAL(info) << "This is an info message";
    BOOST_LOG_TRIVIAL(warning) << "This is a warning message";
    BOOST_LOG_TRIVIAL(error) << "This is an error message";
    BOOST_LOG_TRIVIAL(fatal) << "This is a fatal message";

    std::cout << std::endl;
}

/**
 * @brief 日志配置示例
 * @details 展示如何配置 Boost.Log
 */
void log_configuration() {
    std::cout << "=== 日志配置 ===" << std::endl;

    // 添加通用属性
    boost::log::add_common_attributes();

    // 设置日志级别
    boost::log::core::get()->set_filter(
        boost::log::trivial::severity >= boost::log::trivial::info
    );

    // 这些不会显示（级别低于 info）
    BOOST_LOG_TRIVIAL(trace) << "This is a trace message";
    BOOST_LOG_TRIVIAL(debug) << "This is a debug message";

    // 这些会显示
    BOOST_LOG_TRIVIAL(info) << "This is an info message";
    BOOST_LOG_TRIVIAL(warning) << "This is a warning message";

    std::cout << std::endl;
}

/**
 * @brief 文件日志示例
 * @details 展示如何配置文件日志
 */
void file_logging() {
    std::cout << "=== 文件日志 ===" << std::endl;

    // 配置文件日志
    boost::log::add_file_log(
        boost::log::keywords::file_name = "log_%N.log",
        boost::log::keywords::rotation_size = 10 * 1024 * 1024,  // 10MB
        boost::log::keywords::format = "[%TimeStamp%]: %Message%"
    );

    BOOST_LOG_TRIVIAL(info) << "This message goes to file";

    std::cout << "Log message written to file" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 控制台日志示例
 * @details 展示如何配置控制台日志
 */
void console_logging() {
    std::cout << "=== 控制台日志 ===" << std::endl;

    // 配置控制台日志
    boost::log::add_console_log(
        std::cout,
        boost::log::keywords::format = "[%TimeStamp%]: %Message%"
    );

    BOOST_LOG_TRIVIAL(info) << "This message goes to console";

    std::cout << std::endl;
}

/**
 * @brief Boost.Log 概念说明
 * @details 介绍 Boost.Log 的核心概念
 */
void boost_log_concepts() {
    std::cout << "=== Boost.Log 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Boost.Log 是 Boost 库中的日志组件。" << std::endl;
    std::cout << std::endl;

    std::cout << "核心概念：" << std::endl;
    std::cout << "  - Logger: 日志记录器" << std::endl;
    std::cout << "  - Sink: 日志输出目标" << std::endl;
    std::cout << "  - Filter: 日志过滤器" << std::endl;
    std::cout << "  - Formatter: 日志格式化器" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 灵活的配置" << std::endl;
    std::cout << "  - 多种输出目标" << std::endl;
    std::cout << "  - 异步日志" << std::endl;
    std::cout << "  - 线程安全" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Log 日志库示例 ===" << std::endl;
    std::cout << std::endl;

    boost_log_concepts();
    basic_logging();
    log_configuration();
    // file_logging();  // 取消注释以启用文件日志
    // console_logging();  // 取消注释以启用控制台日志

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}