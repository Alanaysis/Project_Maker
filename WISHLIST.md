# 📝 愿望单 / Wishlist

[English](#english) | [中文](#中文)

---

## 中文

### 如何使用

1. **添加新愿望**：按照下面的模板格式添加
2. **等待实现**：AI 子代理会按照优先级依次实现
3. **查看进度**：状态会更新为 ✅ 已完成

### 愿望单模板

```markdown
### [项目名称]

**一句话描述**：用一句话说明这个项目是什么

**学习目标**：
- 目标1：理解 XXX
- 目标2：掌握 XXX
- 目标3：学会 XXX

**技术栈**：
- 主语言：Python/JS/Go/...
- 框架：...
- 其他：...

**核心循环**：
```
输入 → 处理 → 输出
```

**参考项目**：
- [项目A](...)
- [项目B](...)

**优先级**：P0/P1/P2
- P0：核心基础，必须优先
- P1：重要扩展，其次实现
- P2：高级进阶，最后实现

**预估时长**：X 小时
```

---

## 愿望列表

### 🗄️ 分布式存储

### [多人共用网盘]

**一句话描述**：实现一个支持多用户、文件同步、权限管理的网盘系统

**学习目标**：
- 目标1：理解分布式文件存储原理
- 目标2：掌握文件同步和冲突解决机制
- 目标3：学会权限管理和访问控制

**技术栈**：
- 主语言：C++ / Rust（待调研）
- 框架：无（从零实现）
- 其他：FUSE（文件系统）、LevelDB/RocksDB（存储）

**核心循环**：
```
用户上传 → 文件分块 → 存储 → 元数据更新 → 同步通知 → 其他客户端拉取
```

**参考项目**：
- [Nextcloud](https://github.com/nextcloud/server)
- [Seafile](https://github.com/haiwen/seafile)
- [MinIO](https://github.com/minio/minio)

**优先级**：P1

**预估时长**：8 小时

**最小可用版本**：
- 单机部署
- 支持文件上传/下载
- 基本用户认证
- 简单的目录管理

---

### 🗃️ 数据库内核

### [高并发数据库查询]

**一句话描述**：实现一个支持高并发查询的数据库引擎，包含索引、缓存、并发控制

**学习目标**：
- 目标1：理解 B+ 树索引原理
- 目标2：掌握查询优化和执行计划
- 目标3：学会并发控制和事务管理

**技术栈**：
- 主语言：C / C++（待调研）
- 框架：无（从零实现）
- 其他：无

**核心循环**：
```
SQL 输入 → 词法分析 → 语法分析 → 查询优化 → 执行计划 → 存储引擎 → 结果返回
```

**参考项目**：
- [SQLite](https://github.com/nicedoc/sqlite)
- [LevelDB](https://github.com/google/leveldb)
- [RocksDB](https://github.com/facebook/rocksdb)
- [TiDB](https://github.com/pingcap/tidb)

**优先级**：P0

**预估时长**：10 小时

**最小可用版本**：
- 支持基本 SQL（SELECT、INSERT、UPDATE、DELETE）
- B+ 树索引
- 简单的查询优化
- 基本的并发控制（读写锁）

---

### 🤖 AI 部署

### [端侧极致量化模型（车载）]

**一句话描述**：实现一个极致量化的模型部署框架，支持 INT8/INT4 量化，优化车载场景推理

**学习目标**：
- 目标1：理解模型量化原理（INT8、INT4、混合精度）
- 目标2：掌握推理优化技术（算子融合、内存优化）
- 目标3：学会边缘设备部署和性能调优

**技术栈**：
- 主语言：C++（推理）、Python（训练）
- 框架：PyTorch（训练）、ONNX（中间表示）
- 其他：TensorRT / OpenVINO（推理优化）

**核心循环**：
```
浮点模型 → 量化校准 → 量化模型 → 算子融合 → 引擎构建 → 边缘推理
```

**参考项目**：
- [TensorRT](https://github.com/NVIDIA/TensorRT)
- [ONNX Runtime](https://github.com/microsoft/onnxruntime)
- [NCNN](https://github.com/Tencent/ncnn)
- [MNN](https://github.com/alibaba/MNN)

**优先级**：P0

**预估时长**：10 小时

**最小可用版本**：
- 支持 INT8 量化
- 基本算子融合
- 简单的推理 benchmark
- 车载场景 demo（目标检测）

---

### 🧠 AI 训练

### [微调/RL 后训练框架]

**一句话描述**：实现一个支持 LoRA 微调和 PPO 强化学习的大模型后训练框架

**学习目标**：
- 目标1：理解 LoRA 低秩适配原理
- 目标2：掌握 PPO 强化学习算法
- 目标3：学会分布式训练和梯度同步

**技术栈**：
- 主语言：Python
- 框架：PyTorch
- 其他：Transformers、DeepSpeed（可选）

**核心循环**：
```
基础模型 → LoRA 适配 → 前向传播 → 损失计算 → 反向传播 → 参数更新 → 评估
```

**RL 流程**：
```
提示词 → 模型生成 → 奖励模型评分 → PPO 优化 → 策略更新
```

**参考项目**：
- [PEFT](https://github.com/huggingface/peft)
- [TRL](https://github.com/huggingface/trl)
- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
- [DeepSpeed-Chat](https://github.com/microsoft/DeepSpeedExamples)

**优先级**：P0

**预估时长**：10 小时

**最小可用版本**：
- LoRA 微调功能
- 简单的 PPO 训练循环
- 基本的评估指标
- 单机多卡支持

---

### 🎮 分布式系统

### [分布式游戏系统]

**一句话描述**：实现一个支持多玩家实时对战的分布式游戏服务器

**学习目标**：
- 目标1：理解分布式状态同步原理
- 目标2：掌握网络延迟优化技术
- 目标3：学会一致性哈希和负载均衡

**技术栈**：
- 主语言：C++ / Go（待调研）
- 框架：无（从零实现）
- 其他：Protobuf（序列化）、UDP/TCP（网络）

**核心循环**：
```
玩家输入 → 客户端预测 → 服务器验证 → 状态同步 → 客户端校正
```

**参考项目**：
- [Agones](https://github.com/googleforgames/agones)
- [Nakama](https://github.com/heroiclabs/nakama)
- [Skynet](https://github.com/cloudwu/skynet)

**优先级**：P1

**预估时长**：10 小时

**最小可用版本**：
- 支持 100 人同时在线
- 基本状态同步
- 简单的游戏逻辑（移动、攻击）
- 延迟优化（客户端预测）

---

### ⚙️ 高性能计算

### [HPC 任务调度系统]

**一句话描述**：实现一个高性能计算任务调度系统，支持任务提交、资源分配、作业隔离

**学习目标**：
- 目标1：理解任务调度算法（FIFO、优先级、公平调度）
- 目标2：掌握资源管理和隔离技术
- 目标3：学会容错和任务重试机制

**技术栈**：
- 主语言：C / C++ / Go（待调研）
- 框架：无（从零实现）
- 其他：cgroups（资源隔离）、Docker（容器化）

**核心循环**：
```
任务提交 → 资源评估 → 调度决策 → 任务分配 → 执行监控 → 结果收集
```

**参考项目**：
- [Slurm](https://github.com/SchedMD/slurm)
- [Kubernetes](https://github.com/kubernetes/kubernetes)
- [Apache Mesos](https://github.com/apache/mesos)
- [HTCondor](https://github.com/htcondor/htcondor)

**优先级**：P0

**预估时长**：10 小时

**最小可用版本**：
- 支持任务提交和查询
- 简单的 FIFO 调度
- 基本的资源管理（CPU、内存）
- 任务状态监控

---

### 💬 即时通讯

### [社交聊天软件]

**一句话描述**：实现一个支持实时消息、群聊、文件传输的社交聊天系统

**学习目标**：
- 目标1：理解即时通讯架构（长连接、消息队列）
- 目标2：掌握消息推送和离线存储
- 目标3：学会端到端加密

**技术栈**：
- 主语言：Go / C++（待调研）
- 框架：无（从零实现）
- 其他：WebSocket、Protobuf、Redis（消息队列）

**核心循环**：
```
用户发送 → 服务器接收 → 消息存储 → 推送通知 → 接收方拉取 → 消息展示
```

**参考项目**：
- [Matrix](https://github.com/matrix-org)
- [Rocket.Chat](https://github.com/RocketChat/Rocket.Chat)
- [Signal Server](https://github.com/signalapp/Signal-Server)
- [Tinode](https://github.com/tinode)

**优先级**：P1

**预估时长**：8 小时

**最小可用版本**：
- 支持单聊
- 基本消息推送
- 离线消息存储
- 简单的用户管理

---

### 🥽 图形学

### [VR 应用]

**一句话描述**：实现一个基本的 VR 应用，支持 3D 渲染、头部追踪、手柄交互

**学习目标**：
- 目标1：理解 3D 渲染管线
- 目标2：掌握 VR 立体渲染原理
- 目标3：学会交互设计和性能优化

**技术栈**：
- 主语言：C++ / C#（待调研）
- 框架：Unity / Unreal（待调研）
- 其他：OpenXR、OpenGL/Vulkan

**核心循环**：
```
用户输入 → 场景更新 → 物理模拟 → 渲染 → 后处理 → VR 输出
```

**参考项目**：
- [OpenXR SDK](https://github.com/KhronosGroup/OpenXR-SDK)
- [Godot VR](https://github.com/godotengine/godot)
- [Three.js VR](https://github.com/mrdoob/three.js)

**优先级**：P2

**预估时长**：8 小时

**最小可用版本**：
- 基本 3D 场景渲染
- 头部追踪
- 简单的交互（抓取、点击）
- 60fps 流畅运行

---

## 项目依赖关系

```
基础层
├── 高并发数据库查询（P0）──→ 所有需要存储的项目
└── HPC 任务调度系统（P0）──→ 分布式游戏系统、AI 训练

应用层
├── 端侧极致量化模型（P0）──→ 车载场景
├── 微调/RL 后训练框架（P0）──→ AI 应用
├── 多人共用网盘（P1）──→ 文件共享
├── 分布式游戏系统（P1）──→ 游戏场景
├── 社交聊天软件（P1）──→ 通讯场景
└── VR 应用（P2）──→ 图形学
```

## 建议实现顺序

1. **第一阶段（基础）**：高并发数据库查询、HPC 任务调度系统
2. **第二阶段（核心）**：端侧极致量化模型、微调/RL 后训练框架
3. **第三阶段（应用）**：多人共用网盘、分布式游戏系统、社交聊天软件
4. **第四阶段（进阶）**：VR 应用

---

## English

### How to Use

1. **Add New Wish**: Follow the template format below
2. **Wait for Implementation**: AI sub-agents will implement by priority
3. **Check Progress**: Status will be updated to ✅ Completed

### Wishlist Template

```markdown
### [Project Name]

**One-line Description**: Describe this project in one sentence

**Learning Goals**:
- Goal 1: Understand XXX
- Goal 2: Master XXX
- Goal 3: Learn XXX

**Tech Stack**:
- Main Language: Python/JS/Go/...
- Framework: ...
- Others: ...

**Core Loop**:
```
Input → Process → Output
```

**Reference Projects**:
- [Project A](...)
- [Project B](...)

**Priority**: P0/P1/P2

**Estimated Time**: X hours
```

---

## Wish List

(See Chinese section above for the full list of wishes)
