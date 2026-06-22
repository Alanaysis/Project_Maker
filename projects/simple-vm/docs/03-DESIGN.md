# 技术设计

## 1. 架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户空间                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    SimpleVM (VMM)                     │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │  │
│  │  │  VM     │  │  vCPU   │  │ Memory  │  │   I/O   │ │  │
│  │  │ Manager │  │ Manager │  │ Manager │  │ Handler │ │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘ │  │
│  │       │            │            │            │       │  │
│  │       └────────────┼────────────┼────────────┘       │  │
│  │                    │            │                    │  │
│  │              ┌─────┴────────────┴─────┐              │  │
│  │              │      KVM Wrapper       │              │  │
│  │              └───────────┬────────────┘              │  │
│  └──────────────────────────┼────────────────────────────┘  │
│                             │                               │
│  ┌──────────────────────────┼────────────────────────────┐  │
│  │              System Call Interface                    │  │
│  └──────────────────────────┼────────────────────────────┘  │
├─────────────────────────────┼───────────────────────────────┤
│                        内核空间                              │
│  ┌──────────────────────────┼────────────────────────────┐  │
│  │                    KVM Module                         │  │
│  │  ┌─────────┐  ┌─────────┴─────────┐  ┌─────────┐    │  │
│  │  │  VMX    │  │   Exit Handler    │  │  EPT    │    │  │
│  │  │ Manager │  │                   │  │ Manager │    │  │
│  │  └─────────┘  └───────────────────┘  └─────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                        硬件层                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Intel VT-x / AMD-V                                   │  │
│  │  - VMX Root / Non-Root Mode                           │  │
│  │  - VMCS / VMCB                                        │  │
│  │  - EPT / NPT                                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 主要接口 |
|------|------|----------|
| VM Manager | 管理 VM 生命周期 | create(), destroy(), run() |
| vCPU Manager | 管理虚拟 CPU | create_vcpu(), set_regs(), run() |
| Memory Manager | 管理 Guest 内存 | alloc_memory(), load_image(), read/write() |
| I/O Handler | 处理 I/O 请求 | handle_pio(), handle_mmio() |
| KVM Wrapper | 封装 KVM API | open(), create_vm(), create_vcpu() |

## 2. 核心数据结构

### 2.1 VM 配置

```cpp
struct VMConfig {
    size_t memory_size;      // Guest 内存大小（字节）
    int vcpu_count;          // vCPU 数量
    std::string kernel_path; // 内核镜像路径
    std::string disk_path;   // 磁盘镜像路径（可选）
};
```

### 2.2 VM 状态

```cpp
class VM {
private:
    int vm_fd_;                    // KVM VM 文件描述符
    uint8_t* memory_;              // Guest 内存映射
    size_t memory_size_;           // 内存大小
    std::vector<VCPU*> vcpus_;     // vCPU 列表
    VMConfig config_;              // VM 配置
    bool running_;                 // 运行状态
};
```

### 2.3 vCPU 状态

```cpp
class VCPU {
private:
    int vcpu_fd_;                  // KVM vCPU 文件描述符
    struct kvm_run* kvm_run_;      // KVM 运行时数据
    size_t kvm_run_size_;          // kvm_run 结构大小

public:
    // 寄存器操作
    int get_regs(struct kvm_regs& regs);
    int set_regs(const struct kvm_regs& regs);
    int get_sregs(struct kvm_sregs& sregs);
    int set_sregs(const struct kvm_sregs& sregs);

    // 执行控制
    int run();
    ExitReason get_exit_reason();
};
```

### 2.4 I/O 处理接口

```cpp
class IOHandler {
public:
    virtual ~IOHandler() = default;

    // PIO 处理
    virtual bool handle_port_in(uint16_t port, uint32_t& data, int size) = 0;
    virtual bool handle_port_out(uint16_t port, uint32_t data, int size) = 0;

    // MMIO 处理
    virtual bool handle_mmio_read(uint64_t addr, uint32_t& data, int size) = 0;
    virtual bool handle_mmio_write(uint64_t addr, uint32_t data, int size) = 0;
};
```

## 3. 核心流程

### 3.1 VM 创建流程

