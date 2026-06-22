# 学习笔记

## 1. KVM API 学习笔记

### 1.1 KVM 基础概念

**什么是 KVM?**
- Kernel-based Virtual Machine
- Linux 内核模块，将内核转变为 Hypervisor
- 利用 Intel VT-x / AMD-V 硬件虚拟化支持

**KVM 架构**:
```
┌─────────────────────────────────────┐
│           用户空间                   │
│  ┌─────────────────────────────┐   │
│  │    QEMU / Simple VM         │   │
│  └──────────────┬──────────────┘   │
│                 │ ioctl()          │
├─────────────────┼───────────────────┤
│           内核空间                   │
│  ┌──────────────┴──────────────┐   │
│  │         KVM 模块            │   │
│  │  ┌─────────┐ ┌─────────┐   │   │
│  │  │  VMX    │ │  SVM    │   │   │
│  │  └─────────┘ └─────────┘   │   │
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│           硬件                       │
│  ┌─────────────────────────────┐   │
│  │  Intel VT-x / AMD-V        │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 1.2 关键数据结构

**kvm_userspace_memory_region**:
```cpp
struct kvm_userspace_memory_region {
    __u32 slot;              // 内存槽位号
    __u32 flags;             // 标志
    __u64 guest_phys_addr;   // Guest 物理地址
    __u64 memory_size;       // 内存大小
    __u64 userspace_addr;    // Host 用户空间地址
};
```

**kvm_regs**:
```cpp
struct kvm_regs {
    __u64 rax, rbx, rcx, rdx;
    __u64 rsi, rdi, rsp, rbp;
    __u64 r8, r9, r10, r11;
    __u64 r12, r13, r14, r15;
    __u64 rip, rflags;
};
```

**kvm_run**:
```cpp
struct kvm_run {
    __u8 request_interrupt_window;
    __u8 immediate_exit;
    __u8 padding1[6];
    __u32 exit_reason;
    __u8 ready_for_interrupt_injection;
    __u8 if_flag;
    __u16 flags;
    // ... 更多字段
};
```

### 1.3 学习心得

**心得 1: KVM 的文件描述符模型**
- `/dev/kvm` 是控制通道
- 每个 VM 有自己的文件描述符
- 每个 vCPU 有自己的文件描述符
- 使用 ioctl 进行控制

**心得 2: 内存映射机制**
- Guest 内存是 Host 用户空间内存的映射
- 使用 `mmap()` 分配内存
- 使用 `KVM_SET_USER_MEMORY_REGION` 建立映射
- EPT 负责 Guest 物理地址到 Host 物理地址的转换

**心得 3: VM Exit 处理**
- VM Exit 是 Host-Guest 交互的主要机制
- 常见的退出原因: HLT、I/O、MMIO、异常
- 处理完成后使用 KVM_RUN 继续执行
- 性能优化的关键是减少 VM Exit 次数

## 2. x86 架构学习笔记

### 2.1 处理器模式

**实模式 (Real Mode)**:
- 16 位模式
- 直接访问物理内存
- 无内存保护
- 段地址 = 段寄存器 * 16 + 偏移

**保护模式 (Protected Mode)**:
- 32 位模式
- 内存分段和分页
- 特权级保护 (Ring 0-3)
- 支持虚拟内存

**长模式 (Long Mode)**:
- 64 位模式
- 统一的地址空间
- 更多的寄存器
- 现代操作系统的默认模式

### 2.2 寄存器分类

**通用寄存器**:
- RAX, RBX, RCX, RDX (64 位)
- RSI, RDI, RSP, RBP
- R8-R15 (64 位扩展)

**段寄存器**:
- CS, DS, SS, ES, FS, GS
- 包含段选择子和隐藏的段描述符

**控制寄存器**:
- CR0: 系统控制 (PE, PG 等)
- CR2: 页故障地址
- CR3: 页目录基地址
- CR4: 扩展控制

**调试寄存器**:
- DR0-DR3: 断点地址
- DR6: 调试状态
- DR7: 调试控制

### 2.3 指令执行流程

```
1. 取指 (Fetch)
   - 从 CS:IP 读取指令
   - 更新 IP

