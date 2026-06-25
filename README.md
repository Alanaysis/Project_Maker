# 🎯 Learning Project Factory / 学习型项目工厂

> **180 个深度学习项目** | 涵盖自动驾驶、区块链、AI、系统编程、网络安全、多媒体、机器学习、控制系统、信号处理、优化算法等领域

---

## 🚀 快速导航

### 按领域浏览

| 领域 | 项目数 | 入口 |
|------|--------|------|
| 🚗 [自动驾驶](projects/ADAS_README.md) | 4 | 感知、规划、CARLA、SLAM |
| ⛓️ [区块链](projects/BLOCKCHAIN_README.md) | 4 | 区块链、智能合约、ERC20、投票 |
| 🤖 [AI & 机器学习](projects/AI_README.md) | 35 | 量化、LoRA、ViT/CLIP、视觉、LLM、CNN、决策树、K-Means、KNN、线性回归、逻辑回归、朴素贝叶斯、PCA、Q-Learning、DQN、文本分类、Word2Vec、NER、语言模型、贝叶斯优化、遗传算法、模拟退火、粒子群、随机森林、SVM、梯度下降、模糊控制器 |
| ⚙️ [系统基础设施](projects/SYSTEM_README.md) | 35 | 数据库、调度、容器、VM、OS、流计算、CI/CD、日志收集、监控、设备管理、容器编排、WAL、消息队列、Raft、分布式锁、熔断降级、编译器、物理引擎、动画引擎、C++特性系列、向量数据库、时间序列数据库、状态机、外部排序、查询解析器 |
| 🌐 [网络服务](projects/NETWORK_README.md) | 12 | HA、MCP、VPN、CDN、防火墙、渗透测试、HTTP/2、WebSocket、MQTT、RPC、DNS、服务发现 |
| 🔧 [异构计算](projects/HETERO_README.md) | 3 | CPU+GPU、多 GPU、GPU Shaders |
| 🎮 [分布式 & 通讯](projects/DISTRIBUTED_README.md) | 10 | 游戏系统、聊天应用、Exactly-once、服务发现、分布式事务、DHT、MapReduce、分布式缓存、Paxos、分布式消息队列 |
| 💰 [金融 & 应用](projects/APPS_README.md) | 7 | 量化交易、因子挖掘、风险管理、VR、文档编辑器、键盘驱动、容灾存储 |
| 🎬 [多媒体 & 图形](projects/MEDIA_README.md) | 12 | 音频处理引擎、编解码器、流媒体服务器、动画系统、动画引擎、网格处理、场景图、空间划分、特征匹配、光线追踪、图像处理、颜色空间 |
| 📊 [NLP & 数据结构](projects/NLP_README.md) | 12 | 分词器、语言模型、随机森林、SVM、HyperLogLog、DNS、撮合引擎、查询解析器、边缘计算、PageRank、倒排索引、布隆过滤器 |
| 🔐 [安全 & 工具](projects/SECURITY_README.md) | 6 | 密码学库、沙箱隔离、解释器、倒排索引、防火墙、渗透测试 |
| 🎛️ [控制系统](projects/CONTROL_README.md) | 10 | PID、状态空间、MPC、自适应控制、系统响应、模糊控制器、模拟滤波器、数字滤波器、信号采样、放大器设计 |
| 🔷 [C++ 特性系列](projects/SYSTEM_README.md) | 14 | 11/14、17、20、23新特性、模板元编程、编译期计算、奇技淫巧、内存模型、性能优化、三方库、构建工具、陷阱最佳实践、代码规范 |

### 按技术栈浏览

