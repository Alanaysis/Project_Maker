/**
 * @file nlohmann_example.cpp
 * @brief nlohmann/json 序列化示例
 * @details 展示 nlohmann/json 库的使用方法
 *          nlohmann/json 是最流行的 C++ JSON 库
 *          API 设计简洁，类似 Python 的 json 模块
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <nlohmann/json.hpp>

// 使用 json 别名
using json = nlohmann::json;

/**
 * @brief 基础用法示例
 * @details 展示 JSON 的创建和访问
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 JSON 对象
    json j;
    j["name"] = "John Doe";
    j["age"] = 30;
    j["city"] = "New York";

    // 访问值
    std::cout << "Name: " << j["name"] << std::endl;
    std::cout << "Age: " << j["age"] << std::endl;
    std::cout << "City: " << j["city"] << std::endl;

    // 输出 JSON 字符串
    std::cout << "\nJSON string: " << j.dump(2) << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 解析示例
 * @details 展示 JSON 字符串的解析
 */
void parsing_example() {
    std::cout << "=== 解析示例 ===" << std::endl;

    // JSON 字符串
    std::string json_str = R"({
        "name": "Alice",
        "scores": [95, 87, 92],
        "address": {
            "street": "123 Main St",
            "city": "Boston"
        }
    })";

    // 解析 JSON
    json j = json::parse(json_str);

    // 访问嵌套值
    std::cout << "Name: " << j["name"] << std::endl;
    std::cout << "First score: " << j["scores"][0] << std::endl;
    std::cout << "City: " << j["address"]["city"] << std::endl;

    // 遍历数组
    std::cout << "Scores: ";
    for (const auto& score : j["scores"]) {
        std::cout << score << " ";
    }
    std::cout << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 序列化示例
 * @details 展示 C++ 对象到 JSON 的转换
 */
void serialization_example() {
    std::cout << "=== 序列化示例 ===" << std::endl;

    // 使用结构化绑定
    struct Person {
        std::string name;
        int age;
        std::vector<std::string> hobbies;
    };

    // 自定义序列化
    Person person{"Bob", 25, {"reading", "gaming", "coding"}};

    json j;
    j["name"] = person.name;
    j["age"] = person.age;
    j["hobbies"] = person.hobbies;

    std::cout << "Serialized: " << j.dump(2) << std::endl;

    // 反序列化
    Person parsed;
    parsed.name = j["name"];
    parsed.age = j["age"];
    parsed.hobbies = j["hobbies"].get<std::vector<std::string>>();

    std::cout << "Parsed name: " << parsed.name << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 高级功能示例
 * @details 展示 JSON 的高级特性
 */
void advanced_features() {
    std::cout << "=== 高级功能 ===" << std::endl;

    // JSON Patch
    json original = {{"name", "Alice"}, {"age", 30}};
    json patch = json::parse(R"([
        {"op": "replace", "path": "/age", "value": 31},
        {"op": "add", "path": "/email", "value": "alice@example.com"}
    ])");

    json patched = original.patch(patch);
    std::cout << "Patched: " << patched.dump(2) << std::endl;

    // JSON Pointer
    json data = {{"a", {{"b", {{"c", 42}}}}}};
    int value = data.at(json::pointer("/a/b/c"));
    std::cout << "Value at /a/b/c: " << value << std::endl;

    // 类型检查
    json obj = {{"key", "value"}};
    std::cout << "Is object: " << obj.is_object() << std::endl;
    std::cout << "Is array: " << obj.is_array() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 文件操作示例
 * @details 展示 JSON 文件的读写
 */
void file_operations() {
    std::cout << "=== 文件操作 ===" << std::endl;

    // 写入文件
    json config = {
        {"version", "1.0"},
        {"settings", {
            {"debug", true},
            {"log_level", "INFO"},
            {"max_connections", 100}
        }}
    };

    // 模拟文件写入（实际使用时会写入文件）
    std::string json_str = config.dump(2);
    std::cout << "Config to write:" << std::endl;
    std::cout << json_str << std::endl;

    // 从字符串读取
    json loaded = json::parse(json_str);
    std::cout << "Loaded log_level: " << loaded["settings"]["log_level"] << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== nlohmann/json 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_usage();
    parsing_example();
    serialization_example();
    advanced_features();
    file_operations();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}