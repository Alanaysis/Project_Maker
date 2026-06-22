# 💰 金融 & 应用模块

> 5 个深度学习项目，涵盖量化交易、VR、文档编辑器、键盘驱动、容灾存储

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [quant-trading-system](quant-trading-system/) | 量化交易系统 | Python | ⭐⭐⭐⭐⭐ | ✅ |
| [vr-application](vr-application/) | VR 应用 | C++, OpenGL | ⭐⭐⭐⭐⭐ | ✅ |
| [document-editor](document-editor/) | 文档编辑器 | TypeScript | ⭐⭐⭐⭐ | ✅ |
| [keyboard-driver](keyboard-driver/) | 键盘驱动 | C | ⭐⭐⭐⭐⭐ | ✅ |
| [disaster-recovery-storage](disaster-recovery-storage/) | 容灾存储 | C++ | ⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
量化交易 → VR 应用 → 文档编辑器 → 键盘驱动 → 容灾存储
    ↓          ↓          ↓           ↓           ↓
 策略回测    3D渲染     CRDT算法    中断处理     纠删码
 订单管理    交互系统   协同编辑    去抖算法     故障检测
 风险控制    场景管理   版本控制    矩阵扫描     数据冗余
```

### 推荐学习顺序

1. **quant-trading-system** (量化交易)
   - 学习量化交易策略
   - 理解回测框架设计
   - 掌握风险管理和订单管理

2. **vr-application** (VR 应用)
   - 学习 3D 渲染管线
   - 理解 VR 立体渲染原理
   - 掌握交互设计和性能优化

3. **document-editor** (文档编辑器)
   - 学习 CRDT 算法
   - 理解协同编辑原理
   - 掌握版本控制

4. **keyboard-driver** (键盘驱动)
   - 学习键盘硬件原理
   - 理解中断处理和 DMA
   - 掌握按键去抖和优化

5. **disaster-recovery-storage** (容灾存储)
   - 学习纠删码原理
   - 理解分布式存储
   - 掌握故障检测和恢复

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **Python** | 量化交易 | [Python 官方文档](https://docs.python.org/3/) |
| **C++** | VR、容灾存储 | [C++ 官方文档](https://en.cppreference.com/) |
| **TypeScript** | 文档编辑器 | [TypeScript 文档](https://www.typescriptlang.org/docs/) |
| **C** | 键盘驱动 | [C 官方文档](https://en.cppreference.com/w/c) |
| **OpenGL** | 3D 渲染 | [OpenGL 文档](https://www.opengl.org/sdk/docs/) |

---

## 📊 项目详情

### 1. quant-trading-system (量化交易)

**核心功能**：
- 事件系统（事件驱动架构、事件总线）
- 回测引擎（协调所有模块执行回测）
- 投资组合管理（持仓、资金、盈亏）
- 策略模块（均线策略、动量策略）
- 风险管理（5 种内置风险规则）

**代码量**：约 30 个文件

**快速开始**：
```bash
cd quant-trading-system
pip install -r requirements.txt
python examples/run_backtest.py
```

---

### 2. vr-application (VR 应用)

**核心功能**：
- 3D 渲染系统（OpenGL 4.5、Phong 光照、纹理映射）
- VR 立体渲染（双眼视图、畸变校正、OpenXR 集成）
- 头部追踪（6DoF、桌面模式鼠标控制）
- 交互系统（射线检测、碰撞体、抓取/释放）

**代码量**：约 39 个文件

**快速开始**：
```bash
cd vr-application
mkdir build && cd build
cmake ..
make
./vr_application
```

---

### 3. document-editor (文档编辑器)

**核心功能**：
- CRDT 文档（RGA 算法、无冲突文本存储）
- 富文本格式化（加粗、斜体、下划线、删除线、代码）
- 版本历史（快照、提交、标签、差异、回滚）
- 协同编辑管理器（广播模式、对等节点管理）

**代码量**：约 20 个文件

**快速开始**：
```bash
cd document-editor
npm install
npm test
npm run example:basic
```

---

### 4. keyboard-driver (键盘驱动)

**核心功能**：
- 矩阵扫描模块（6x14 矩阵键盘扫描）
- 中断处理模块（中断初始化、服务程序）
- 去抖模块（3 种算法：定时器、计数器、状态机）
- 输入事件模块（事件队列、处理器注册、事件分发）

**代码量**：约 22 个文件

**快速开始**：
```bash
cd keyboard-driver
make
./keyboard_demo
```

---

### 5. disaster-recovery-storage (容灾存储)

**核心功能**：
- 纠删码编解码（Reed-Solomon、GF(2^8)）
- 数据分片与重组
- 多副本管理（NWR Quorum 机制）
- 故障检测与恢复（心跳检测、Phi Accrual Failure Detector）

**代码量**：约 30 个文件

**快速开始**：
```bash
cd disaster-recovery-storage
./build.sh
```

---

## 📚 学习资源

### 书籍
- 《量化投资》
- 《VR 开发》
- 《操作系统设计》

### 课程
- [Quantopian](https://www.quantopian.com/)
- [Unity Learn](https://learn.unity.com/)

### 开源项目
- [vnpy](https://github.com/vnpy/vnpy)
- [OpenXR](https://github.com/KhronosGroup/OpenXR-SDK)
- [Monaco Editor](https://github.com/microsoft/monaco-editor)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)