2. 译码 (Decode)
   - 解析指令格式
   - 确定操作数

3. 执行 (Execute)
   - 执行算术/逻辑运算
   - 访问寄存器

4. 访存 (Memory)
   - 读写内存 (如果需要)
   - 地址转换

5. 写回 (Write Back)
   - 将结果写回寄存器
```

### 2.4 学习心得

**心得 1: 段寄存器的重要性**
- 段寄存器在实模式和保护模式下有不同的含义
- 在保护模式下，段寄存器包含段选择子
- 隐藏的段描述符缓存了段的基地址、界限和属性

**心得 2: 特权级保护**
- Ring 0 (内核) 到 Ring 3 (用户)
- 特权级检查在内存访问和指令执行时进行
- 系统调用通过门描述符实现特权级切换

**心得 3: 中断和异常**
- 中断是异步事件 (硬件中断)
- 异常是同步事件 (除零、页故障等)
- 中断描述符表 (IDT) 定义了中断处理程序
- 通过 INT 指令可以触发软件中断

## 3. 虚拟化技术学习笔记

### 3.1 为什么需要硬件虚拟化?

**软件模拟的问题**:
- 敏感指令 (如 POPF) 在不同特权级下行为不同
- 二进制翻译效率低
- 无法完全模拟所有行为

**硬件虚拟化的优势**:
- VMX root mode (Host) 和 non-root mode (Guest)
- 硬件自动处理敏感指令
- 减少 VMM 干预
- 提高性能

### 3.2 VMX 操作

**VM Entry**:
- 从 root mode 进入 non-root mode
- 加载 Guest 状态 (从 VMCS)
- 开始执行 Guest 代码

**VM Exit**:
- 从 non-root mode 返回 root mode
- 保存 Guest 状态 (到 VMCS)
- 跳转到 Host 的 exit handler

**VMCS (Virtual Machine Control Structure)**:
- Guest 状态区域
- Host 状态区域
- VM 执行控制字段
- VM Exit 信息字段

### 3.3 内存虚拟化

**两阶段地址转换**:
```
Guest Virtual Address (GVA)
        │
        ▼
Guest Physical Address (GPA)
        │  ← EPT (Extended Page Tables)
        ▼
Host Physical Address (HPA)
```

**EPT (Extended Page Tables)**:
- 由硬件自动遍历
- 减少 VMM 干预
- 支持大页 (2MB, 1GB)
- 支持脏页跟踪

### 3.4 学习心得

**心得 1: VM Exit 的开销**
- VM Exit 需要保存/恢复大量状态
- 典型开销: 1-10 微秒
- 优化策略: 减少 Exit 次数、批量处理

**心得 2: EPT 的作用**
- EPT 实现了 Guest 物理地址到 Host 物理地址的转换
- 硬件自动遍历 EPT，性能接近原生
- 支持内存超分 (overcommit)

**心得 3: 中断虚拟化**
- 虚拟中断通过 VMCS 注入到 Guest
- APICv 可以减少中断相关的 VM Exit
- 中批合并 (interrupt coalescing) 可以提高性能

## 4. 开发过程中的问题和解决方案

### 4.1 问题 1: VM Entry 失败

**现象**: KVM_EXIT_FAIL_ENTRY，错误码 0x80000021

**原因**: rflags 寄存器设置不正确

**解决方案**:
```cpp
// rflags 的第 1 位必须为 1
struct kvm_regs regs;
memset(&regs, 0, sizeof(regs));
regs.rip = entry_point;
regs.rflags = 0x2;  // 必须设置
ioctl(vcpu_fd, KVM_SET_REGS, &regs);
```

### 4.2 问题 2: 段寄存器设置错误

**现象**: Guest 执行异常

**原因**: 段寄存器的基地址和界限设置不正确

**解决方案**:
```cpp
struct kvm_sregs sregs;
ioctl(vcpu_fd, KVM_GET_SREGS, &sregs);

