# Robot Arm Kinematics / 机械臂运动学

> **Learning robot kinematics through implementation** / **通过实现学习机器人运动学**

---

## 📖 Project Description / 项目描述

### English

This project implements robot arm kinematics from scratch as a learning tool.
It covers both forward and inverse kinematics for serial manipulators using
Denavit-Hartenberg (DH) parameters.

**What you'll learn:**
- How DH parameters define robot geometry
- Forward kinematics: computing end-effector pose from joint angles
- Inverse kinematics: computing joint angles for desired end-effector pose
- Jacobian matrix: velocity mapping and singularity analysis
- Workspace analysis and visualization
- Trajectory planning between waypoints

### 中文

本项目从零实现机械臂运动学，作为学习工具。涵盖使用 DH 参数对串联机械臂的正向和逆向运动学。

**你将学到：**
- DH 参数如何定义机器人几何结构
- 正向运动学：从关节角度计算末端位姿
- 逆向运动学：从期望末端位姿计算关节角度
- 雅可比矩阵：速度映射和奇异分析
- 工作空间分析与可视化
- 路径点之间的轨迹规划

---

## 🎯 Learning Objectives / 学习目标

1. **理解 DH 参数** - 掌握标准 DH 和修正 DH 参数法的区别与应用
2. **掌握正向运动学** - 通过齐次变换矩阵计算末端执行器位姿
3. **学会逆向运动学** - 掌握解析法和数值法求解 IK
4. **雅可比矩阵分析** - 理解速度映射、可操作性和奇异点
5. **工作空间可视化** - 理解机械臂可达区域
6. **轨迹规划** - 学习关节空间和笛卡尔空间的轨迹生成

---

## 📁 Project Structure / 项目结构

```
robot-arm-kinematics/
├── src/                          # Source code / 源代码
│   ├── __init__.py
│   ├── dh_parameters.py          # DH 参数计算
│   ├── forward_kinematics.py     # 正向运动学
│   ├── inverse_kinematics.py     # 逆向运动学
│   ├── jacobian.py               # 雅可比矩阵
│   ├── workspace.py              # 工作空间可视化
│   └── mapping.py                # 关节空间到笛卡尔空间映射
├── examples/                     # 示例脚本
│   ├── 01_2r_fk_ik.py           # 2R 机械臂正向/逆向运动学
│   ├── 02_3r_simulation.py       # 3R 机械臂仿真
│   ├── 03_path_planning.py       # 路径规划演示
│   └── 04_workspace_visualization.py  # 工作空间可视化
├── tests/                        # 单元测试
│   ├── test_dh_parameters.py
│   ├── test_forward_kinematics.py
│   ├── test_inverse_kinematics.py
│   ├── test_jacobian.py
│   └── test_mapping.py
├── outputs/                      # 生成的图表
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run / 如何运行

### 1. Install Dependencies / 安装依赖

```bash
pip install -r requirements.txt
```

### 2. Run Examples / 运行示例

```bash
# Example 1: 2R arm forward/inverse kinematics
python examples/01_2r_fk_ik.py

# Example 2: 3R arm simulation
python examples/02_3r_simulation.py

# Example 3: Path planning demo
python examples/03_path_planning.py

# Example 4: Workspace visualization
python examples/04_workspace_visualization.py
```

All examples generate plots in the `outputs/` directory.

### 3. Run Tests / 运行测试

```bash
pip install pytest
pytest tests/ -v
```

---

## 📐 DH Parameter Explanation / DH 参数详解

### Denavit-Hartenberg Convention

The DH convention provides a systematic method for naming coordinate frames
and computing transformation matrices between adjacent links.

### Standard DH Parameters (标准 DH 参数)

For each joint i, four parameters define the transformation from frame i-1 to frame i:

| Parameter | Symbol | Description |
|-----------|--------|-------------|
| Joint angle | θ_i | Rotation around z_{i-1} |
| Link offset | d_i | Translation along z_{i-1} |
| Link length | a_i | Translation along x_i |
| Link twist | α_i | Rotation around x_i |

**Transformation matrix T_i^{i-1}:**

```
T = [cos(θ)   -sin(θ)cos(α)   sin(θ)sin(α)   a*cos(θ) ]
    [sin(θ)    cos(θ)cos(α)  -cos(θ)sin(α)   a*sin(θ) ]
    [0         sin(α)          cos(α)          d        ]
    [0         0               0               1        ]
```

### Modified DH Parameters (修正 DH 参数)

The modified convention places x_i at the base of z_i, which simplifies
computation for serial manipulators:

| Parameter | Symbol | Description |
|-----------|--------|-------------|
| Joint angle | θ_i | Rotation around z_i |
| Link offset | d_i | Translation along z_i |
| Link length | a_{i-1} | Translation along x_{i-1} |
| Link twist | α_{i-1} | Rotation around x_{i-1} |

### Forward Kinematics / 正向运动学

The overall transformation from base to end-effector:

```
T_0^n = T_0^1 × T_1^2 × ... × T_{n-1}^n
```

### Inverse Kinematics / 逆向运动学

For a 2R planar arm with target (x, y):

```
cos(θ₂) = (x² + y² - l₁² - l₂²) / (2·l₁·l₂)

θ₂ = atan2(±√(1-cos²(θ₂)), cos(θ₂))
θ₁ = atan2(y, x) - atan2(k₂, k₁)

where k₁ = l₁ + l₂·cos(θ₂), k₂ = l₂·sin(θ₂)
```

Two solutions exist: elbow-up (θ₂ > 0) and elbow-down (θ₂ < 0).

---

## 📊 Core Loop / 核心循环

```
关节角度 → DH 参数 → 正向运动学 → 末端位置
末端位置 → 逆向运动学 → 关节角度
```

1. **关节角度 → DH 参数**: 将关节角度代入 DH 变换矩阵
2. **DH 参数 → 正向运动学**: 连乘所有变换矩阵得到末端位姿
3. **正向运动学 → 末端位置**: 从变换矩阵提取位置和方向
4. **末端位置 → 逆向运动学**: 通过解析或数值方法求解关节角度
5. **逆向运动学 → 关节角度**: 得到 IK 解并验证

---

## 📚 References / 参考资料

- Craig, J. J. "Introduction to Robotics: Mechanics and Control"
- Spong, S., Hutchinson, S., & Vidyasagar, M. "Robot Modeling and Control"
- Murray, Li, & Sastry "A Mathematical Introduction to Robotic Manipulation"

---

## 🔧 Tech Stack / 技术栈

- **Language**: Python 3
- **Numerical**: NumPy, SciPy
- **Visualization**: Matplotlib

---

## 📝 License

MIT License
