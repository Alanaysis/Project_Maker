/**
 * @file basic_example.cpp
 * @brief Cap'n Proto 序列化示例
 * @details 展示 Cap'n Proto 的基本用法
 *          Cap'n Proto 是一个零拷贝序列化协议
 *          极低延迟，适合 RPC 和性能敏感场景
 */

#include <iostream>
#include <string>

/**
 * @brief Cap'n Proto 概念说明
 * @details 介绍 Cap'n Proto 的核心概念
 */
void capnproto_concepts() {
    std::cout << "=== Cap'n Proto 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Cap'n Proto 是一个高效的序列化协议。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  1. 零拷贝 - 直接读取数据，无需解析" << std::endl;
    std::cout << "  2. 极快 - 比 Protocol Buffers 快得多" << std::endl;
    std::cout << "  3. 内存映射 - 可以直接 mmap 文件" << std::endl;
    std::cout << "  4. 向前/向后兼容" << std::endl;
    std::cout << "  5. 内置 RPC 框架" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 使用流程说明
 * @details 介绍 Cap'n Proto 的使用流程
 */
void usage_workflow() {
    std::cout << "=== 使用流程 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "1. 定义 Schema（.capnp 文件）" << std::endl;
    std::cout << "   @0xdbb9ad1f14bf0b36;" << std::endl;
    std::cout << "   struct Person {" << std::endl;
    std::cout << "     id @0 :UInt32;" << std::endl;
    std::cout << "     name @1 :Text;" << std::endl;
    std::cout << "     email @2 :Text;" << std::endl;
    std::cout << "   }" << std::endl;
    std::cout << std::endl;

    std::cout << "2. 生成代码" << std::endl;
    std::cout << "   capnp compile -oc++ message.capnp" << std::endl;
    std::cout << std::endl;

    std::cout << "3. 使用生成的代码" << std::endl;
    std::cout << "   // 创建消息" << std::endl;
    std::cout << "   ::capnp::MallocMessageBuilder message;" << std::endl;
    std::cout << "   auto person = message.initRoot<Person>();" << std::endl;
    std::cout << "   person.setId(1);" << std::endl;
    std::cout << "   person.setName(\"Alice\");" << std::endl;
    std::cout << std::endl;

    std::cout << "   // 序列化" << std::endl;
    std::cout << "   auto data = capnp::messageToFlatArray(message);" << std::endl;
    std::cout << std::endl;

    std::cout << "   // 反序列化" << std::endl;
    std::cout << "   auto reader = capnp::FlatArrayMessageReader(data);" << std::endl;
    std::cout << "   auto person = reader.getRoot<Person>();" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 与其他序列化库对比
 * @details 比较 Cap'n Proto 与其他序列化库
 */
void comparison() {
    std::cout << "=== 与其他库对比 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Cap'n Proto vs Protobuf：" << std::endl;
    std::cout << "  - Cap'n Proto: 零拷贝，更快" << std::endl;
    std::cout << "  - Protobuf: 更易用，更广泛" << std::endl;
    std::cout << std::endl;

    std::cout << "Cap'n Proto vs FlatBuffers：" << std::endl;
    std::cout << "  - 两者都是零拷贝" << std::endl;
    std::cout << "  - Cap'n Proto 有内置 RPC" << std::endl;
    std::cout << "  - FlatBuffers 更简单" << std::endl;
    std::cout << std::endl;

    std::cout << "适用场景：" << std::endl;
    std::cout << "  - 高性能 RPC" << std::endl;
    std::cout << "  - 低延迟系统" << std::endl;
    std::cout << "  - 内存映射文件" << std::endl;
    std::cout << "  - 实时通信" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 安装说明
 * @details 介绍如何安装 Cap'n Proto
 */
void installation() {
    std::cout << "=== 安装说明 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "安装 Cap'n Proto：" << std::endl;
    std::cout << std::endl;

    std::cout << "# Ubuntu" << std::endl;
    std::cout << "sudo apt install capnproto libcapnp-dev" << std::endl;
    std::cout << std::endl;

    std::cout << "# macOS" << std::endl;
    std::cout << "brew install capnp" << std::endl;
    std::cout << std::endl;

    std::cout << "# 从源码编译" << std::endl;
    std::cout << "git clone https://github.com/capnproto/capnproto.git" << std::endl;
    std::cout << "cd capnproto/c++" << std::endl;
    std::cout << "cmake -B build" << std::endl;
    std::cout << "cmake --build build" << std::endl;
    std::cout << "sudo cmake --install build" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Cap'n Proto 序列化示例 ===" << std::endl;
    std::cout << std::endl;

    capnproto_concepts();
    usage_workflow();
    comparison();
    installation();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 Cap'n Proto 示例需要先生成代码" << std::endl;
    std::cout << "请运行: capnp compile -oc++ schemas/message.capnp" << std::endl;

    return 0;
}