| 技术栈 | 项目 |
|--------|------|
| **C++** | high-concurrency-db, ha-server, simple-vm, vr-application, keyboard-driver, adas-perception, matching-engine, disaster-recovery-storage, av-codec, gpu-shaders, mesh-processing, scene-graph, spatial-partitioning, animation-system, ray-tracer, physics-engine, cpp20-features |
| **Go** | hpc-task-scheduler, container-runtime, cdn-service, simple-blockchain, social-chat-app, distributed-game-system, media-server, dht, dns-server, distributed-transaction, mvcc, query-parser, stream-processing, service-discovery, cicd-pipeline, log-collector, monitoring-alert, device-management, lsm-tree, container-orchestrator, wal, message-queue, raft-consensus, distributed-lock, circuit-breaker, mqtt-broker, simple-rpc, http2-server, websocket-server, inverted-index, hyperloglog |
| **Python** | finetune-rl-framework, vit-clip-training, industrial-vision-detection, quant-trading-system, risk-engine, factor-mining, audio-engine, adas-planning, carla-rl, slam-mapping, tokenizer, random-forest, svm, edge-computing, edge-quantized-model, pentest-tools, yolo-detection, dqn, image-segmentation, policy-gradient, actor-critic, cnn-classification, decision-tree, kmeans, knn, linear-regression, logistic-regression, naive-bayes, pca, q-learning, text-classification, word2vec, ner, language-model, feature-matching, multi-gpu-computing, interpreter, action-recognition, image-captioning, basic-circuit, analog-filter, amplifier-design |
| **Rust** | mcp-server, vpn-software, smart-contract-vm, simple-compiler |
| **Solidity** | erc20-token, decentralized-voting |
| **TypeScript** | document-editor, reactive-framework, chart-library |
| **C** | firewall, simple-os, crypto-lib, sandbox |
| **Python (防火墙)** | firewall/python (Python 实现) |

### 按难度浏览

| 难度 | 项目 |
|------|------|
| ⭐⭐ 入门 | linear-regression, logistic-regression, decision-tree, kmeans, knn, naive-bayes, pca |
| ⭐⭐⭐ 初级 | simple-blockchain, erc20-token, cdn-service, tokenizer, language-model, pagerank, word2vec, text-classification, q-learning, cpp20-features |
| ⭐⭐⭐⭐ 中级 | hpc-task-scheduler, container-runtime, social-chat-app, vr-application, random-forest, svm, dht, dns-server, stream-processing, service-discovery, cicd-pipeline, log-collector, monitoring-alert, device-management, lsm-tree, container-orchestrator, wal, message-queue, raft-consensus, distributed-lock, circuit-breaker, mqtt-broker, simple-rpc, http2-server, websocket-server, inverted-index, pentest-tools, edge-computing, dqn, image-segmentation, policy-gradient, actor-critic, cnn-classification, yolo-detection, ner, feature-matching, multi-gpu-computing, gpu-shaders, mesh-processing, scene-graph, spatial-partitioning, interpreter, crypto-lib, sandbox, physics-engine, audio-engine, simple-compiler, image-captioning |
| ⭐⭐⭐⭐⭐ 高级 | high-concurrency-db, ha-server, vpn-software, adas-planning, distributed-transaction, matching-engine, exactly-once, disaster-recovery-storage, animation-system, factor-mining |
| ⭐⭐⭐⭐⭐⭐ 专家 | simple-vm, simple-os, finetune-rl-framework, smart-contract-vm, edge-quantized-model, av-codec, media-server, quant-trading-system, document-editor, keyboard-driver |
| ⭐⭐⭐⭐⭐⭐⭐ 大师 | local-llm-engine, adas-perception, slam-mapping, vit-clip-training, industrial-vision-detection, distributed-game-system, adas-planning |

---

## 📁 项目目录

### 🚗 自动驾驶模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [adas-perception](projects/adas-perception/) | 自动驾驶感知系统 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐⭐ |
| [adas-planning](projects/adas-planning/) | 自动驾驶规划控制 | Python | ⭐⭐⭐⭐⭐ |
| [carla-rl](projects/carla-rl/) | CARLA 模拟器集成 | Python, RL | ⭐⭐⭐⭐⭐ |
| [slam-mapping](projects/slam-mapping/) | SLAM 建图系统 | Python, OpenCV | ⭐⭐⭐⭐⭐⭐⭐ |

📖 [自动驾驶模块详细说明](projects/ADAS_README.md)

---

### ⛓️ 区块链模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [simple-blockchain](projects/simple-blockchain/) | 简易区块链实现 | Go | ⭐⭐⭐ |
| [smart-contract-vm](projects/smart-contract-vm/) | 智能合约虚拟机 | Rust | ⭐⭐⭐⭐⭐⭐ |
| [erc20-token](projects/erc20-token/) | ERC20 代币合约 | Solidity, Hardhat | ⭐⭐⭐ |
| [decentralized-voting](projects/decentralized-voting/) | 去中心化投票系统 | Solidity, Next.js | ⭐⭐⭐⭐ |