// 设置代码段
sregs.cs.base = 0;
sregs.cs.limit = 0xFFFFFFFF;
sregs.cs.selector = 1 << 3;  // 选择子
sregs.cs.type = 11;  // 代码段，可执行，可读
sregs.cs.present = 1;
sregs.cs.dpl = 0;  // 特权级 0
sregs.cs.s = 1;  // 代码/数据段
sregs.cs.l = 0;  // 32 位模式
sregs.cs.db = 1;  // 32 位

// 设置数据段
sregs.ds.base = 0;
sregs.ds.limit = 0xFFFFFFFF;
sregs.ds.selector = 2 << 3;
sregs.ds.type = 3;  // 数据段，可读，可写
sregs.ds.present = 1;
sregs.ds.dpl = 0;
sregs.ds.s = 1;

ioctl(vcpu_fd, KVM_SET_SREGS, &sregs);
```

### 4.3 问题 3: I/O 处理不正确

**现象**: Guest 输出的字符不正确

**原因**: I/O 端口处理逻辑错误

**解决方案**:
```cpp
// 正确的 I/O 处理
void handle_io(struct kvm_run* run) {
    uint16_t port = run->io.port;
    uint8_t* data = (uint8_t*)run + run->io.data_offset;
    int size = run->io.size;
    int direction = run->io.direction;

    if (direction == KVM_EXIT_IO_OUT) {
        // 输出操作
        if (port == 0x3F8) {  // 串口
            putchar(*data);
            fflush(stdout);
        }
    } else if (direction == KVM_EXIT_IO_IN) {
        // 输入操作
        if (port == 0x3F8 + 5) {  // LSR
            // 表示发送缓冲区为空
            *data = 0x20;
        }
    }
}
```

## 5. 参考资源

### 5.1 官方文档

- [Intel Software Developer Manual](https://software.intel.com/en-us/articles/intel-sdm)
- [KVM API Documentation](https://www.kernel.org/doc/html/latest/virt/kvm/api.html)
- [Linux Kernel Documentation](https://www.kernel.org/doc/)

### 5.2 开源项目

- [kvmtool](https://github.com/kvmtool/kvmtool) - 轻量级 KVM VMM
- [QEMU](https://github.com/qemu/qemu) - 完整的虚拟机监控器
- [Firecracker](https://github.com/firecracker-microvm/firecracker) - AWS 轻量级 VMM

### 5.3 学习资源

- [Writing a Simple OS from Scratch](https://www.cs.bham.ac.uk/~exr/lectures/opsys/10_11/lectures/os-dev.pdf)
- [OSDev Wiki](https://wiki.osdev.org/)
- [KVM Forum](https://www.linux-kvm.org/page/Main_Page)

## 6. 待深入学习的内容

- [ ] VT-x 的 VMCS 结构详解
- [ ] EPT 的页表结构和遍历过程
- [ ] APIC 虚拟化 (APICv)
- [ ] IOMMU 和设备直通 (VT-d)
- [ ] virtio 设备模型
- [ ] 容器和虚拟机的区别
- [ ] 安全虚拟化和可信执行环境

## 7. 学习时间记录

| 日期 | 学习内容 | 时长 | 收获 |
|------|----------|------|------|
| 2024-01-01 | KVM API 基础 | 2h | 理解了 KVM 的文件描述符模型 |
| 2024-01-02 | x86 寄存器 | 1h | 掌握了寄存器分类和用途 |
| 2024-01-03 | VM 创建流程 | 3h | 实现了基本的 VM 创建 |
| 2024-01-04 | 指令执行 | 4h | 实现了简单的指令执行循环 |
| 2024-01-05 | I/O 处理 | 2h | 实现了串口输出 |

**总学习时长**: 12 小时

**学习进度**: 60%

**下一步计划**: 实现中断处理和更多指令支持
