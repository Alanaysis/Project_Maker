# Low-Power Embedded Design / 嵌入式低功耗设计

> **A learning framework for embedded low-power design techniques**
> 嵌入式低功耗设计技术学习框架

---

## 📖 Project Description / 项目描述

### English

This project implements a comprehensive embedded low-power design framework for learning purposes. It covers the core concepts and techniques used in power-constrained embedded systems, including:

- **Power Mode Management**: Active, Idle, Sleep, Deep Sleep, Standby, and Off modes with configurable transitions
- **Clock Gating**: Peripheral-level clock enable/disable to reduce dynamic power
- **Peripheral Power Control**: Domain-level power gating for deeper power savings
- **Wake-up Source Management**: Configurable wake-up sources (pin interrupts, RTC, UART, etc.)
- **DVFS (Dynamic Voltage Frequency Scaling)**: Intelligent voltage-frequency scaling to minimize energy per operation
- **Power Monitoring & Profiling**: Energy tracking and analysis for optimization

### 中文

本项目实现了一个全面的嵌入式低功耗设计学习框架。它涵盖了功耗受限嵌入式系统中使用的核心概念和技术，包括：

- **功耗模式管理**：活动、空闲、睡眠、深度睡眠、待机、关闭模式，支持可配置转换
- **时钟门控**：外设级时钟使能/禁用以降低动态功耗
- **外设电源控制**：域级电源门控实现更深的功耗节省
- **唤醒源管理**：可配置的唤醒源（引脚中断、实时时钟、串口等）
- **DVFS（动态电压频率调节）**：智能电压频率调节以最小化每次操作的能耗
- **功耗监测和分析**：能耗跟踪和分析以优化功耗

---

## 🎯 Learning Objectives / 学习目标

### English

- Understand the three components of power consumption in embedded systems
- Master different sleep modes and their trade-offs
- Learn clock gating and power gating techniques
- Understand DVFS principles and implementation
- Analyze power consumption patterns and identify optimization opportunities

### 中文

- 理解嵌入式系统中功耗的三个组成部分
- 掌握不同睡眠模式及其权衡
- 学习时钟门控和电源门控技术
- 理解 DVFS 原理和实现
- 分析功耗使用模式并识别优化机会

---

## 📚 Low-Power Design Theory / 低功耗设计理论

### English

#### Power Consumption Components / 功耗组成部分

**1. Dynamic Power (动态功耗)**
```
P_dyn = α × C × V² × f
```
Where α is the switching activity factor, C is load capacitance, V is supply voltage, and f is clock frequency.

**2. Static Power (静态功耗)**
```
P_static = I_leakage × V
```
Leakage current increases with temperature and decreases with process node scaling.

**3. Total Power (总功耗)**
```
P_total = P_dyn + P_static
```

#### Key Techniques / 关键技术

| Technique | Power Savings | Wake-up Latency | Use Case |
|-----------|--------------|-----------------|----------|
| Clock Gating | 10-50% | ~2μs | Always-on peripherals |
| Sleep Mode | 90-95% | ~10μs | Short idle periods |
| Deep Sleep | 99%+ | ~100μs | Long idle periods |
| DVFS | 20-80% | N/A | Variable workloads |

### 中文

#### 功耗组成部分

**1. 动态功耗**
```
P_dyn = α × C × V² × f
```
其中 α 是翻转活动因子，C 是负载电容，V 是供电电压，f 是时钟频率。

**2. 静态功耗**
```
P_static = I_leakage × V
```
漏电流随温度增加，随工艺节点缩小而减小。

**3. 总功耗**
```
P_total = P_dyn + P_static
```

#### 关键技术

| 技术 | 功耗节省 | 唤醒延迟 | 适用场景 |
|------|---------|---------|---------|
| 时钟门控 | 10-50% | ~2μs | 常供电外设 |
| 睡眠模式 | 90-95% | ~10μs | 短空闲期 |
| 深度睡眠 | 99%+ | ~100μs | 长空闲期 |
| DVFS | 20-80% | N/A | 可变工作负载 |

---

## 🏗️ Project Structure / 项目结构

```
low-power/
├── include/
│   └── low_power.h          # Core header with all data structures and API
├── src/
│   └── low_power.c          # Core framework implementation
├── examples/
│   ├── power_modes_demo.c   # Power mode switching demonstration
│   ├── wakeup_demo.c        # Wake-up source handling demo
│   ├── power_analysis_demo.c # Power consumption analysis demo
│   └── dvfs_demo.c          # DVFS demonstration
├── tests/
│   └── test_low_power.c     # Unit tests for all modules
├── docs/                      # Documentation directory
├── Makefile                   # Build system
└── README.md                  # This file
```

---

## 🚀 How to Build and Run / 如何构建和运行

### English

#### Build / 构建

```bash
# Build all examples
make

# Build and run tests
make test

# Clean build artifacts
make clean
```

#### Run Examples / 运行示例

