/**
 * @file rapidjson_example.cpp
 * @brief RapidJSON 序列化示例
 * @details 展示 RapidJSON 的基本用法
 *          RapidJSON 是一个高性能的 JSON 库
 *          适合性能敏感场景
 */

#include <iostream>
#include <string>
#include <rapidjson/document.h>
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>

/**
 * @brief 基础用法示例
 * @details 展示 RapidJSON 的基本操作
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // JSON 字符串
    const char* json = R"({
        "name": "Alice",
        "age": 30,
        "city": "New York"
    })";

    // 解析 JSON
    rapidjson::Document document;
    document.Parse(json);

    // 检查解析是否成功
    if (document.HasParseError()) {
        std::cerr << "JSON parse error" << std::endl;
        return;
    }

    // 访问值
    std::cout << "Name: " << document["name"].GetString() << std::endl;
    std::cout << "Age: " << document["age"].GetInt() << std::endl;
    std::cout << "City: " << document["city"].GetString() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 创建 JSON 示例
 * @details 展示如何创建 JSON 对象
 */
void create_json() {
    std::cout << "=== 创建 JSON ===" << std::endl;

    // 创建 JSON 对象
    rapidjson::Document document;
    document.SetObject();

    // 添加成员
    rapidjson::Document::AllocatorType& allocator = document.GetAllocator();

    document.AddMember("name", "Bob", allocator);
    document.AddMember("age", 25, allocator);
    document.AddMember("city", "Boston", allocator);

    // 添加数组
    rapidjson::Value hobbies(rapidjson::kArrayType);
    hobbies.PushBack("reading", allocator);
    hobbies.PushBack("gaming", allocator);
    hobbies.PushBack("coding", allocator);
    document.AddMember("hobbies", hobbies, allocator);

    // 序列化为字符串
    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    document.Accept(writer);

    std::cout << "JSON: " << buffer.GetString() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 嵌套对象示例
 * @details 展示如何处理嵌套的 JSON 对象
 */
void nested_objects() {
    std::cout << "=== 嵌套对象 ===" << std::endl;

    const char* json = R"({
        "user": {
            "name": "Charlie",
            "age": 35,
            "address": {
                "street": "123 Main St",
                "city": "Chicago"
            }
        }
    })";

    rapidjson::Document document;
    document.Parse(json);

    // 访问嵌套对象
    const rapidjson::Value& user = document["user"];
    std::cout << "Name: " << user["name"].GetString() << std::endl;
    std::cout << "Age: " << user["age"].GetInt() << std::endl;

    const rapidjson::Value& address = user["address"];
    std::cout << "Street: " << address["street"].GetString() << std::endl;
    std::cout << "City: " << address["city"].GetString() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 数组处理示例
 * @details 展示如何处理 JSON 数组
 */
void array_handling() {
    std::cout << "=== 数组处理 ===" << std::endl;

    const char* json = R"({
        "scores": [95, 87, 92, 78, 88]
    })";

    rapidjson::Document document;
    document.Parse(json);

    // 遍历数组
    const rapidjson::Value& scores = document["scores"];
    std::cout << "Scores: ";
    for (rapidjson::SizeType i = 0; i < scores.Size(); ++i) {
        std::cout << scores[i].GetInt() << " ";
    }
    std::cout << std::endl;

    // 计算平均分
    double sum = 0;
    for (rapidjson::SizeType i = 0; i < scores.Size(); ++i) {
        sum += scores[i].GetInt();
    }
    double average = sum / scores.Size();
    std::cout << "Average: " << average << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 类型检查示例
 * @details 展示如何检查 JSON 值的类型
 */
void type_checking() {
    std::cout << "=== 类型检查 ===" << std::endl;

    const char* json = R"({
        "string": "hello",
        "number": 42,
        "float": 3.14,
        "boolean": true,
        "null": null,
        "array": [1, 2, 3],
        "object": {"key": "value"}
    })";

    rapidjson::Document document;
    document.Parse(json);

    // 检查类型
    std::cout << "string is string: " << document["string"].IsString() << std::endl;
    std::cout << "number is int: " << document["number"].IsInt() << std::endl;
    std::cout << "float is double: " << document["float"].IsDouble() << std::endl;
    std::cout << "boolean is bool: " << document["boolean"].IsBool() << std::endl;
    std::cout << "null is null: " << document["null"].IsNull() << std::endl;
    std::cout << "array is array: " << document["array"].IsArray() << std::endl;
    std::cout << "object is object: " << document["object"].IsObject() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief RapidJSON 概念说明
 * @details 介绍 RapidJSON 的核心概念
 */
void rapidjson_concepts() {
    std::cout << "=== RapidJSON 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "RapidJSON 是一个高性能的 JSON 库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 高性能" << std::endl;
    std::cout << "  - SAX/DOM 解析" << std::endl;
    std::cout << "  - 内存池" << std::endl;
    std::cout << "  - 头文件库" << std::endl;
    std::cout << std::endl;

    std::cout << "与 nlohmann/json 对比：" << std::endl;
    std::cout << "  - RapidJSON: 更快，更底层" << std::endl;
    std::cout << "  - nlohmann/json: 更易用，更现代" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== RapidJSON 序列化示例 ===" << std::endl;
    std::cout << std::endl;

    rapidjson_concepts();
    basic_usage();
    create_json();
    nested_objects();
    array_handling();
    type_checking();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}