# ⚡ 数字/模拟电路模块

> 11 个项目 | 涵盖逻辑门、组合/时序逻辑、CPU、基本电路、放大器、滤波器、ADC/DAC、Verilog、芯片布局、时序分析

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [logic-gates](logic-gates/) | 逻辑门模拟器 | Python | ⭐⭐⭐ | ✅ |
| [combinational-logic](combinational-logic/) | 组合逻辑电路 | Python | ⭐⭐⭐⭐ | ✅ |
| [sequential-logic](sequential-logic/) | 时序逻辑电路 | Python | ⭐⭐⭐⭐ | ✅ |
| [simple-cpu](simple-cpu/) | 简易 CPU 设计 | C++/Rust | ⭐⭐⭐⭐⭐ | ✅ |
| [basic-circuit](basic-circuit/) | 基本电路模拟 | Python, NumPy | ⭐⭐⭐ | ✅ |
| [amplifier-design](amplifier-design/) | 放大器设计 | Python, matplotlib | ⭐⭐⭐ | ✅ |
| [analog-filter](analog-filter/) | 模拟滤波器 | Python, scipy | ⭐⭐⭐ | ✅ |
| [adc-dac](adc-dac/) | ADC/DAC 模拟 | Python, matplotlib | ⭐⭐⭐⭐ | ✅ |
| [verilog-simulator](verilog-simulator/) | Verilog 模拟器 | C++/Rust | ⭐⭐⭐⭐⭐ | ✅ |
| [chip-placement](chip-placement/) | 芯片布局布线 | C++/Rust | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [timing-analysis](timing-analysis/) | 时序分析 | C++/Rust | ⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
逻辑门 → 组合逻辑 → 时序逻辑 → CPU 设计 → 基本电路 → 放大器 → 滤波器 → ADC/DAC → Verilog → 芯片布局 → 时序分析
     ↓         ↓          ↓          ↓          ↓         ↓         ↓         ↓         ↓         ↓          ↓
  基本门     加法器     触发器     取指执行   电路分析   运放设计   频域分析   采样量化   事件驱动   布局布线   静态时序
  真值表     MUX/DEC   计数器     译码执行   网表       增益       波特图     量化噪声   仿真       时序分析   Slack
```

### 推荐学习顺序

1. **logic-gates** (逻辑门模拟器)
   - 学习基本逻辑门
   - 理解真值表
   - 掌握电路仿真

2. **combinational-logic** (组合逻辑电路)
   - 学习加法器/MUX/译码器
   - 理解组合逻辑综合
   - 掌握电路设计

3. **sequential-logic** (时序逻辑电路)
   - 学习触发器/计数器
   - 理解状态机
   - 掌握时序图

4. **simple-cpu** (简易 CPU 设计)
   - 学习取指译码执行
   - 理解数据通路
   - 掌握指令集

5. **basic-circuit** (基本电路模拟)
   - 学习 SPICE 算法
   - 理解节点分析
   - 掌握瞬态分析

6. **amplifier-design** (放大器设计)
   - 学习运放设计
   - 理解反馈理论
   - 掌握频率响应

7. **analog-filter** (模拟滤波器)
   - 学习滤波器设计
   - 理解频域分析
   - 掌握 Butterworth/Chebyshev

8. **adc-dac** (ADC/DAC 模拟)
   - 学习采样/量化
   - 理解 SNR/ENOB
   - 掌握混叠检测

9. **verilog-simulator** (Verilog 模拟器)
   - 学习 Verilog 语法
   - 理解事件驱动仿真
   - 掌握波形输出

10. **chip-placement** (芯片布局布线)
    - 学习解析布局
    - 理解模拟退火
    - 掌握布线算法

11. **timing-analysis** (时序分析)
    - 学习静态时序分析
    - 理解建立/保持时间
    - 掌握关键路径

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **Python** | 仿真和模拟 | [Python 官方文档](https://docs.python.org/3/) |
| **numpy** | 数值计算 | [NumPy 文档](https://numpy.org/) |
| **scipy** | 科学计算 | [SciPy 文档](https://scipy.org/) |
| **matplotlib** | 可视化 | [Matplotlib 文档](https://matplotlib.org/) |
| **C++** | 模拟器/EDA | [C++ 官方文档](https://en.cppreference.com/) |
| **Rust** | 模拟器/EDA | [Rust 官方文档](https://doc.rust-lang.org/) |

---

## 📚 学习资源

### 书籍
- 《数字设计》- Morris Mano
- 《模拟集成电路设计》- Razavi
- 《Verilog HDL 设计》- Jim Li
- 《VLSI 设计》- Wakerly

### 开源项目
- [Verilator](https://github.com/verilator/verilator)
- [Yosys](https://github.com/YosysHQ/yosys)
- [ngspice](https://github.com/ngspice/ngspice)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)
