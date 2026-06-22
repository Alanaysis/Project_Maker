#include "vm.h"
#include "vcpu.h"
#include "memory.h"
#include "io.h"

#include <iostream>
#include <fstream>
#include <cstring>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/kvm.h>

namespace simple_vm {

// 构造函数
VM::VM() = default;

// 析构函数
VM::~VM() {
    cleanup();
}

// 工厂方法 - 创建 VM 实例
std::unique_ptr<VM> VM::create(const VMConfig& config) {
    // 验证配置
    if (config.memory_size == 0) {
        return nullptr;
    }
    if (config.vcpu_count <= 0) {
        return nullptr;
    }

    auto vm = std::unique_ptr<VM>(new VM());
    if (!vm->init(config)) {
        return nullptr;
    }
    return vm;
}

// 初始化 VM
bool VM::init(const VMConfig& config) {
    config_ = config;

    // 1. 打开 KVM 设备
    kvm_fd_ = open("/dev/kvm", O_RDWR | O_CLOEXEC);
    if (kvm_fd_ < 0) {
        error_message_ = "Failed to open /dev/kvm: " + std::string(strerror(errno));
        return false;
    }

    // 2. 检查 KVM API 版本
    int api_version = ioctl(kvm_fd_, KVM_GET_API_VERSION, 0);
    if (api_version != KVM_API_VERSION) {
        error_message_ = "KVM API version mismatch: expected " +
                        std::to_string(KVM_API_VERSION) +
                        ", got " + std::to_string(api_version);
        cleanup();
        return false;
    }

    // 3. 创建 VM
    vm_fd_ = ioctl(kvm_fd_, KVM_CREATE_VM, 0);
    if (vm_fd_ < 0) {
        error_message_ = "Failed to create VM: " + std::string(strerror(errno));
        cleanup();
        return false;
    }

    // 4. 初始化内存
    if (!init_memory(config.memory_size)) {
        cleanup();
        return false;
    }

    // 5. 初始化 vCPU
    if (!init_vcpus(config.vcpu_count)) {
        cleanup();
        return false;
    }

    state_ = VMState::Created;
    return true;
}

// 清理资源
void VM::cleanup() {
    // 释放 vCPU
    vcpus_.clear();

    // 释放内存
    if (memory_) {
        munmap(memory_, memory_size_);
        memory_ = nullptr;
        memory_size_ = 0;
    }

    // 关闭文件描述符
    if (vm_fd_ >= 0) {
        close(vm_fd_);
        vm_fd_ = -1;
    }
    if (kvm_fd_ >= 0) {
        close(kvm_fd_);
        kvm_fd_ = -1;
    }
}

// 初始化内存
bool VM::init_memory(size_t size) {
    // 分配内存
    memory_ = static_cast<uint8_t*>(
        mmap(nullptr, size,
             PROT_READ | PROT_WRITE,
             MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE,
             -1, 0)
    );

    if (memory_ == MAP_FAILED) {
        error_message_ = "Failed to allocate memory: " + std::string(strerror(errno));
        memory_ = nullptr;
        return false;
    }

    memory_size_ = size;

    // 清零内存
    memset(memory_, 0, size);

    // 设置用户空间内存区域
    struct kvm_userspace_memory_region region = {
        .slot = 0,
        .flags = 0,
        .guest_phys_addr = 0,
        .memory_size = size,
        .userspace_addr = reinterpret_cast<uint64_t>(memory_),
    };

    int ret = ioctl(vm_fd_, KVM_SET_USER_MEMORY_REGION, &region);
    if (ret < 0) {
        error_message_ = "Failed to set user memory region: " + std::string(strerror(errno));
        cleanup();
        return false;
    }

    return true;
}

// 初始化 vCPU
bool VM::init_vcpus(int count) {
    for (int i = 0; i < count; i++) {
        auto vcpu = std::make_unique<VCPU>(vm_fd_, kvm_fd_, io_handler_.get());
        if (!vcpu->init()) {
            error_message_ = "Failed to create vCPU " + std::to_string(i);
            return false;
        }
        vcpus_.push_back(std::move(vcpu));
    }
    return true;
}

// 加载程序到 Guest 内存
bool VM::load_program(const std::string& path, uint64_t load_addr) {
    // 打开文件
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        error_message_ = "Failed to open program file: " + path;
        return false;
    }

