/**
 * @file basic_example.cpp
 * @brief MessagePack 序列化示例
 * @details 展示 MessagePack 的基本用法
 *          MessagePack 是一种高效的二进制序列化格式
 *          类似 JSON，但更小更快
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <msgpack.hpp>

/**
 * @brief 基础用法示例
 * @details 展示 MessagePack 的基本序列化和反序列化
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 序列化
    msgpack::sbuffer buffer;
    msgpack::pack(buffer, 42);
    msgpack::pack(buffer, "Hello, World!");
    msgpack::pack(buffer, std::vector<int>{1, 2, 3});

    std::cout << "Serialized size: " << buffer.size() << " bytes" << std::endl;

    // 反序列化
    size_t offset = 0;

    // 反序列化整数
    auto oh1 = msgpack::unpack(buffer.data(), buffer.size(), offset);
    int value = oh1->as<int>();
    std::cout << "Integer: " << value << std::endl;

    // 反序列化字符串
    auto oh2 = msgpack::unpack(buffer.data(), buffer.size(), offset);
    std::string str = oh2->as<std::string>();
    std::cout << "String: " << str << std::endl;

    // 反序列化数组
    auto oh3 = msgpack::unpack(buffer.data(), buffer.size(), offset);
    std::vector<int> vec = oh3->as<std::vector<int>>();
    std::cout << "Vector: ";
    for (int v : vec) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 自定义类型示例
 * @details 展示如何序列化自定义类型
 */
void custom_types() {
    std::cout << "=== 自定义类型 ===" << std::endl;

    // 定义结构体
    struct Person {
        std::string name;
        int age;
        std::string email;

        MSGPACK_DEFINE_MAP(name, age, email);
    };

    // 序列化
    Person person{"Alice", 30, "alice@example.com"};
    msgpack::sbuffer buffer;
    msgpack::pack(buffer, person);

    std::cout << "Serialized size: " << buffer.size() << " bytes" << std::endl;

    // 反序列化
    auto oh = msgpack::unpack(buffer.data(), buffer.size());
    auto deserialized = oh->as<Person>();

    std::cout << "Name: " << deserialized.name << std::endl;
    std::cout << "Age: " << deserialized.age << std::endl;
    std::cout << "Email: " << deserialized.email << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 容器序列化示例
 * @details 展示如何序列化各种容器
 */
void container_serialization() {
    std::cout << "=== 容器序列化 ===" << std::endl;

    // 序列化 map
    std::map<std::string, int> scores = {
        {"Alice", 95},
        {"Bob", 87},
        {"Charlie", 92}
    };

    msgpack::sbuffer buffer;
    msgpack::pack(buffer, scores);

    // 反序列化
    auto oh = msgpack::unpack(buffer.data(), buffer.size());
    auto deserialized = oh->as<std::map<std::string, int>>();

    std::cout << "Scores:" << std::endl;
    for (const auto& [name, score] : deserialized) {
        std::cout << "  " << name << ": " << score << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief MessagePack 概念说明
 * @details 介绍 MessagePack 的核心概念
 */
void msgpack_concepts() {
    std::cout << "=== MessagePack 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "MessagePack 是一种二进制序列化格式。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 类似 JSON 的数据模型" << std::endl;
    std::cout << "  - 二进制格式，更紧凑" << std::endl;
    std::cout << "  - 跨语言支持" << std::endl;
    std::cout << "  - 高性能" << std::endl;
    std::cout << std::endl;

    std::cout << "与 JSON 对比：" << std::endl;
    std::cout << "  - 更小的体积" << std::endl;
    std::cout << "  - 更快的解析" << std::endl;
    std::cout << "  - 但不是文本格式" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== MessagePack 序列化示例 ===" << std::endl;
    std::cout << std::endl;

    msgpack_concepts();
    basic_usage();
    custom_types();
    container_serialization();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}