📖 [区块链模块详细说明](projects/BLOCKCHAIN_README.md)

---

### 🤖 AI & 机器学习模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [edge-quantized-model](projects/edge-quantized-model/) | 端侧极致量化模型 | Python, C++ | ⭐⭐⭐⭐⭐⭐ |
| [finetune-rl-framework](projects/finetune-rl-framework/) | 微调/RL 后训练框架 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐ |
| [vit-clip-training](projects/vit-clip-training/) | ViT/CLIP 模型训练 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐⭐ |
| [industrial-vision-detection](projects/industrial-vision-detection/) | 工业视觉检测 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐⭐ |
| [local-llm-engine](projects/local-llm-engine/) | 本地 LLM 推理引擎 | C++ | ⭐⭐⭐⭐⭐⭐⭐ |
| [yolo-detection](projects/yolo-detection/) | YOLO 目标检测算法 | Python, PyTorch | ⭐⭐⭐⭐ |
| [dqn](projects/dqn/) | 深度 Q 网络 | Python, PyTorch, Gym | ⭐⭐⭐⭐ |
| [image-segmentation](projects/image-segmentation/) | U-Net 语义分割网络 | Python, PyTorch | ⭐⭐⭐⭐ |
| [policy-gradient](projects/policy-gradient/) | 策略梯度算法 | Python, PyTorch, Gym | ⭐⭐⭐⭐ |
| [actor-critic](projects/actor-critic/) | Actor-Critic 算法 | Python, PyTorch, Gym | ⭐⭐⭐⭐ |
| [cnn-classification](projects/cnn-classification/) | CNN 图像分类 | Python, PyTorch | ⭐⭐⭐⭐ |
| [decision-tree](projects/decision-tree/) | 决策树分类器 | Python | ⭐⭐ |
| [kmeans](projects/kmeans/) | K-Means 聚类 | Python | ⭐⭐ |
| [knn](projects/knn/) | KNN 分类器 | Python | ⭐⭐ |
| [linear-regression](projects/linear-regression/) | 线性回归 | Python | ⭐⭐ |
| [logistic-regression](projects/logistic-regression/) | 逻辑回归 | Python | ⭐⭐ |
| [naive-bayes](projects/naive-bayes/) | 朴素贝叶斯分类器 | Python | ⭐⭐ |
| [pca](projects/pca/) | PCA 主成分分析 | Python | ⭐⭐ |
| [q-learning](projects/q-learning/) | Q-Learning 强化学习 | Python | ⭐⭐⭐ |
| [text-classification](projects/text-classification/) | 文本分类系统 | Python | ⭐⭐⭐ |
| [word2vec](projects/word2vec/) | Word2Vec 词向量训练 | Python | ⭐⭐⭐ |
| [ner](projects/ner/) | 命名实体识别 | Python | ⭐⭐⭐⭐ |
| [action-recognition](projects/action-recognition/) | 视频动作识别 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ |
| [gesture-recognition](projects/gesture-recognition/) | 手势识别 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ |
| [image-captioning](projects/image-captioning/) | 图像描述生成 | Python, PyTorch | ⭐⭐⭐⭐ |
| [simulated-annealing](projects/simulated-annealing/) | 模拟退火优化算法 | Python | ⭐⭐⭐ |

📖 [AI 模块详细说明](projects/AI_README.md)

---