```
┌──────────────┐
│  开始创建 VM  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────────┐
│ 打开 /dev/kvm├────►│ 检查 KVM 版本   │
└──────┬───────┘     └────────┬────────┘
       │                      │
       ▼                      ▼
┌──────────────┐     ┌─────────────────┐
│ 创建 VM 实例 ├────►│ 设置 VM 属性    │
└──────┬───────┘     └────────┬────────┘
       │                      │
       ▼                      ▼
┌──────────────┐     ┌─────────────────┐
│ 分配 Guest   ├────►│ 映射到 VM 地址  │
│ 内存         │     │ 空间            │
└──────┬───────┘     └────────┬────────┘
       │                      │
       ▼                      ▼
┌──────────────┐     ┌─────────────────┐
│ 加载程序到   ├────►│ 设置入口点      │
│ Guest 内存   │     │                 │
└──────┬───────┘     └────────┬────────┘
       │                      │
       ▼                      ▼
┌──────────────┐
│  VM 创建完成  │
└──────────────┘
```

### 3.2 指令执行循环

```
┌─────────────────┐
│   开始执行循环   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  设置 vCPU 状态  │
│  (寄存器、段等)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    KVM_RUN      │◄──────────────────────┐
│  (进入 Guest)   │                       │
└────────┬────────┘                       │
         │                                │
         ▼                                │
┌─────────────────┐                       │
│   VM Exit 发生   │                       │
└────────┬────────┘                       │
         │                                │
         ▼                                │
┌─────────────────┐                       │
│  检查退出原因    │                       │
└────────┬────────┘                       │
         │                                │
    ┌────┴────┬──────┬──────┬──────┐      │
    │         │      │      │      │      │
    ▼         ▼      ▼      ▼      ▼      │
 ┌─────┐  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
 │ HLT │  │ I/O │ │ MMIO│ │ EXCP│ │ ... │
 └──┬──┘  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
    │        │       │       │       │
    │        ▼       ▼       ▼       │
    │    ┌─────────────────────┐     │
    │    │   处理 Exit 原因    │     │
    │    └──────────┬──────────┘     │
    │               │                │
    └───────────────┴────────────────┘
         │
         ▼
┌─────────────────┐
│    继续执行     │
│   或退出循环    │
└─────────────────┘
```

## 4. 内存布局

### 4.1 Guest 物理内存布局

```
0x00000000 ┌────────────────────┐
           │  实模式中断向量表   │  0x0000 - 0x03FF
0x00000400 ├────────────────────┤
           │  BIOS 数据区       │  0x0400 - 0x04FF
0x00000500 ├────────────────────┤
           │  可用内存          │
           │        ...         │
0x00007C00 ├────────────────────┤
           │  引导扇区加载地址  │  0x7C00 - 0x7DFF
0x00007E00 ├────────────────────┤
           │  可用内存          │
           │        ...         │
0x000A0000 ├────────────────────┤
           │  传统 ISA 空间     │
0x000C0000 ├────────────────────┤
           │  ROM 空间          │
0x00100000 ├────────────────────┤
           │  内核加载地址      │  1MB+
           │        ...         │
           │  Guest 内存        │
           │        ...         │
           └────────────────────┘
```

### 4.2 内存映射

```cpp
// 内存区域描述
struct MemoryRegion {
    uint64_t guest_phys_addr;  // Guest 物理地址
    uint64_t host_virt_addr;   // Host 虚拟地址
    size_t size;               // 区域大小
    uint32_t flags;            // 访问权限
};
```

## 5. I/O 处理设计

### 5.1 串口模拟

```cpp
class SerialPort : public IOHandler {
private:
    uint16_t base_port_;       // 基地址 (0x3F8)
    uint8_t thr_;              // 发送保持寄存器
    uint8_t rbr_;              // 接收缓冲寄存器
    uint8_t ier_;              // 中断使能寄存器
    uint8_t iir_;              // 中断标识寄存器
    uint8_t lcr_;              // 线路控制寄存器
    uint8_t mcr_;              // 调制解调器控制寄存器
    uint8_t lsr_;              // 线路状态寄存器
    uint8_t msr_;              // 调制解调器状态寄存器
    uint8_t scr_;              // 暂存寄存器

public:
    bool handle_port_in(uint16_t port, uint32_t& data, int size) override;
    bool handle_port_out(uint16_t port, uint32_t data, int size) override;
};
```

### 5.2 I/O 端口分配

