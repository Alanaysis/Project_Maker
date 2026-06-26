# ⚙️ 机械工程模块

> 10 个项目 | 涵盖机械臂、齿轮、凸轮、连杆、振动、热力学、流体力学、CAD、有限元、3D 打印

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [robot-arm-kinematics](robot-arm-kinematics/) | 机械臂运动学 | Python, numpy, matplotlib | ⭐⭐⭐⭐ | ✅ |
| [gear-transmission](gear-transmission/) | 齿轮传动系统 | Python, matplotlib | ⭐⭐⭐ | ✅ |
| [cam-mechanism](cam-mechanism/) | 凸轮机构设计 | Python, matplotlib | ⭐⭐⭐⭐ | ✅ |
| [linkage-mechanism](linkage-mechanism/) | 连杆机构分析 | Python, matplotlib | ⭐⭐⭐⭐ | ✅ |
| [vibration-analysis](vibration-analysis/) | 振动分析系统 | Python, scipy, matplotlib | ⭐⭐⭐⭐⭐ | ✅ |
| [thermodynamics](thermodynamics/) | 热力学模拟 | Python, numpy, matplotlib | ⭐⭐⭐⭐⭐ | ✅ |
| [fluid-mechanics](fluid-mechanics/) | 流体力学基础 | Python, numpy, matplotlib | ⭐⭐⭐⭐ | ✅ |
| [cad-kernel](cad-kernel/) | CAD 内核基础 | C++, Rust | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [finite-element](finite-element/) | 有限元分析基础 | Python, numpy, scipy | ⭐⭐⭐⭐⭐ | ✅ |
| [3d-print-slicer](3d-print-slicer/) | 3D 打印切片器 | Python, numpy | ⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
机械臂运动学 → 齿轮传动 → 凸轮机构 → 连杆机构 → 振动分析 → 热力学 → 流体力学
      ↓            ↓          ↓          ↓           ↓          ↓          ↓
   DH参数      齿轮比计算   轮廓设计    Grashof条件  模态分析   热传导方程  伯努利方程
   FK/IK      传动效率     运动规律    耦合曲线     FRF       有限差分   管道流动
```

### 推荐学习顺序

1. **robot-arm-kinematics** (机械臂运动学)
   - 学习 DH 参数和正向运动学
   - 理解逆向运动学求解
   - 掌握 Jacobian 矩阵

2. **gear-transmission** (齿轮传动系统)
   - 学习齿轮几何和传动比
   - 理解齿轮系分析
   - 掌握效率计算

3. **cam-mechanism** (凸轮机构设计)
   - 学习凸轮轮廓生成
   - 理解从动件运动规律
   - 掌握压力角分析

4. **linkage-mechanism** (连杆机构分析)
   - 学习四连杆机构分析
   - 理解位置/速度/加速度分析
   - 掌握耦合曲线生成

5. **vibration-analysis** (振动分析系统)
   - 学习自由/受迫振动
   - 理解模态分析
   - 掌握频响函数

6. **thermodynamics** (热力学模拟)
   - 学习热传导方程
   - 理解有限差分法
   - 掌握边界条件处理

7. **fluid-mechanics** (流体力学基础)
   - 学习伯努利方程
   - 理解管道流动计算
   - 掌握雷诺数分析

8. **cad-kernel** (CAD 内核基础)
   - 学习 B-rep 数据模型
   - 理解布尔运算
   - 掌握曲面建模

9. **finite-element** (有限元分析基础)
   - 学习网格生成
   - 理解刚度矩阵组装
   - 掌握应力分析

10. **3d-print-slicer** (3D 打印切片器)
    - 学习 STL 解析
    - 理解切片算法
    - 掌握 G-code 生成

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **Python** | 仿真和模拟 | [Python 官方文档](https://docs.python.org/3/) |
| **numpy** | 数值计算 | [NumPy 文档](https://numpy.org/) |
| **scipy** | 科学计算 | [SciPy 文档](https://scipy.org/) |
| **matplotlib** | 可视化 | [Matplotlib 文档](https://matplotlib.org/) |
| **C++** | CAD/有限元 | [C++ 官方文档](https://en.cppreference.com/) |
| **Rust** | CAD 内核 | [Rust 官方文档](https://doc.rust-lang.org/) |

---

## 📚 学习资源

### 书籍
- 《机器人学导论》- John J. Craig
- 《机械原理》- 孙恒
- 《有限元分析》- C.S. Huang
- 《计算流体力学》- 邱建熹

### 开源项目
- [OpenCascade](https://github.com/OpenCascade/OCCT) - CAD 内核
- [TensorFlow](https://github.com/tensorflow/tensorflow) - 数值计算
- [Blender](https://github.com/blender/blender) - 3D 建模

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)