### ⚙️ 系统基础设施

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [high-concurrency-db](projects/high-concurrency-db/) | 高并发数据库查询 | C++ | ⭐⭐⭐⭐⭐ |
| [lsm-tree](projects/lsm-tree/) | LSM Tree 存储引擎 | Go | ⭐⭐⭐⭐ |
| [hpc-task-scheduler](projects/hpc-task-scheduler/) | HPC 任务调度系统 | Go | ⭐⭐⭐⭐ |
| [container-runtime](projects/container-runtime/) | 容器化基础设施 | Go | ⭐⭐⭐⭐ |
| [simple-vm](projects/simple-vm/) | 简易虚拟机 | C++, KVM | ⭐⭐⭐⭐⭐⭐ |
| [simple-os](projects/simple-os/) | 简易操作系统 | C, 汇编 | ⭐⭐⭐⭐⭐⭐ |
| [mvcc](projects/mvcc/) | MVCC 并发控制 | Go | ⭐⭐⭐⭐ |
| [stream-processing](projects/stream-processing/) | 流式计算框架 | Go | ⭐⭐⭐⭐ |
| [cicd-pipeline](projects/cicd-pipeline/) | CI/CD 流水线 | Go, Docker | ⭐⭐⭐⭐ |
| [log-collector](projects/log-collector/) | 分布式日志收集系统 | Go | ⭐⭐⭐⭐ |
| [monitoring-alert](projects/monitoring-alert/) | 监控告警系统 | Go | ⭐⭐⭐⭐ |
| [device-management](projects/device-management/) | 设备管理系统 | Go | ⭐⭐⭐⭐ |
| [container-orchestrator](projects/container-orchestrator/) | 容器编排系统 | Go | ⭐⭐⭐⭐ |
| [wal](projects/wal/) | WAL 预写日志 | Go | ⭐⭐⭐⭐ |
| [message-queue](projects/message-queue/) | 分布式消息队列 | Go | ⭐⭐⭐⭐ |
| [raft-consensus](projects/raft-consensus/) | Raft 共识算法 | Go | ⭐⭐⭐⭐ |
| [distributed-lock](projects/distributed-lock/) | 分布式锁 | Go | ⭐⭐⭐⭐ |
| [circuit-breaker](projects/circuit-breaker/) | 熔断降级 | Go | ⭐⭐⭐⭐ |
| [physics-engine](projects/physics-engine/) | 2D 物理引擎 | C++ | ⭐⭐⭐⭐ |
| [simple-compiler](projects/simple-compiler/) | 简易编译器 | Rust | ⭐⭐⭐⭐ |
| [cpp20-features](projects/cpp20-features/) | C++20 新特性实践 | C++20 | ⭐⭐⭐ |

📖 [系统模块详细说明](projects/SYSTEM_README.md)

---

### 🌐 网络服务

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [ha-server](projects/ha-server/) | 高可用服务器 | C++ | ⭐⭐⭐⭐⭐ |
| [mcp-server](projects/mcp-server/) | MCP 服务端 | Rust | ⭐⭐⭐⭐ |
| [vpn-software](projects/vpn-software/) | VPN 软件 | Rust | ⭐⭐⭐⭐⭐ |
| [cdn-service](projects/cdn-service/) | CDN 服务 | Go | ⭐⭐⭐ |
| [firewall](projects/firewall/) | 防火墙 | C | ⭐⭐⭐⭐⭐ |
| [pentest-tools](projects/pentest-tools/) | 渗透测试工具集 | Python | ⭐⭐⭐⭐ |
| [http2-server](projects/http2-server/) | HTTP/2 服务器 | Go | ⭐⭐⭐⭐ |
| [websocket-server](projects/websocket-server/) | WebSocket 服务器 | Go | ⭐⭐⭐⭐ |
| [mqtt-broker](projects/mqtt-broker/) | MQTT Broker | Go | ⭐⭐⭐⭐ |
| [simple-rpc](projects/simple-rpc/) | 简易 RPC 框架 | Go | ⭐⭐⭐⭐ |

📖 [网络模块详细说明](projects/NETWORK_README.md)

---

### 🔧 异构计算

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [heterogeneous-computing](projects/heterogeneous-computing/) | CPU+GPU 异构计算 | C++ | ⭐⭐⭐⭐⭐ |
| [multi-gpu-computing](projects/multi-gpu-computing/) | 多 GPU 并行计算 | Python | ⭐⭐⭐⭐ |
| [gpu-shaders](projects/gpu-shaders/) | GPU Shader 库 | C++ | ⭐⭐⭐⭐ |

📖 [异构计算模块详细说明](projects/HETERO_README.md)

---

