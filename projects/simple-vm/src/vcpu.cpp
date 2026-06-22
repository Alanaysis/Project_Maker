#include "vcpu.h"
#include "io.h"

#include <iostream>
#include <cstring>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>
#include <linux/kvm.h>

namespace simple_vm {

// 构造函数
VCPU::VCPU(int vm_fd, int kvm_fd, IOHandler* io_handler)
    : vm_fd_(vm_fd), kvm_fd_(kvm_fd), io_handler_(io_handler) {
}

// 析构函数
VCPU::~VCPU() {
    if (run_) {
        munmap(run_, run_size_);
    }
    if (vcpu_fd_ >= 0) {
        close(vcpu_fd_);
    }
}

// 初始化 vCPU
bool VCPU::init() {
    // 1. 创建 vCPU
    vcpu_fd_ = ioctl(vm_fd_, KVM_CREATE_VCPU, 0);
    if (vcpu_fd_ < 0) {
        std::cerr << "Failed to create vCPU: " << strerror(errno) << std::endl;
        return false;
    }

    // 2. 获取 kvm_run 结构大小
    run_size_ = ioctl(kvm_fd_, KVM_GET_VCPU_MMAP_SIZE, 0);
    if (run_size_ <= 0) {
        std::cerr << "Failed to get vCPU mmap size: " << strerror(errno) << std::endl;
        return false;
    }

    // 3. 映射 kvm_run 结构
    run_ = static_cast<struct kvm_run*>(
        mmap(nullptr, run_size_,
             PROT_READ | PROT_WRITE,
             MAP_SHARED, vcpu_fd_, 0)
    );

    if (run_ == MAP_FAILED) {
        std::cerr << "Failed to mmap vCPU run structure: " << strerror(errno) << std::endl;
        run_ = nullptr;
        return false;
    }

    // 4. 设置实模式
    if (!setup_real_mode()) {
        return false;
    }

    initialized_ = true;
    return true;
}

// 设置实模式
bool VCPU::setup_real_mode() {
    // 获取特殊寄存器
    struct kvm_sregs sregs;
    if (ioctl(vcpu_fd_, KVM_GET_SREGS, &sregs) < 0) {
        std::cerr << "Failed to get special registers: " << strerror(errno) << std::endl;
        return false;
    }

    // 设置段寄存器为实模式
    // 代码段
    sregs.cs.base = 0;
    sregs.cs.limit = 0xFFFFFFFF;
    sregs.cs.selector = 0;
    sregs.cs.type = 0x0B;  // 代码段，可执行，可读，已访问
    sregs.cs.present = 1;
    sregs.cs.dpl = 0;
    sregs.cs.s = 1;
    sregs.cs.l = 0;
    sregs.cs.db = 1;  // 32 位
    sregs.cs.g = 0;

    // 数据段
    sregs.ds.base = 0;
    sregs.ds.limit = 0xFFFFFFFF;
    sregs.ds.selector = 0;
    sregs.ds.type = 0x03;  // 数据段，可读，可写，已访问
    sregs.ds.present = 1;
    sregs.ds.dpl = 0;
    sregs.ds.s = 1;
    sregs.ds.l = 0;
    sregs.ds.db = 1;
    sregs.ds.g = 0;

    // 额外段
    sregs.es = sregs.ds;
    sregs.fs = sregs.ds;
    sregs.gs = sregs.ds;
    sregs.ss = sregs.ds;

    // 设置特殊寄存器
    if (ioctl(vcpu_fd_, KVM_SET_SREGS, &sregs) < 0) {
        std::cerr << "Failed to set special registers: " << strerror(errno) << std::endl;
        return false;
    }

    // 设置通用寄存器
    struct kvm_regs regs;
    memset(&regs, 0, sizeof(regs));
    regs.rip = 0x7C00;  // 默认入口点
    regs.rsp = 0x0;      // 栈指针
    regs.rflags = 0x2;   // 必须设置的标志位

    if (ioctl(vcpu_fd_, KVM_SET_REGS, &regs) < 0) {
        std::cerr << "Failed to set registers: " << strerror(errno) << std::endl;
        return false;
    }

    return true;
}

// 设置入口点
bool VCPU::set_entry_point(uint64_t entry) {
    struct kvm_regs regs;
    if (ioctl(vcpu_fd_, KVM_GET_REGS, &regs) < 0) {
        return false;
    }

    regs.rip = entry;

    if (ioctl(vcpu_fd_, KVM_SET_REGS, &regs) < 0) {
        return false;
    }

    return true;
}

// 设置栈指针
bool VCPU::set_stack_pointer(uint64_t sp) {
    struct kvm_regs regs;
    if (ioctl(vcpu_fd_, KVM_GET_REGS, &regs) < 0) {
        return false;
    }

    regs.rsp = sp;

    if (ioctl(vcpu_fd_, KVM_SET_REGS, &regs) < 0) {
        return false;
    }

    return true;
}

// 获取通用寄存器
bool VCPU::get_registers(kvm_regs& regs) {
    return ioctl(vcpu_fd_, KVM_GET_REGS, &regs) == 0;
}

// 设置通用寄存器
bool VCPU::set_registers(const kvm_regs& regs) {
    return ioctl(vcpu_fd_, KVM_SET_REGS, &regs) == 0;
}

// 获取特殊寄存器
bool VCPU::get_special_registers(kvm_sregs& sregs) {
    return ioctl(vcpu_fd_, KVM_GET_SREGS, &sregs) == 0;
}

// 设置特殊寄存器
bool VCPU::set_special_registers(const kvm_sregs& sregs) {
    return ioctl(vcpu_fd_, KVM_SET_SREGS, &sregs) == 0;
}

// 运行 vCPU
int VCPU::run() {
    if (!initialized_) {
        return -1;
    }

    // 运行 vCPU
    int ret = ioctl(vcpu_fd_, KVM_RUN, 0);
    if (ret < 0) {
        std::cerr << "KVM_RUN failed: " << strerror(errno) << std::endl;
        return -1;
    }

    // 处理退出
    if (!handle_exit()) {
        return -1;
    }

    return 0;
}

// 处理 VM Exit
bool VCPU::handle_exit() {
    switch (run_->exit_reason) {
        case KVM_EXIT_HLT:
            exit_reason_ = ExitReason::HLT;
            return handle_hlt();

        case KVM_EXIT_IO:
            exit_reason_ = ExitReason::IO;
            return handle_io();

        case KVM_EXIT_MMIO:
            exit_reason_ = ExitReason::MMIO;
            return handle_mmio();

        case KVM_EXIT_EXCEPTION:
            exit_reason_ = ExitReason::Exception;
            return handle_exception();

        case KVM_EXIT_FAIL_ENTRY:
            exit_reason_ = ExitReason::FailEntry;
            std::cerr << "KVM_EXIT_FAIL_ENTRY: hardware_entry_failure_reason=0x"
                      << std::hex << run_->fail_entry.hardware_entry_failure_reason
                      << std::dec << std::endl;
            return false;

        case KVM_EXIT_INTERNAL_ERROR:
            exit_reason_ = ExitReason::InternalError;
            std::cerr << "KVM_EXIT_INTERNAL_ERROR: suberror="
                      << run_->internal.suberror << std::endl;
            return false;

        case KVM_EXIT_SHUTDOWN:
            exit_reason_ = ExitReason::ShutDown;
            return true;

        default:
            exit_reason_ = ExitReason::Unknown;
            std::cerr << "Unknown exit reason: " << run_->exit_reason << std::endl;
            return false;
    }
}

// 处理 I/O 退出
bool VCPU::handle_io() {
    // 获取 I/O 信息
    uint16_t port = run_->io.port;
    int size = run_->io.size;
    int direction = run_->io.direction;
    uint8_t* data = reinterpret_cast<uint8_t*>(run_) + run_->io.data_offset;

    if (direction == KVM_EXIT_IO_OUT) {
        // 输出操作
        uint32_t value = 0;
        memcpy(&value, data, size);

        if (io_handler_) {
            io_handler_->handle_port_out(port, value, size);
        }
    } else if (direction == KVM_EXIT_IO_IN) {
        // 输入操作
        uint32_t value = 0;

        if (io_handler_) {
            io_handler_->handle_port_in(port, value, size);
        }

        memcpy(data, &value, size);
    }

    return true;
}

// 处理 MMIO 退出
bool VCPU::handle_mmio() {
    uint64_t addr = run_->mmio.phys_addr;
    int size = run_->mmio.len;
    uint8_t* data = run_->mmio.data;
    int is_write = run_->mmio.is_write;

    if (is_write) {
        uint32_t value = 0;
        memcpy(&value, data, size);

        if (io_handler_) {
            io_handler_->handle_mmio_write(addr, value, size);
        }
    } else {
        uint32_t value = 0;

        if (io_handler_) {
            io_handler_->handle_mmio_read(addr, value, size);
        }

        memcpy(data, &value, size);
    }

    return true;
}

// 处理 HLT 退出
bool VCPU::handle_hlt() {
    // HLT 指令导致 VM Exit
    // 这是正常的退出方式
    return true;
}

// 处理异常退出
bool VCPU::handle_exception() {
    std::cerr << "Exception: vector=" << run_->exception.exception
              << ", error_code=" << run_->exception.error_code << std::endl;
    return false;
}

// 获取退出原因字符串
const char* VCPU::get_exit_reason_string() const {
    switch (exit_reason_) {
        case ExitReason::HLT:
            return "HLT";
        case ExitReason::IO:
            return "I/O";
        case ExitReason::MMIO:
            return "MMIO";
        case ExitReason::Exception:
            return "Exception";
        case ExitReason::InternalError:
            return "Internal Error";
        case ExitReason::ShutDown:
            return "Shutdown";
        case ExitReason::FailEntry:
            return "Fail Entry";
        default:
            return "Unknown";
    }
}

}  // namespace simple_vm
