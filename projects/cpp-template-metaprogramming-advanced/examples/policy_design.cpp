/**
 * @file policy_design.cpp
 * @brief 策略模式示例
 */

#include <iostream>
#include <string>
#include "../include/design_patterns/policy_design.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Policy-based Design ===" << std::endl;
    std::cout << std::endl;

    // 1. 策略化容器
    std::cout << "--- 1. Policy-based Container ---" << std::endl;

    PolicyBasedVector<int, ThrowBoundsCheck> safe_vec;
    safe_vec.push_back(10);
    safe_vec.push_back(20);
    safe_vec.push_back(30);
    std::cout << "Safe vector[0]: " << safe_vec[0] << std::endl;
    std::cout << "Safe vector[2]: " << safe_vec[2] << std::endl;

    try {
        safe_vec[10];  // 越界，抛出异常
    } catch (const std::out_of_range& e) {
        std::cout << "Caught: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    // 2. 策略化消息系统
    std::cout << "--- 2. Policy-based Message System ---" << std::endl;

    MessageSystem<PlainTextFormat, ConsoleOutput>::info("Plain text message");
    MessageSystem<JsonFormat, ConsoleOutput>::info("JSON message");
    std::cout << std::endl;

    // 3. 策略化序列化
    std::cout << "--- 3. Policy-based Serialization ---" << std::endl;

    DataStore<double, BinarySerialization> bin_store("pi", 3.14159);
    DataStore<double, TextSerialization> text_store("pi", 3.14159);
    std::cout << "Binary: " << bin_store.serialize().size() << " bytes" << std::endl;
    std::cout << "Text: " << text_store.serialize() << std::endl;
    std::cout << std::endl;

    // 4. 策略化线程安全
    std::cout << "--- 4. Policy-based Threading ---" << std::endl;

    ThreadSafeVector<int, NoLocking> fast_vec;
    fast_vec.push_back(1);
    std::cout << "No-locking vector size: " << fast_vec.size() << std::endl;

    ThreadSafeVector<int, MutexLocking> safe_vec2;
    safe_vec2.push_back(1);
    std::cout << "Mutex-locking vector size: " << safe_vec2.size() << std::endl;
    std::cout << std::endl;

    std::cout << "Policy-based design allows compile-time customization" << std::endl;
    std::cout << "with zero runtime overhead." << std::endl;

    return 0;
}
