#ifndef SIMPLE_VM_MEMORY_H
#define SIMPLE_VM_MEMORY_H

#include <cstdint>
#include <cstddef>

namespace simple_vm {

// 内存区域标志
enum MemoryFlags {
    MEM_READ = 1 << 0,
    MEM_WRITE = 1 << 1,
    MEM_EXEC = 1 << 2,
};

// 内存区域描述
struct MemoryRegion {
    uint64_t guest_phys_addr;  // Guest 物理地址
    uint64_t host_virt_addr;   // Host 虚拟地址
    size_t size;               // 区域大小
    uint32_t flags;            // 访问权限
};

// 内存管理器类
class MemoryManager {
public:
    MemoryManager();
    ~MemoryManager();

    // 禁止拷贝和赋值
    MemoryManager(const MemoryManager&) = delete;
    MemoryManager& operator=(const MemoryManager&) = delete;

    // 分配 Guest 内存
    // size: 内存大小（字节）
    // 返回内存指针，失败返回 nullptr
    uint8_t* alloc_guest_memory(size_t size);

    // 释放 Guest 内存
    void free_guest_memory();

    // 获取内存指针
    uint8_t* get_memory() const { return memory_; }

    // 获取内存大小
    size_t get_size() const { return memory_size_; }

    // 写入数据到 Guest 内存
    bool write(uint64_t addr, const void* data, size_t size);

    // 从 Guest 内存读取数据
    bool read(uint64_t addr, void* data, size_t size);

    // 加载文件到 Guest 内存
    bool load_file(const std::string& path, uint64_t load_addr);

    // 清零内存
    void clear();

private:
    // Guest 内存
    uint8_t* memory_ = nullptr;
    size_t memory_size_ = 0;
};

}  // namespace simple_vm

#endif  // SIMPLE_VM_MEMORY_H
