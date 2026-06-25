/**
 * @file policy_classes.cpp
 * @brief 策略类示例
 *
 * 通过模板参数组合不同的策略类来定制类的行为。
 */

#include <iostream>
#include <string>
#include "../include/advanced_templates/policy_classes.hpp"
#include "../include/design_patterns/policy_design.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Policy Classes Demo ===" << std::endl;
    std::cout << std::endl;

    // 1. 策略化容器
    std::cout << "--- 1. Policy-based Vector ---" << std::endl;

    // 使用异常边界检查
    PolicyBasedVector<int, ThrowBoundsCheck> safe_vec;
    safe_vec.push_back(1);
    safe_vec.push_back(2);
    safe_vec.push_back(3);
    std::cout << "Safe vector[0] = " << safe_vec[0] << std::endl;
    std::cout << "Safe vector[1] = " << safe_vec[1] << std::endl;

    // 使用无边界检查（更快但不安全）
    PolicyBasedVector<int, NoBoundsCheck> fast_vec;
    fast_vec.push_back(10);
    fast_vec.push_back(20);
    std::cout << "Fast vector[0] = " << fast_vec[0] << std::endl;
    std::cout << std::endl;

    // 2. 策略化日志器
    std::cout << "--- 2. Policy-based Logger ---" << std::endl;

    // 详细日志，输出到控制台
    Logger<ConsoleOutputPolicy, VerboseLevel>::debug("This is a debug message");
    Logger<ConsoleOutputPolicy, VerboseLevel>::info("This is an info message");
    Logger<ConsoleOutputPolicy, VerboseLevel>::error("This is an error message");
    std::cout << std::endl;

    // 只输出错误
    Logger<ConsoleOutputPolicy, ErrorOnlyLevel>::debug("This debug message will NOT appear");
    Logger<ConsoleOutputPolicy, ErrorOnlyLevel>::info("This info message will NOT appear");
    Logger<ConsoleOutputPolicy, ErrorOnlyLevel>::error("This error message WILL appear");
    std::cout << std::endl;

    // 禁用日志
    Logger<NullOutputPolicy, VerboseLevel>::debug("This will not be printed");
    Logger<NullOutputPolicy, VerboseLevel>::info("This will not be printed either");
    std::cout << "(Null logger: no output)" << std::endl;
    std::cout << std::endl;

    // 3. 策略化消息系统
    std::cout << "--- 3. Policy-based Message System ---" << std::endl;

    // 纯文本格式
    MessageSystem<PlainTextFormat, ConsoleOutput>::info("Hello from plain text");
    MessageSystem<PlainTextFormat, ConsoleOutput>::error("Error in plain text");
    std::cout << std::endl;

    // JSON 格式
    MessageSystem<JsonFormat, ConsoleOutput>::info("Hello from JSON");
    MessageSystem<JsonFormat, ConsoleOutput>::error("Error in JSON");
    std::cout << std::endl;

    // 4. 策略化序列化
    std::cout << "--- 4. Policy-based Serialization ---" << std::endl;

    DataStore<int, BinarySerialization> bin_store("count", 42);
    std::cout << "Binary serialized: ";
    for (char c : bin_store.serialize()) {
        std::cout << std::hex << (int)(unsigned char)c << " ";
    }
    std::cout << std::endl;

    DataStore<int, TextSerialization> text_store("count", 42);
    std::cout << "Text serialized: " << text_store.serialize() << std::endl;
    std::cout << std::endl;

    // 5. 策略化线程安全
    std::cout << "--- 5. Policy-based Threading ---" << std::endl;

    // 单线程版本（无锁开销）
    ThreadSafeVector<int, NoLocking> single_thread_vec;
    single_thread_vec.push_back(1);
    std::cout << "Single-threaded vector size: " << single_thread_vec.size() << std::endl;

    // 多线程版本（有锁保护）
    ThreadSafeVector<int, MutexLocking> multi_thread_vec;
    multi_thread_vec.push_back(1);
    std::cout << "Multi-threaded vector size: " << multi_thread_vec.size() << std::endl;
    std::cout << std::endl;

    std::cout << "Key insight: Policy classes allow you to customize behavior" << std::endl;
    std::cout << "at compile time with zero runtime overhead." << std::endl;

    return 0;
}
