# 电路仿真 SPICE 调研报告

## 1. SPICE 简介

SPICE (Simulation Program with Integrated Circuit Emphasis) 是最广泛使用的电路仿真程序之一，最初由加州大学伯克利分校于 1970 年代开发。

### 1.1 发展历史

| 年份 | 事件 |
|------|------|
| 1971 | SPICE1 在伯克利诞生 |
| 1975 | SPICE2 发布 |
| 1983 | SPICE3 发布 |
| 1985 | 商业化开始 (HSPICE, PSPICE) |
| 1998 | 开源 ngspice 发布 |
| 至今 | 各种商业和开源版本共存 |

### 1.2 主要功能

- **直流分析 (DC Analysis)**: 计算电路的直流工作点
- **交流分析 (AC Analysis)**: 频率响应分析
- **瞬态分析 (Transient Analysis)**: 时间域仿真
- **噪声分析 (Noise Analysis)**: 电子噪声分析
- **失真分析 (Distortion Analysis)**: 非线性失真分析

## 2. 核心算法

### 2.1 改进节点分析法 (MNA)

MNA 是 SPICE 使用的核心算法，用于建立电路方程：

```
[G B] [v]   [i]
[C D] [j] = [e]
```

**矩阵元素**:
- **G**: 电导矩阵 (n×n)
- **B, C**: 电压源连接矩阵
- **D**: 通常为零矩阵
- **v**: 节点电压向量
- **j**: 电压源电流向量
- **i**: 电流源向量
- **e**: 电压源向量

### 2.2 元件印记 (Stamp)

每个电路元件对 MNA 矩阵有特定的贡献：

**电阻 R 连接节点 i 和 j**:
```
G[i,i] += 1/R
G[j,j] += 1/R
G[i,j] -= 1/R
G[j,i] -= 1/R
```

**电压源 V 连接节点 i 和 j**:
```
B[i,k] = 1
B[j,k] = -1
C[k,i] = 1
C[k,j] = -1
e[k] = V
```

### 2.3 数值积分

瞬态分析使用数值积分方法：

**后向欧拉法 (Backward Euler)**:
```
v(t+h) = v(t) + h * dv/dt(t+h)
```

**梯形法 (Trapezoidal)**:
```
v(t+h) = v(t) + h/2 * [dv/dt(t) + dv/dt(t+h)]
```

**Gear 方法 (BDF)**:
- 二阶: 使用前两个时间点
- 更高阶: 使用更多历史点

## 3. 电路元件模型

### 3.1 无源元件

| 元件 | 符号 | 电压-电流关系 |
|------|------|--------------|
| 电阻 R | R | V = IR |
| 电容 C | C | I = C dV/dt |
| 电感 L | L | V = L dI/dt |

### 3.2 有源元件

| 元件 | 符号 | 描述 |
|------|------|------|
| 独立电压源 | V | 固定电压 |
| 独立电流源 | I | 固定电流 |
| 受控电压源 | E, H | 电压/电流控制 |
| 受控电流源 | F, G | 电压/电流控制 |

### 3.3 半导体器件

| 器件 | 模型 |
|------|------|
| 二极管 | Shockley 方程 |
| BJT | Ebers-Moll, Gummel-Poon |
| MOSFET | Shichman-Hodges, BSIM |

## 4. 分析类型详解

### 4.1 直流分析

**目的**: 计算电路的直流工作点

**算法**:
1. 建立 MNA 矩阵
2. 求解线性方程组 Ax = b
3. 提取节点电压和支路电流

**应用**:
- 偏置点计算
- 直流扫描
- 戴维南等效

### 4.2 交流分析

**目的**: 计算电路的频率响应

**算法**:
1. 在每个频率点建立复数 MNA 矩阵
2. 求解复数线性方程组
3. 计算幅度和相位

**应用**:
- 滤波器设计
- 放大器频率响应
- 稳定性分析

### 4.3 瞬态分析

**目的**: 计算电路的时间域响应

**算法**:
1. 将动态元件转换为伴随模型
2. 在每个时间点求解线性方程组
3. 更新元件状态

**应用**:
- 开关电源仿真
- 数字电路时序
- 信号完整性分析

## 5. 网表格式

### 5.1 SPICE 网表语法

```
* 注释行
标题行

* 元件定义
Rname n1 n2 value
Cname n1 n2 value
Lname n1 n2 value
Vname n1 n2 DC value
Vname n1 n2 AC mag phase
Vname n1 n2 SIN(vo va freq)
Iname n1 n2 value

* 分析命令
.dc vsource start stop step
.ac dec/lin/oct npoints fstart fstop
.tran tstep tstop

.end
```

### 5.2 单位后缀

| 后缀 | 值 |
|------|-----|
| T | 10^12 |
| G | 10^9 |
| MEG | 10^6 |
| K | 10^3 |
| M | 10^-3 |
| U | 10^-6 |
| N | 10^-9 |
| P | 10^-12 |
| F | 10^-15 |

## 6. 参考资料

### 6.1 经典教材

1. **"Circuit Simulation"** by Farid N. Najm
   - 全面介绍电路仿真理论和算法
   - 涵盖 MNA、数值积分、收敛性分析

2. **"SPICE: A Guide to Circuit Simulation and Analysis Using PSpice"** by Paul Tuinenga
   - SPICE 使用指南
   - 包含大量实际示例

3. **"Computer-Aided Circuit Analysis Tools"** by Mohammed Ismail
   - 计算机辅助电路分析
   - 深入算法细节

### 6.2 开源实现

1. **ngspice**: 开源 SPICE 仿真器
   - 网站: http://ngspice.sourceforge.net/
   - 支持所有标准分析类型

2. **QUCS**: 电路仿真套件
   - 网站: https://qucs.sourceforge.net/
   - 图形化界面

3. **PySpice**: Python SPICE 接口
   - GitHub: https://github.com/FabriceSalvaire/PySpice
   - 支持 ngspice 和 xyce

### 6.3 学术资源

1. **伯克利 SPICE 项目**: 原始 SPICE 源码和文档
2. **IEEE Transactions on CAD**: 电路仿真算法研究
3. **DAC/ICCAD 会议**: 最新仿真技术进展

## 7. 项目实现策略

### 7.1 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 语言 | Python | 易于学习和实现 |
| 线性代数 | NumPy/SciPy | 高效矩阵运算 |
| 可视化 | Matplotlib | 丰富的绘图功能 |
| 测试 | pytest | 简洁的测试框架 |

### 7.2 实现阶段

**阶段 1: 基础框架**
- 元件模型
- 网表解析
- 矩阵建立

**阶段 2: 分析引擎**
- 直流分析
- 交流分析
- 瞬态分析

**阶段 3: 应用扩展**
- 实际电路示例
- 参数扫描
- 结果可视化

### 7.3 测试策略

1. **单元测试**: 测试每个元件的印记
2. **集成测试**: 测试完整电路分析
3. **验证测试**: 与理论值对比
4. **性能测试**: 大规模电路测试
