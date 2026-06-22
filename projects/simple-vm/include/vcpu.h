#ifndef SIMPLE_VM_VCPU_H
#define SIMPLE_VM_VCPU_H

#include <cstdint>
#include <linux/kvm.h>

namespace simple_vm {

// 前向声明
class IOHandler;
class VM;

// VM Exit 原因
enum class ExitReason {
    Unknown,
    HLT,
    IO,
    MMIO,
    Exception,
    InternalError,
    ShutDown,
    FailEntry,
};

// vCPU 类 - 虚拟 CPU
class VCPU {
public:
    // 构造函数
    // vm_fd: VM 文件描述符
    // kvm_fd: KVM 文件描述符
    // io_handler: I/O 处理器
    VCPU(int vm_fd, int kvm_fd, IOHandler* io_handler);

    // 析构函数
    ~VCPU();

    // 禁止拷贝和赋值
    VCPU(const VCPU&) = delete;
    VCPU& operator=(const VCPU&) = delete;

    // 初始化 vCPU
    bool init();

    // 设置入口点（RIP 寄存器）
    bool set_entry_point(uint64_t entry);

    // 设置栈指针（RSP 寄存器）
    bool set_stack_pointer(uint64_t sp);

    // 获取通用寄存器
    bool get_registers(kvm_regs& regs);

    // 设置通用寄存器
    bool set_registers(const kvm_regs& regs);

    // 获取特殊寄存器
    bool get_special_registers(kvm_sregs& sregs);

    // 设置特殊寄存器
    bool set_special_registers(const kvm_sregs& sregs);

    // 运行 vCPU（执行 Guest 代码）
    // 返回 0 表示正常退出，负数表示错误
    int run();

    // 获取退出原因
    ExitReason get_exit_reason() const { return exit_reason_; }

    // 获取 kvm_run 结构（用于获取详细的退出信息）
    const kvm_run* get_run() const { return run_; }

    // 获取 vCPU 文件描述符
    int get_fd() const { return vcpu_fd_; }

    // 获取错误信息
    const char* get_exit_reason_string() const;

private:
    // 设置段寄存器（实模式）
    bool setup_real_mode();

    // 处理 VM Exit
    bool handle_exit();

    // 处理 I/O 退出
    bool handle_io();

    // 处理 MMIO 退出
    bool handle_mmio();

    // 处理 HLT 退出
    bool handle_hlt();

    // 处理异常退出
    bool handle_exception();

    // 文件描述符
    int vcpu_fd_ = -1;
    int vm_fd_ = -1;
    int kvm_fd_ = -1;

    // kvm_run 结构
    struct kvm_run* run_ = nullptr;
    size_t run_size_ = 0;

    // 退出原因
    ExitReason exit_reason_ = ExitReason::Unknown;

    // I/O 处理器
    IOHandler* io_handler_ = nullptr;

    // 是否已初始化
    bool initialized_ = false;
};

}  // namespace simple_vm

#endif  // SIMPLE_VM_VCPU_H
