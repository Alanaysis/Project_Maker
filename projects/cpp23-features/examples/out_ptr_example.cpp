/**
 * @file out_ptr_example.cpp
 * @brief C++23 std::out_ptr 示例
 *
 * std::out_ptr 是 C++23 引入的输出指针适配器，用于简化 C API 的使用。
 * 它可以将智能指针转换为原始指针的指针，便于传递给 C API。
 *
 * 主要特点：
 * - 简化智能指针与 C API 的交互
 * - 自动管理资源生命周期
 * - 支持 unique_ptr 和 shared_ptr
 * - 避免资源泄漏
 *
 * 编译命令：
 * g++ -std=c++23 -o out_ptr_example out_ptr_example.cpp
 */

#include <iostream>
#include <memory>
#include <cstdio>
#include <cstring>
#include <string>
#include <stdexcept>

// 模拟 C API
extern "C" {
    // 模拟的 C 结构体
    typedef struct {
        char* data;
        size_t size;
    } c_buffer_t;

    // 模拟的 C API 函数：创建缓冲区
    int c_buffer_create(c_buffer_t** buffer, size_t size) {
        if (!buffer || size == 0) return -1;

        *buffer = (c_buffer_t*)malloc(sizeof(c_buffer_t));
        if (!*buffer) return -1;

        (*buffer)->data = (char*)malloc(size);
        if (!(*buffer)->data) {
            free(*buffer);
            *buffer = nullptr;
            return -1;
        }

        (*buffer)->size = size;
        memset((*buffer)->data, 0, size);
        return 0;
    }

    // 模拟的 C API 函数：销毁缓冲区
    void c_buffer_destroy(c_buffer_t* buffer) {
        if (buffer) {
            free(buffer->data);
            free(buffer);
        }
    }

    // 模拟的 C API 函数：设置数据
    int c_buffer_set(c_buffer_t* buffer, const char* data, size_t size) {
        if (!buffer || !data || size > buffer->size) return -1;
        memcpy(buffer->data, data, size);
        return 0;
    }

    // 模拟的 C API 函数：获取数据
    const char* c_buffer_get(const c_buffer_t* buffer) {
        return buffer ? buffer->data : nullptr;
    }

    // 模拟的 C API 函数：获取大小
    size_t c_buffer_size(const c_buffer_t* buffer) {
        return buffer ? buffer->size : 0;
    }
}

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 传统方式：手动管理资源
    {
        c_buffer_t* raw_buffer = nullptr;
        if (c_buffer_create(&raw_buffer, 256) != 0) {
            std::cerr << "Failed to create buffer" << std::endl;
            return;
        }

        c_buffer_set(raw_buffer, "Hello, C API!", 13);
        std::cout << "Traditional: " << c_buffer_get(raw_buffer) << std::endl;

        c_buffer_destroy(raw_buffer);
    }

    // 使用 std::out_ptr
    {
        std::unique_ptr<c_buffer_t, decltype(&c_buffer_destroy)> buffer(
            nullptr, &c_buffer_destroy
        );

        if (c_buffer_create(std::out_ptr(buffer), 256) != 0) {
            std::cerr << "Failed to create buffer" << std::endl;
            return;
        }

        c_buffer_set(buffer.get(), "Hello, out_ptr!", 15);
        std::cout << "out_ptr: " << c_buffer_get(buffer.get()) << std::endl;

        // 自动销毁
    }
}

// ========== 2. 使用自定义删除器 ==========

void custom_deleter() {
    std::cout << "\n=== 自定义删除器 ===" << std::endl;

    // 定义删除器
    struct BufferDeleter {
        void operator()(c_buffer_t* buffer) const {
            std::cout << "  Destroying buffer..." << std::endl;
            c_buffer_destroy(buffer);
        }
    };

    // 使用 unique_ptr 和自定义删除器
    std::unique_ptr<c_buffer_t, BufferDeleter> buffer;

    if (c_buffer_create(std::out_ptr(buffer), 512) != 0) {
        std::cerr << "Failed to create buffer" << std::endl;
        return;
    }

    c_buffer_set(buffer.get(), "Custom deleter works!", 20);
    std::cout << "Data: " << c_buffer_get(buffer.get()) << std::endl;

    // 离开作用域时自动调用删除器
}

// ========== 3. 文件操作示例 ==========

void file_operations() {
    std::cout << "\n=== 文件操作示例 ===" << std::endl;

    // 使用 unique_ptr 管理 FILE*
    auto file_deleter = [](FILE* f) {
        if (f) {
            std::cout << "  Closing file..." << std::endl;
            fclose(f);
        }
    };

    std::unique_ptr<FILE, decltype(file_deleter)> file(nullptr, file_deleter);

    // 打开文件
    file.reset(fopen("/tmp/test_cpp23.txt", "w"));
    if (!file) {
        std::cerr << "Failed to open file" << std::endl;
        return;
    }

    fprintf(file.get(), "Hello from C++23!\n");
    fprintf(file.get(), "Using std::out_ptr\n");

    // 文件会在离开作用域时自动关闭
}

// ========== 4. 多个资源管理 ==========

