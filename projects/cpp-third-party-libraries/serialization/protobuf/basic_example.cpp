/**
 * @file basic_example.cpp
 * @brief Protobuf 序列化示例
 * @details 展示 Protocol Buffers 的基本用法
 *          Protobuf 是 Google 开发的序列化框架
 *          跨语言、跨平台、高效紧凑
 */

#include <iostream>
#include <string>
#include <fstream>

// 包含生成的头文件
#include "message.pb.h"

/**
 * @brief 创建消息示例
 * @details 展示如何创建和填充 Protobuf 消息
 */
void create_message() {
    std::cout << "=== 创建消息 ===" << std::endl;

    // 创建 Person 消息
    tutorial::Person person;
    person.set_name("Alice");
    person.set_id(123);
    person.set_email("alice@example.com");

    // 添加电话号码
    auto* phone1 = person.add_phones();
    phone1->set_number("123-456-7890");
    phone1->set_type(tutorial::Person::MOBILE);

    auto* phone2 = person.add_phones();
    phone2->set_number("098-765-4321");
    phone2->set_type(tutorial::Person::HOME);

    std::cout << "Person created:" << std::endl;
    std::cout << "  Name: " << person.name() << std::endl;
    std::cout << "  ID: " << person.id() << std::endl;
    std::cout << "  Email: " << person.email() << std::endl;
    std::cout << "  Phones: " << person.phones_size() << std::endl;

    for (int i = 0; i < person.phones_size(); ++i) {
        const auto& phone = person.phones(i);
        std::cout << "    " << phone.number() << " ("
                  << (phone.type() == tutorial::Person::MOBILE ? "Mobile" : "Home")
                  << ")" << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 序列化示例
 * @details 展示如何将消息序列化为二进制数据
 */
void serialize_example() {
    std::cout << "=== 序列化 ===" << std::endl;

    tutorial::Person person;
    person.set_name("Bob");
    person.set_id(456);
    person.set_email("bob@example.com");

    // 序列化为字符串
    std::string serialized;
    person.SerializeToString(&serialized);

    std::cout << "Serialized size: " << serialized.size() << " bytes" << std::endl;

    // 序列化为字节数组
    std::vector<char> bytes(serialized.begin(), serialized.end());
    std::cout << "Bytes size: " << bytes.size() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 反序列化示例
 * @details 展示如何从二进制数据反序列化消息
 */
void deserialize_example() {
    std::cout << "=== 反序列化 ===" << std::endl;

    // 创建并序列化
    tutorial::Person original;
    original.set_name("Charlie");
    original.set_id(789);
    original.set_email("charlie@example.com");

    std::string serialized;
    original.SerializeToString(&serialized);

    // 反序列化
    tutorial::Person deserialized;
    deserialized.ParseFromString(serialized);

    std::cout << "Deserialized:" << std::endl;
    std::cout << "  Name: " << deserialized.name() << std::endl;
    std::cout << "  ID: " << deserialized.id() << std::endl;
    std::cout << "  Email: " << deserialized.email() << std::endl;

    // 验证
    bool equal = (original.name() == deserialized.name() &&
                  original.id() == deserialized.id() &&
                  original.email() == deserialized.email());
    std::cout << "  Equal: " << (equal ? "Yes" : "No") << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 文件操作示例
 * @details 展示如何将消息写入和读取文件
 */
void file_operations() {
    std::cout << "=== 文件操作 ===" << std::endl;

    // 创建地址簿
    tutorial::AddressBook address_book;

    // 添加人员
    auto* person1 = address_book.add_people();
    person1->set_name("Alice");
    person1->set_id(1);
    person1->set_email("alice@example.com");

    auto* person2 = address_book.add_people();
    person2->set_name("Bob");
    person2->set_id(2);
    person2->set_email("bob@example.com");

    // 写入文件
    std::string filename = "address_book.bin";
    std::ofstream output(filename, std::ios::binary);
    address_book.SerializeToOstream(&output);
    output.close();

    std::cout << "Address book saved to " << filename << std::endl;

    // 读取文件
    tutorial::AddressBook loaded;
    std::ifstream input(filename, std::ios::binary);
    loaded.ParseFromIstream(&input);
    input.close();

    std::cout << "Loaded " << loaded.people_size() << " people:" << std::endl;
    for (int i = 0; i < loaded.people_size(); ++i) {
        const auto& person = loaded.people(i);
        std::cout << "  " << person.name() << " (ID: " << person.id() << ")" << std::endl;
    }

    // 清理
    std::remove(filename.c_str());

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Protobuf 序列化示例 ===" << std::endl;
    std::cout << std::endl;

    create_message();
    serialize_example();
    deserialize_example();
    file_operations();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}