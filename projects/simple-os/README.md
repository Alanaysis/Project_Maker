# 简易操作系统 (Simple OS)

> 一个用于学习操作系统内核原理的教学项目

## 项目简介

Simple OS 是一个从零开始实现的简易操作系统内核，旨在帮助学习者深入理解操作系统的核心概念和实现原理。项目参考了 xv6、Linux 和 MINIX 的设计理念，但大幅简化以适合初学者。

## 学习目标

通过本项目，你将学到：

1. **引导加载过程** - 理解计算机如何从 BIOS 到内核启动
2. **内核初始化** - 掌握内核各子系统的初始化流程
3. **进程管理** - 学会进程创建、调度和切换
4. **内存管理** - 理解分页机制和虚拟内存
5. **中断处理** - 掌握硬件中断和系统调用机制
6. **文件系统** - 了解基本的文件系统实现

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| C 语言 | 内核主体实现 | ⭐⭐⭐ |
| x86 汇编 | 引导加载、中断处理 | ⭐⭐⭐⭐ |
| NASM | 汇编器 | ⭐⭐ |
| GCC | C 编译器 | ⭐⭐ |
| QEMU | 虚拟机测试 | ⭐ |
| Make | 构建系统 | ⭐⭐ |

## 重点难点

### ⭐ 重点
- **GDT/IDT 初始化**：全局描述符表和中断描述符表是保护模式的基础
- **分页机制**：虚拟地址到物理地址的转换
- **上下文切换**：进程切换时的寄存器保存和恢复
- **系统调用**：用户态到内核态的切换

### 💡 值得思考
1. 为什么需要保护模式？实模式有什么限制？
2. 虚拟内存如何实现进程间的内存隔离？
3. 中断和异常有什么区别？
4. 如何设计一个公平的进程调度算法？
5. 文件系统的目录结构如何实现？

## 项目结构

```
simple-os/
├── boot/           # 引导加载程序
│   ├── boot.asm    # 主引导扇区
│   └── loader.asm  # 加载器
├── kernel/         # 内核核心
│   ├── main.c      # 内核入口
│   ├── gdt.c       # GDT 初始化
│   ├── idt.c       # IDT 初始化
│   └── timer.c     # 定时器中断
├── drivers/        # 设备驱动
│   ├── screen.c    # 屏幕输出
│   └── keyboard.c  # 键盘驱动
├── mm/             # 内存管理
│   ├── memory.c    # 内存管理
│   └── paging.c    # 分页管理
├── process/        # 进程管理
│   ├── process.c   # 进程管理
│   └── scheduler.c # 进程调度
├── fs/             # 文件系统
│   └── fs.c        # 简单文件系统
├── include/        # 头文件
├── tests/          # 单元测试
├── docs/           # 文档
└── examples/       # 使用示例
```

## 快速开始

### 环境要求

- GCC (支持 32 位编译)
- NASM 汇编器
- QEMU 模拟器
- Make

### 编译运行

```bash
# 安装依赖 (Ubuntu/Debian)
sudo apt-get install gcc nasm qemu-system-x86 make

# 编译内核
make

# 在 QEMU 中运行
make run

# 调试模式运行
make debug
```

### 学习路径

1. **第一阶段：引导加载**
   - 阅读 `boot/boot.asm`
   - 理解主引导扇区的工作原理
   - 学习实模式到保护模式的切换

2. **第二阶段：内核初始化**
   - 阅读 `kernel/main.c`
   - 理解 GDT/IDT 的初始化
   - 学习中断处理机制

3. **第三阶段：内存管理**
   - 阅读 `mm/memory.c` 和 `mm/paging.c`
   - 理解分页机制
   - 学习虚拟内存管理

4. **第四阶段：进程管理**
   - 阅读 `process/process.c`
   - 理解进程控制块
   - 学习进程调度算法

## 参考资源

- [xv6 源码](https://github.com/mit-pdos/xv6-public)
- [MIT 6.S081 课程](https://pdos.csail.mit.edu/6.828/2020/)
- [OSDev Wiki](https://wiki.osdev.org)
- [Operating Systems: Three Easy Pieces](https://pages.cs.wisc.edu/~remzi/OSTEP/)
- [Writing an OS in Rust](https://os.phil-opp.com) (概念通用)

## 许可证

本项目仅用于学习目的，采用 MIT 许可证。
