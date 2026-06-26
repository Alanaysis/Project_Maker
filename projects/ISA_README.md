# 🖥️ 指令集架构模块

> 4 个项目 | 涵盖 RISC-V、ARM、x86 模拟器、指令集对比分析

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [riscv-simulator](riscv-simulator/) | RISC-V 指令集模拟器 | C/Rust | ⭐⭐⭐⭐⭐ | ✅ |
| [arm-simulator](arm-simulator/) | ARM 指令集模拟器 | Python | ⭐⭐⭐⭐⭐ | ✅ |
| [x86-simulator](x86-simulator/) | x86 指令集模拟器 | C/Rust | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [instruction-set-comparison](instruction-set-comparison/) | 指令集对比分析 | Python | ⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
RISC-V 模拟 → ARM 模拟 → x86 模拟 → 指令集对比
     ↓           ↓           ↓           ↓
  精简指令集   ARM 架构    复杂指令集   CISC vs RISC
  访存指令     Thumb 模式   变长编码   性能对比
  中断异常     NEON SIMD   保护模式    代码密度
```

### 推荐学习顺序

1. **riscv-simulator** (RISC-V 模拟器)
   - 学习 RISC-V 指令集
   - 理解单周期/多周期处理器
   - 掌握访存指令

2. **arm-simulator** (ARM 模拟器)
   - 学习 ARM 架构
   - 理解 Thumb 模式
   - 掌握 NEON SIMD

3. **x86-simulator** (x86 模拟器)
   - 学习 x86 变长编码
   - 理解保护模式
   - 掌握中断处理

4. **instruction-set-comparison** (指令集对比分析)
   - 对比 CISC vs RISC
   - 分析性能差异
   - 理解设计哲学

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **C** | 模拟器核心 | [C 官方文档](https://en.cppreference.com/w/c) |
| **Rust** | 模拟器核心 | [Rust 官方文档](https://doc.rust-lang.org/) |
| **Python** | ARM 模拟/分析 | [Python 官方文档](https://docs.python.org/3/) |

---

## 📚 学习资源

### 书籍
- 《计算机体系结构：量化研究方法》
- 《RISC-V 用户手册》
- 《x86 汇编语言》

### 开源项目
- [QEMU](https://github.com/qemu/qemu)
- [RISC-V GNU Toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)
