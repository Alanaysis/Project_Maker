#include <iostream>
#include <cassert>
#include <cstring>

#include "io.h"

using namespace simple_vm;

// 简单的测试框架
#define TEST(name) \
    void test_##name(); \
    struct TestRunner_##name { \
        TestRunner_##name() { \
            std::cout << "Running " #name "... "; \
            test_##name(); \
            std::cout << "PASSED" << std::endl; \
        } \
    } runner_##name; \
    void test_##name()

#define ASSERT(condition) \
    do { \
        if (!(condition)) { \
            std::cerr << "Assertion failed: " #condition << std::endl; \
            std::cerr << "  at " << __FILE__ << ":" << __LINE__ << std::endl; \
            exit(1); \
        } \
    } while (0)

#define ASSERT_EQ(a, b) \
    do { \
        if ((a) != (b)) { \
            std::cerr << "Assertion failed: " #a " == " #b << std::endl; \
            std::cerr << "  Expected: " << (b) << std::endl; \
            std::cerr << "  Got: " << (a) << std::endl; \
            std::cerr << "  at " << __FILE__ << ":" << __LINE__ << std::endl; \
            exit(1); \
        } \
    } while (0)

// 测试串口输出
TEST(serial_port_output) {
    // 使用字符串缓冲区
    char buffer[256];
    memset(buffer, 0, sizeof(buffer));
    FILE* output = fmemopen(buffer, sizeof(buffer), "w");

    SerialPort serial(0x3F8, output);

    // 输出字符 'A'
    uint32_t data = 'A';
    bool result = serial.handle_port_out(0x3F8, data, 1);
    ASSERT(result);

    // 刷新缓冲区
    fflush(output);

    // 验证输出
    ASSERT_EQ(buffer[0], 'A');

    fclose(output);
}

// 测试串口多字符输出
TEST(serial_port_multiple_chars) {
    char buffer[256];
    memset(buffer, 0, sizeof(buffer));
    FILE* output = fmemopen(buffer, sizeof(buffer), "w");

    SerialPort serial(0x3F8, output);

    // 输出 "Hello"
    const char* str = "Hello";
    for (int i = 0; str[i]; i++) {
        uint32_t data = str[i];
        serial.handle_port_out(0x3F8, data, 1);
    }

    fflush(output);

    // 验证输出
    ASSERT_EQ(strcmp(buffer, "Hello"), 0);

    fclose(output);
}

// 测试串口 LSR 读取
TEST(serial_port_lsr) {
    SerialPort serial;

    uint32_t data = 0;
    bool result = serial.handle_port_in(0x3F8 + 5, data, 1);
    ASSERT(result);

    // LSR 应该有 THRE 和 TSRE 位设置
    ASSERT(data & 0x20);  // THRE
    ASSERT(data & 0x40);  // TSRE
}

// 测试串口输出缓冲区
TEST(serial_port_buffer) {
    SerialPort serial;

    // 输出字符
    uint32_t data = 'X';
    serial.handle_port_out(0x3F8, data, 1);

    // 检查缓冲区
    std::string output = serial.get_output();
    ASSERT_EQ(output, "X");

    // 清空缓冲区
    serial.clear_output();
    output = serial.get_output();
    ASSERT_EQ(output, "");
}

// 测试调试端口
TEST(debug_port) {
    DebugPort debug(0x402);

    // 输出字符
    uint32_t data = 'D';
    bool result = debug.handle_port_out(0x402, data, 1);
    ASSERT(result);

    // 检查输出
    std::string output = debug.get_output();
    ASSERT_EQ(output, "D");
}

// 测试调试端口读取
TEST(debug_port_read) {
    DebugPort debug(0x402);

    uint32_t data = 0xFF;
    bool result = debug.handle_port_in(0x402, data, 1);
    ASSERT(result);
    ASSERT_EQ(data, 0);
}

// 测试复合 I/O 处理器
TEST(composite_handler) {
    CompositeIOHandler composite;

    // 添加串口
    composite.add_handler(std::make_unique<SerialPort>());

    // 输出字符
    uint32_t data = 'C';
    bool result = composite.handle_port_out(0x3F8, data, 1);
    ASSERT(result);
}

// 测试复合处理器端口路由
TEST(composite_routing) {
    CompositeIOHandler composite;

    // 添加调试端口
    composite.add_handler(std::make_unique<DebugPort>(0x402));

    // 输出到调试端口
    uint32_t data = 'R';
    bool result = composite.handle_port_out(0x402, data, 1);
    ASSERT(result);

    // 输出到未处理的端口（应该成功但被忽略）
    result = composite.handle_port_out(0x1234, data, 1);
    ASSERT(result);
}

// 测试端口范围检查
TEST(port_range_check) {
    SerialPort serial(0x3F8);

    // 端口范围外的端口
    uint32_t data = 0;
    bool result = serial.handle_port_in(0x100, data, 1);
    ASSERT(!result);

    result = serial.handle_port_out(0x100, data, 1);
    ASSERT(!result);
}

// 主函数
int main() {
    std::cout << "=== I/O Tests ===" << std::endl;
    std::cout << std::endl;

    // 测试会自动运行

    std::cout << std::endl;
    std::cout << "All I/O tests passed!" << std::endl;

    return 0;
}
