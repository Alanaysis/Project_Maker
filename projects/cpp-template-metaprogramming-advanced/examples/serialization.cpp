/**
 * @file serialization.cpp
 * @brief 序列化框架示例
 */

#include <iostream>
#include <string>
#include <vector>
#include "../include/applications/serialization.hpp"

// 定义一个可序列化的结构体
struct Person {
    std::string name;
    int age;
    double height;
};

// 定义字段描述
constexpr auto person_fields = std::make_tuple(
    tmp::make_field("name", &Person::name),
    tmp::make_field("age", &Person::age),
    tmp::make_field("height", &Person::height)
);

int main() {
    using namespace tmp;

    std::cout << "=== Serialization Framework ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本类型序列化
    std::cout << "--- 1. Basic Type Serialization ---" << std::endl;
    std::cout << "int: " << serialize_value(42) << std::endl;
    std::cout << "double: " << serialize_value(3.14) << std::endl;
    std::cout << "bool: " << serialize_value(true) << std::endl;
    std::cout << "string: " << serialize_value(std::string("hello")) << std::endl;
    std::cout << std::endl;

    // 2. 向量序列化
    std::cout << "--- 2. Vector Serialization ---" << std::endl;
    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::cout << "vector<int>: " << serialize_vector(vec) << std::endl;

    std::vector<std::string> svec = {"hello", "world"};
    std::cout << "vector<string>: " << serialize_vector(svec) << std::endl;
    std::cout << std::endl;

    // 3. JSON 序列化器
    std::cout << "--- 3. JSON Serializer ---" << std::endl;
    Serializer<JsonFormat> serializer;
    serializer.begin_object();
    serializer.write_field("name", std::string("Alice"));
    serializer.write_field("age", 30);
    serializer.write_field("height", 1.65);
    serializer.end_object();
    std::cout << "JSON: " << serializer.str() << std::endl;
    std::cout << std::endl;

    // 4. 结构体自动序列化
    std::cout << "--- 4. Struct Auto-serialization ---" << std::endl;
    Person p{"Bob", 25, 1.75};
    std::string json = auto_serialize(p, person_fields);
    std::cout << "Person JSON: " << json << std::endl;
    std::cout << std::endl;

    // 5. 二进制序列化
    std::cout << "--- 5. Binary Serialization ---" << std::endl;
    BinarySerializer bin_serializer;
    bin_serializer.write(42);
    bin_serializer.write(3.14);
    bin_serializer.write_string("hello");

    std::cout << "Binary size: " << bin_serializer.buffer().size() << " bytes" << std::endl;

    BinaryDeserializer bin_deserializer(bin_serializer.buffer());
    std::cout << "Deserialized int: " << bin_deserializer.read<int>() << std::endl;
    std::cout << "Deserialized double: " << bin_deserializer.read<double>() << std::endl;
    std::cout << "Deserialized string: " << bin_deserializer.read_string() << std::endl;
    std::cout << std::endl;

    // 6. 类型特征检测
    std::cout << "--- 6. Type Trait Detection ---" << std::endl;
    std::cout << "Person has serialize: "
              << has_serialize_method<Person>::value << std::endl;
    std::cout << "int has serialize: "
              << has_serialize_method<int>::value << std::endl;

    return 0;
}
