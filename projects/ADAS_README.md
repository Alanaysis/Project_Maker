# 🚗 自动驾驶模块

> 4 个深度学习项目，涵盖感知、规划、模拟、建图

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [adas-perception](adas-perception/) | 自动驾驶感知系统 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐⭐ | ✅ |
| [adas-planning](adas-planning/) | 自动驾驶规划控制 | Python | ⭐⭐⭐⭐⭐ | ✅ |
| [carla-rl](carla-rl/) | CARLA 模拟器集成 | Python, RL | ⭐⭐⭐⭐⭐ | ✅ |
| [slam-mapping](slam-mapping/) | SLAM 建图系统 | Python, OpenCV | ⭐⭐⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
感知系统 → 规划控制 → CARLA 模拟 → SLAM 建图
   ↓           ↓           ↓           ↓
 3D检测     路径规划     强化学习     视觉里程计
```

### 推荐学习顺序

1. **adas-perception** (感知系统)
   - 学习 LiDAR 点云处理
   - 理解 PointPillars 3D 检测
   - 掌握多传感器融合

2. **adas-planning** (规划控制)
   - 学习 A*、Dijkstra、RRT 路径规划
   - 理解 PID、MPC、Stanley 控制
   - 掌握轨迹生成

3. **carla-rl** (CARLA 模拟)
   - 学习 CARLA 模拟器集成
   - 理解强化学习在自动驾驶中的应用
   - 掌握 Gym 环境接口

4. **slam-mapping** (SLAM 建图)
   - 学习视觉里程计
   - 理解特征匹配和位姿估计
   - 掌握回环检测

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **Python** | 主语言 | [Python 官方文档](https://docs.python.org/3/) |
| **PyTorch** | 深度学习框架 | [PyTorch 官方文档](https://pytorch.org/docs/stable/) |
| **OpenCV** | 计算机视觉 | [OpenCV 官方文档](https://docs.opencv.org/) |
| **Open3D** | 点云处理 | [Open3D 官方文档](http://www.open3d.org/docs/) |
| **CARLA** | 自动驾驶模拟器 | [CARLA 官方文档](https://carla.readthedocs.io/) |
| **Stable-Baselines3** | 强化学习库 | [SB3 官方文档](https://stable-baselines3.readthedocs.io/) |

---

## 📊 项目详情

### 1. adas-perception (感知系统)

**核心功能**：
- LiDAR 点云处理（加载、过滤、降采样）
- PointPillars 3D 目标检测
- 多种骨干网络（ResNet18、VGG16、MobileNetV2）
- 可视化工具（点云、3D 框、BEV）

**代码量**：约 3000 行

**快速开始**：
```bash
cd adas-perception
pip install -r requirements.txt
python examples/demo.py
```

---

### 2. adas-planning (规划控制)

**核心功能**：
- 路径规划算法（A*、Dijkstra、RRT、Theta*）
- 控制算法（PID、MPC、Stanley、LQR）
- 车辆模型（PointMass、Bicycle、Kinematic、Dynamic）
- 轨迹生成和可视化

**代码量**：约 2500 行

**快速开始**：
```bash
cd adas-planning
pip install -r requirements.txt
python examples/simple_demo.py
```

---

### 3. carla-rl (CARLA 模拟)

**核心功能**：
- Gymnasium 环境接口
- Mock 环境（无需 CARLA 即可开发）
- PPO 训练代理
- 奖励工程（进度、速度、车道保持、碰撞）

**代码量**：约 4500 行

**快速开始**：
```bash
cd carla-rl
pip install -e .
python scripts/train.py --mock
```

---

### 4. slam-mapping (SLAM 建图)

**核心功能**：
- ORB 特征提取和匹配
- 视觉里程计（位姿估计）
- 关键帧和 3D 地图点管理
- 回环检测

**代码量**：约 3000 行

**快速开始**：
```bash
cd slam-mapping
pip install -r requirements.txt
python main.py demo --visualize
```

---

## 📚 学习资源

### 书籍
- 《自动驾驶系统设计》
- 《SLAM 十四讲》
- 《Probabilistic Robotics》

### 课程
- [Stanford CS231n](http://cs231n.stanford.edu/)
- [MIT 6.S094](http://selfdrivingcars.mit.edu/)

### 开源项目
- [Apollo](https://github.com/ApolloAuto/apollo)
- [Autoware](https://github.com/autowarefoundation/autoware)
- [OpenPCDet](https://github.com/open-mmlab/OpenPCDet)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)
