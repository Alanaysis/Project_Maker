# 开发手册

## 1. 环境搭建

### 1.1 系统要求

- **操作系统**: Linux (Ubuntu 20.04+, Fedora 32+, Arch Linux)
- **内核版本**: 5.4+ (需要 KVM 支持)
- **CPU**: 支持 VT-x 的 x86_64 处理器
- **内存**: 至少 4GB RAM

### 1.2 检查 KVM 支持

```bash
# 检查 CPU 是否支持 VT-x
grep -E '(vmx|svm)' /proc/cpuinfo

# 检查 KVM 模块是否加载
lsmod | grep kvm

# 检查 /dev/kvm 是否存在
ls -la /dev/kvm
```

### 1.3 安装依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    git \
    nasm \
    gdb
```

**Fedora/RHEL:**
```bash
sudo dnf install -y \
    gcc-c++ \
    cmake \
    git \
    nasm \
    gdb
```

**Arch Linux:**
```bash
sudo pacman -S \
    base-devel \
    cmake \
    git \
    nasm \
    gdb
```

### 1.4 权限配置

```bash
# 将当前用户添加到 kvm 组
sudo usermod -aG kvm $USER

# 或者修改 /dev/kvm 权限（临时）
sudo chmod 666 /dev/kvm

# 重新登录以使组生效
```

## 2. 项目构建

### 2.1 编译项目

```bash
# 克隆项目
git clone <repository-url>
cd simple-vm

# 创建构建目录
mkdir build && cd build

# 配置 CMake
cmake ..

# 编译
make -j$(nproc)
```

### 2.2 运行测试

```bash
# 在 build 目录下
make test

# 或者使用 CTest
ctest --verbose
```

### 2.3 安装（可选）

```bash
sudo make install
```

## 3. 核心模块解析

### 3.1 KVM 初始化模块

**文件**: `src/vm.cpp`

**关键代码**:
```cpp
// 打开 KVM 设备
int kvm_fd = open("/dev/kvm", O_RDWR | O_CLOEXEC);
if (kvm_fd < 0) {
    throw VMError::KVMOpenFailed;
}

// 检查 KVM 版本
int ret = ioctl(kvm_fd, KVM_GET_API_VERSION, 0);
if (ret != KVM_API_VERSION) {
    throw VMError::KVMVersionMismatch;
}

// 创建 VM
int vm_fd = ioctl(kvm_fd, KVM_CREATE_VM, 0);
if (vm_fd < 0) {
    throw VMError::VMCreateFailed;
}
```

**学习要点**:
- KVM 使用文件描述符和 ioctl 进行控制
- 版本检查确保 API 兼容性
- VM 是 vCPU 和内存的容器

### 3.2 内存管理模块

**文件**: `src/memory.cpp`

**关键代码**:
```cpp
// 分配 Guest 内存
void* memory = mmap(NULL, memory_size,
                    PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE,
                    -1, 0);

// 设置用户空间内存区域
struct kvm_userspace_memory_region region = {
    .slot = 0,
    .flags = 0,
    .guest_phys_addr = 0,
    .memory_size = memory_size,
    .userspace_addr = (uint64_t)memory,
};

int ret = ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &region);
```

**学习要点**:
- Guest 内存是 Host 用户空间内存的映射
- `kvm_userspace_memory_region` 定义映射关系
- 内存区域可以有不同的 slot

### 3.3 vCPU 管理模块

**文件**: `src/vcpu.cpp`

**关键代码**:
```cpp
// 创建 vCPU
int vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0);

// 获取 kvm_run 结构大小
size_t mmap_size = ioctl(kvm_fd, KVM_GET_VCPU_MMAP_SIZE, 0);

// 映射 kvm_run 结构
struct kvm_run* run = (struct kvm_run*)mmap(NULL, mmap_size,
                                            PROT_READ | PROT_WRITE,
                                            MAP_SHARED, vcpu_fd, 0);

// 设置寄存器
struct kvm_regs regs = {
    .rip = 0x7C00,  // 入口点
    .rsp = 0x0,     // 栈指针
    .rflags = 0x2,  // 必须设置的标志位
};
ioctl(vcpu_fd, KVM_SET_REGS, &regs);

// 运行 vCPU
ioctl(vcpu_fd, KVM_RUN, 0);
```

**学习要点**:
- 每个 vCPU 有自己的文件描述符
- `kvm_run` 结构用于 Host-Guest 通信
- 寄存器状态在 VM Entry/Exit 时自动保存/恢复

### 3.4 VM Exit 处理模块

**文件**: `src/vcpu.cpp`

**关键代码**:
```cpp
// 运行循环
while (running) {
    int ret = ioctl(vcpu_fd, KVM_RUN, 0);
    if (ret < 0) {
        // 错误处理
        break;
    }

    switch (run->exit_reason) {
        case KVM_EXIT_HLT:
            // Guest 执行了 HLT 指令
            handle_hlt();
            break;

        case KVM_EXIT_IO:
            // Guest 进行了 I/O 操作
            handle_io(run->io);
            break;

        case KVM_EXIT_MMIO:
            // Guest 进行了 MMIO 访问
            handle_mmio(run->mmio);
            break;

        case KVM_EXIT_FAIL_ENTRY:
            // VM Entry 失败
            handle_fail_entry();
            break;

        case KVM_EXIT_INTERNAL_ERROR:
            // 内部错误
            handle_internal_error();
            break;

        default:
            // 未知退出原因
            handle_unknown_exit();
            break;
    }
}
```

**学习要点**:
- VM Exit 是 Host-Guest 交互的主要机制
- 不同的退出原因需要不同的处理策略
- 性能优化的关键是减少 VM Exit 次数

### 3.5 I/O 处理模块

**文件**: `src/io.cpp`

**关键代码**:
```cpp
// 串口输出处理
void SerialPort::handle_out(uint16_t port, uint32_t data) {
    switch (port - base_port_) {
        case 0:  // THR (Transmitter Holding Register)
            if (lcr_ & 0x80) {
                // DLAB = 1, 设置波特率除数低字节
                divisor_low_ = data;
            } else {
                // DLAB = 0, 发送字符
                putchar(data);
                fflush(stdout);
            }
            break;

        case 1:  // IER
            if (lcr_ & 0x80) {
                // DLAB = 1, 设置波特率除数高字节
                divisor_high_ = data;
            } else {
                ier_ = data;
            }
            break;

        case 3:  // LCR
            lcr_ = data;
            break;

        // ... 其他寄存器
    }
}
```

**学习要点**:
- I/O 端口是 x86 特有的 I/O 机制
- 串口是最简单的输出设备
- 寄存器复用需要根据上下文判断

## 4. 调试技巧

### 4.1 使用 GDB 调试

```bash
# 编译时添加调试信息
cmake -DCMAKE_BUILD_TYPE=Debug ..