    // 获取文件大小
    size_t file_size = file.tellg();
    file.seekg(0, std::ios::beg);

    // 检查地址范围
    if (file_size > memory_size_ || load_addr > memory_size_ - file_size) {
        error_message_ = "Program exceeds memory bounds";
        return false;
    }

    // 读取文件到内存
    if (!file.read(reinterpret_cast<char*>(memory_ + load_addr), file_size)) {
        error_message_ = "Failed to read program file";
        return false;
    }

    // 设置入口点
    for (auto& vcpu : vcpus_) {
        if (!vcpu->set_entry_point(load_addr)) {
            error_message_ = "Failed to set entry point";
            return false;
        }
    }

    std::cout << "Loaded program: " << path
              << " (" << file_size << " bytes)"
              << " at address 0x" << std::hex << load_addr << std::dec
              << std::endl;

    return true;
}

// 写入 Guest 内存
bool VM::write_guest_memory(uint64_t addr, const void* data, size_t size) {
    if (addr + size > memory_size_) {
        error_message_ = "Write out of bounds";
        return false;
    }

    memcpy(memory_ + addr, data, size);
    return true;
}

// 读取 Guest 内存
bool VM::read_guest_memory(uint64_t addr, void* data, size_t size) {
    if (addr + size > memory_size_) {
        error_message_ = "Read out of bounds";
        return false;
    }

    memcpy(data, memory_ + addr, size);
    return true;
}

// 设置 I/O 处理器
void VM::set_io_handler(std::unique_ptr<IOHandler> handler) {
    io_handler_ = std::move(handler);

    // 更新所有 vCPU 的 I/O 处理器
    for (auto& vcpu : vcpus_) {
        // 注意：这里需要重新创建 vCPU 来更新 io_handler
        // 在实际实现中，可能需要更好的方式来更新 io_handler
    }
}

// 运行 VM
bool VM::run() {
    if (vcpus_.empty()) {
        error_message_ = "No vCPUs available";
        return false;
    }

    running_ = true;
    state_ = VMState::Running;

    std::cout << "VM is running..." << std::endl;

    // 运行第一个 vCPU（单 vCPU 模式）
    bool success = run_vcpu(0);

    running_ = false;
    state_ = success ? VMState::Stopped : VMState::Error;

    return success;
}

// 运行单个 vCPU
bool VM::run_vcpu(int vcpu_index) {
    if (vcpu_index >= static_cast<int>(vcpus_.size())) {
        error_message_ = "Invalid vCPU index";
        return false;
    }

    auto& vcpu = vcpus_[vcpu_index];

    while (running_) {
        // 运行 vCPU
        int ret = vcpu->run();
        if (ret < 0) {
            error_message_ = "vCPU run failed";
            return false;
        }

        // 获取退出原因
        ExitReason reason = vcpu->get_exit_reason();

        switch (reason) {
            case ExitReason::HLT:
                // Guest 执行了 HLT 指令，正常退出
                std::cout << "VM halted" << std::endl;
                return true;

            case ExitReason::IO:
                // I/O 操作已由 vCPU 处理
                break;

            case ExitReason::MMIO:
                // MMIO 操作已由 vCPU 处理
                break;

            case ExitReason::ShutDown:
                // Guest 关机
                std::cout << "VM shutdown" << std::endl;
                return true;

            case ExitReason::Exception:
                // Guest 异常
                error_message_ = "VM exception occurred";
                return false;

            case ExitReason::FailEntry:
                // VM Entry 失败
                error_message_ = "VM entry failed";
                return false;

            case ExitReason::InternalError:
                // 内部错误
                error_message_ = "VM internal error";
                return false;

            default:
                // 未知退出原因
                error_message_ = "Unknown VM exit reason: " +
                                std::to_string(static_cast<int>(reason));
                return false;
        }
    }

    return true;
}

// 停止 VM
void VM::stop() {
    running_ = false;
}

}  // namespace simple_vm
