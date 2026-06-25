#include <cstdint>
#include <cstddef>
#include <string>
#include "parser.h"

/**
 * @file fuzz_target.cpp
 * @brief LibFuzzer 模糊测试目标
 *
 * LibFuzzer 是一个覆盖率引导的模糊测试引擎，内置于 Clang。
 * 它会自动生成输入数据，尝试发现程序中的 bug。
 *
 * 使用方法:
 *   clang++ -fsanitize=fuzzer,address -g -o fuzz_target fuzz_target.cpp parser.cpp -I../include
 *   ./fuzz_target corpus/
 */

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    // 将输入数据转换为字符串
    std::string input(reinterpret_cast<const char*>(data), size);

    // 测试 parse_int
    parser::parse_int(input);

    // 测试 parse_expression
    parser::parse_expression(input);

    // 测试 validate_parentheses
    parser::validate_parentheses(input);

    // 测试 parse_paren_expression
    parser::parse_paren_expression(input);

    return 0;
}
