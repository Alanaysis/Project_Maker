# Sensor Fusion / 传感器融合

> 实现 IMU/加速度计传感器融合的学习项目

---

## 📖 Project Description / 项目描述

### English

A comprehensive learning project for implementing sensor fusion algorithms for IMU (Inertial Measurement Unit) data processing. This project covers the core algorithms used in attitude estimation, including:

- **Complementary Filter**: Simple and efficient sensor fusion
- **Kalman Filter (EKF)**: Optimal recursive estimation
- **Madgwick Filter**: Gradient-based attitude estimation
- **Mahony Filter**: PI-based attitude estimation

### 中文

实现 IMU (惯性测量单元) 数据处理的传感器融合算法的综合学习项目。本项目涵盖姿态估计的核心算法，包括：

- **互补滤波器**: 简单高效的传感器融合
- **卡尔曼滤波器 (EKF)**: 最优递归估计
- **Madgwick 滤波器**: 基于梯度的姿态估计
- **Mahony 滤波器**: 基于 PI 的姿态估计

---

## 🎯 Learning Objectives / 学习目标

### English

1. **Understand Sensor Fusion**: Learn how to combine data from multiple sensors to get more accurate estimates
2. **Master Kalman Filtering**: Understand the theory and implementation of Kalman filters
3. **Learn Attitude Estimation**: Master different attitude representation methods (Euler angles, quaternions, rotation matrices)

### 学习目标

1. **理解传感器融合**: 学习如何结合多个传感器的数据获得更准确的估计
2. **掌握卡尔曼滤波**: 理解卡尔曼滤波的理论和实现
3. **学会姿态估计**: 掌握不同的姿态表示方法 (欧拉角、四元数、旋转矩阵)

---

## 📁 Project Structure / 项目结构

```
sensor-fusion/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── coordinate_transform.py   # 坐标变换 (欧拉角、四元数、旋转矩阵)
│   ├── sensor_calibration.py     # 传感器校准
│   ├── data_preprocessing.py     # 数据预处理 (滤波、异常值检测)
│   ├── complementary_filter.py   # 互补滤波器
│   ├── kalman_filter.py          # 卡尔曼滤波器 (含 EKF)
│   ├── madgwick_filter.py        # Madgwick 滤波器
│   └── mahony_filter.py          # Mahony 滤波器
├── examples/                     # 示例程序
│   ├── 01_raw_sensor_processing.py    # 原始传感器数据处理
│   ├── 02_complementary_filter_demo.py # 互补滤波器演示
│   ├── 03_kalman_filter_demo.py        # 卡尔曼滤波器演示
│   └── 04_attitude_comparison.py       # 姿态估计算法对比
├── tests/                        # 单元测试
│   └── test_sensor_fusion.py
├── README.md
├── requirements.txt
└── Makefile
```

---

## 🚀 How to Run / 如何运行

### Prerequisites / 前置条件

```bash
pip install numpy
```

### Run Examples / 运行示例

```bash
# 方法 1: 使用 Makefile
make example-1    # 原始传感器数据处理
make example-2    # 互补滤波器演示
make example-3    # 卡尔曼滤波器演示
make example-4    # 姿态估计对比

# 方法 2: 直接运行
python examples/01_raw_sensor_processing.py
python examples/02_complementary_filter_demo.py
python examples/03_kalman_filter_demo.py
python examples/04_attitude_comparison.py
```

### Run Tests / 运行测试

```bash
# 方法 1: 使用 Makefile
make test

# 方法 2: 直接运行
python -m pytest tests/ -v
python tests/test_sensor_fusion.py
```

---

## 📚 Sensor Fusion Theory / 传感器融合理论基础

### Coordinate Representations / 姿态表示

| 表示方法 | 维度 | 优点 | 缺点 |
|---------|------|------|------|
| 欧拉角 | 3 | 直观易懂 | 万向锁 |
| 四元数 | 4 | 无奇异点 | 不直观 |
| 旋转矩阵 | 9 | 数学简洁 | 冗余 |

### Filter Comparison / 滤波器对比

| 算法 | 计算量 | 精度 | 参数调节 | 适用场景 |
|------|--------|------|----------|----------|
| 互补滤波 | ⭐ | 中等 | 1 个参数 | 资源受限 |
| EKF | ⭐⭐⭐ | 高 | 协方差矩阵 | 高精度需求 |
| Madgwick | ⭐⭐ | 高 | 1 个参数 | 嵌入式系统 |
| Mahony | ⭐⭐ | 高 | 2 个参数 | 有磁力计 |

### Key Formulas / 核心公式

**Complementary Filter**:
```
θ_fused = α · (θ_prev + ω·dt) + (1-α) · θ_accel
```

**Kalman Filter**:
```
Prediction:  x̂ₖ = F·x̂ₖ₋₁ + B·uₖ
              Pₖ = F·Pₖ₋₁·Fᵀ + Q

Update:       Kₖ = Pₖ·Hᵀ·(H·Pₖ·Hᵀ + R)⁻¹
              x̂ₖ = x̂ₖ + Kₖ·(zₖ - H·x̂ₖ)
              Pₖ = (I - Kₖ·H)·Pₖ
```

**Quaternion Propagation**:
```
q̇ = ½ · ω_q ⊗ q
```

---

## 🔧 Core Loop / 核心流程

```
传感器数据 → 数据预处理 → 融合算法 → 姿态输出
     ↓           ↓           ↓         ↓
  加速度计    滤波/校准    EKF/互补   欧拉角
  陀螺仪      异常检测    Madgwick   四元数
  磁力计      坐标转换    Mahony     旋转矩阵
```

---

## 📝 References / 参考

1. Madgwick, S. "An efficient orientation filter for inertial and inertial/magnetic sensor arrays"
2. Mahony, R. "Nonlinear complementary filters on the special orthogonal group"
3. Welch, G. & Bishop, G. "An introduction to the Kalman filter"
4. https://www.x-io.co.uk/open-source-imu-and-ahrs-algorithms/

---

## 📄 License

MIT License
