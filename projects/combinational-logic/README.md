# 组合逻辑电路模拟 (Combinational Logic Circuit Simulation)

## 项目简介 | Project Description

本项目是一个用于学习和理解组合逻辑电路的教育性项目。它使用Python实现了各种基本的组合逻辑电路组件，包括加法器、乘法器、多路选择器、译码器、编码器等。

This project is an educational tool for learning and understanding combinational logic circuits. It implements various basic combinational logic circuit components in Python, including adders, multipliers, multiplexers, decoders, encoders, and more.

## 学习目标 | Learning Objectives

- **理解组合逻辑**: 掌握组合逻辑电路的基本原理和特性
  - Understand combinational logic: master basic principles and characteristics

- **掌握加法器**: 学习半加器、全加器、行波进位加法器的实现
  - Master adders: learn half adder, full adder, ripple carry adder implementations

- **掌握多路选择器**: 理解MUX的原理和应用
  - Master multiplexers: understand MUX principles and applications

- **学会电路优化**: 了解不同电路结构的速度和面积权衡
  - Learn circuit optimization: understand speed-area tradeoffs of different circuit structures

## 项目结构 | Project Structure

```
combinational-logic/
├── src/                          # 源代码 | Source code
│   ├── __init__.py
│   ├── gates.py                  # 基本逻辑门 | Basic logic gates
│   ├── adders.py                 # 加法器和减法器 | Adders & subtractors
│   ├── multiplier.py             # 乘法器 | Multiplier circuits
│   ├── mux_demux.py              # 多路选择器和解复用器 | MUX & DEMUX
│   ├── encoder_decoder.py        # 编码器和译码器 | Encoders & decoders
│   ├── comparator.py             # 数值比较器 | Magnitude comparators
│   ├── tri_state.py              # 三态缓冲器 | Tri-state buffers
│   └── logic_synthesis.py        # 基于MUX的逻辑综合 | MUX-based synthesis
├── examples/                     # 演示脚本 | Demo scripts
│   ├── adder_subtractor_demo.py  # 加法器/减法器仿真
│   ├── mux_demo.py               # 多路选择器演示
│   ├── decoder_encoder_demo.py   # 译码器/编码器演示
│   └── custom_circuit_design.py  # 自定义电路设计
├── tests/                        # 单元测试 | Unit tests
│   └── test_combinational_logic.py
├── README.md
└── requirements.txt
```

## 组合逻辑理论背景 | Combinational Logic Theory Background

### 什么是组合逻辑？ | What is Combinational Logic?

组合逻辑电路的输出仅取决于当前输入，与之前的状态无关。它与时序逻辑电路（有记忆功能）相对。

The output of a combinational logic circuit depends only on the current inputs, not on previous states. This contrasts with sequential logic circuits which have memory.

### 基本逻辑门 | Basic Logic Gates

| 门类型 | 名称 | 运算 | 真值表 |
|--------|------|------|--------|
| AND | 与门 | A AND B | 1仅当所有输入为1 |
| OR | 或门 | A OR B | 1当任一输入为1 |
| NOT | 非门 | NOT A | 输入取反 |
| XOR | 异或门 | A XOR B | 输入不同时为1 |
| NAND | 与非门 | NOT(A AND B) | AND的反相 |
| NOR | 或非门 | NOT(A OR B) | OR的反相 |
| XNOR | 同或门 | A XNOR B | 输入相同时为1 |

### 核心组件 | Core Components

1. **加法器 (Adders)**: 执行二进制加法
   - 半加器 (Half Adder): 2个1位输入
   - 全加器 (Full Adder): 3个1位输入（含进位）
   - 行波进位加法器 (Ripple Carry Adder): 多位级联

2. **乘法器 (Multipliers)**: 执行二进制乘法
   - 直接乘法器: 部分积法
   - Wallace树乘法器: 压缩器树加速

3. **多路选择器 (Multiplexers)**: 从多个输入中选择一个
   - 2:1, 4:1, 8:1 MUX
   - 可用于实现任意布尔函数

4. **译码器 (Decoders)**: 将编码信息解码
   - 二进制译码器: 3-8线
   - BCD译码器: 4-10线
   - 7段译码器: 驱动数码管

5. **编码器 (Encoders)**: 将多个输入编码
   - 二进制编码器: 8-3线
   - BCD编码器: 十进制编码

6. **比较器 (Comparators)**: 比较两个数的大小
   - 1位比较器
   - 4位/多位比较器

## 如何运行示例 | How to Run Examples

### 运行所有示例 | Run All Examples

```bash
# 加法器/减法器仿真
python examples/adder_subtractor_demo.py

# 多路选择器演示
python examples/mux_demo.py

# 译码器/编码器演示
python examples/decoder_encoder_demo.py

# 自定义电路设计
python examples/custom_circuit_design.py
```

### 运行测试 | Run Tests

```bash
python -m pytest tests/ -v
# 或
python -m unittest tests/test_combinational_logic.py -v
```

## 技术栈 | Tech Stack

- **语言**: Python 3
- **框架**: 无 (纯Python实现)
- **依赖**: 无

## 贡献 | Contributing

欢迎提交问题和改进建议！

Issues and pull requests are welcome!

## 许可证 | License

MIT License