void multiple_resources() {
    std::cout << "\n=== 多个资源管理 ===" << std::endl;

    // 管理多个缓冲区
    std::unique_ptr<c_buffer_t, decltype(&c_buffer_destroy)> buffer1(nullptr, &c_buffer_destroy);
    std::unique_ptr<c_buffer_t, decltype(&c_buffer_destroy)> buffer2(nullptr, &c_buffer_destroy);

    if (c_buffer_create(std::out_ptr(buffer1), 128) != 0 ||
        c_buffer_create(std::out_ptr(buffer2), 256) != 0) {
        std::cerr << "Failed to create buffers" << std::endl;
        return;
    }

    c_buffer_set(buffer1.get(), "Buffer 1", 8);
    c_buffer_set(buffer2.get(), "Buffer 2", 8);

    std::cout << "Buffer 1: " << c_buffer_get(buffer1.get()) << std::endl;
    std::cout << "Buffer 2: " << c_buffer_get(buffer2.get()) << std::endl;

    // 所有缓冲区会在离开作用域时自动销毁
}

// ========== 5. 与 shared_ptr 结合 ==========

void shared_ptr_example() {
    std::cout << "\n=== 与 shared_ptr 结合 ===" << std::endl;

    // shared_ptr 也需要 out_ptr
    std::shared_ptr<c_buffer_t> buffer(nullptr, c_buffer_destroy);

    if (c_buffer_create(std::out_ptr(buffer), 128) != 0) {
        std::cerr << "Failed to create buffer" << std::endl;
        return;
    }

    c_buffer_set(buffer.get(), "Shared buffer", 13);
    std::cout << "Data: " << c_buffer_get(buffer.get()) << std::endl;

    // 共享所有权
    auto buffer2 = buffer;
    std::cout << "Shared count: " << buffer.use_count() << std::endl;
}

// ========== 6. 错误处理 ==========

void error_handling() {
    std::cout << "\n=== 错误处理 ===" << std::endl;

    std::unique_ptr<c_buffer_t, decltype(&c_buffer_destroy)> buffer(nullptr, &c_buffer_destroy);

    // 尝试创建缓冲区
    int result = c_buffer_create(std::out_ptr(buffer), 0);  // 大小为 0 会失败
    if (result != 0) {
        std::cout << "Expected error: buffer creation failed (size = 0)" << std::endl;
    }

    // 使用更大的大小
    result = c_buffer_create(std::out_ptr(buffer), 128);
    if (result == 0) {
        std::cout << "Buffer created successfully" << std::endl;
        c_buffer_set(buffer.get(), "Error handling works", 20);
        std::cout << "Data: " << c_buffer_get(buffer.get()) << std::endl;
    }
}

// ========== 7. 封装 C API ==========

class BufferWrapper {
private:
    std::unique_ptr<c_buffer_t, decltype(&c_buffer_destroy)> buffer_;

public:
    BufferWrapper() : buffer_(nullptr, &c_buffer_destroy) {}

    bool create(size_t size) {
        return c_buffer_create(std::out_ptr(buffer_), size) == 0;
    }

    bool set(const std::string& data) {
        if (!buffer_) return false;
        return c_buffer_set(buffer_.get(), data.c_str(), data.size()) == 0;
    }

    std::string get() const {
        if (!buffer_) return "";
        const char* data = c_buffer_get(buffer_.get());
        return data ? std::string(data, c_buffer_size(buffer_.get())) : "";
    }

    size_t size() const {
        return buffer_ ? c_buffer_size(buffer_.get()) : 0;
    }

    explicit operator bool() const {
        return buffer_ != nullptr;
    }
};

void wrapper_example() {
    std::cout << "\n=== 封装 C API ===" << std::endl;

    BufferWrapper buffer;

    if (buffer.create(256)) {
        buffer.set("Wrapped C API");
        std::cout << "Data: " << buffer.get() << std::endl;
        std::cout << "Size: " << buffer.size() << std::endl;
    } else {
        std::cerr << "Failed to create buffer" << std::endl;
    }
}

// ========== 8. 性能考虑 ==========

void performance_considerations() {
    std::cout << "\n=== 性能考虑 ===" << std::endl;

    // out_ptr 本身没有运行时开销
    // 它只是一个适配器，在编译时解析

    std::unique_ptr<c_buffer_t, decltype(&c_buffer_destroy)> buffer(nullptr, &c_buffer_destroy);

    // 创建多个缓冲区
    for (int i = 0; i < 5; ++i) {
        if (c_buffer_create(std::out_ptr(buffer), 64) == 0) {
            std::string data = "Buffer " + std::to_string(i);
            c_buffer_set(buffer.get(), data.c_str(), data.size());
            std::cout << "Created: " << c_buffer_get(buffer.get()) << std::endl;
        }
        // buffer 会在下次循环时自动释放并重新创建
    }
}

int main() {
    std::cout << "C++23 std::out_ptr 示例\n" << std::endl;

    basic_usage();
    custom_deleter();
    file_operations();
    multiple_resources();
    shared_ptr_example();
    error_handling();
    wrapper_example();
    performance_considerations();

    return 0;
}
