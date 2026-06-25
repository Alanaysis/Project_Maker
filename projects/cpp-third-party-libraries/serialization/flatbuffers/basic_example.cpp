/**
 * @file basic_example.cpp
 * @brief FlatBuffers 序列化示例
 * @details 展示 FlatBuffers 的基本用法
 *          FlatBuffers 是 Google 开发的零拷贝序列化库
 *          适合游戏、性能敏感场景
 *
 * 注意：此示例需要先使用 flatc 生成代码
 * flatc --cpp schemas/message.fbs
 */

#include <iostream>
#include <string>
#include <flatbuffers/flatbuffers.h>

// 包含生成的头文件
// #include "message_generated.h"

/**
 * @brief FlatBuffers 概念说明
 * @details 介绍 FlatBuffers 的核心概念
 */
void flatbuffers_concepts() {
    std::cout << "=== FlatBuffers 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "FlatBuffers 是一个跨平台的序列化库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  1. 零拷贝 - 直接访问序列化数据" << std::endl;
    std::cout << "  2. 高性能 - 无需解析/反序列化" << std::endl;
    std::cout << "  3. 内存高效 - 紧凑的二进制格式" << std::endl;
    std::cout << "  4. 跨语言 - 支持多种编程语言" << std::endl;
    std::cout << "  5. 向前/向后兼容" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 使用流程说明
 * @details 介绍 FlatBuffers 的使用流程
 */
void usage_workflow() {
    std::cout << "=== 使用流程 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "1. 定义 Schema（.fbs 文件）" << std::endl;
    std::cout << "   table User {" << std::endl;
    std::cout << "       id:int;" << std::endl;
    std::cout << "       name:string;" << std::endl;
    std::cout << "   }" << std::endl;
    std::cout << std::endl;

    std::cout << "2. 生成代码" << std::endl;
    std::cout << "   flatc --cpp message.fbs" << std::endl;
    std::cout << std::endl;

    std::cout << "3. 使用生成的代码" << std::endl;
    std::cout << "   // 创建" << std::endl;
    std::cout << "   FlatBufferBuilder builder;" << std::endl;
    std::cout << "   auto name = builder.CreateString(\"Alice\");" << std::endl;
    std::cout << "   auto user = CreateUser(builder, 1, name);" << std::endl;
    std::cout << "   builder.Finish(user);" << std::endl;
    std::cout << std::endl;

    std::cout << "   // 读取" << std::endl;
    std::cout << "   auto user = GetUser(buffer_data);" << std::endl;
    std::cout << "   std::cout << user->name();" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 与其他序列化库对比
 * @details 比较 FlatBuffers 与其他序列化库
 */
void comparison() {
    std::cout << "=== 与其他库对比 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "FlatBuffers vs Protobuf：" << std::endl;
    std::cout << "  - FlatBuffers: 零拷贝，更快" << std::endl;
    std::cout << "  - Protobuf: 更易用，功能更全" << std::endl;
    std::cout << std::endl;

    std::cout << "FlatBuffers vs JSON：" << std::endl;
    std::cout << "  - FlatBuffers: 二进制，高性能" << std::endl;
    std::cout << "  - JSON: 文本，易调试" << std::endl;
    std::cout << std::endl;

    std::cout << "适用场景：" << std::endl;
    std::cout << "  - 游戏开发" << std::endl;
    std::cout << "  - 实时系统" << std::endl;
    std::cout << "  - 性能敏感应用" << std::endl;
    std::cout << "  - 跨语言通信" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 代码生成说明
 * @details 介绍如何生成 FlatBuffers 代码
 */
void code_generation() {
    std::cout << "=== 代码生成 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "安装 FlatBuffers 编译器：" << std::endl;
    std::cout << "  # Ubuntu" << std::endl;
    std::cout << "  sudo apt install flatbuffers-compiler" << std::endl;
    std::cout << std::endl;

    std::cout << "  # macOS" << std::endl;
    std::cout << "  brew install flatbuffers" << std::endl;
    std::cout << std::endl;

    std::cout << "  # Windows" << std::endl;
    std::cout << "  vcpkg install flatbuffers" << std::endl;
    std::cout << std::endl;

    std::cout << "生成 C++ 代码：" << std::endl;
    std::cout << "  flatc --cpp message.fbs" << std::endl;
    std::cout << std::endl;

    std::cout << "生成其他语言代码：" << std::endl;
    std::cout << "  flatc --java message.fbs" << std::endl;
    std::cout << "  flatc --python message.fbs" << std::endl;
    std::cout << "  flatc --go message.fbs" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== FlatBuffers 序列化示例 ===" << std::endl;
    std::cout << std::endl;

    flatbuffers_concepts();
    usage_workflow();
    comparison();
    code_generation();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 FlatBuffers 示例需要先生成代码" << std::endl;
    std::cout << "请运行: flatc --cpp schemas/message.fbs" << std::endl;

    return 0;
}