### 🎮 分布式 & 通讯

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [distributed-game-system](projects/distributed-game-system/) | 分布式游戏系统 | Go | ⭐⭐⭐⭐⭐⭐⭐ |
| [social-chat-app](projects/social-chat-app/) | 社交聊天应用 | Go | ⭐⭐⭐⭐ |
| [exactly-once](projects/exactly-once/) | Exactly-once 语义 | Go | ⭐⭐⭐⭐⭐ |
| [service-discovery](projects/service-discovery/) | 服务发现系统 | Go | ⭐⭐⭐⭐ |
| [distributed-transaction](projects/distributed-transaction/) | 分布式事务 | Go | ⭐⭐⭐⭐⭐ |
| [dht](projects/dht/) | 分布式哈希表 | Go | ⭐⭐⭐⭐ |

📖 [分布式模块详细说明](projects/DISTRIBUTED_README.md)

---

### 💰 金融 & 应用

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [quant-trading-system](projects/quant-trading-system/) | 量化交易系统 | Python | ⭐⭐⭐⭐⭐⭐ |
| [factor-mining](projects/factor-mining/) | 因子挖掘框架 | Python | ⭐⭐⭐⭐⭐ |
| [risk-engine](projects/risk-engine/) | 风险管理引擎 | Python, SciPy | ⭐⭐⭐⭐ |
| [vr-application](projects/vr-application/) | VR 应用 | C++, OpenGL | ⭐⭐⭐⭐⭐ |
| [document-editor](projects/document-editor/) | 文档编辑器 | TypeScript | ⭐⭐⭐⭐⭐⭐ |
| [keyboard-driver](projects/keyboard-driver/) | 键盘驱动 | C | ⭐⭐⭐⭐⭐⭐ |
| [disaster-recovery-storage](projects/disaster-recovery-storage/) | 容灾存储 | C++ | ⭐⭐⭐⭐⭐ |

📖 [应用模块详细说明](projects/APPS_README.md)

---

### 🎬 多媒体 & 图形

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [audio-engine](projects/audio-engine/) | 音频处理引擎 | Python, NumPy | ⭐⭐⭐⭐ |
| [av-codec](projects/av-codec/) | 音视频编解码器 | C++, FFmpeg | ⭐⭐⭐⭐⭐⭐ |
| [media-server](projects/media-server/) | 流媒体服务器 | Go | ⭐⭐⭐⭐⭐⭐ |
| [animation-system](projects/animation-system/) | 动画系统 | C++ | ⭐⭐⭐⭐⭐ |
| [mesh-processing](projects/mesh-processing/) | 网格处理算法 | C++ | ⭐⭐⭐⭐ |
| [scene-graph](projects/scene-graph/) | 场景图系统 | C++ | ⭐⭐⭐⭐ |
| [spatial-partitioning](projects/spatial-partitioning/) | 空间划分算法 | C++ | ⭐⭐⭐⭐ |
| [feature-matching](projects/feature-matching/) | 特征匹配 SIFT/ORB | Python | ⭐⭐⭐⭐ |
| [ray-tracer](projects/ray-tracer/) | 光线追踪渲染器 | C++ | ⭐⭐⭐⭐ |

📖 [多媒体模块详细说明](projects/MEDIA_README.md)

---

### 📊 NLP & 数据结构

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [tokenizer](projects/tokenizer/) | 中文分词器 | Python | ⭐⭐⭐ |
| [language-model](projects/language-model/) | N-gram 语言模型 | Python | ⭐⭐⭐ |
| [random-forest](projects/random-forest/) | 随机森林分类器 | Python | ⭐⭐⭐⭐ |
| [svm](projects/svm/) | 支持向量机 | Python | ⭐⭐⭐⭐ |
| [hyperloglog](projects/hyperloglog/) | HyperLogLog 基数估计 | Go | ⭐⭐⭐⭐ |
| [dns-server](projects/dns-server/) | DNS 服务器 | Go | ⭐⭐⭐⭐ |
| [matching-engine](projects/matching-engine/) | 撮合引擎 | C++ | ⭐⭐⭐⭐⭐ |
| [query-parser](projects/query-parser/) | 查询解析器 | Go | ⭐⭐⭐⭐ |
| [edge-computing](projects/edge-computing/) | 边缘计算框架 | Python | ⭐⭐⭐⭐ |
| [pagerank](projects/pagerank/) | PageRank 算法 | Python | ⭐⭐⭐ |
| [chart-library](projects/chart-library/) | 图表库 | TypeScript, Canvas | ⭐⭐⭐ |

