#ifndef SIMPLE_VM_VM_H
#define SIMPLE_VM_VM_H

#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include <functional>

namespace simple_vm {

// 前向声明
class VCPU;
class IOHandler;

// VM 错误码
enum class VMError {
    Success = 0,
    KVMOpenFailed,
    KVMVersionMismatch,
    VMCreateFailed,
    VCPUCreateFailed,
    MemoryAllocFailed,
    MemoryMapFailed,
    RunFailed,
    InvalidConfig,
    IOError,
    ProgramLoadFailed,
};

// VM 配置
struct VMConfig {
    size_t memory_size = 4 * 1024 * 1024;  // 默认 4MB
    int vcpu_count = 1;                      // 默认 1 个 vCPU
    std::string kernel_path;                 // 内核镜像路径（可选）
};

// VM 状态
enum class VMState {
    Created,
    Running,
    Stopped,
    Error,
};

// VM 类 - 虚拟机监控器的核心类
class VM {
public:
    // 工厂方法 - 创建 VM 实例
    static std::unique_ptr<VM> create(const VMConfig& config);

    // 析构函数 - 自动清理资源
    ~VM();

    // 禁止拷贝和赋值
    VM(const VM&) = delete;
    VM& operator=(const VM&) = delete;

    // 加载程序到 Guest 内存
    // path: 程序文件路径
    // load_addr: 加载地址（Guest 物理地址）
    bool load_program(const std::string& path, uint64_t load_addr);

    // 直接写入 Guest 内存
    bool write_guest_memory(uint64_t addr, const void* data, size_t size);

    // 读取 Guest 内存
    bool read_guest_memory(uint64_t addr, void* data, size_t size);

    // 运行 VM
    // 返回 true 表示正常退出，false 表示错误
    bool run();

    // 停止 VM
    void stop();

    // 获取 VM 状态
    VMState get_state() const { return state_; }

    // 获取错误信息
    std::string get_error_message() const { return error_message_; }

    // 设置 I/O 处理器
    void set_io_handler(std::unique_ptr<IOHandler> handler);

    // 获取 vCPU 数量
    int get_vcpu_count() const { return vcpus_.size(); }

private:
    VM();  // 私有构造函数，使用 create() 工厂方法

    // 初始化 VM
    bool init(const VMConfig& config);

    // 清理资源
    void cleanup();

    // 初始化内存
    bool init_memory(size_t size);

    // 初始化 vCPU
    bool init_vcpus(int count);

    // 运行单个 vCPU
    bool run_vcpu(int vcpu_index);

    // KVM 相关文件描述符
    int kvm_fd_ = -1;      // /dev/kvm 文件描述符
    int vm_fd_ = -1;       // VM 文件描述符

    // Guest 内存
    uint8_t* memory_ = nullptr;
    size_t memory_size_ = 0;

    // vCPU 列表
    std::vector<std::unique_ptr<VCPU>> vcpus_;

    // I/O 处理器
    std::unique_ptr<IOHandler> io_handler_;

    // VM 状态
    VMState state_ = VMState::Created;
    bool running_ = false;

    // 错误信息
    std::string error_message_;

    // 配置
    VMConfig config_;
};

}  // namespace simple_vm

#endif  // SIMPLE_VM_VM_H
