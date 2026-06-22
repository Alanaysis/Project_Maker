#include <iostream>
#include <cassert>
#include <cstring>

#include "vm.h"
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

#define ASSERT_NE(a, b) \
    do { \
        if ((a) == (b)) { \
            std::cerr << "Assertion failed: " #a " != " #b << std::endl; \
            std::cerr << "  at " << __FILE__ << ":" << __LINE__ << std::endl; \
            exit(1); \
        } \
    } while (0)

// 测试 VM 创建
TEST(vm_creation) {
    VMConfig config;
    config.memory_size = 4 * 1024 * 1024;  // 4MB
    config.vcpu_count = 1;

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);
    ASSERT_EQ(vm->get_state(), VMState::Created);
}

// 测试无效配置
TEST(invalid_config) {
    // 内存为 0
    VMConfig config1;
    config1.memory_size = 0;
    auto vm1 = VM::create(config1);
    ASSERT_EQ(vm1, nullptr);

    // vCPU 数量为 0
    VMConfig config2;
    config2.memory_size = 4 * 1024 * 1024;
    config2.vcpu_count = 0;
    auto vm2 = VM::create(config2);
    ASSERT_EQ(vm2, nullptr);
}

// 测试内存读写
TEST(memory_read_write) {
    VMConfig config;
    config.memory_size = 4 * 1024 * 1024;
    config.vcpu_count = 1;

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);

    // 写入数据
    const char* test_data = "Hello, VM!";
    bool result = vm->write_guest_memory(0x1000, test_data, strlen(test_data));
    ASSERT(result);

    // 读取数据
    char buffer[256];
    memset(buffer, 0, sizeof(buffer));
    result = vm->read_guest_memory(0x1000, buffer, strlen(test_data));
    ASSERT(result);

    // 验证数据
    ASSERT_EQ(strcmp(buffer, test_data), 0);
}

// 测试边界检查
TEST(memory_bounds_check) {
    VMConfig config;
    config.memory_size = 4 * 1024 * 1024;
    config.vcpu_count = 1;

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);

    // 写入超出范围
    char data[] = "test";
    bool result = vm->write_guest_memory(config.memory_size, data, sizeof(data));
    ASSERT(!result);

    // 读取超出范围
    char buffer[256];
    result = vm->read_guest_memory(config.memory_size, buffer, sizeof(buffer));
    ASSERT(!result);
}

// 测试程序加载
TEST(load_program) {
    VMConfig config;
    config.memory_size = 4 * 1024 * 1024;
    config.vcpu_count = 1;

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);

    // 创建一个临时测试文件
    const char* test_file = "/tmp/test_program.bin";
    FILE* f = fopen(test_file, "wb");
    if (f) {
        // 写入一个简单的程序（HLT 指令）
        uint8_t hlt = 0xF4;
        fwrite(&hlt, 1, 1, f);
        fclose(f);

        // 加载程序
        bool result = vm->load_program(test_file, 0x7C00);
        ASSERT(result);

        // 清理
        remove(test_file);
    }
}

// 测试 vCPU 数量
TEST(vcpu_count) {
    VMConfig config;
    config.memory_size = 4 * 1024 * 1024;
    config.vcpu_count = 1;

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);
    ASSERT_EQ(vm->get_vcpu_count(), 1);
}

// 测试 I/O 处理器设置
TEST(io_handler) {
    VMConfig config;
    config.memory_size = 4 * 1024 * 1024;
    config.vcpu_count = 1;

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);

    // 设置 I/O 处理器
    auto io_handler = std::make_unique<CompositeIOHandler>();
    io_handler->add_handler(std::make_unique<SerialPort>());
    vm->set_io_handler(std::move(io_handler));
}

// 测试 VM 停止
TEST(vm_stop) {
    VMConfig config;
    config.memory_size = 4 * 1024 * 1024;
    config.vcpu_count = 1;

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);

    // 停止 VM（应该不会崩溃）
    vm->stop();
}

// 测试多次创建和销毁
TEST(multiple_create_destroy) {
    for (int i = 0; i < 10; i++) {
        VMConfig config;
        config.memory_size = 4 * 1024 * 1024;
        config.vcpu_count = 1;

        auto vm = VM::create(config);
        ASSERT_NE(vm, nullptr);
    }
}

// 主函数
int main() {
    std::cout << "=== Simple VM Tests ===" << std::endl;
    std::cout << std::endl;

    // 测试会自动运行（通过 TestRunner）

    std::cout << std::endl;
    std::cout << "All tests passed!" << std::endl;

    return 0;
}