# 使用 GDB 启动
gdb ./build/simple-vm

# 设置断点
(gdb) break main
(gdb) break VM::run

# 运行程序
(gdb) run examples/hello.bin

# 单步执行
(gdb) next
(gdb) step

# 查看寄存器
(gdb) info registers

# 查看内存
(gdb) x/10x $rip
```

### 4.2 查看 KVM 调试信息

```bash
# 启用内核调试信息
echo 1 > /sys/module/kvm/parameters/kvm_debug

# 查看 dmesg 日志
dmesg | grep kvm
```

### 4.3 常见问题排查

**问题 1: 权限拒绝**
```
Failed to open /dev/kvm: Permission denied
```
**解决**: 将用户添加到 kvm 组或修改设备权限

**问题 2: KVM 版本不兼容**
```
KVM API version mismatch
```
**解决**: 更新内核或检查 KVM 模块版本

**问题 3: VM Entry 失败**
```
KVM_EXIT_FAIL_ENTRY
```
**解决**: 检查寄存器设置，特别是 rflags 和段寄存器

## 5. 测试策略

### 5.1 单元测试

```cpp
// tests/test_vm.cpp
TEST(VMTest, CreateVM) {
    VMConfig config = {
        .memory_size = 4 * 1024 * 1024,  // 4MB
        .vcpu_count = 1,
    };

    auto vm = VM::create(config);
    ASSERT_NE(vm, nullptr);
}

TEST(VMTest, LoadProgram) {
    auto vm = VM::create({.memory_size = 4 * 1024 * 1024});

    // 加载测试程序
    bool result = vm->load_program("tests/test.bin", 0x7C00);
    ASSERT_TRUE(result);
}
```

### 5.2 集成测试

```cpp
// tests/test_integration.cpp
TEST(IntegrationTest, HelloWorld) {
    auto vm = VM::create({.memory_size = 4 * 1024 * 1024});
    vm->load_program("examples/hello.bin", 0x7C00);

    // 捕获标准输出
    testing::internal::CaptureStdout();
    vm->run();
    std::string output = testing::internal::GetCapturedStdout();

    EXPECT_EQ(output, "Hello, World!\n");
}
```

### 5.3 测试覆盖率

```bash
# 编译时启用覆盖率
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON ..

# 运行测试
make test

# 生成覆盖率报告
make coverage
```

## 6. 性能分析

### 6.1 使用 perf 分析

```bash
# 记录性能数据
perf record -g ./build/simple-vm examples/hello.bin

# 查看报告
perf report

# 查看火焰图
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

### 6.2 关键性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| VM 创建时间 | < 10ms | 从调用 create 到返回 |
| 指令执行速度 | > 1M/s | 每秒执行的指令数 |
| VM Exit 延迟 | < 1us | 从 Exit 到处理完成 |
| 内存占用 | < 10MB | VMM 进程本身 |

## 7. 代码规范

### 7.1 命名规范

- **类名**: PascalCase (如 `VM`, `VCPU`)
- **函数名**: camelCase (如 `createVM`, `runVcpu`)
- **变量名**: snake_case (如 `vm_fd`, `memory_size`)
- **常量**: kPascalCase (如 `kDefaultMemorySize`)
- **宏**: UPPER_SNAKE_CASE (如 `VM_EXIT_HLT`)

### 7.2 注释规范

```cpp
/**
 * 创建一个虚拟机实例
 *
 * @param config 虚拟机配置
 * @return 虚拟机实例指针，失败返回 nullptr
 *
 * 示例:
 *   auto vm = VM::create({.memory_size = 4 * 1024 * 1024});
 */
static std::unique_ptr<VM> create(const VMConfig& config);
```

### 7.3 错误处理规范

```cpp
// 使用返回值表示错误
int ret = ioctl(fd, KVM_CREATE_VM, 0);
if (ret < 0) {
    LOG_ERROR("Failed to create VM: %s", strerror(errno));
    return VMError::VMCreateFailed;
}

// 或使用异常（在 C++ 中）
if (ioctl(fd, KVM_CREATE_VM, 0) < 0) {
    throw VMException("Failed to create VM", errno);
}
```

## 8. 版本控制

### 8.1 Git 工作流

```
main (稳定版本)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/vcpu-management
  │     ├── feature/io-handling
  │     └── feature/memory-management
  │
  └── release/v1.0
```

### 8.2 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(vcpu): add register get/set functions

- Implement get_registers() and set_registers()
- Add unit tests for register operations
- Update documentation

Closes #123
```