| 端口范围 | 设备 | 说明 |
|----------|------|------|
| 0x00 - 0x0F | DMA 控制器 1 | |
| 0x20 - 0x21 | PIC 1 | 主中断控制器 |
| 0x40 - 0x43 | PIT | 定时器 |
| 0x60 - 0x64 | 键盘 | |
| 0x70 - 0x71 | CMOS | |
| 0x80 | POST 代码 | 调试用 |
| 0xA0 - 0xA1 | PIC 2 | 从中断控制器 |
| 0x1F0 - 0x1F7 | IDE 控制器 | 硬盘 |
| 0x3F8 - 0x3FF | COM1 | 串口 1 |
| 0x402 | QEMU 调试端口 | 调试输出 |

## 6. 错误处理

### 6.1 错误类型

```cpp
enum class VMError {
    Success = 0,
    KVMOpenFailed,        // 无法打开 /dev/kvm
    KVMVersionMismatch,   // KVM 版本不兼容
    VMCreateFailed,       // 创建 VM 失败
    VCPUCreateFailed,     // 创建 vCPU 失败
    MemoryAllocFailed,    // 内存分配失败
    MemoryMapFailed,      // 内存映射失败
    RunFailed,            // 运行失败
    InvalidConfig,        // 无效配置
    IOError,              // I/O 错误
};
```

### 6.2 错误处理策略

1. **致命错误**: 记录日志，清理资源，退出程序
2. **可恢复错误**: 记录日志，尝试恢复或返回错误码
3. **警告**: 记录日志，继续执行

## 7. 接口设计

### 7.1 公共 API

```cpp
namespace simple_vm {

// 虚拟机类
class VM {
public:
    // 创建 VM
    static std::unique_ptr<VM> create(const VMConfig& config);

    // 析构函数（自动清理资源）
    ~VM();

    // 加载程序到 Guest 内存
    bool load_program(const std::string& path, uint64_t load_addr);

    // 写入 Guest 内存
    bool write_guest_memory(uint64_t addr, const void* data, size_t size);

    // 读取 Guest 内存
    bool read_guest_memory(uint64_t addr, void* data, size_t size);

    // 运行 VM
    bool run();

    // 停止 VM
    void stop();

    // 获取 VM 状态
    VMState get_state() const;

private:
    VM();  // 使用 create() 工厂方法
    bool init(const VMConfig& config);
    void cleanup();

    // KVM 相关
    int kvm_fd_;
    int vm_fd_;
    uint8_t* memory_;
    size_t memory_size_;
    std::vector<std::unique_ptr<VCPU>> vcpus_;
    std::unique_ptr<IOHandler> io_handler_;
    bool running_;
};

// vCPU 类
class VCPU {
public:
    VCPU(int vm_fd);
    ~VCPU();

    // 寄存器操作
    bool get_registers(kvm_regs& regs);
    bool set_registers(const kvm_regs& regs);
    bool get_special_registers(kvm_sregs& sregs);
    bool set_special_registers(const kvm_sregs& sregs);

    // 执行
    int run();

    // 退出信息
    ExitReason get_exit_reason() const;
    const kvm_run* get_run() const;

private:
    int vcpu_fd_;
    struct kvm_run* run_;
    size_t run_size_;
};

}  // namespace simple_vm
```

## 8. 线程模型

### 8.1 单线程模型（初始版本）

```
Main Thread
    │
    ├── VM 创建
    ├── 内存初始化
    ├── 程序加载
    │
    └── 执行循环
        ├── vCPU 0 run()
        ├── 处理 Exit
        └── 继续执行
```

### 8.2 多线程模型（扩展版本）

```
Main Thread
    │
    ├── VM 创建
    ├── 内存初始化
    ├── 程序加载
    │
    ├── vCPU Thread 0 ──► 执行循环
    ├── vCPU Thread 1 ──► 执行循环
    └── I/O Thread ──► 处理异步 I/O
```

## 9. 性能优化

### 9.1 关键优化点

1. **减少 VM Exit**
   - 批量处理 I/O
   - 使用 MSR 直通

2. **内存优化**
   - 使用 huge pages
   - 延迟分配内存

3. **I/O 优化**
   - 使用 virtio 设备
   - 异步 I/O 处理

## 10. 安全考虑

### 10.1 安全措施

1. **输入验证**
   - 所有 Guest 地址必须在有效范围内
   - I/O 端口访问必须检查权限

2. **资源限制**
   - 限制 Guest 内存大小
   - 限制 vCPU 数量

3. **隔离性**
   - 使用 KVM 的内存隔离
   - 不允许 Guest 直接访问 Host 资源