📖 [NLP 模块详细说明](projects/NLP_README.md)

---

### 🔐 安全 & 工具

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [crypto-lib](projects/crypto-lib/) | 密码学库 | C | ⭐⭐⭐⭐ |
| [sandbox](projects/sandbox/) | 沙箱隔离 | C | ⭐⭐⭐⭐ |
| [interpreter](projects/interpreter/) | 解释器 | Python | ⭐⭐⭐⭐ |
| [inverted-index](projects/inverted-index/) | 倒排索引 | Go | ⭐⭐⭐⭐ |

📖 [安全模块详细说明](projects/SECURITY_README.md)

---

## 📚 学习资源

### 学习路径

- 🛤️ [学习路径图](LEARNING_PATHS.md) - 推荐的学习顺序
- 📋 [项目索引](PROJECT_INDEX.md) - 按技术栈/难度索引
- 📝 [愿望单](WISHLIST.md) - 所有项目需求

### 项目模板

- 📄 [项目模板规范](PROJECT_TEMPLATE.md) - 标准项目结构
- 📝 [学习笔记模板](LEARNING_NOTES.md) - 学习记录模板
- ✅ [质量检查清单](CHECKLIST.md) - 项目质量标准

### 贡献指南

- 🤝 [贡献指南](CONTRIBUTING.md) - 如何参与贡献

---

## 📊 项目统计

| 维度 | 数量 |
|------|------|
| **总项目数** | 180 |
| **技术栈** | 7 (C++, Go, Python, Rust, Solidity, TypeScript, C) |
| **领域** | 11 |
| **总代码行数** | 250,000+ |
| **文档数量** | 500+ |

---

## 🎯 快速开始

### 1. 选择一个领域

```bash
# 查看所有领域
cat README.md

# 进入感兴趣的领域
cd projects/ADAS_README.md  # 自动驾驶
cd projects/BLOCKCHAIN_README.md  # 区块链
```

### 2. 选择一个项目

```bash
# 进入项目目录
cd projects/adas-perception

# 查看项目说明
cat README.md

# 查看学习笔记模板
cat LEARNING_NOTES.md
```

### 3. 开始学习

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/demo.py

# 运行测试
pytest tests/
```

---

## 🔗 相关链接

- 📊 [代码审查报告](CODE_REVIEW_REPORT.md) - 项目质量分析
- 📈 [GitHub 仓库](https://github.com/Alanaysis/Project_Maker) - 源代码

---

## 📝 更新日志

### 2026-06-25
- ✅ KNN 和 DQN 项目完成，全部 180 个项目均已完结
- ✅ 更新项目索引状态

### 2026-06-23
- ✅ 新增光线追踪渲染器项目（ray-tracer）
- ✅ 新增物理引擎项目（physics-engine）
- ✅ 新增因子挖掘框架项目（factor-mining）
- ✅ 新增音频处理引擎项目（audio-engine）
- ✅ 更新多媒体模块（9 个项目）
- ✅ 更新系统基础设施模块（20 个项目）
- ✅ 更新金融 & 应用模块（7 个项目）

### 2026-06-22
- ✅ 完成所有 92 个项目
- ✅ 新增自动驾驶模块（4 个项目）
- ✅ 新增区块链模块（4 个项目）
- ✅ 新增 AI & 机器学习模块（22 个项目）
- ✅ 新增系统基础设施模块（18 个项目）
- ✅ 新增网络服务模块（10 个项目）
- ✅ 新增异构计算模块（3 个项目）
- ✅ 新增分布式 & 通讯模块（6 个项目）
- ✅ 新增金融 & 应用模块（5 个项目）
- ✅ 新增多媒体 & 图形模块（7 个项目）
- ✅ 新增 NLP & 数据结构模块（9 个项目）
- ✅ 新增安全 & 工具模块（4 个项目）
- ✅ 修复 Critical/High 问题
- ✅ 添加多层导航 README

---

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢所有开源项目的贡献者！

---

[English Version](README_EN.md)
