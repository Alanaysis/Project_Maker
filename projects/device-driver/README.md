# 设备驱动框架 (Device Driver Framework)

## 项目描述 / Project Description

本项目是一个用于学习 Linux 设备驱动开发的综合性框架实现。它涵盖了 Linux 字符设备驱动的完整生命周期，从模块初始化到设备注销，从中断处理到 DMA 管理。

This project is a comprehensive framework for learning Linux device driver development. It covers the full lifecycle of a Linux character device driver, from module initialization to device cleanup, from interrupt handling to DMA management.

**核心循环 / Core Loop**: 设备注册 → 中断处理 → 数据读写 → 设备注销

## 学习目标 / Learning Objectives

### Linux 驱动模型理解
- [x] 字符设备驱动模型 (cdev)
- [x] 设备类和设备节点创建
- [x] 平台驱动模型
- [x] 设备树解析

### 字符设备驱动
- [x] 文件操作 (open, release, read, write, ioctl)
- [x] 动态主设备号分配
- [x] 阻塞和非阻塞 I/O
- [x] poll/select/epoll 支持

### 中断处理
- [x] request_irq / free_irq
- [x] IRQ 处理程序实现
- [x] 边沿触发和电平触发
- [x] 共享 IRQ 线
- [x] 顶半部/底半部分离

### 高级主题
- [x] 内存映射 I/O (ioremap)
- [x] DMA 相干内存管理
- [x] 自旋锁和互斥锁同步
- [x] 等待队列和定时器
- [x] 工作队列

## 项目结构 / Project Structure

```
device-driver/
├── Makefile              # 构建系统
├── README.md             # 本文件
├── include/
│   └── device_framework.h   # 公共头文件
├── src/
│   └── device_framework.c   # 核心驱动框架实现
├── examples/
│   ├── simple_char_device.c   # 简单字符设备驱动
│   ├── interrupt_driver.c     # 中断驱动示例
│   ├── platform_driver_dt.c   # 平台驱动+设备树
│   ├── mmio_driver.c          # 内存映射I/O示例
│   └── user_test.c            # 用户空间测试程序
├── tests/
│   └── test_framework.c     # 单元测试框架
└── docs/
    └── linux-driver-model.md # Linux驱动模型文档
```

## 如何运行示例 / How to Run Examples

### 1. 构建内核模块 / Build Kernel Module

```bash
# 构建
make

# 安装并加载模块 (需要 root)
sudo make install
```

### 2. 验证模块加载 / Verify Module Loading

```bash
# 查看模块状态
lsmod | grep device_framework

# 查看内核日志
dmesg | tail -20

# 检查设备节点
ls -la /dev/device_framework
```

### 3. 运行用户空间测试 / Run User-Space Tests

```bash
# 构建测试程序
make example

# 运行测试
./examples/user_test

# 或者
make test
```

### 4. 手动测试 / Manual Testing

```bash
# 写入数据
echo "Hello, Device Driver!" > /dev/device_framework

# 读取数据
cat /dev/device_framework

# 使用 IOCTL 获取状态
sudo ./examples/user_test
```

### 5. 卸载模块 / Unload Module

```bash
sudo make remove
# 或
sudo rmmod device_framework
```

## Linux 驱动模型架构 / Linux Driver Model Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Space                           │
│  /dev/device_framework  (设备节点)                      │
└────────────────────────┬────────────────────────────────┘
                         │  syscalls (read/write/ioctl)
┌────────────────────────▼────────────────────────────────┐
│              Kernel Space - VFS Layer                   │
│              Character Device Subsystem                  │
│              (cdev, file_operations)                    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Device Framework Core                       │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ cdev      │  │ Class    │  │ Device Node      │    │
│  │ (字符设备) │  │ (设备类) │  │ (设备节点)       │    │
│  └───────────┘  └──────────┘  └──────────────────┘    │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Mutex     │  │ Spinlock │  │ Wait Queue       │    │
│  │ (互斥锁)  │  │ (自旋锁) │  │ (等待队列)       │    │
│  └───────────┘  └──────────┘  └──────────────────┘    │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ IRQ Handler│  │ DMA      │  │ MMIO             │    │
│  │ (中断处理) │  │ (DMA)    │  │ (内存映射)       │    │
│  └───────────┘  └──────────┘  └──────────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Platform Driver / Device Tree               │
│  ┌───────────────┐  ┌────────────────────┐             │
│  │ Platform Bus  │  │ Device Tree (DT)   │             │
│  │ (平台总线)    │  │ (设备树)           │             │
│  └───────────────┘  └────────────────────┘             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Hardware / Physical Device                  │
│  ┌───────────────┐  ┌────────────────────┐             │
│  │ Registers     │  │ Interrupt Lines    │             │
│  │ (寄存器)      │  │ (中断线)           │             │
│  └───────────────┘  └────────────────────┘             │
│  ┌───────────────┐  ┌────────────────────┐             │
│  │ MMIO Region   │  │ DMA Buffer         │             │
│  │ (内存映射区)  │  │ (DMA缓冲区)        │             │
│  └───────────────┘  └────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

## 关键概念 / Key Concepts

### 字符设备驱动流程 / Character Device Driver Flow

1. **模块初始化** (`module_init`)
   - 分配设备号 (`alloc_chrdev_region`)
   - 初始化 cdev (`cdev_init`)
   - 注册 cdev (`cdev_add`)
   - 创建设备类 (`class_create`)
   - 创建设备节点 (`device_create`)

2. **文件操作** (`file_operations`)
   - `open` - 打开设备
   - `release` - 关闭设备
   - `read` - 读取数据
   - `write` - 写入数据
   - `unlocked_ioctl` - 控制命令
   - `poll` - 轮询支持

3. **模块清理** (`module_exit`)
   - 销毁设备节点
   - 销毁设备类
   - 删除 cdev
   - 释放设备号
   - 释放资源

### 中断处理流程 / Interrupt Handling Flow

1. **中断请求** (`request_irq`)
   - 指定中断号
   - 指定处理函数
   - 指定触发类型
   - 指定共享标识

2. **中断处理** (ISR)
   - 顶半部：快速处理，不能睡眠
   - 底半部：延迟处理（工作队列/tasklet）

3. **中断释放** (`free_irq`)

## 模块参数 / Module Parameters

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| major_number | int | 0 | 主设备号 (0=动态分配) |
| buffer_size | int | 4096 | 内部缓冲区大小 |
| irq_trigger_type | int | 1 | IRQ触发类型 (0=无, 1=上升沿, 2=下降沿, 3=双边沿) |

## 许可证 / License

GPL-2.0

## 作者 / Author

Device Driver Framework Team

## 版本 / Version

1.0.0
