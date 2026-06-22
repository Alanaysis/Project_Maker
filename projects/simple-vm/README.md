# Simple VM - 简易虚拟机监控器

## 项目简介

Simple VM 是一个基于 KVM API 的简易虚拟机监控器（VMM），用于学习 x86 架构和虚拟化技术。

## 学习目标

- **x86 架构理解**：掌握寄存器、内存模型、指令执行流程
- **虚拟化技术（VT-x）**：理解 VMX root/non-root 模式、VM exit 处理
- **内存虚拟化**：了解 EPT（Extended Page Tables）机制
- **I/O 虚拟化**：掌握 PIO（Port I/O）和 MMIO 处理

## 技术栈

| 技术 | 说明 | 学习难度 |
|------|------|----------|
| C/C++ | 主要实现语言 | ⭐⭐⭐ |
| KVM API | Linux 内核虚拟化接口 | ⭐⭐⭐⭐ |
| x86 指令集 | 目标架构 | ⭐⭐⭐⭐ |
| Linux 系统编程 | ioctl、mmap 等 | ⭐⭐⭐ |

## 核心架构

```
┌─────────────────────────────────────────────┐
│              用户空间 (VMM)                  │
├─────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ VM 管理  │  │ vCPU    │  │ 内存    │    │
│  │ 模块    │  │ 管理    │  │ 管理    │    │
│  └────┬────┘  └────┬────┘  └────┬────┘    │
│       │            │            │          │
│       └────────────┼────────────┘          │
│                    │                       │
│              ┌─────┴─────┐                 │
│              │  KVM API  │                 │
│              └─────┬─────┘                 │
├────────────────────┼───────────────────────┤
│              内核空间                       │
│              ┌─────┴─────┐                 │
│              │    KVM    │                 │
│              └───────────┘                 │
└─────────────────────────────────────────────┘
```

## 重点难点

### ⭐ 重点
1. **KVM API 使用**：理解 `/dev/kvm` 接口和 ioctl 调用
2. **VM Exit 处理**：正确处理各种退出原因
3. **内存映射**：正确设置用户空间与 Guest 内存的映射

### ⭐ 难点
1. **x86 指令解码**：解析复杂的指令格式
2. **中断处理**：模拟 PIC/APIC 中断控制器
3. **I/O 模拟**：处理 PIO 和 MMIO 访问

### 💡 值得思考
1. 为什么 KVM 需要 VT-x 硬件支持？
2. VM Entry 和 VM Exit 的性能开销来自哪里？
3. 如何设计高效的内存虚拟化方案？
4. 软件模拟 vs 硬件辅助虚拟化的权衡？

## 项目结构

```
simple-vm/
├── include/          # 头文件
│   ├── vm.h         # 虚拟机管理
│   ├── vcpu.h       # vCPU 管理
│   ├── memory.h     # 内存管理
│   └── io.h         # I/O 处理
├── src/             # 源代码
│   ├── main.cpp     # 主程序
│   ├── vm.cpp       # 虚拟机实现
│   ├── vcpu.cpp     # vCPU 实现
│   ├── memory.cpp   # 内存管理实现
│   └── io.cpp       # I/O 处理实现
├── tests/           # 单元测试
├── examples/        # 示例程序
└── docs/            # 文档
```

## 快速开始

```bash
# 编译
make

# 运行示例
./build/simple-vm examples/hello.asm
```

## 参考资源

- [KVM API Documentation](https://www.kernel.org/doc/html/latest/virt/kvm/api.html)
- [Intel Software Developer Manual](https://software.intel.com/en-us/articles/intel-sdm)
- [kvmtool](https://github.com/kvmtool/kvmtool) - 轻量级 KVM VMM
- [Firecracker](https://github.com/firecracker-microvm/firecracker) - AWS 轻量级 VMM

## 相关项目

| 项目 | 特点 | 适用场景 |
|------|------|----------|
| QEMU | 功能完整、设备模拟丰富 | 生产环境 |
| Firecracker | 轻量级、快速启动 | Serverless |
| kvmtool | 代码简洁、易于学习 | 学习研究 |
| Cloud Hypervisor | Rust 实现、现代架构 | 云环境 |

## 许可证

MIT License