```bash
# Run all examples
make run-all

# Run individual examples
./build/power_modes_demo    # Power mode switching demo
./build/wakeup_demo         # Wake-up source handling demo
./build/power_analysis_demo # Power consumption analysis demo
./build/dvfs_demo           # DVFS demonstration
```

### 中文

#### 构建

```bash
# 构建所有示例
make

# 构建并运行测试
make test

# 清理构建产物
make clean
```

#### 运行示例

```bash
# 运行所有示例
make run-all

# 运行单个示例
./build/power_modes_demo    # 功耗模式切换演示
./build/wakeup_demo         # 唤醒源处理演示
./build/power_analysis_demo # 功耗分析演示
./build/dvfs_demo           # DVFS演示
```

---

## 📊 Examples Description / 示例说明

### English

#### 1. Power Modes Demo (`power_modes_demo.c`)
Demonstrates the complete power mode switching cycle: Active → Idle → Sleep → Deep Sleep → Wakeup. Shows how each mode affects power consumption and wake-up latency.

#### 2. Wake-up Source Demo (`wakeup_demo.c`)
Demonstrates configuring and handling multiple wake-up sources including pin interrupts, RTC alarms, UART, and timers. Shows priority-based wake-up selection.

#### 3. Power Analysis Demo (`power_analysis_demo.c`)
Demonstrates power consumption analysis for a typical sensor node. Compares deep sleep vs sleep mode strategies and shows clock gating impact.

#### 4. DVFS Demo (`dvfs_demo.c`)
Demonstrates Dynamic Voltage Frequency Scaling with multiple operating points. Shows different DVFS policies (aggressive, balanced, efficient) and their energy trade-offs.

### 中文

#### 1. 功耗模式演示 (`power_modes_demo.c`)
演示完整的功耗模式切换周期：活动 → 空闲 → 睡眠 → 深度睡眠 → 唤醒。展示每种模式对功耗和唤醒延迟的影响。

#### 2. 唤醒源演示 (`wakeup_demo.c`)
演示配置和处理多个唤醒源，包括引脚中断、实时时钟报警、串口和定时器。展示基于优先级的唤醒选择。

#### 3. 功耗分析演示 (`power_analysis_demo.c`)
演示典型传感器节点的功耗分析。对比深度睡眠与睡眠模式策略，展示时钟门控的影响。

#### 4. DVFS演示 (`dvfs_demo.c`)
演示具有多个工作点的动态电压频率调节。展示不同 DVFS 策略（激进、平衡、高效）及其能耗权衡。

---

## 🔧 Core Concepts / 核心概念

### English

#### Power Mode Trade-offs / 功耗模式权衡

```
Performance ←→ Power Savings
    ↑              ↑
Active    Sleep    Deep Sleep    Off
(Fast)   (Medium)  (Slow)       (Reset)
```

#### DVFS Operating Points / DVFS工作点

```
Point | Voltage | Frequency | Power   | Energy/op
------+---------+-----------+---------+----------
  0   |  3.3V   |  72 MHz   |  Highest|  Lowest
  1   |  3.0V   |  48 MHz   |  High   |  Low
  2   |  2.7V   |  36 MHz   |  Medium |  Medium
  3   |  2.5V   |  24 MHz   |  Low    |  High
  4   |  2.2V   |  12 MHz   |  Lower  |  Higher
  5   |  1.8V   |   4 MHz   |  Low    |  Higher
  6   |  1.5V   |   1 MHz   |  Lower  |  Highest
  7   |  1.2V   | 100 kHz   |  Lowest |  Highest
```

#### Wake-up Source Latency / 唤醒源延迟

| Source | Latency | Power Impact |
|--------|---------|-------------|
| Pin Interrupt | ~2μs | Minimal |
| RTC Alarm | ~5μs | Low |
| Timer | ~10μs | Medium |
| UART/I2C/SPI | ~20μs | Medium |
| Comparator | ~5μs | Low |

### 中文

#### 功耗模式权衡

```
性能 ←→ 功耗节省
    ↑              ↑
活动    睡眠    深度睡眠    关闭
(快)   (中)    (慢)       (复位)
```

#### 唤醒源延迟

| 源 | 延迟 | 功耗影响 |
|----|------|---------|
| 引脚中断 | ~2μs | 极小 |
| 实时时钟报警 | ~5μs | 低 |
| 定时器 | ~10μs | 中 |
| 串口/I2C/SPI | ~20μs | 中 |
| 比较器 | ~5μs | 低 |

---

## 📝 Notes / 说明

### English

This is a **simulation-based learning framework**. All power measurements and timing are simulated for educational purposes. On real hardware, actual values will depend on:

- MCU architecture and silicon process
- External circuit design (LDO efficiency, load)
- PCB layout and parasitic capacitance
- Temperature and operating conditions

### 中文

这是一个**基于模拟的学习框架**。所有功耗测量和时序都是为教育目的而模拟的。在真实硬件上，实际值取决于：

- MCU 架构和硅工艺
- 外部电路设计（LDO 效率、负载）
- PCB 布局和寄生电容
- 温度和工作条件

---

## 📄 License / 许可证

This project is for educational purposes only.

本项目仅用于教育目的。
