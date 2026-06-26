# 🎯 Learning Project Factory / 学习型项目工厂

> **225 个学习项目** | 涵盖自动驾驶、区块链、AI、系统编程、控制系统、网络安全、多媒体、机器学习、异构计算、机械工程、嵌入式、指令集、移动端等领域

---

## 🚀 快速导航

### 按领域浏览

| 领域 | 项目数 | 入口 |
|------|--------|------|
| 🚗 [自动驾驶](projects/ADAS_README.md) | 4 | 感知、规划、CARLA、SLAM |
| ⛓️ [区块链](projects/BLOCKCHAIN_README.md) | 4 | 区块链、智能合约、ERC20、投票 |
| 🤖 [AI & 深度学习](projects/AI_README.md) | 31 | ViT/CLIP、量化、LoRA、YOLO、GAN、DQN、强化学习、CLIP、扩散模型、目标检测、语义分割、姿态估计、超分辨率、风格迁移、点云、动作识别、手势识别、文字检测、图像描述、视觉问答、NERF、DETR、Swin Transformer、对比学习、工业视觉、本地LLM推理 |
| 🧮 [机器学习算法](projects/NLP_README.md) | 20 | 线性回归、逻辑回归、决策树、K-Means、KNN、朴素贝叶斯、PCA、随机森林、SVM、梯度下降、贝叶斯优化、遗传算法、模拟退火、粒子群、线性规划、凸优化 |
| ⚙️ [系统基础设施](projects/SYSTEM_README.md) | 48 | 数据库、存储引擎、调度、容器、VM、OS、流计算、CI/CD、日志收集、监控、设备管理、容器编排、WAL、消息队列、Raft、分布式锁、MVCC、向量数据库、时间序列数据库、状态机、外部排序、查询解析器、编译器、响应式框架、流媒体服务器、物理引擎、物理模拟引擎、栅格化引擎、图层合成引擎、3D建模引擎、贝塞尔引擎、SVG渲染器、约束求解器 |
| 🌐 [网络服务](projects/NETWORK_README.md) | 12 | HA、MCP、VPN、CDN、防火墙、渗透测试、HTTP/2、WebSocket、MQTT、RPC、DNS、服务发现 |
| 🔧 [异构计算](projects/HETERO_README.md) | 3 | CPU+GPU、多 GPU、GPU Shader |
| 🎮 [分布式 & 通讯](projects/DISTRIBUTED_README.md) | 6 | 游戏系统、聊天应用、Exactly-once、服务发现、分布式事务、DHT |
| 💰 [金融 & 量化](projects/APPS_README.md) | 6 | 量化交易、因子挖掘、风险管理、高频交易、撮合引擎、容灾存储 |
| 🎬 [多媒体 & 图形](projects/MEDIA_README.md) | 17 | 音频引擎、音视频编解码、流媒体服务器、光线追踪、物理引擎、3D物理模拟、网格处理、场景图、空间划分、特征匹配、图像去噪、图像修复、图像超分、图像识别、OCR、表格识别、点云、视频理解、动作识别、手势识别、风格迁移、深度估计、颜色空间引擎 |
| 📊 [NLP & 数据结构](projects/NLP_README.md) | 14 | 分词器、语言模型、Word2Vec、文本分类、随机森林、SVM、HyperLogLog、倒排索引、布隆过滤器、PageRank、查询解析器、撮合引擎、边缘计算、DNS服务器 |
| 🔐 [安全 & 工具](projects/SECURITY_README.md) | 6 | 密码学库、沙箱隔离、解释器、RISC-V模拟器、代码编辑器、表单引擎 |
| 🎛️ [控制系统](projects/CONTROL_README.md) | 6 | PID、状态空间、MPC、自适应控制、模糊控制器、系统响应 |
| 🔷 [C++ 特性系列](projects/SYSTEM_README.md) | 14 | 11/14、17、20、23新特性、模板元编程、编译期计算、奇技淫巧、内存模型、性能优化、三方库、构建工具、陷阱最佳实践、代码规范 |
| 📷 [计算机视觉](projects/AI_README.md) | 22 | YOLO、ViT、CLIP、语义分割、姿态估计、超分辨率、风格迁移、点云、动作识别、手势识别、文字检测、图像描述、工业视觉检测、本地LLM推理、扩散模型、DETR、Swin Transformer、NERF、OCR、表格识别、图像去噪、图像修复、深度估计、视频理解、特征匹配、视频理解 |
| ⚙️ [机械工程](projects/MECHANICAL_README.md) | 10 | 机械臂运动学、齿轮传动、凸轮机构、连杆机构、振动分析、热力学模拟、流体力学、CAD内核、有限元分析、3D打印切片 |
| 🔌 [嵌入式系统](projects/EMBEDDED_README.md) | 11 | RTOS内核、设备驱动、通信协议栈、传感器融合、嵌入式GUI、OTA升级、低功耗设计、嵌入式文件系统、嵌入式网络栈、嵌入式安全、边缘推理引擎 |
| 🖥️ [指令集架构](projects/ISA_README.md) | 4 | RISC-V模拟器、ARM模拟器、x86模拟器、指令集对比分析 |
| 📱 [移动端开发](projects/MOBILE_README.md) | 4 | iOS应用、Android应用、鸿蒙应用、跨平台框架原理 |
| ⚡ [数字/模拟电路](projects/CIRCUITS_README.md) | 8 | 逻辑门、组合逻辑、时序逻辑、简易CPU、基本电路、放大器设计、模拟滤波器、ADC/DAC、Verilog模拟器、芯片布局布线、时序分析 |

### 按技术栈浏览

| 技术栈 | 项目 |
|--------|------|
| **C++** | high-concurrency-db, ha-server, simple-vm, adas-perception, matching-engine, disaster-recovery-storage, av-codec, gpu-shader-library, mesh-processing, scene-graph, spatial-partitioning, animation-system, ray-tracer, physics-engine, physics-simulation-engine, streaming-server, cpp20-features, cpp17-features, cpp11-14-features, cpp23-features, cpp-template-metaprogramming, cpp-template-metaprogramming-advanced, cpp-compile-time-computation, cpp-memory-model-concurrency, cpp-performance-optimization, cpp-tricks-and-tips, cpp-pitfalls-best-practices, cpp-third-party-libraries, cpp-build-system-toolchain, cpp-coding-standards, dns-server, riscv-simulator, 3d-modeling-engine, bezier-engine, svg-renderer, rasterization-engine, layer-compositing-engine, code-editor |
| **Go** | hpc-task-scheduler, container-runtime, cdn-service, simple-blockchain, social-chat-app, distributed-game-system, media-server, dht, dns-server, distributed-transaction, mvcc, query-parser, stream-processing, service-discovery, cicd-pipeline, log-collector, monitoring-alert, device-management, lsm-tree, container-orchestrator, wal, message-queue, raft-consensus, distributed-lock, circuit-breaker, mqtt-broker, simple-rpc, http2-server, websocket-server, inverted-index, hyperloglog, distributed-cache, mapreduce, paxos, high-throughput-message-queue, constraint-solver, constraint-solver-py, form-engine, time-series-db, vector-db, state-machine, external-sort |
| **Python** | edge-quantized-model, vit-clip-training, industrial-vision-detection, quant-trading-system, risk-engine, factor-mining, audio-engine, adas-planning, carla-rl, slam-mapping, tokenizer, random-forest, svm, edge-computing, edge-quantized-model, dqn, image-segmentation, policy-gradient, actor-critic, cnn-classification, decision-tree, kmeans, knn, linear-regression, logistic-regression, naive-bayes, pca, q-learning, text-classification, word2vec, ner, language-model, feature-matching, multi-gpu-computing, interpreter, action-recognition, image-captioning, basic-circuit, analog-filter, amplifier-design, gan, pose-estimation, super-resolution, style-transfer, point-cloud, gesture-recognition, text-detection, genetic-algorithm, gradient-descent, simulated-annealing, particle-swarm, bayesian-optimization, linear-programming, diffusion-model, detr, swin-transformer, nerf, ocr, table-recognition, depth-estimation, image-denoising, image-inpainting, video-understanding, face-recognition, object-tracking, visual-qa, color-space-engine, fourier-transform, digital-filter, signal-sampling, system-response, pid-controller, state-space, adaptive-controller, fuzzy-controller, mpc-controller, state-machine, convex-optimization, streaming-algorithm, chart-library, virtual-scroll, drag-drop, reactive-framework, timeline-engine, clip, vit, yolo-detection, hft-engine |
| **Rust** | mcp-server, vpn-software, smart-contract-vm, simple-compiler |
| **Solidity** | erc20-token, decentralized-voting |
| **TypeScript** | document-editor, reactive-framework, chart-library, timeline-engine, virtual-scroll, drag-drop |
| **C** | firewall, simple-os, crypto-lib, sandbox |

### 按难度浏览

| 难度 | 项目 |
|------|------|
| ⭐⭐ 入门 | linear-regression, logistic-regression, decision-tree, kmeans, knn, naive-bayes, pca, pid-controller, tokenizer, language-model, pagerank, basic-circuit, logic-gates, state-machine |
| ⭐⭐⭐ 初级 | simple-blockchain, erc20-token, cdn-service, language-model, word2vec, text-classification, q-learning, cpp20-features, cpp17-features, cpp11-14-features, cpp23-features, genetic-algorithm, gradient-descent, simulated-annealing, particle-swarm, digital-filter, signal-sampling, analog-filter, amplifier-design, adaptive-controller, fuzzy-controller, decentralized-voting, bayesian-optimization, clip, vit, hyperloglog, inverted-index, bloom-filter, constraint-solver-py, external-sort, chart-library, face-recognition, fourier-transform |
| ⭐⭐⭐⭐ 中级 | hpc-task-scheduler, container-runtime, social-chat-app, random-forest, svm, dht, dns-server, stream-processing, service-discovery, cicd-pipeline, log-collector, monitoring-alert, device-management, lsm-tree, container-orchestrator, wal, message-queue, raft-consensus, distributed-lock, circuit-breaker, mqtt-broker, simple-rpc, http2-server, websocket-server, inverted-index, edge-computing, dqn, image-segmentation, policy-gradient, actor-critic, cnn-classification, yolo-detection, ner, feature-matching, multi-gpu-computing, gpu-sher-library, mesh-processing, scene-graph, spatial-partitioning, interpreter, physics-engine, audio-engine, simple-compiler, image-captioning, gan, pose-estimation, super-resolution, style-transfer, point-cloud, gesture-recognition, text-detection, diffusion-model, detr, swin-transformer, ocr, table-recognition, depth-estimation, image-denoising, image-inpainting, video-understanding, visual-qa, color-space-engine, svg-renderer, bezier-engine, 3d-modeling-engine, rasterization-engine, layer-compositing-engine, time-series-db, vector-db, mvcc, query-parser, distributed-cache, mapreduce, paxos, high-throughput-message-queue, constraint-solver, form-engine, code-editor, reactive-framework, timeline-engine, virtual-scroll, drag-drop, state-space, mpc-controller, system-response, convex-optimization, streaming-algorithm, nerf, face-recognition, object-tracking, gesture-recognition, hft-engine, adas-planning, carla-rl |
| ⭐⭐⭐⭐⭐ 高级 | high-concurrency-db, ha-server, adas-planning, distributed-transaction, matching-engine, exactly-once, disaster-recovery-storage, animation-system, factor-mining, edge-quantized-model, finetune-rl-framework, industrial-vision-detection, cpp-template-metaprogramming, cpp-memory-model-concurrency, cpp-performance-optimization, cpp-tricks-and-tips, cpp-pitfalls-best-practices, streaming-server, container-runtime, simple-os, simple-vm, cicd-pipeline, log-collector, monitoring-alert, device-management, container-orchestrator, wal, message-queue, raft-consensus, distributed-lock, circuit-breaker, mqtt-broker, http2-server, websocket-server, pentest-tools, yolo-detection, image-segmentation, policy-gradient, actor-critic, gan, pose-estimation, super-resolution, style-transfer, point-cloud, action-recognition, text-detection, image-captioning, linear-programming, local-llm-engine, vit-clip-training, quant-trading-system, risk-engine, vpn-software, smart-contract-vm, adas-perception, distributed-game-system, high-throughput-message-queue, mapreduce, paxos, lsm-tree, lsm-tree, hpc-task-scheduler, lsm-tree, lsm-tree |
| ⭐⭐⭐⭐⭐⭐ 专家 | simple-vm, simple-os, finetune-rl-framework, smart-contract-vm, av-codec, media-server, quant-trading-system, document-editor, keyboard-driver, edge-computing, physics-simulation-engine, 3d-modeling-engine, code-editor |
| ⭐⭐⭐⭐⭐⭐⭐ 大师 | adas-perception, slam-mapping, vit-clip-training, industrial-vision-detection, distributed-game-system, local-llm-engine |

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

### 🤖 AI & 深度学习模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [edge-quantized-model](projects/edge-quantized-model/) | 端侧极致量化模型 | Python, C++ | ⭐⭐⭐⭐⭐⭐ |
| [finetune-rl-framework](projects/finetune-rl-framework/) | 微调/RL 后训练框架 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐ |
| [vit-clip-training](projects/vit-clip-training/) | ViT/CLIP 模型训练 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐⭐ |
| [industrial-vision-detection](projects/industrial-vision-detection/) | 工业视觉检测 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐⭐ |
| [local-llm-engine](projects/local-llm-engine/) | 本地 LLM 推理引擎 | C++ | ⭐⭐⭐⭐⭐⭐⭐ |
| [yolo-detection](projects/yolo-detection/) | YOLO 目标检测算法 | Python, PyTorch | ⭐⭐⭐⭐ |
| [clip](projects/clip/) | CLIP 对比学习模型 | Python, PyTorch | ⭐⭐⭐⭐ |
| [vit](projects/vit/) | Vision Transformer 图像分类 | Python, PyTorch | ⭐⭐⭐⭐ |
| [detr](projects/detr/) | DETR 目标检测模型 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [swin-transformer](projects/swin-transformer/) | Swin Transformer 视觉模型 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [diffusion-model](projects/diffusion-model/) | 扩散模型生成 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [nerf](projects/nerf/) | NERF 神经辐射场 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐ |
| [dqn](projects/dqn/) | 深度 Q 网络 | Python, PyTorch, Gym | ⭐⭐⭐⭐ |
| [image-segmentation](projects/image-segmentation/) | U-Net 语义分割网络 | Python, PyTorch | ⭐⭐⭐⭐ |
| [pose-estimation](projects/pose-estimation/) | 人体姿态估计 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ |
| [super-resolution](projects/super-resolution/) | 图像超分辨率 | Python, PyTorch | ⭐⭐⭐⭐ |
| [style-transfer](projects/style-transfer/) | 神经风格迁移 | Python, PyTorch | ⭐⭐⭐⭐ |
| [gan](projects/gan/) | GAN 生成对抗网络 | Python, PyTorch | ⭐⭐⭐⭐ |
| [point-cloud](projects/point-cloud/) | 3D 点云处理 (PointNet) | Python, PyTorch | ⭐⭐⭐⭐ |
| [action-recognition](projects/action-recognition/) | 视频动作识别 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ |
| [gesture-recognition](projects/gesture-recognition/) | 手势识别 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ |
| [text-detection](projects/text-detection/) | 文字检测 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ |
| [image-captioning](projects/image-captioning/) | 图像描述生成 | Python, PyTorch | ⭐⭐⭐⭐ |
| [face-recognition](projects/face-recognition/) | 人脸识别 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [object-tracking](projects/object-tracking/) | 目标跟踪 | Python, PyTorch | ⭐⭐⭐⭐ |
| [visual-qa](projects/visual-qa/) | 视觉问答 VQA | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [video-understanding](projects/video-understanding/) | 视频理解 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [depth-estimation](projects/depth-estimation/) | 深度估计 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [image-denoising](projects/image-denoising/) | 图像去噪 | Python, PyTorch | ⭐⭐⭐⭐ |
| [image-inpainting](projects/image-inpainting/) | 图像修复/补全 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [multi-gpu-computing](projects/multi-gpu-computing/) | 多 GPU 并行计算 | Python | ⭐⭐⭐⭐ |

📖 [AI 模块详细说明](projects/AI_README.md)

---

### 🧮 机器学习算法模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [cnn-classification](projects/cnn-classification/) | CNN 图像分类 | Python, PyTorch | ⭐⭐⭐⭐ |
| [decision-tree](projects/decision-tree/) | 决策树分类器 | Python | ⭐⭐ |
| [kmeans](projects/kmeans/) | K-Means 聚类 | Python | ⭐⭐ |
| [knn](projects/knn/) | KNN 分类器 | Python | ⭐⭐ |
| [linear-regression](projects/linear-regression/) | 线性回归 | Python | ⭐⭐ |
| [logistic-regression](projects/logistic-regression/) | 逻辑回归 | Python | ⭐⭐ |
| [naive-bayes](projects/naive-bayes/) | 朴素贝叶斯分类器 | Python | ⭐⭐ |
| [pca](projects/pca/) | PCA 主成分分析 | Python | ⭐⭐ |
| [random-forest](projects/random-forest/) | 随机森林分类+回归 | Python, NumPy | ⭐⭐⭐⭐ |
| [svm](projects/svm/) | 支持向量机 | Python | ⭐⭐⭐⭐ |
| [q-learning](projects/q-learning/) | Q-Learning 强化学习 | Python, NumPy | ⭐⭐⭐ |
| [policy-gradient](projects/policy-gradient/) | 策略梯度算法 | Python, PyTorch, Gym | ⭐⭐⭐⭐ |
| [actor-critic](projects/actor-critic/) | Actor-Critic 算法 | Python, PyTorch, Gym | ⭐⭐⭐⭐ |
| [genetic-algorithm](projects/genetic-algorithm/) | 遗传算法优化框架 | Python, matplotlib | ⭐⭐⭐ |
| [gradient-descent](projects/gradient-descent/) | 梯度下降优化算法 | Python, numpy | ⭐⭐⭐ |
| [simulated-annealing](projects/simulated-annealing/) | 模拟退火优化算法 | Python, matplotlib | ⭐⭐⭐ |
| [particle-swarm](projects/particle-swarm/) | 粒子群优化算法 | Python, matplotlib | ⭐⭐⭐ |
| [bayesian-optimization](projects/bayesian-optimization/) | 贝叶斯优化（高斯过程） | Python, NumPy, SciPy | ⭐⭐⭐⭐ |
| [linear-programming](projects/linear-programming/) | 线性规划（单纯形法） | Python, NumPy | ⭐⭐⭐⭐ |
| [convex-optimization](projects/convex-optimization/) | 凸优化算法 | Python, SciPy | ⭐⭐⭐⭐⭐ |

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
| [distributed-transaction](projects/distributed-transaction/) | 分布式事务 | Go | ⭐⭐⭐⭐⭐ |
| [distributed-cache](projects/distributed-cache/) | 分布式缓存系统 | Go | ⭐⭐⭐⭐ |
| [mapreduce](projects/mapreduce/) | 分布式 MapReduce | Go | ⭐⭐⭐⭐⭐ |
| [paxos](projects/paxos/) | Paxos 共识算法 | Go | ⭐⭐⭐⭐⭐ |
| [high-throughput-message-queue](projects/high-throughput-message-queue/) | 高吞吐消息队列 | Go | ⭐⭐⭐⭐⭐ |
| [exactly-once](projects/exactly-once/) | Exactly-once 语义 | Go | ⭐⭐⭐⭐⭐ |
| [state-machine](projects/state-machine/) | 状态机 | Go | ⭐⭐⭐⭐ |
| [external-sort](projects/external-sort/) | 外部排序 | Python | ⭐⭐⭐⭐ |
| [query-parser](projects/query-parser/) | 查询解析器 | Go | ⭐⭐⭐⭐ |
| [vector-db](projects/vector-db/) | 向量数据库 | Python, NumPy | ⭐⭐⭐⭐ |
| [time-series-db](projects/time-series-db/) | 时间序列数据库 | Go | ⭐⭐⭐⭐⭐ |
| [physics-engine](projects/physics-engine/) | 2D 物理引擎 | C++ | ⭐⭐⭐⭐ |
| [physics-simulation-engine](projects/physics-simulation-engine/) | 3D 物理模拟引擎 | C++ | ⭐⭐⭐⭐⭐ |
| [rasterization-engine](projects/rasterization-engine/) | 光栅化渲染引擎 | C++ | ⭐⭐⭐⭐⭐ |
| [layer-compositing-engine](projects/layer-compositing-engine/) | 图层合成引擎 | C++ | ⭐⭐⭐⭐⭐ |
| [3d-modeling-engine](projects/3d-modeling-engine/) | 3D 建模引擎 | C++ | ⭐⭐⭐⭐⭐⭐ |
| [bezier-engine](projects/bezier-engine/) | 贝塞尔曲线引擎 | C++ | ⭐⭐⭐⭐ |
| [svg-renderer](projects/svg-renderer/) | SVG 渲染器 | C++ | ⭐⭐⭐⭐ |
| [streaming-server](projects/streaming-server/) | 流媒体服务器 | C++17/20 | ⭐⭐⭐⭐⭐ |
| [gpu-shader-library](projects/gpu-shader-library/) | GPU 着色器库 | C++17/20, GLSL | ⭐⭐⭐⭐ |
| [reactive-framework](projects/reactive-framework/) | 响应式数据绑定框架 | TypeScript, Proxy | ⭐⭐⭐⭐ |
| [timeline-engine](projects/timeline-engine/) | 时间线动画引擎 | TypeScript | ⭐⭐⭐⭐ |
| [chart-library](projects/chart-library/) | 图表库 | TypeScript, Canvas | ⭐⭐⭐ |
| [virtual-scroll](projects/virtual-scroll/) | 虚拟滚动组件 | TypeScript | ⭐⭐⭐⭐ |
| [drag-drop](projects/drag-drop/) | 拖放框架 | TypeScript | ⭐⭐⭐⭐ |
| [code-editor](projects/code-editor/) | 代码编辑器 | TypeScript | ⭐⭐⭐⭐⭐ |
| [form-engine](projects/form-engine/) | 表单引擎 | TypeScript | ⭐⭐⭐⭐ |
| [constraint-solver](projects/constraint-solver/) | 约束求解器 | Go | ⭐⭐⭐⭐⭐ |
| [constraint-solver-py](projects/constraint-solver-py/) | 约束求解器 (Python) | Python | ⭐⭐⭐⭐ |
| [basic-circuit](projects/basic-circuit/) | 基本电路模拟 | Python, NumPy | ⭐⭐⭐ |
| [logic-gates](projects/logic-gates/) | 逻辑门模拟器 | Python | ⭐⭐⭐⭐ |
| [riscv-simulator](projects/riscv-simulator/) | RISC-V 模拟器 | Python | ⭐⭐⭐⭐⭐ |

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
| [dns-server](projects/dns-server/) | DNS 服务器 | Go | ⭐⭐⭐⭐ |
| [service-discovery](projects/service-discovery/) | 服务发现系统 | Go | ⭐⭐⭐⭐ |

📖 [网络模块详细说明](projects/NETWORK_README.md)

---

### 🔧 异构计算

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [heterogeneous-computing](projects/heterogeneous-computing/) | CPU+GPU 异构计算 | C++ | ⭐⭐⭐⭐⭐ |
| [multi-gpu-computing](projects/multi-gpu-computing/) | 多 GPU 并行计算 | Python | ⭐⭐⭐⭐ |
| [gpu-shader-library](projects/gpu-shader-library/) | GPU Shader 库 | C++ | ⭐⭐⭐⭐ |

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

### 💰 金融 & 量化

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [quant-trading-system](projects/quant-trading-system/) | 量化交易系统 | Python | ⭐⭐⭐⭐⭐⭐ |
| [factor-mining](projects/factor-mining/) | 因子挖掘框架 | Python | ⭐⭐⭐⭐⭐ |
| [risk-engine](projects/risk-engine/) | 风险管理引擎 | Python, SciPy | ⭐⭐⭐⭐ |
| [hft-engine](projects/hft-engine/) | 高频交易引擎 | C++17/20 | ⭐⭐⭐⭐⭐⭐⭐ |
| [matching-engine](projects/matching-engine/) | 撮合引擎 | C++ | ⭐⭐⭐⭐⭐ |
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
| [animation-engine](projects/animation-engine/) | 动画引擎 | C++ | ⭐⭐⭐⭐ |
| [mesh-processing](projects/mesh-processing/) | 网格处理算法 | C++ | ⭐⭐⭐⭐ |
| [scene-graph](projects/scene-graph/) | 场景图系统 | C++ | ⭐⭐⭐⭐ |
| [spatial-partitioning](projects/spatial-partitioning/) | 空间划分算法 | C++ | ⭐⭐⭐⭐ |
| [feature-matching](projects/feature-matching/) | 特征匹配 SIFT/ORB | Python | ⭐⭐⭐⭐ |
| [ray-tracer](projects/ray-tracer/) | 光线追踪渲染器 | C++ | ⭐⭐⭐⭐ |
| [color-space-engine](projects/color-space-engine/) | 颜色空间引擎 | Python, NumPy | ⭐⭐⭐⭐ |
| [image-processing-engine](projects/image-processing-engine/) | 图像处理引擎 | Python, NumPy | ⭐⭐⭐⭐ |
| [ocr](projects/ocr/) | OCR 光学字符识别 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [table-recognition](projects/table-recognition/) | 表格识别 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [point-cloud](projects/point-cloud/) | 3D 点云处理 | Python, PyTorch | ⭐⭐⭐⭐ |
| [depth-estimation](projects/depth-estimation/) | 深度估计 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [video-understanding](projects/video-understanding/) | 视频理解 | Python, PyTorch | ⭐⭐⭐⭐⭐ |

📖 [多媒体模块详细说明](projects/MEDIA_README.md)

---

### 📊 NLP & 数据结构

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [tokenizer](projects/tokenizer/) | 中文分词器 | Python | ⭐⭐⭐ |
| [language-model](projects/language-model/) | N-gram 语言模型 | Python | ⭐⭐⭐ |
| [text-classification](projects/text-classification/) | 文本分类系统 | Python, NumPy | ⭐⭐⭐⭐ |
| [word2vec](projects/word2vec/) | 词向量 Word2Vec | Python, NumPy | ⭐⭐⭐⭐ |
| [ner](projects/ner/) | 命名实体识别 | Python | ⭐⭐⭐⭐ |
| [random-forest](projects/random-forest/) | 随机森林分类+回归 | Python, NumPy | ⭐⭐⭐⭐ |
| [svm](projects/svm/) | 支持向量机 | Python | ⭐⭐⭐⭐ |
| [hyperloglog](projects/hyperloglog/) | HyperLogLog 基数估计 | Go | ⭐⭐⭐⭐ |
| [inverted-index](projects/inverted-index/) | 倒排索引 | Go | ⭐⭐⭐⭐ |
| [bloom-filter](projects/bloom-filter/) | 布隆过滤器 | Go | ⭐⭐⭐⭐ |
| [pagerank](projects/pagerank/) | PageRank 算法 | Python | ⭐⭐⭐ |
| [matching-engine](projects/matching-engine/) | 撮合引擎 | C++ | ⭐⭐⭐⭐⭐ |
| [query-parser](projects/query-parser/) | 查询解析器 | Go | ⭐⭐⭐⭐ |
| [edge-computing](projects/edge-computing/) | 边缘计算框架 | Python | ⭐⭐⭐⭐ |

📖 [NLP 模块详细说明](projects/NLP_README.md)

---

### 🔐 安全 & 工具

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [crypto-lib](projects/crypto-lib/) | 密码学库 | C | ⭐⭐⭐⭐ |
| [sandbox](projects/sandbox/) | 沙箱隔离 | C | ⭐⭐⭐⭐ |
| [interpreter](projects/interpreter/) | 解释器 | Python | ⭐⭐⭐⭐ |
| [riscv-simulator](projects/riscv-simulator/) | RISC-V 模拟器 | Python | ⭐⭐⭐⭐⭐ |
| [firewall](projects/firewall/) | 防火墙 | C | ⭐⭐⭐⭐⭐ |
| [pentest-tools](projects/pentest-tools/) | 渗透测试工具集 | Python | ⭐⭐⭐⭐ |

📖 [安全模块详细说明](projects/SECURITY_README.md)

---

### 🎛️ 控制系统

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [pid-controller](projects/pid-controller/) | PID 控制器实现 | Python | ⭐⭐ |
| [state-space](projects/state-space/) | 状态空间模型 | Python, scipy | ⭐⭐⭐ |
| [adaptive-controller](projects/adaptive-controller/) | 自适应控制器 (MRAC) | Python, scipy | ⭐⭐⭐ |
| [fuzzy-controller](projects/fuzzy-controller/) | 模糊控制器 | Python | ⭐⭐⭐ |
| [mpc-controller](projects/mpc-controller/) | 模型预测控制 (MPC) | Python, scipy | ⭐⭐⭐⭐ |
| [system-response](projects/system-response/) | 系统响应分析 | Python, scipy | ⭐⭐⭐ |
| [robot-arm-kinematics](projects/robot-arm-kinematics/) | 机械臂运动学 | Python, numpy, matplotlib | ⭐⭐⭐⭐ |

📖 [控制系统模块详细说明](projects/CONTROL_README.md)

---

### 🔷 C++ 特性系列

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [cpp11-14-features](projects/cpp11-14-features/) | C++11/14 新特性 | C++ | ⭐⭐⭐ |
| [cpp17-features](projects/cpp17-features/) | C++17 新特性实践 | C++17 | ⭐⭐⭐ |
| [cpp20-features](projects/cpp20-features/) | C++20 新特性实践 | C++20 | ⭐⭐⭐ |
| [cpp23-features](projects/cpp23-features/) | C++23 新特性实践 | C++23 | ⭐⭐⭐⭐ |
| [cpp-template-metaprogramming](projects/cpp-template-metaprogramming/) | 模板元编程 | C++ | ⭐⭐⭐⭐⭐ |
| [cpp-template-metaprogramming-advanced](projects/cpp-template-metaprogramming-advanced/) | 模板元编程高级 | C++ | ⭐⭐⭐⭐⭐⭐ |
| [cpp-compile-time-computation](projects/cpp-compile-time-computation/) | 编译期计算 | C++ | ⭐⭐⭐⭐⭐ |
| [cpp-tricks-and-tips](projects/cpp-tricks-and-tips/) | C++ 奇技淫巧集锦 | C++17/20 | ⭐⭐⭐⭐ |
| [cpp-memory-model-concurrency](projects/cpp-memory-model-concurrency/) | 内存模型与并发 | C++ | ⭐⭐⭐⭐⭐ |
| [cpp-performance-optimization](projects/cpp-performance-optimization/) | 性能优化 | C++ | ⭐⭐⭐⭐⭐ |
| [cpp-pitfalls-best-practices](projects/cpp-pitfalls-best-practices/) | 陷阱与最佳实践 | C++ | ⭐⭐⭐⭐⭐ |
| [cpp-third-party-libraries](projects/cpp-third-party-libraries/) | 三方库集成 | C++ | ⭐⭐⭐⭐ |
| [cpp-build-system-toolchain](projects/cpp-build-system-toolchain/) | 构建系统工具链 | C++ | ⭐⭐⭐⭐⭐ |
| [cpp-coding-standards](projects/cpp-coding-standards/) | 代码规范 | C++ | ⭐⭐⭐ |

📖 [系统模块详细说明](projects/SYSTEM_README.md)

---

### ⚙️ 机械工程模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [robot-arm-kinematics](projects/robot-arm-kinematics/) | 机械臂运动学 | Python, numpy, matplotlib | ⭐⭐⭐⭐ |
| [gear-transmission](projects/gear-transmission/) | 齿轮传动系统 | Python, matplotlib | ⭐⭐⭐ |
| [cam-mechanism](projects/cam-mechanism/) | 凸轮机构设计 | Python, matplotlib | ⭐⭐⭐⭐ |
| [linkage-mechanism](projects/linkage-mechanism/) | 连杆机构分析 | Python, matplotlib | ⭐⭐⭐⭐ |
| [vibration-analysis](projects/vibration-analysis/) | 振动分析系统 | Python, scipy, matplotlib | ⭐⭐⭐⭐⭐ |
| [thermodynamics](projects/thermodynamics/) | 热力学模拟 | Python, numpy, matplotlib | ⭐⭐⭐⭐⭐ |
| [fluid-mechanics](projects/fluid-mechanics/) | 流体力学基础 | Python, numpy, matplotlib | ⭐⭐⭐⭐ |
| [cad-kernel](projects/cad-kernel/) | CAD 内核基础 | C++, Rust | ⭐⭐⭐⭐⭐⭐ |
| [finite-element](projects/finite-element/) | 有限元分析基础 | Python, numpy, scipy | ⭐⭐⭐⭐⭐ |
| [3d-print-slicer](projects/3d-print-slicer/) | 3D 打印切片器 | Python, numpy | ⭐⭐⭐⭐⭐ |

📖 [机械工程模块详细说明](projects/MECHANICAL_README.md)

---

### 🔌 嵌入式系统模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [rtos-kernel](projects/rtos-kernel/) | RTOS 内核 | C | ⭐⭐⭐⭐⭐ |
| [device-driver](projects/device-driver/) | 设备驱动框架 | C, Linux kernel | ⭐⭐⭐⭐⭐ |
| [comm-protocol](projects/comm-protocol/) | 通信协议栈 (UART/SPI/I2C) | C | ⭐⭐⭐⭐ |
| [sensor-fusion](projects/sensor-fusion/) | 传感器融合 | C/Python, numpy | ⭐⭐⭐⭐⭐ |
| [embedded-gui](projects/embedded-gui/) | 嵌入式 GUI 框架 | C | ⭐⭐⭐⭐⭐ |
| [ota-upgrade](projects/ota-upgrade/) | OTA 升级系统 | C/Go | ⭐⭐⭐⭐ |
| [low-power](projects/low-power/) | 低功耗设计 | C | ⭐⭐⭐⭐ |
| [embedded-fs](projects/embedded-fs/) | 嵌入式文件系统 | C | ⭐⭐⭐⭐⭐ |
| [embedded-network](projects/embedded-network/) | 嵌入式网络栈 | C | ⭐⭐⭐⭐⭐ |
| [embedded-security](projects/embedded-security/) | 嵌入式安全 | C | ⭐⭐⭐⭐⭐ |
| [edge-inference](projects/edge-inference/) | 边缘推理引擎 | C/C++ | ⭐⭐⭐⭐⭐⭐ |

📖 [嵌入式模块详细说明](projects/EMBEDDED_README.md)

---

### 🖥️ 指令集架构模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [riscv-simulator](projects/riscv-simulator/) | RISC-V 指令集模拟器 | C/Rust | ⭐⭐⭐⭐⭐ |
| [arm-simulator](projects/arm-simulator/) | ARM 指令集模拟器 | Python | ⭐⭐⭐⭐⭐ |
| [x86-simulator](projects/x86-simulator/) | x86 指令集模拟器 | C/Rust | ⭐⭐⭐⭐⭐⭐ |
| [instruction-set-comparison](projects/instruction-set-comparison/) | 指令集对比分析 | Python | ⭐⭐⭐ |

📖 [指令集模块详细说明](projects/ISA_README.md)

---

### 📱 移动端开发模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [ios-app](projects/ios-app/) | iOS 基础应用 | Python (模拟 iOS 架构) | ⭐⭐⭐⭐ |
| [android-app](projects/android-app/) | Android 基础应用 | Python (模拟 Android 架构) | ⭐⭐⭐⭐ |
| [harmonyos-app](projects/harmonyos-app/) | 鸿蒙基础应用 | Python (模拟 ArkUI) | ⭐⭐⭐⭐ |
| [cross-platform](projects/cross-platform/) | 跨平台框架原理 | Python (模拟 Flutter) | ⭐⭐⭐⭐⭐ |

📖 [移动端模块详细说明](projects/MOBILE_README.md)

---

### ⚡ 数字/模拟电路模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [logic-gates](projects/logic-gates/) | 逻辑门模拟器 | Python | ⭐⭐⭐ |
| [combinational-logic](projects/combinational-logic/) | 组合逻辑电路 | Python | ⭐⭐⭐⭐ |
| [sequential-logic](projects/sequential-logic/) | 时序逻辑电路 | Python | ⭐⭐⭐⭐ |
| [simple-cpu](projects/simple-cpu/) | 简易 CPU 设计 | C++/Rust | ⭐⭐⭐⭐⭐ |
| [basic-circuit](projects/basic-circuit/) | 基本电路模拟 | Python, NumPy | ⭐⭐⭐ |
| [amplifier-design](projects/amplifier-design/) | 放大器设计 | Python, matplotlib | ⭐⭐⭐ |
| [analog-filter](projects/analog-filter/) | 模拟滤波器 | Python, scipy | ⭐⭐⭐ |
| [adc-dac](projects/adc-dac/) | ADC/DAC 模拟 | Python, matplotlib | ⭐⭐⭐⭐ |
| [verilog-simulator](projects/verilog-simulator/) | Verilog 模拟器 | C++/Rust | ⭐⭐⭐⭐⭐ |
| [chip-placement](projects/chip-placement/) | 芯片布局布线 | C++/Rust | ⭐⭐⭐⭐⭐⭐ |
| [timing-analysis](projects/timing-analysis/) | 时序分析 | C++/Rust | ⭐⭐⭐⭐⭐ |

📖 [电路模块详细说明](projects/CIRCUITS_README.md)

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
| **总项目数** | 225 |
| **技术栈** | 10 (C++, Go, Python, Rust, Solidity, TypeScript, C, C, C, C++) |
| **领域** | 20 |
| **总代码行数** | 350,000+ |
| **文档数量** | 800+ |

---

## 🎯 快速开始

### 1. 选择一个领域

```bash
# 进入感兴趣的领域
cd projects/adas-perception   # 自动驾驶
cd projects/simple-blockchain # 区块链
cd projects/dqn               # AI & 深度学习
cd projects/high-concurrency-db # 系统基础设施
```

### 2. 查看项目说明

```bash
# 查看项目 README
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

### 2026-06-26
- ✅ **完成 device-driver（设备驱动框架 C 实现）** - 从零实现 Linux 设备驱动框架学习项目，包含完整的字符设备驱动、中断处理、平台驱动模型、内存映射 I/O 和 DMA 管理
  - `src/device_framework.c`: 核心驱动框架（字符设备注册、cdev 管理、文件操作、中断处理、平台驱动、DMA 管理、设备树解析）
  - `include/device_framework.h`: 公共头文件（IOCTL 命令、数据结构、常量定义）
  - `examples/simple_char_device.c`: 简单字符设备驱动（动态主设备号、cdev 注册、基础文件操作）
  - `examples/interrupt_driver.c`: 中断驱动示例（IRQ 处理、顶半部/底半部、工作队列、定时器模拟）
  - `examples/platform_driver_dt.c`: 平台驱动+设备树（probe/remove、设备树解析、MMIO 映射）
  - `examples/mmio_driver.c`: 内存映射 I/O 示例（ioremap、寄存器读写、资源管理）
  - `examples/user_test.c`: 用户空间测试程序（open/close/read/write/ioctl/poll 测试）
  - `tests/test_framework.c`: 单元测试框架（数据结构、常量验证、内存对齐）
  - `docs/linux-driver-model.md`: Linux 驱动模型架构文档（8 层架构图、关键 API 参考）
  - `Makefile`: 构建系统（模块构建、安装、测试、清理）
  - `README.md`: 中英双语文档（含驱动模型架构、学习目标、运行指南）

### 2026-06-26
- ✅ **完成 cam-mechanism（凸轮机构学习项目 Python 实现）** - 从零实现凸轮机构设计与运动分析学习项目，包含完整的凸轮轮廓生成、8种从动件运动规律、压力角分析、曲率分析、赫兹接触应力和动力学仿真
  - `src/motion_laws.py`: 运动规律模块（等速、等加速等减速、摆线、3/4/5次多项式、简谐、改良正弦、改良梯形共8种运动规律）
  - `src/cam_profile.py`: 凸轮轮廓生成（对心/偏置移动从动件、摆动从动件、滚子/平底/尖顶从动件、压力角计算、曲率分析）
  - `src/pressure_angle.py`: 压力角分析（解析计算、限值校核、自锁判断）
  - `src/contact_stress.py`: 赫兹接触应力分析（接触半宽、应力分布、动态载荷计算）
  - `src/dynamic_analysis.py`: 动力学分析（惯性力、固有频率、动态放大系数、脱离接触检测）
  - `src/visualization.py`: 可视化工具（凸轮轮廓图、运动规律对比、压力角图、动力学图、综合报告）
  - `examples/example1_cam_profile.py`: 凸轮轮廓生成（5种从动件类型）
  - `examples/example2_motion_law_comparison.py`: 运动规律对比（8种规律性能对比）
  - `examples/example3_pressure_angle.py`: 压力角分析（基圆半径/偏置距影响）
  - `examples/example4_dynamic_simulation.py`: 动力学仿真（角速度影响、接触应力、综合报告）
  - `tests/test_motion_laws.py`: 运动规律单元测试
  - `tests/test_cam_profile.py`: 凸轮轮廓生成测试
  - `tests/test_dynamic_analysis.py`: 动力学分析测试
  - `tests/test_contact_stress.py`: 接触应力测试
  - `README.md`: 中英双语文档（含凸轮理论基础、公式、运行指南）
  - `requirements.txt`: 依赖定义（numpy, matplotlib）

### 2026-06-26
- ✅ **完成 finite-element（有限元分析基础 Python 实现）** - 从零实现基础有限元分析学习项目，包含完整的2D/3D网格生成、单元刚度矩阵计算、全局刚度矩阵组装、边界条件处理、线性静态分析、应力计算和Von Mises应力分析
  - `src/mesh.py`: 网格生成（三角形/四边形/四面体单元、圆形区域网格、网格细化、质量评估）
  - `src/elements.py`: 单元刚度矩阵（CST常应变三角形、Euler-Bernoulli梁、2D/3D桁架、4节点四边形等参单元、平面应力/应变弹性矩阵）
  - `src/assembly.py`: 全局组装（GlobalAssembler类、稀疏矩阵、边界条件直接法/罚函数法、反力计算）
  - `src/postprocess.py`: 后处理（应变计算、应力恢复、Von Mises应力、主应力、应变能、节点应力平均）
  - `src/visualize.py`: 可视化（网格图、位移云图、变形形状、应力云图、收敛性分析、梁变形图）
  - `examples/01_cantilever_beam.py`: 2D悬臂梁弯曲模拟（与弹性力学解析解对比）
  - `examples/02_plate_with_hole.py`: 带孔平板应力集中分析（Kt≈3验证）
  - `examples/03_3d_truss.py`: 3D空间四面体桁架分析
  - `examples/04_mesh_convergence.py`: 网格收敛性研究（5级细化）
  - `tests/test_mesh.py`: 网格模块测试（三角形/四边形/四面体/圆形/细化/质量）
  - `tests/test_elements.py`: 单元刚度矩阵测试（对称性/正定性/刚体模式）
  - `tests/test_assembly.py`: 组装模块测试（组装/边界条件/求解）
  - `tests/test_postprocess.py`: 后处理测试（应变/应力/Von Mises/应变能/主应力）
  - `README.md`: 中英双语文档（含FEM理论基础、公式、运行指南）
  - `requirements.txt`: 依赖定义（numpy, scipy, matplotlib）

### 2026-06-26
- ✅ **完成 chip-placement（芯片布局布线 C++ 实现）** - 从零实现基础 EDA 布局布线算法学习项目，包含完整的网表解析器、解析布局、模拟退火布局、全局布线、详细布线（迷宫布线/BFS 和 A*）、静态时序分析、关键路径分析和线长/拥塞评估
  - `include/`: 5 个头文件 (netlist.h, placement.h, routing.h, timing.h, analysis.h)
  - `src/`: 5 个实现文件 (netlist.cpp, placement.cpp, routing.cpp, timing.cpp, analysis.cpp)
  - `examples/placement_demo.cpp`: 解析布局 + 模拟退火布局演示
  - `examples/routing_demo.cpp`: 全局布线 + 详细布线（迷宫/BFS + A*）演示
  - `examples/timing_demo.cpp`: 静态时序分析演示（到达时间/需求时间/Slack/关键路径）
  - `examples/wire_length_demo.cpp`: 线长优化对比演示（HPWL、拥塞分析）
  - `tests/test_chip_placement.cpp`: 16 个单元测试（网表解析、布局、布线、时序、线长、拥塞）
  - `netlists/`: 2 个示例网表文件
  - `README.md`: 中英双语文档（含 EDA 理论基础：HPWL、Elmore 延迟、STA 等）
  - `Makefile`: 构建系统（all/run-all/test/clean/help）

### 2026-06-26
- ✅ **完成 cross-platform（跨平台框架原理 Python 实现）** - 从零实现跨平台框架核心原理学习项目，包含完整的 Dart VM 模拟器、Skia 渲染引擎、Widget 树、布局引擎、Platform Channel 桥接机制和图层合成器
  - `src/dart_vm.py`: Dart VM 核心（字节码指令集、Dart 对象模型、标记-清除垃圾回收器、VM 执行引擎）
  - `src/rendering_engine.py`: Skia 渲染引擎（Color/Colors 颜色系统、Paint 画笔、Rect 矩形、Offset 偏移量、Path 路径、Canvas 画布、Scene 渲染场景、Layer 图层）
  - `src/widget_tree.py`: Widget 树构建器（Widget/Element/RenderObject 三层架构、StatelessWidget、RenderBox/RenderFlex/RenderStack）
  - `src/layout_engine.py`: 布局引擎（BoxConstraints 约束系统、LayoutEngine 三遍布局、布局策略、LayoutDebugger 调试工具）
  - `src/platform_channel.py`: 平台通道桥接（StandardCodec 编解码器、MethodChannel/EventChannel/BasicMessageChannel、PlatformView 嵌入）
  - `src/composition.py`: 图层合成（LayerCompositor 图层合成器、FrameRenderer 帧渲染、RasterCache 光栅缓存、RenderingPipeline 渲染管线）
  - `examples/widget_tree_demo.py`: Widget 树构建演示
  - `examples/platform_channel_demo.py`: 平台通道通信演示
  - `examples/custom_rendering_demo.py`: 自定义渲染演示
  - `examples/cross_platform_layout_demo.py`: 跨平台布局演示
  - `tests/test_dart_vm.py`: Dart VM 单元测试
  - `tests/test_rendering_engine.py`: 渲染引擎单元测试
  - `tests/test_integration.py`: 集成测试（Widget/布局/平台通道/合成）
  - `README.md`: 中英双语文档（含跨平台架构理论基础、渲染管线、布局系统、Platform Channel、运行指南）
  - `requirements.txt`: 依赖定义（无外部依赖）

### 2026-06-26
- ✅ **完成 ios-app（iOS 基础应用 Python 实现）** - 从零实现 iOS 架构 Python 模拟学习项目，包含完整的 RunLoop 事件循环、UIView 视图层次、Auto Layout 约束系统、UINavigationController 导航控制器、UITableView 表格视图、URLSession 网络请求、KVO 数据绑定和 ViewModel MVVM 架构
  - `src/core/__init__.py`: 核心架构 (RunLoop 运行循环、MainThread 主线程管理、Application 应用生命周期)
  - `src/ui/__init__.py`: UI 组件 (UIView/UILabel/UIButton/UIImageView/UITextField/UIScrollView、UIViewController、UINavigationController、UITableView、Auto Layout 约束系统、UIGestureRecognizer 手势识别器)
  - `src/network/__init__.py`: 网络模块 (URLSession/URLRequest/URLResponse/URLSessionDataTask、NetworkManager 高层 API)
  - `src/binding/__init__.py`: 数据绑定 (KVOObserver/Observable/Binding/ViewModel MVVM)
  - `examples/01_basic_ui_layout.py`: 基础 UI 布局演示 (视图层次、Auto Layout、手势识别、UIScrollView)
  - `examples/02_navigation_controller.py`: 导航控制器演示 (push/pop/栈管理)
  - `examples/03_table_view_demo.py`: 表格视图演示 (普通表格、分组表格、UITableViewController)
  - `examples/04_network_request_demo.py`: 网络请求演示 (URLSession/NetworkManager/KVO 数据绑定)
  - `tests/test_ios_app.py`: 150 个单元测试 (RunLoop/UIView/UIViewController/UINavigationController/UITableView/Auto Layout/手势识别/URLSession/KVO/ViewModel/集成测试)
  - `README.md`: 中英双语文档 (含 iOS 架构理论基础、核心概念对照表、运行指南)
  - `requirements.txt`: 依赖定义 (无外部依赖)

### 2026-06-26
- ✅ **完成 adc-dac（ADC/DAC 模拟 Python 实现）** - 从零实现模数/数模转换模拟学习项目，包含完整的采样、量化、ADC/DAC 模型、重建滤波器和信号质量指标
  - `src/sampling.py`: 采样模块 (理想采样、奈奎斯特频率计算、混叠检测、孔径误差、采样时钟生成)
  - `src/quantization.py`: 量化模块 (均匀量化、A-law/mu-law 非均匀量化、量化噪声分析、自适应量化)
  - `src/adc.py`: 理想 ADC 模型 (采样→量化→编码完整流程、SNR 计算)
  - `src/dac.py`: 理想 DAC 模型 (解码→ZOH/理想重建、分辨率计算)
  - `src/reconstruction.py`: 重建滤波器 (零阶保持、sinc 理想插值、低通滤波重建、ZOH 频率响应)
  - `src/metrics.py`: 信号质量指标 (SNR、SINAD、THD、ENOB、SFDR、噪声底、综合 ADC 分析)
  - `examples/01_adc_dac_simulation.py`: ADC/DAC 完整仿真 (含可视化、多位数对比)
  - `examples/02_quantization_error_analysis.py`: 量化误差分析 (均匀 vs A-law vs mu-law、SNR 对比)
  - `examples/03_sampling_rate_effects.py`: 采样率效应 (混叠演示、SNR vs 采样率)
  - `examples/04_snr_vs_bit_depth.py`: SNR vs 位数分析 (理论公式验证、THD/ENOB 分析)
  - `tests/`: 完整单元测试 (采样/量化/ADC/DAC/重建滤波器)
  - `README.md`: 中英双语文档 (含采样定理、量化理论、SNR 公式推导、运行指南)
  - `requirements.txt`: 依赖定义 (numpy, matplotlib)

### 2026-06-26
- ✅ **完成 combinational-logic（组合逻辑电路 Python 实现）** - 从零实现组合逻辑电路模拟学习项目，包含完整的逻辑门、加法器、乘法器、多路选择器、译码器、编码器、比较器、三态缓冲器和基于MUX的逻辑综合
  - `src/gates.py`: 基本逻辑门（AND/OR/NOT/XOR/NAND/NOR/XNOR）
  - `src/adders.py`: 加法器（半加器、全加器、行波进位加法器、减法器）
  - `src/multiplier.py`: 乘法器（直接乘法器、Wallace树乘法器）
  - `src/mux_demux.py`: 多路选择器/解复用器（2:1/4:1/8:1 MUX、1:2/1:8 DEMUX）
  - `src/encoder_decoder.py`: 编码器/译码器（二进制、BCD、7段译码器）
  - `src/comparator.py`: 数值比较器（1位、4位、n位比较器）
  - `src/tri_state.py`: 三态缓冲器/总线驱动器
  - `src/logic_synthesis.py`: 基于MUX的逻辑综合
  - `examples/adder_subtractor_demo.py`: 加法器/减法器仿真
  - `examples/mux_demo.py`: 多路选择器演示
  - `examples/decoder_encoder_demo.py`: 译码器/编码器演示
  - `examples/custom_circuit_design.py`: 自定义电路设计（投票电路、比较器、7段显示、ALU等）
  - `tests/test_combinational_logic.py`: 45个单元测试
  - `README.md`: 中英双语文档（含组合逻辑理论基础、公式、运行指南）
  - `requirements.txt`: 依赖定义（无外部依赖）

### 2026-06-26
- ✅ **完成 sequential-logic（时序逻辑电路 Python 实现）** - 从零实现时序逻辑电路模拟学习项目，包含完整的触发器、计数器、寄存器和有限状态机
  - `src/flip_flops.py`: SR锁存器（基本存储元件、置位/复位/保持/无效状态）和JK触发器（真值表、边沿触发、翻转模式）
  - `src/d_and_t_ff.py`: D触发器（数据捕获、边沿触发）和T触发器（分频器、翻转操作）
  - `src/counter.py`: 计数器（异步纹波计数器、同步计数器、加减计数器、模N计数器、频率分频器）
  - `src/register.py`: 寄存器（SIPO串行输入并行输出、PISO并行输入串行输出、PIPO并行输入并行输出、双向移位寄存器）
  - `src/fsm.py`: 有限状态机（摩尔型/米利型、序列检测器、交通灯状态机、售货机状态机）
  - `src/timing_diagram.py`: 时序图生成（时钟信号、信号波形、计数器时序图、FSM时序图）
  - `examples/01_flip_flop_simulation.py`: 触发器仿真（SR锁存器、JK/D/T触发器、触发器级联分频器）
  - `examples/02_counter_simulation.py`: 计数器仿真（纹波/同步/模数/加减计数器、频率分频器）
  - `examples/04_register_operations.py`: 寄存器操作（SIPO/PISO/PIPO/双向移位、延迟线）
  - `examples/05_fsm_demo.py`: 状态机演示（序列检测、交通灯、售货机、偶校验器）
  - `tests/test_sequential_logic.py`: 单元测试（触发器/计数器/寄存器/状态机各模块）
  - `README.md`: 中英双语文档（含时序逻辑理论基础、公式、运行指南）
  - `requirements.txt`: 依赖定义（matplotlib, numpy）

### 2026-06-26
- ✅ **完成 sensor-fusion（传感器融合 Python 实现）** - 从零实现 IMU 传感器融合学习项目，包含完整的坐标变换、传感器校准、互补滤波、卡尔曼滤波、Madgwick 滤波器和 Mahony 滤波器
  - `src/coordinate_transform.py`: 坐标变换（欧拉角↔四元数↔旋转矩阵、四元数乘法/共轭/归一化、向量旋转、反对称矩阵、角速度到四元数导数）
  - `src/sensor_calibration.py`: 传感器校准（加速度计偏置/比例因子/6面校准、陀螺仪零偏/温度补偿、磁力计硬铁/软铁椭圆拟合、校准管理器）
  - `src/data_preprocessing.py`: 数据预处理（移动平均、一阶低通、异常值检测、传感器数据处理器）
  - `src/complementary_filter.py`: 互补滤波器（四元数互补滤波、自适应增益、2D互补滤波）
  - `src/kalman_filter.py`: 卡尔曼滤波器（标准KF、扩展EKF、姿态EKF含陀螺偏置估计、互补卡尔曼）
  - `src/madgwick_filter.py`: Madgwick 滤波器（梯度下降姿态估计、自适应beta）
  - `src/mahony_filter.py`: Mahony 滤波器（PI反馈姿态估计、自适应增益）
  - `examples/01_raw_sensor_processing.py`: 原始传感器数据处理（模拟数据、滤波效果对比）
  - `examples/02_complementary_filter_demo.py`: 互补滤波器演示（不同增益对比、自适应滤波）
  - `examples/03_kalman_filter_demo.py`: 卡尔曼滤波器演示（EKF vs 互补滤波、仅加速度计对比）
  - `examples/04_attitude_comparison.py`: 姿态估计对比（5种算法性能对比）
  - `tests/test_sensor_fusion.py`: 单元测试（坐标变换/校准/预处理/各滤波器）
  - `README.md`: 中英双语文档（含传感器融合理论基础、公式、运行指南）
  - `requirements.txt`: 依赖定义（numpy）
  - `Makefile`: 构建目标（测试、示例运行、安装）

### 2026-06-26
- ✅ **完成 3d-print-slicer（3D 打印切片器 Python 实现）** - 从零实现 3D 打印切片算法学习项目，包含完整的 STL 解析、网格切片、层生成、填充图案、路径规划和 G-code 生成
  - `src/stl_parser.py`: STL 文件解析器（二进制/ASCII 格式、STLTriangle/STLModel 类、边界框计算、面积计算）
  - `src/mesh_slicer.py`: 网格切片算法（三角形-平面相交、线性插值交点、SliceSegment/Layer 类、周长提取）
  - `src/layer_generator.py`: 层生成（LayerGeometry 类、周长环路、填充区域、面积估算）
  - `src/infill_generator.py`: 填充图案生成（Grid/Honeycomb/Gyroid/Concentric 四种图案、InfillPattern 枚举）
  - `src/toolpath_planner.py`: 路径规划（ToolpathPlanner 类、先轮廓后填充策略、Travel 优化）
  - `src/gcode_generator.py`: G-code 生成（GCodeGenerator 类、挤出量计算、温度控制、时间/材料估算）
  - `src/support_generator.py`: 支撑结构生成（悬垂检测、SupportStructure 类、interface 层）
  - `examples/01_stl_loading.py`: STL 加载演示（测试模型生成、网格信息展示）
  - `examples/02_slicing_demo.py`: 切片演示（圆柱体切片、ASCII 层可视化、层统计）
  - `examples/03_gcode_generation.py`: G-code 生成演示（盒模型切片、G-code 输出、打印估算）
  - `examples/04_infill_comparison.py`: 填充图案对比（四种图案 ASCII 可视化、密度对比）
  - `tests/test_stl_parser.py`: STL 解析器测试（三角形/模型/文件加载）
  - `tests/test_mesh_slicer.py`: 切片算法测试（相交/层/线段）
  - `tests/test_infill_generator.py`: 填充图案测试（四种图案/百分比/边界）
  - `tests/test_gcode_generator.py`: G-code 生成测试（头尾/挤出/移动/估算）
  - `README.md`: 中英双语文档（含切片理论基础、公式推导、运行指南）
  - `requirements.txt`: 依赖定义（numpy）

### 2026-06-26
- ✅ **完成 vibration-analysis（振动分析系统 Python 实现）** - 从零实现机械振动分析学习项目，包含完整的自由振动、强迫振动、模态分析、频响函数、多自由度系统和共振检测
  - `src/free_vibration.py`: 自由振动分析（无阻尼/有阻尼、固有频率、阻尼比、对数衰减率、能量耗散）
  - `src/forced_vibration.py`: 强迫振动响应（简谐/阶跃/脉冲激励、频响函数、稳态幅值）
  - `src/modal_analysis.py`: 模态分析（固有频率、模态振型、正交性验证、模态参与系数、模态叠加法）
  - `src/frequency_response.py`: 频响函数（位移/速度/加速度FRF、Bode图、Nyquist图、 receptance）
  - `src/multi_dof.py`: 多自由度系统（弹簧-质量矩阵构建、悬臂梁/固支梁模型、模态叠加响应）
  - `src/resonance.py`: 共振检测（共振频率、Q因子、半功率带宽、共振峰检测、避免设计）
  - `examples/01_spring_mass_simulation.py`: 弹簧-质量系统仿真（自由/强迫振动、共振分析、多自由度）
  - `examples/02_modal_analysis_demo.py`: 模态分析演示（SDOF/MDOF模态、正交性验证、悬臂梁、模态叠加）
  - `examples/03_forced_vibration_response.py`: 强迫振动响应（简谐/阶跃/脉冲、频率扫描、共振避免）
  - `examples/04_resonance_analysis.py`: 共振分析（共振曲线、峰检测、带宽分析、设计建议）
  - `tests/test_free_vibration.py`: 自由振动测试（固有频率/阻尼比/振动响应/对数衰减/能量）
  - `tests/test_forced_vibration.py`: 强迫振动测试（简谐/阶跃/脉冲/FRF/稳态幅值）
  - `tests/test_modal_analysis.py`: 模态分析测试（模态分析/正交性/参与系数/多自由度系统）
  - `tests/test_resonance.py`: 共振检测测试（共振频率/Q因子/带宽/峰值检测/安全裕度/设计）
  - `README.md`: 中英双语文档（含振动理论基础、公式、运行指南）
  - `requirements.txt`: 依赖定义

### 2026-06-26
- ✅ **完成 thermodynamics（热力学模拟 Python 实现）** - 从零实现热传导和热对流模拟学习项目，包含完整的有限差分法求解器、Crank-Nicolson 方法、三种边界条件、稳态/瞬态分析和可视化
  - `src/heat_conduction.py`: 热传导方程求解器（1D/2D、显式 FTCS、隐式 BTCS、Crank-Nicolson、三对角矩阵求解器 Thomas 算法）
  - `src/boundary_conditions.py`: 边界条件模块（Dirichlet/Neumann/Robin 三类边界条件、1D/2D 应用）
  - `src/heat_source.py`: 热源建模（均匀/点源/时变/温度依赖热源）
  - `src/analysis.py`: 稳态和瞬态分析（解析解、热时间常数、傅里叶数、毕渥数、热流计算）
  - `examples/example_1d_rod.py`: 一维杆热传导（温度演化、稳态验证、解析解对比）
  - `examples/example_2d_plate.py`: 二维平板温度分布（中心热源、等温线、热力图）
  - `examples/example_transient.py`: 瞬态热传递（热波传播、周期性热源、边界热流）
  - `examples/example_boundary_effects.py`: 边界条件影响对比（Dirichlet/Neumann/Robin 对比、毕渥数分析）
  - `tests/test_heat_conduction.py`: 26 个单元测试（1D/2D 求解、边界条件、热源、分析函数、三对角求解器）
  - `README.md`: 中英双语文档（含传热理论基础、傅里叶定律、无量纲数、材料参数、运行指南）
  - `requirements.txt`: 依赖定义

### 2026-06-26
- ✅ **完成 fluid-mechanics（流体力学基础 Python 实现）** - 从零实现流体力学基础学习项目，包含完整的伯努利方程求解、Darcy-Weisbach管道流动计算、Reynolds数与流动状态分类、水头损失分析和压力降计算
  - `src/bernoulli.py`: 伯努利方程求解器（压力/速度/高程求解、总水头计算、压力系数、能量分布分析）
  - `src/pipe_flow.py`: Darcy-Weisbach管道流动计算（Colebrook/Swamee-Jain摩擦系数、沿程损失、PipeSegment/PipeNetwork类）
  - `src/reynolds.py`: Reynolds数计算与流动状态分类（层流/过渡流/湍流判据、Sutherland粘度公式、流体物性库）
  - `src/head_loss.py`: 水头损失计算（沿程损失、局部损失、等效长度、HeadLossCalculator综合计算器）
  - `src/continuity.py`: 连续性方程分析（截面积/流量/流速计算、ContinuityAnalyzer分析器）
  - `src/pressure_drop.py`: 压力降分析（摩擦压降、高程压降、加速度压降、PressureDropAnalyzer分析器）
  - `examples/bernoulli_demo.py`: 伯努利方程演示（水平管道、文丘里管、高度变化、能量分布可视化）
  - `examples/pipe_network.py`: 管道网络分析（串联/并联网络、管道选型、摩擦系数对比）
  - `examples/flow_regime_viz.py`: 流动状态可视化（Reynolds数范围、流动相图、速度剖面、临界速度对比）
  - `examples/pressure_drop_calc.py`: 压力降计算（简单管道、局部损失、高程影响、长距离管道）
  - `tests/test_fluid_mechanics.py`: 单元测试（伯努利/管道流动/Reynolds数/水头损失/连续性/压力降/集成测试）
  - `README.md`: 中英双语文档（含流体力学理论基础、公式推导、运行指南）
  - `requirements.txt`: 依赖定义

### 2026-06-26
- ✅ **完成 gear-transmission（齿轮传动系统 Python 实现）** - 从零实现齿轮传动力学学习项目，包含完整的直齿轮几何、齿轮比计算、传动分析、效率评估和三种齿轮系（简单、复合、行星）
  - `src/spur_gear.py`: 直齿轮几何（分度圆/基圆/齿顶圆/齿根圆直径计算、渐开线轮廓生成、根切检测、质量估算）
  - `src/gear_ratio.py`: 齿轮比计算（单级/简单齿轮系/复合齿轮系传动比、方向变化、最优齿数组合搜索）
  - `src/transmission.py`: 扭矩与速度传递（功率计算、逐级分析、转速/扭矩/功率传递链）
  - `src/efficiency.py`: 效率分析（啮合效率模型、蜗轮蜗杆效率、功率损失分解、配置对比）
  - `src/gear_train.py`: 齿轮系分析（简单齿轮系、复合齿轮系、行星齿轮系及威利斯方程求解）
  - `src/contact_ratio.py`: 重合度计算（啮合路径、端面重合度、接触质量评估）
  - `examples/01_single_gear_pair.py`: 单级齿轮副仿真（齿轮几何、传动比、重合度、可视化）
  - `examples/02_compound_gear_train.py`: 复合齿轮系（多级传动、逐级分析、布局图）
  - `examples/03_planetary_gear_system.py`: 行星齿轮系统（6种运行模式、威利斯方程、可视化）
  - `examples/04_efficiency_comparison.py`: 效率对比（各类型效率、级数影响、蜗轮蜗杆、功率损失分解）
  - `tests/test_gear_transmission.py`: 45 个单元测试（齿轮几何/齿轮比/传动/效率/重合度/齿轮系）
  - `README.md`: 中英双语文档（含齿轮理论基础、公式、运行指南）
  - `requirements.txt`: 依赖定义

### 2026-06-26
- ✅ **完成 robot-arm-kinematics（机械臂运动学 Python 实现）** - 从零实现机械臂运动学学习项目，包含完整的 DH 参数计算、正向/逆向运动学、雅可比矩阵分析、工作空间可视化和轨迹规划
  - `src/dh_parameters.py`: DH 参数计算（标准 DH 和修正 DH）、齐次变换矩阵、所有中间变换计算
  - `src/forward_kinematics.py`: 正向运动学求解器（ForwardKinematics 类）、2R 机械臂闭式解、PUMA 560 运动学
  - `src/inverse_kinematics.py`: 逆向运动学（2R 解析 IK、数值 IK、PUMA 560 IK 框架）、旋转矩阵到轴角转换
  - `src/jacobian.py`: 雅可比矩阵计算（几何法）、Moore-Penrose 伪逆、可操作性指数、奇异条件数
  - `src/workspace.py`: 工作空间可视化（2R 环形区域、3R 圆形区域、3D 采样）、可操作性椭球、奇异分析
  - `src/mapping.py`: 关节空间到笛卡尔空间映射（线性/三次/五次多项式轨迹、SLERP 姿态插值、路径点规划）
  - `examples/01_2r_fk_ik.py`: 2R 机械臂正向/逆向运动学演示（含工作空间可视化）
  - `examples/02_3r_simulation.py`: 3R 机械臂仿真（轨迹追踪、雅可比分析）
  - `examples/03_path_planning.py`: 路径规划演示（笛卡尔直线、轨迹平滑、路径点规划）
  - `examples/04_workspace_visualization.py`: 工作空间可视化（密度分析、3D 工作空间、可操作性、奇异分析）
  - `tests/test_dh_parameters.py`: DH 参数测试（标准/修正 DH、变换矩阵、连乘一致性）
  - `tests/test_forward_kinematics.py`: 正向运动学测试（2R 闭式解、ForwardKinematics 类、姿态）
  - `tests/test_inverse_kinematics.py`: 逆向运动学测试（2R 解析 IK、数值 IK、所有解）
  - `tests/test_jacobian.py`: 雅可比矩阵测试（形状、线性/角速度部分、伪逆、可操作性、速度映射）
  - `tests/test_mapping.py`: 映射测试（线性/三次/五次轨迹、路径长度）
  - `README.md`: 中英双语文档（含 DH 参数详解、运动学公式、运行指南）

### 2026-06-26
- ✅ **完成 dht（分布式哈希表 Go 实现）** - 从零实现 Chord DHT 协议学习项目，包含完整的 ID 生成、节点管理、指纹表路由、键值存储、环稳定化和数据迁移
  - `src/id.go`: ID 生成（SHA-1/CRC32 哈希）、环距离计算、指纹表索引、一致性哈希区间判断
  - `src/node.go`: Chord 节点实现（后继/前驱指针、指纹表维护、键值存储、心跳存活检测）
  - `src/store.go`: 线程安全键值存储（Put/Get/Delete/Keys/Size/Clear/ForEach）
  - `src/ring.go`: Chord 环模拟（节点添加/移除、稳定协议、前驱修复、键查找、环完整性验证）
  - `src/simulator.go`: 高级模拟器（节点加入/离开、键迁移追踪、心跳监控、状态打印）
  - `examples/01_basic_ring.go`: 基础环演示（节点加入、环结构、指纹表）
  - `examples/02_key_lookup.go`: 键查找演示（存储、查找、数据分布）
  - `examples/03_node_join_leave.go`: 节点加入/离开演示（数据迁移、环恢复）
  - `examples/04_key_migration.go`: 键迁移演示（初始分布、中间节点、节点移除、数据完整性）
  - `tests/id_test.go`: ID 测试（NextID/PrevID/Distance/哈希/指纹表索引/区间判断）
  - `tests/node_test.go`: 节点测试（创建/指针/指纹表/存储/心跳）
  - `tests/store_test.go`: 存储测试（Put/Get/Delete/Keys/Size/Clear/Has/ForEach/覆盖）
  - `tests/ring_test.go`: 环测试（创建/添加/移除/查找/存储/检索/删除/稳定/完整性）
  - `tests/simulator_test.go`: 模拟器测试（加入/存储/检索/迁移追踪/心跳监控）
  - `README.md`: 中英双语文档（含 Chord 协议详解、架构图、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-26
- ✅ **完成 linkage-mechanism（连杆机构分析 Python 实现）** - 从零实现四连杆机构位置/速度/加速度分析学习项目，包含 Grashof 条件判断、矢量环位置分析、Freudenstein 方程、传动角计算、连杆曲线生成和完整可视化
  - `src/position_analysis.py`: 位置分析核心（Grashof条件分类、矢量环方程求解、连杆圆计算、摇杆摆动范围、连杆曲线生成）
  - `src/velocity_analysis.py`: 速度分析（角速度求解、线速度计算、传动角评估）
  - `src/acceleration_analysis.py`: 加速度分析（角加速度求解、线加速度计算）
  - `src/visualization.py`: 可视化（连杆图、连杆曲线、传动角图、相位图、加速度图、综合分析图）
  - `examples/01_fourbar_simulation.py`: 四连杆完整仿真
  - `examples/02_coupler_curves.py`: 连杆曲线可视化（曲柄摇杆/双曲柄/双摇杆/变点机构对比）
  - `examples/03_crank_rocker.py`: 曲柄摇杆机构详细分析
  - `examples/04_slider_crank.py`: 滑块曲柄机构分析
  - `tests/test_position_analysis.py`: 位置分析测试（Grashof/分类/位置/连杆圆/连杆曲线/摇杆范围）
  - `tests/test_velocity_analysis.py`: 速度分析测试（角速度/线速度/传动角）
  - `tests/test_acceleration_analysis.py`: 加速度分析测试（角加速度/线加速度/单位缩放）
  - `tests/test_visualization.py`: 可视化测试（各绘图函数）
  - `README.md`: 中英双语文档（含连杆理论、Grashof条件、矢量环法、运行指南）
  - `requirements.txt`: 依赖定义

### 2026-06-26
- ✅ **完成 raft-consensus（Raft 共识算法 Go 实现）** - 从零实现 Raft 共识算法学习项目，包含完整的领导者选举、日志复制、安全性验证和集群成员管理
  - `src/raft.go`: 核心类型定义（StateRole、Follower/Candidate/Leader 状态、LogEntry、ClientRequest、StateMachine）
  - `src/node.go`: 节点管理（StartNode、run 事件循环、Shutdown、SubmitRequest、状态转换）
  - `src/election.go`: 领导者选举（随机超时、投票机制、选举限制、心跳发送、AppendEntries）
  - `src/log_replication.go`: 日志复制（AppendEntries RPC、matchIndex/nextIndex 跟踪、提交索引计算、日志一致性检查）
  - `src/safety.go`: 安全性验证（选举限制、日志匹配、状态机安全、集群安全验证）
  - `src/cluster.go`: 集群管理（成员变更、联合共识、多数计算）
  - `examples/leader_election.go`: 领导者选举演示
  - `examples/log_replication.go`: 日志复制演示
  - `examples/log_consistency.go`: 日志一致性演示（含故障恢复）
  - `examples/cluster_demo.go`: 完整集群演示（选举+复制+一致性+成员变更）
  - `tests/raft_test.go`: 20 个单元测试（选举/日志复制/一致性/安全性/集群管理）
  - `README.md`: 中英双语文档（含 Raft 算法详解、架构图、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-26
- ✅ **完成 distributed-lock（分布式锁 Go 实现）** - 从零实现分布式锁学习项目，包含完整的 Redis/ZooKeeper/etcd 多后端支持、基础锁、可重入锁、公平锁、读写锁、Redlock 算法、Watchdog 自动续期和完整测试
  - `internal/lock/lock.go`: 核心接口定义（Lock、ReentrantLock、ReadWriteLock、FairLock）、功能选项模式、Config 配置
  - `internal/redis/lock.go`: Redis 单节点分布式锁（SET NX PX 模式）、原子 Lua 脚本（获取/释放/续期）、重试机制
  - `internal/redis/redlock.go`: Redlock 多节点算法（quorum 机制、有效性时间计算、容错释放）
  - `internal/redis/watchdog.go`: Watchdog 自动续期器（TTL/3 间隔续期、goroutine 管理、安全停止）
  - `internal/redis/reentrant.go`: 可重入锁（原子计数、同一 owner 多次获取、递减释放）
  - `internal/redis/fair.go`: 公平锁（Redis List FIFO 队列、顺序获取、位置查询）
  - `internal/redis/rwlock.go`: 读写锁（多读单写、原子 Lua 脚本、读写计数）
  - `internal/zookeeper/lock.go`: ZooKeeper 分布式锁（临时顺序节点、Watch 机制、FIFO 语义）
  - `internal/etcd/lock.go`: etcd 分布式锁（Lease 机制、事务获取、KeepAlive 续期）
  - `pkg/utils/id.go`: ID 生成工具
  - `cmd/demo/main.go`: 综合演示程序
  - `examples/main.go`: 基础使用示例
  - `examples/example_test.go`: 示例测试
  - `examples/task_scheduler.go`: 分布式任务调度器示例
  - `examples/inventory.go`: 库存管理示例
  - `examples/ratelimiter.go`: 限流器示例
  - `tests/lock_test.go`: 锁功能测试
  - `tests/redlock_test.go`: Redlock 测试
  - `tests/watchdog_test.go`: Watchdog 测试
  - `docs/01-RESEARCH.md`: 分布式锁理论研究
  - `docs/02-DESIGN.md`: 架构设计文档
  - `docs/03-IMPLEMENTATION.md`: 实现细节文档
  - `docs/04-TESTING.md`: 测试策略文档
  - `docs/05-DEVELOPMENT.md`: 开发指南
  - `README.md`: 中英双语文档（含架构图、算法详解、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-26
- ✅ **完成 dns-server（DNS 服务器 Go 实现）** - 从零实现 DNS 服务器学习项目，包含完整的 DNS 协议编解码、域名压缩、资源记录类型、DNS 缓存、区域文件解析和递归查询解析
  - `src/packet.go`: DNS 数据包格式（Header、Question、ResourceRecord）、消息编解码、域名压缩、记录类型（A/AAAA/CNAME/MX/TXT/NS/SOA/PTR）、缓存实现
  - `src/zone.go`: 区域文件解析器（SOA/NS/A/AAAA/CNAME/MX/TXT/PTR 记录类型）、通配符查找、TTL 后缀解析、多行记录合并
  - `src/resolver.go`: 递归解析器（缓存检查→区域查找→CNAME 链→上游转发）、DNS 转发器、查询处理
  - `src/server.go`: DNS 服务器实现（UDP 监听、查询处理循环、配置管理）
  - `examples/01_query_response.go`: DNS 查询和响应演示（线格式、十六进制转储、编解码往返）
  - `examples/02_caching.go`: 缓存演示（TTL 过期、LRU 驱逐、缓存统计）
  - `examples/03_zone_file.go`: 区域文件加载演示（SOA/NS/A/AAAA/CNAME/MX/TXT 解析、查找）
  - `examples/04_recursive_resolution.go`: 递归解析演示（A/AAAA/MX/CNAME/TXT/NS 解析、NXDOMAIN、缓存行为）
  - `tests/packet_test.go`: 数据包测试（类型字符串、标头标志、编解码往返、域名压缩、缓存操作）
  - `tests/zone_test.go`: 区域文件测试（SOA/NS/A/AAAA/CNAME/MX/TXT/PTR 解析、TTL 解析、查找、通配符）
  - `tests/resolver_test.go`: 解析器测试（基本解析、缓存、NXDOMAIN、CNAME、MX、NS 解析、查询处理）
  - `README.md`: 中英双语文档（含 DNS 协议详解、架构图、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-26
- ✅ **完成 distributed-transaction（分布式事务 Go 实现）** - 从零实现分布式事务学习项目，包含完整的 2PC、3PC、Saga、TCC 四种协议实现，多个演示程序和完整测试
  - `coordinator/coordinator.go`: 2PC 协调者（ExecuteTransaction、PreparePhase、CommitPhase、AbortPhase、超时处理、并发安全）
  - `coordinator/three_phase.go`: 3PC 协调者（CanCommitPhase、PreCommitPhase、DoCommitPhase、AbortAll、超时处理）
  - `participant/participant.go`: 参与者 Cohort 接口和 DefaultCohort 实现（Prepare/Commit/Abort、状态机、错误模拟、延迟模拟）
  - `transaction/transaction.go`: 事务模型（TxState 状态枚举、SetData/GetData、线程安全状态管理）
  - `saga/saga.go`: 编排式 Saga（Step/Saga 类型、Execute 正向执行+逆序补偿、状态管理）
  - `saga/choreography.go`: 协调式 Saga（ChoreographySaga、EventBus 事件总线、参与者事件驱动）
  - `tcc/tcc.go`: TCC 事务（TCCTransaction、TCCParticipant、Try/Confirm/Cancel 三阶段、cancelAll 补偿）
  - `pkg/utils/logger.go`: 日志工具（LogLevel、Logger、Debug/Info/Warn/Error）
  - `cmd/main.go`: 命令行入口（2PC/3PC/Saga/TCC 演示、失败场景模拟）
  - `examples/order/main.go`: 订单系统示例（库存/订单/支付服务，四种模式对比）
  - `examples/transfer/main.go`: 转账系统示例（Saga/TCC 转账对比）
  - `tests/coordinator_test.go`: 2PC 协调者测试（11 个测试用例：创建/注册/执行/并发/超时）
  - `tests/three_phase_test.go`: 3PC 协调者测试（9 个测试用例：创建/注册/执行/并发/2PC vs 3PC 对比）
  - `tests/participant_test.go`: 参与者测试（8 个测试用例：Prepare/Commit/Abort/状态/接口实现）
  - `tests/transaction_test.go`: 事务测试（6 个测试用例：创建/状态/并发/数据）
  - `tests/saga_test.go`: Saga 测试（9 个测试用例：编排/协调式/补偿/数据流）
  - `tests/tcc_test.go`: TCC 测试（8 个测试用例：Try/Confirm/Cancel/数据流/状态）
  - `README.md`: 中英双语文档（含架构图、2PC vs 3PC 对比、核心接口）
  - `go.mod`: Go 模块定义

### 2026-06-26
- ✅ **完成 monitoring-alert（监控告警系统 Go 实现）** - 从零实现监控告警系统学习项目，包含完整的指标采集、时序数据存储、查询聚合、告警规则引擎、异常检测和仪表盘数据提供
  - `src/aggregation/aggregation.go`: 聚合函数库（avg/sum/min/max/count/stddev/median/percentile/rate/delta/last/first，多指标聚合，按标签分组聚合）
  - `src/anomaly/anomaly.go`: 异常检测器（静态阈值、动态阈值、Z-Score、IQR、EWMA 五种检测算法）
  - `src/dashboard/dashboard.go`: 仪表盘数据提供者（时序图/仪表盘/统计值/柱状图/热力图面板类型）
  - `src/filter/filter.go`: 指标过滤器（名称/标签/时间范围/值范围过滤，标签匹配器，复合过滤器）
  - `src/alert/engine.go`: 阈值告警引擎（表达式解析、阈值比较、规则评估、告警管理、通知协调）
  - `src/alert/trend.go`: 趋势告警引擎（增长/下降/尖峰趋势检测）
  - `src/alert/composite.go`: 组合告警引擎（AND/OR 多条件组合）
  - `src/notifier/notifier.go`: 通知器（控制台/Webhook/多通道/节流通知）
  - `internal/model/metric.go`: 指标模型（Counter/Gauge/Histogram 类型，时序数据点）
  - `internal/model/alert.go`: 告警模型（严重级别、状态管理、告警规则）
  - `internal/collector/collector.go`: 指标采集器（系统指标/自定义采集器/采集器管理器）
  - `internal/storage/tsdb.go`: 内存时序数据库（写入/读取/查询/删除/保留策略/查询引擎）
  - `examples/metrics_collection/main.go`: 指标采集演示（系统指标、自定义指标、多轮采集）
  - `examples/time_series_query/main.go`: 时序存储与查询演示（写入/查询/聚合/分组）
  - `examples/alert_rules/main.go`: 告警规则配置与触发演示（阈值/趋势/异常检测/通知）
  - `examples/dashboard_data/main.go`: 仪表盘数据演示（面板创建/数据获取/聚合展示）
  - `tests/model_test.go`: 模型测试（指标/时序/告警/规则）
  - `tests/collector_test.go`: 采集器测试（系统/自定义/管理器/并发）
  - `tests/storage_test.go`: 存储测试（写入/读取/查询/删除/保留策略）
  - `tests/alert_test.go`: 告警引擎测试（阈值/多规则/告警管理/节流/摘要）
  - `tests/trend_test.go`: 趋势测试（增长/下降/尖峰/数学边界/精度）
  - `tests/composite_test.go`: 组合告警测试（AND/OR/复杂组合/并发）
  - `tests/notifier_test.go`: 通知器测试（控制台/Webhook/多通道/节流）
  - `README.md`: 中英双语文档（含架构图、核心概念、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 service-discovery（服务发现 Go 实现）** - 从零实现服务发现学习项目，包含完整的服务注册、健康检查、服务发现、负载均衡和分布式 KV 存储
  - `src/types.go`: 核心类型（ServiceInstance、HealthCheckConfig、LoadBalancerType、ConsulKVEntry、ConsulKVStore、DiscoveryCache）
  - `src/registry.go`: 服务注册中心（ServiceRegistry、注册/注销、TTL 过期、健康状态更新、实例查找）
  - `src/healthcheck.go`: 健康检查器（TCP/HTTP/自定义健康检查、后台检查循环、故障检测）
  - `src/loadbalancer.go`: 负载均衡器（轮询/加权/最少连接/随机算法、连接追踪）
  - `src/broker.go`: 服务协调器（ServiceBroker、注册/发现/缓存、KV 同步、过期清理）
  - `src/main.go`: 入口程序
  - `examples/register_discover.go`: 服务注册与发现演示（多实例注册、服务查询、负载均衡获取）
  - `examples/health_check.go`: 健康检查演示（TCP/HTTP/自定义检查、故障与恢复检测）
  - `examples/load_balance.go`: 负载均衡演示（四种算法对比、权重分配、连接追踪）
  - `examples/failure_recovery.go`: 服务故障与恢复演示（注册/故障/检测/恢复/注销完整生命周期）
  - `tests/registry_test.go`: 注册中心测试（实例操作/验证/健康更新/TTL 过期/服务列表）
  - `tests/loadbalancer_test.go`: 负载均衡测试（轮询/加权/最少连接/随机/空实例/策略切换/连接追踪）
  - `tests/kv_store_test.go`: KV 存储测试（Put/Get/Delete/List/CAS/Flags/TTL/缓存）
  - `README.md`: 中英双语文档（含架构图、核心概念、算法详解、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 circuit-breaker（熔断降级 Go 实现）** - 从零实现熔断器模式学习项目，包含完整的三态状态机、降级策略、限流器、重试机制和舱壁模式
  - `src/circuit_breaker.go`: 熔断器核心（Config、CircuitBreaker、Execute、状态转换、失败率/连续失败触发、半开状态限制请求数）
  - `src/states.go`: 三态定义（Closed/Open/HalfOpen）+ String/IsValid/CanExecute 方法
  - `src/metrics.go`: 指标统计（总请求/成功/失败计数、连续成功/失败、失败率计算）
  - `src/fallback.go`: 四种降级策略（DefaultFallback、CacheFallback、StaticFallback、CompositeFallback）
  - `src/retry.go`: 重试器（指数退避、抖动、可重试判断、RetryResult、RetryableCircuitBreaker）
  - `src/ratelimiter.go`: 三种限流器（FixedWindowLimiter、SlidingWindowLimiter、TokenBucketLimiter）
  - `src/bulkhead.go`: 舱壁模式（Bulkhead、BulkheadPool、BulkheadCircuitBreaker）
  - `examples/main.go`: 基础示例（基本使用、降级策略、真实场景模拟、限流器、重试机制）
  - `examples/api_gateway.go`: API 网关示例（服务端点封装、路由、熔断+限流+重试组合、微服务调用）
  - `examples/failure_simulation.go`: 故障模拟演示（状态机演进、波动失败率）
  - `examples/fallback_demo.go`: 降级策略演示（静态/缓存/组合/自定义降级对比）
  - `examples/bulkhead_demo.go`: 舱壁模式演示（基本舱壁、舱壁池、舱壁+熔断组合、资源隔离）
  - `tests/circuit_breaker_test.go`: 熔断器测试（Closed状态、失败阈值、超时转换、半开恢复/回退、降级、重置、失败率）
  - `tests/states_test.go`: 状态测试（String/IsValid/CanExecute）
  - `tests/metrics_test.go`: 指标测试（成功/失败记录、失败率、连续计数器、重置）
  - `tests/retry_test.go`: 重试测试（首次成功/重试后成功/超限、可重试判断、指数退避、最大间隔、零重试、总耗时、带熔断重试）
  - `tests/ratelimiter_test.go`: 限流器测试（固定窗口/滑动窗口/令牌桶的Allow/AllowN/GetAvailable/窗口重置/并发安全）
  - `tests/bulkhead_test.go`: 舱壁测试（TryAcquire/Release/并发/Close/GetStats、舱壁池CRUD、舱壁+熔断组合、半开限制请求数）
  - `README.md`: 中英双语文档（含熔断原理、状态机、降级策略、限流算法、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 cicd-pipeline（CI/CD 流水线 Go 实现）** - 从零实现 CI/CD 流水线框架，包含完整的流水线定义、阶段编排、触发器、制品管理和 Webhook 处理
  - `pipeline/pipeline.go`: 核心类型（Pipeline、Stage、Step、Trigger、Context、PipelineResult、ArtifactManager、WebhookHandler、Runner、BuildConfig、TestConfig、DeployConfig、ParallelExecutor 等）
  - `examples/basic_pipeline.go`: 基础流水线演示（单阶段、顺序步骤）
  - `examples/multi_stage.go`: 多阶段流水线（build → test → deploy-staging → deploy-production）
  - `examples/parallel_test.go`: 并行测试执行（unit/integration/e2e/lint 并行）
  - `examples/deployment.go`: 部署流水线（制品管理、Webhook 通知、滚动/蓝绿部署）
  - `tests/pipeline_test.go`: 45 个单元测试（流水线/阶段/步骤/触发器/制品/部署/并行/Webhook/运行器）
  - `README.md`: 中英双语文档（含架构图、CI/CD 概念详解、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 stream-processing（流式计算框架 Go 实现）** - 从零实现流式计算框架学习项目，包含完整的窗口聚合、状态管理、水位线和迟到数据处理
  - `src/stream.go`: 核心类型（Event、Window、WindowAssigner、Aggregator、Watermark、StateManager、Trigger、Source/Sink 接口）
  - `src/windowed_stream.go`: WindowedStream 高级 API（窗口处理循环、迟到事件策略、描述性统计）
  - `src/session_window.go`: SessionWindow 和 SessionManager（动态会话窗口管理、过期关闭）
  - `examples/word_count.go`: 经典流式词频统计
  - `examples/sliding_window.go`: 滑动窗口温度聚合
  - `examples/session_window.go`: 会话窗口用户行为分析
  - `examples/late_event_handling.go`: 水位线演进和迟到事件策略演示
  - `tests/stream_test.go`: 33 个单元测试（事件/窗口/分配器/聚合器/水位线/状态/触发器/会话窗口/流处理）
  - `README.md`: 中英双语文档（含架构图、核心概念、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 bloom-filter（布隆过滤器 Go 实现）** - 从零实现布隆过滤器学习项目，包含标准布隆过滤器、计数布隆过滤器、参数计算和合并功能
  - `src/bloomfilter.go`: 核心实现（BloomFilter 标准布隆过滤器、CountingBloomFilter 计数布隆过滤器、Kirsch-Mitzenmacher 双哈希、参数计算、合并操作）
  - `examples/main.go`: 综合演示（基本用法、误判率演示、最优参数计算、计数布隆过滤器）
  - `examples/false_positive_rate.go`: 误判率演示（不同 FP 率对比、不同填充率对比、填充演化）
  - `examples/optimal_size.go`: 最优参数计算器（多场景计算、FP 率与内存关系、数学公式验证）
  - `examples/counting_bloom.go`: 计数布隆过滤器演示（插入/删除、重复处理、压力测试）
  - `tests/bloomfilter_test.go`: 34 个单元测试（基本操作/最优参数/重置/合并/误判率/并发/边界情况）
  - `README.md`: 中英双语文档（含数学公式、算法原理、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 mvcc（MVCC 并发控制 Go 实现）** - 从零实现多版本并发控制学习项目，包含完整的版本管理、快照隔离、冲突检测、垃圾回收和 SSI
  - `src/mvcc.go`: 核心 MVCC 引擎（MVCCStorage、Transaction、SnapshotManager、ConflictDetector、GarbageCollector、TransactionManager）
  - `src/demos.go`: 6 个综合演示（基本操作/快照隔离/冲突检测/垃圾回收/死锁检测/SSI）
  - `src/demo_utils.go`: 演示工具函数
  - `examples/basic_mvcc.go`: 基本 MVCC 操作演示（事务/快照读/写入提交/版本链）
  - `examples/snapshot_isolation.go`: 快照隔离演示（一致视图/并发读/脏读防护/不可重复读防护）
  - `examples/conflict_detection.go`: 冲突检测演示（写-写/读-写/写偏斜/无冲突场景）
  - `examples/garbage_collection.go`: 垃圾回收演示（版本链增长/GC 安全/快照保护）
  - `tests/mvcc_test.go`: 核心功能测试（事务/版本链/时间戳/回滚）
  - `tests/conflict_test.go`: 冲突检测测试（写-写/读-写/等待图/死锁）
  - `tests/gc_test.go`: 垃圾回收测试（有/无快照/GC 统计/多键）
  - `tests/snapshot_test.go`: 快照管理测试（事务生命周期/快照隔离/时间戳）
  - `README.md`: 中英双语文档（含 MVCC 理论、架构图、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 query-parser（查询解析器 Go 实现）** - 从零实现搜索查询解析器，包含完整的递归下降解析器、布尔查询、短语查询、模糊匹配、通配符和范围查询
  - `src/types.go`: 类型定义（Token、TokenType、QueryNode、QueryNodeType、BooleanOperator、QueryTree、QueryStats）
  - `src/tokenizer.go`: 词法分析器（词元化、TokenStream 游标、布尔运算符识别、短语边界处理）
  - `src/parser.go`: 递归下降解析器（OR/AND/NOT 优先级、短语/范围/模糊/通配符/Boost 语法）
  - `src/normalize.go`: 查询规范化（去停用词、小写化、空格折叠、树规范化、ASCII 树可视化）
  - `src/executors.go`: 执行引擎（Levenshtein 距离模糊匹配、通配符 * / ? 匹配、范围查询、相关性评分、文档评分）
  - `examples/boolean_query.go`: 布尔查询解析演示（AND/OR/NOT 及优先级）
  - `examples/phrase_query.go`: 短语查询演示（精确短语匹配与文档匹配）
  - `examples/fuzzy_query.go`: 模糊查询演示（Levenshtein 距离计算与匹配评分）
  - `examples/query_tree.go`: 查询树可视化（AST 树形结构展示）
  - `examples/query_execution.go`: 查询执行演示（模拟文档库上的查询执行与排序）
  - `tests/queryparser_test.go`: 完整单元测试（词法分析/解析/规范化/模糊匹配/通配符/范围查询/相关性评分/TokenStream）
  - `README.md`: 中英双语文档（含查询语言语法、运算符优先级、运行指南）
  - `go.mod`: Go 模块定义

### 2026-06-25
- ✅ **完成 pagerank（PageRank 网页排序算法 Python 实现）** - 从零实现 PageRank 算法学习项目，包含完整的幂迭代求解器、阻尼因子处理、个性化 PageRank、HITS 算法及稀疏矩阵优化
  - `src/graph.py`: 图表示（Graph 类、邻接矩阵/邻接表双存储、转移矩阵构建、悬垂节点处理、示例图/随机图/无标度图生成器）
  - `src/pagerank.py`: PageRank 核心算法（幂迭代法、阻尼因子、收敛检测、稀疏矩阵加速、个性化 PageRank、批量计算、收敛迭代次数估算）
  - `src/sparse_utils.py`: 稀疏矩阵工具（内存分析、格式转换、稀疏度计算）
  - `src/hits.py`: HITS 算法（Hub/Authority 值计算、子图 HITS）
  - `examples/simple_pagerank.py`: 简单网页图 PageRank + HITS 对比
  - `examples/large_scale.py`: 大规模图模拟（100~5000 节点基准测试）
  - `examples/personalized_pagerank.py`: 个性化 PageRank 演示（不同种子节点/阻尼因子影响）
  - `examples/convergence_viz.py`: 收敛可视化（收敛曲线、分数柱状图、算法对比图）
  - `tests/test_pagerank.py`: 34 个单元测试全部通过（图操作/PageRank 计算/个性化 PageRank/HITS/稀疏工具/边界情况）
  - `README.md`: 中英双语文档（含 PageRank 公式推导、算法原理、运行指南）
  - `requirements.txt`: 依赖（numpy, matplotlib）

### 2026-06-25
- ✅ **完成 linear-programming（线性规划求解器 Python 实现）** - 从零实现单纯形法线性规划求解器，包含完整的标准形转换、两阶段法、大M法、对偶问题求解、灵敏度分析和解分析模块
  - `src/problem.py`: 问题建模（LPProblem 数据类、create_problem/minimize/maximize 工厂函数、文本格式化）
  - `src/standard_form.py`: 标准形转换（StandardFormConverter、松弛/剩余变量添加、增广矩阵构造）
  - `src/simplex.py`: 单纯形算法（SimplexSolver、单纯形表、检验数、进基/出基变量选择、主元运算、两阶段法）
  - `src/big_m.py`: 大M法求解器（BigMSolver、人工变量惩罚、无界解检测）
  - `src/dual.py`: 对偶问题求解（DualSolver、对偶构造、影子价格、互补松弛验证）
  - `src/sensitivity.py`: 灵敏度分析（SensitivityAnalyzer、目标系数范围、RHS范围、100%规则）
  - `src/analysis.py`: 解分析（SolutionAnalyzer、无界解检测、多重最优解检测、替代最优解查找）
  - `examples/01_production_planning.py`: 生产计划问题（最大化利润、影子价格、灵敏度分析）
  - `examples/02_diet_problem.py`: 饮食问题（最小化成本、大M法求解）
  - `examples/03_transportation.py`: 运输问题（供需平衡、最优运输方案）
  - `examples/04_graphical_method.py`: 图解法可视化（matplotlib 可行域、最优解标记）
  - `examples/05_sensitivity_analysis.py`: 灵敏度分析演示（影子价格、100%规则、实际变化演示）
  - `tests/test_linear_programming.py`: 完整单元测试（问题建模/标准形/单纯形/大M法/对偶/灵敏度/解分析/边界情况）
  - `README.md`: 中英双语文档（含单纯形法逐步详解、算法对比表、数学符号说明）
  - `requirements.txt`: 依赖（numpy）

### 2026-06-25
- ✅ **完成 hyperloglog（HyperLogLog 基数估计 Go 实现）** - 从零实现 HyperLogLog 基数估计算法，包含完整的桶分配、前导零统计、调和平均数计算、偏差校正、精度调优及可视化功能
  - `src/hyperloglog.go`: HyperLogLog 核心算法（哈希、桶索引提取、rho 计算、调和平均数、范围校正、合并操作、置信区间）
  - `src/visualize.go`: 可视化工具（sketch 信息打印、寄存器分布直方图、置信区间格式化输出）
  - `examples/basic_demo.go`: 基础基数估计演示（唯一元素计数、重复元素处理、随机字符串测试）
  - `examples/accuracy_comparison.go`: 不同精度值（p=4~16）的准确性对比
  - `examples/memory_comparison.go`: HyperLogLog vs 精确计数的内存使用对比
  - `examples/stress_test.go`: 压力测试（缩放性、合并准确性、精度敏感性、大规模性能）
  - `tests/hyperloglog_test.go`: 完整单元测试（初始化、添加元素、重复处理、克隆/合并、精度计算、置信区间）
  - `README.md`: 中英双语文档（含算法详解、数学基础、精度-内存权衡表、运行指南）

### 2026-06-25
- ✅ **完成 genetic-algorithm（遗传算法优化框架 Python 实现）** - 从零实现遗传算法优化框架，包含完整的个体/种群管理、4种选择方法、6种交叉算子、6种变异算子、4种收敛检测、世代/稳态两种进化模式
  - `src/individual.py`: 个体类（基因/适应度管理、深拷贝、排序/哈希支持）+ 种群类（评估、统计、多样性分析）
  - `src/selection.py`: 4种选择方法（锦标赛/轮盘赌/排名/精英保留）+ 工厂函数
  - `src/crossover.py`: 6种交叉算子（单点/多点/均匀/算术/BLX-alpha/顺序OX）+ 工厂函数
  - `src/mutation.py`: 6种变异算子（位翻转/交换/逆序/高斯/边界/均匀）+ 工厂函数
  - `src/convergence.py`: 4种收敛检测（多样性/适应度增益/组合/固定代数）+ 工厂函数
  - `src/config.py`: GA参数配置类（种群大小/交叉率/变异率/选择方法等）
  - `src/core.py`: 核心引擎（世代模式+稳态模式进化循环、优化主流程）
  - `src/suites.py`: 标准测试函数库（Sphere/Rosenbrock/Rastrigin/Ackley/Griewank）+ 便捷工厂函数
  - `examples/function_optimization.py`: 4个经典函数优化演示
  - `examples/tsp_solver.py`: TSP旅行商问题求解（OX交叉+逆序变异）
  - `examples/knapsack_problem.py`: 0/1背包问题求解（二进制编码+罚函数法）
  - `examples/visualization.py`: 适应度进化曲线/选择方法对比/多样性可视化
  - `tests/`: 完整单元测试（个体/种群/选择/交叉/变异/收敛/配置/核心引擎）
  - `README.md`: 中英双语文档（含GA理论背景、算子详解、使用示例、FAQ）

### 2026-06-25
- ✅ **完成 particle-swarm（粒子群优化算法 Python 实现）** - 从零实现粒子群优化算法库，包含标准 PSO、自适应 PSO、混沌 PSO 变体及神经网络训练、特征选择等应用
  - `src/particle.py`: 粒子类（位置/速度管理、个体最佳、适应度评估、速度更新公式、边界约束）
  - `src/swarm.py`: 标准 PSO（Swarm 类、PSOConfig 配置、线性递减/自适应惯性权重、收敛检测、轨迹追踪）
  - `src/adaptive_pso.py`: 自适应 PSO（种群多样性计算、收敛速率估计、动态参数调整 w/c1/c2）
  - `src/chaos_pso.py`: 混沌 PSO（Logistic/Tent/Sinusoidal 混沌映射、混沌初始化、混沌扰动速度更新）
  - `src/functions.py`: 5 个基准测试函数（Sphere/Rosenbrock/Rastrigin/Ackley/Griewank）+ 注册表
  - `src/visualizer.py`: 可视化工具（收敛曲线、2D 搜索空间、粒子轨迹、多函数/多参数对比）
  - `src/neural_network.py`: PSO 训练神经网络（前向传播、权重优化、XOR/螺旋数据集、MSE/交叉熵损失）
  - `src/feature_selection.py`: 二进制 PSO 特征选择（Sigmoid 转换、特征数量约束、交叉验证评估）
  - `examples/`: 7 个示例脚本（基础 PSO、多函数优化、参数调优、自适应/混沌 PSO、神经网络训练、特征选择）
  - `tests/`: 89 个单元测试（粒子/粒子群/自适应/混沌/测试函数/神经网络/特征选择）
  - `README.md`: 中英双语文档（含 PSO 理论、速度更新公式、惯性权重策略、测试函数详解、使用示例）

### 2026-06-25
- ✅ **完成 bayesian-optimization（贝叶斯优化 Python 实现）** - 从零实现贝叶斯优化学习框架，包含完整的高斯过程回归、三种采集函数和 BO 优化循环
  - `src/kernel.py`: 核函数库（RBF 平方指数核、Matern 核 nu=0.5/1.5/2.5、组合核 sum/product）+ 协方差矩阵计算与 Cholesky 分解
  - `src/gaussian_process.py`: 高斯过程回归（Cholesky 分解推理、预测均值/方差、函数采样、边际似然计算、增量更新）
  - `src/acquisition.py`: 三种采集函数（Expected Improvement 与探索利用平衡、Upper Confidence Bound 理论保证、Probability of Improvement 最基础）
  - `src/optimization.py`: 超参数优化（多起点 L-BFGS-B、Latin Hypercube 采样、边际似然最大化、采集函数最大化）
  - `src/noise_model.py`: 噪声建模（同方差不确定性、异方差扩展、自适应噪声估计）
  - `src/benchmarks.py`: 基准测试函数库（Branin 3最小值、Hartmann d维、Booth、Rastrigin、Ackley）+ 工厂函数
  - `src/bo_loop.py`: BO 主循环（LHS 初始化、GP 建模、EI/UCB/PI 采集、多起点优化、轨迹追踪）
  - `examples/optimize_branin.py`: Branin 2D 优化 + 3 面板可视化（函数/GP 均值/GP 方差）+ 收敛曲线
  - `examples/optimize_hartmann.py`: Hartmann 6D 优化 + 三种采集函数对比收敛图
  - `examples/compare_acquisitions.py`: EI vs UCB vs PI 多基准对比
  - `examples/hparam_tuning.py`: 神经网络超参数调优（学习率/宽度/正则化）
  - `examples/visualize_bo.py`: 1D BO 过程逐步可视化（GP 演化/不确定性/采集函数）
  - `tests/`: 6 个测试文件（核函数/GP/采集函数/基准/噪声/优化）共 80+ 单元测试
  - `README.md`: 中英双语文档（含 GP 理论、核函数详解、采集函数公式、基准函数表、使用示例）

### 2026-06-25
- ✅ **完成 convex-optimization（凸优化求解器 Python 实现）** - 从零实现凸优化求解器，包含完整的凸性检测、梯度下降、牛顿法、内点法、拉格朗日乘子法、KKT 条件求解器和阻尼线搜索模块
  - `src/convexity_checker.py`: 凸性检测工具（Hessian 数值计算、PSD/PD 检查、Jensen 不等式验证、常见凸函数）
  - `src/gradient_descent.py`: 梯度下降变体（标准 GD、动量 GD、AdaGrad）
  - `src/newton_method.py`: 牛顿法优化器（标准牛顿法、阻尼牛顿法、Newton 减量）
  - `src/interior_point.py`: 内点法（原对偶内点法、障碍函数法、对数障碍）
  - `src/lagrangian.py`: 拉格朗日乘子法（标准拉格朗日、增广拉格朗日、ADMM）
  - `src/kkt_solver.py`: KKT 条件求解器（KKT 验证、原对偶牛顿法、活跃集法）
  - `src/line_search.py`: 阻尼线搜索（回溯线搜索、Wolfe 条件、Zoom 阶段）
  - `src/convergence.py`: 收敛检测器（梯度/步长/函数值收敛、收敛速率分析）
  - `examples/01_linear_programming.py`: 线性规划（内点法求解 LP）
  - `examples/02_quadratic_programming.py`: 二次规划（QP 问题求解）
  - `examples/03_svm_convex.py`: SVM 作为凸优化（对偶问题求解、线性/RBF 核）
  - `examples/04_portfolio_optimization.py`: 投资组合优化（Markowitz 有效前沿）
  - `examples/05_visualization.py`: 优化过程可视化（Rosenbrock 函数、方法对比）
  - `tests/`: 8 个测试文件（凸性/梯度下降/牛顿法/内点法/拉格朗日/KKT/线搜索/收敛）
  - `README.md`: 中英双语文档（含凸优化理论基础、KKT 条件详解、算法对比表）

### 2026-06-25
- ✅ **完成 simulated-annealing（模拟退火优化算法 Python 实现）** - 从零实现模拟退火优化算法库，包含完整的温度调度、接受准则、邻域搜索和收敛检测模块
  - `src/core.py`: 核心 SA 算法（SimulatedAnnealing 类、SAResult 数据类、完整优化循环）
  - `src/temperature.py`: 4 种温度调度器（指数/线性/对数/自适应冷却）
  - `src/acceptance.py`: Metropolis 准则 + Boltzmann 概率计算
  - `src/neighborhood.py`: 6 种邻域策略（swap/insert/reverse/multi_switch/continuous/adaptive）
  - `src/cooling.py`: 冷却方案管理（指数/线性/自适应冷却 + 工厂函数）
  - `src/convergence.py`: 收敛检测器（能量/接受率/连续未改进检测 + 早停）
  - `src/restart.py`: 重启机制（RestartManager + DiversificationRestart）
  - `examples/tsp_solver.py`: TSP 求解器（3 种邻域策略对比）
  - `examples/function_optimization.py`: 4 个测试函数优化（Sphere/Rastrigin/Rosenbrock/Ackley）
  - `examples/visualization.py`: 2D 函数可视化 + 搜索轨迹 + 动画
  - `examples/sa_vs_ga.py`: SA vs GA 对比测试（3 个函数，10 次运行统计）
  - `tests/`: 50+ 个单元测试（核心/温度/接受/邻域/冷却/收敛/重启/集成）
  - `README.md`: 中英双语文档（含 SA 理论、数学公式、使用示例）

### 2026-06-25
- ✅ **完成 mapreduce（分布式 MapReduce Go 实现）** - 从零实现分布式 MapReduce 框架，包含完整的 Master-Worker 模型、Shuffle 机制和容错设计
  - `src/mr.go`: 核心框架（Master、Worker、Task 调度、MapFunc/ReduceFunc 类型定义、分区函数、哈希函数）
  - `src/io.go`: 文件 I/O（输入分片读取、中间文件管理、分区写入、输出写入、键排序）
  - `examples/word_count.go`: 词频统计（经典 MapReduce 示例）
  - `examples/distributed_sort.go`: 分布式排序（外部排序模式）
  - `examples/log_analysis.go`: 日志分析（多键输出、HTTP 日志解析）
  - `examples/multi_stage_pipeline.go`: 多阶段流水线（链式 MapReduce 作业）
  - `tests/mr_test.go`: 12 个单元测试（Master 创建、词频统计、哈希一致性、分区器、任务状态、Worker 管理等）
  - `README.md`: 中英双语文档（含架构图、执行流程、设计决策）

### 2026-06-25
- ✅ **完成 vector-db（向量数据库 Python 实现）** - 从零实现向量数据库，支持近似最近邻搜索，包含三种索引算法
  - `src/metrics.py`: 3 种相似度度量（Euclidean、Cosine、Dot Product）+ 批量计算
  - `src/brute_force.py`: 暴力 KNN 搜索（精确基准）
  - `src/lsh.py`: 局部敏感哈希 LSH（随机投影，近似搜索）
  - `src/kdtree.py`: KD-Tree 精确搜索（支持范围查询）
  - `src/vector_store.py`: 高层向量存储接口（统一三种索引策略）
  - `examples/`: 4 个演示脚本（基本操作、LSH vs 暴力对比、KD-Tree 搜索、图像相似度）
  - `tests/`: 56 个单元测试全部通过
  - `README.md`: 中英双语文档（含 ANN 算法详解、数学公式推导）

### 2026-06-25
- ✅ **完成 distributed-cache（分布式缓存系统 Go 实现）** - 从零实现高并发分布式缓存系统，包含一致性哈希、多种淘汰策略和集群支持
  - `src/cache.go`: 内存缓存核心（LRU/LFU/TTL 三种淘汰策略、热键检测、缓存预热、并发安全）
  - `src/hashring.go`: 一致性哈希环（虚拟节点、顺时针路由、节点增删）
  - `src/cluster.go`: 多节点缓存集群（数据分布、优雅降级、统计聚合）
  - `examples/main.go`: 单节点缓存演示（LRU/LFU/TTL 淘汰、统计、热键、预热）
  - `examples/cluster.go`: 多节点集群演示（数据分布、节点故障、统计）
  - `examples/hashring.go`: 一致性哈希可视化（键分布、节点移除影响）
  - `examples/benchmark.go`: 性能基准测试（LRU/LFU/TTL/集群并发对比）
  - `tests/`: 26 个单元测试 + 11 个基准测试全部通过
  - `README.md`: 中英双语文档（含缓存原理、一致性哈希、淘汰策略详解）

### 2026-06-25
- ✅ **完成 time-series-db（时间序列数据库 Go 实现）** - 从零实现时序数据存储和查询引擎，包含完整的压缩算法和聚合查询
  - `src/tsdb.go`: 核心存储引擎（Storage、Series、Point 数据模型，时间索引、Delta 编码、Delta-of-Delta 编码、RLE 压缩、下采样聚合、标签过滤、持久化）
  - `src/series.go`: 系列管理（创建、查询、批量写入、跨系列查询）
  - `src/mock_data.go`: 模拟数据生成器（正弦模式、恒定值、随机游走）
  - `src/tsdb_test.go`: 26 个单元测试全部通过
  - `examples/01_basic_query.go`: 基本写入和查询操作演示
  - `examples/02_compression_demo.go`: 压缩率对比演示（Delta/RLE/Delta-of-Delta）
  - `examples/03_aggregation_demo.go`: 聚合查询（avg/min/max/sum 下采样）
  - `examples/04_range_filter_demo.go`: 时间范围查询与标签过滤
  - `README.md`: 中英双语文档（含压缩算法详解、架构图、性能特征表）

### 2026-06-25
- ✅ **完成 bezier-engine（贝塞尔曲线引擎 Python 实现）** - 从零实现贝塞尔曲线数学计算和渲染引擎，包含完整的 Bernstein 多项式计算、De Casteljau 算法、曲线细分、相交检测等核心模块
  - `src/linear_bezier.py`: 线性贝塞尔曲线（2 点）
  - `src/quadratic_bezier.py`: 二次贝塞尔曲线（3 控制点）
  - `src/cubic_bezier.py`: 三次贝塞尔曲线（4 控制点）
  - `src/de_casteljau.py`: De Casteljau 递归算法（评估 + 细分）
  - `src/subdivision.py`: 曲线细分（递归、自适应）
  - `src/curve_intersection.py`: 曲线-直线/曲线-曲线相交检测
  - `src/tangent_normal.py`: 切线、法向量、曲率计算
  - `src/curve_length.py`: 曲线长度（梯形/辛普森/高斯/自适应）
  - `examples/`: 4 个演示脚本（交互式绘制、细分可视化、曲线拟合、动画渲染）
  - `tests/`: 40 个单元测试全部通过
  - `README.md`: 中英双语文档（含 Bernstein 多项式数学推导）

### 2026-06-25
- ✅ **完成 constraint-solver（约束求解器 Python 实现）** - 从零实现 CAD 几何约束求解器，支持多种约束类型和牛顿-拉夫森数值求解
  - `src/entities.py`: 点、线、圆几何实体类
  - `src/constraints.py`: 9 种约束类型（距离、角度、平行、垂直、共线、同心、相切、等半径、中点）
  - `src/constraint_graph.py`: 约束图构建、约束传播引擎、依赖分析、过约束/欠约束检测
  - `src/solver.py`: 牛顿-拉夫森求解器（稀疏 Jacobian、有限差分、阻尼步长）
  - `examples/`: 4 个演示脚本（草图求解器、几何构造、交互式求解器、可视化）
  - `tests/`: 完整单元测试和集成测试
  - `README.md`: 中英双语文档（含数值方法理论基础）

### 2026-06-25
- ✅ **完成 external-sort（外部排序算法）** - 从零实现大文件外部排序算法，包含完整的两阶段算法（分块排序 + k 路归并）
  - `src/chunk.py`: 文件分块模块（按大小分割、临时文件管理）
  - `src/in_memory_sort.py`: 内存排序（Timsort、快速排序、归并排序三种算法对比）
  - `src/k_way_merge.py`: k 路归并（最小堆实现、多阶段归并）
  - `src/external_sort.py`: 外部排序主逻辑（完整流程、结果验证）
  - `src/memory_management.py`: 内存管理（自适应 k 选择、I/O 成本估算）
  - `src/io_optimization.py`: I/O 优化（缓冲读写、写合并）
  - `examples/`: 4 个演示脚本（基本排序、内存 vs 外部对比、基准测试、可视化）
  - `tests/`: 32 个单元测试全部通过
  - `README.md`: 中英双语文档（含算法详解、复杂度分析）

### 2026-06-25
- ✅ **完成 state-machine（状态机框架 Rust 实现）** - 从零实现通用状态机框架，支持状态转换、事件驱动、历史记录、层次状态机
  - `src/state_machine.rs`: 核心状态机引擎（泛型状态/事件、事件处理、转换图可视化）
  - `src/transition.rs`: 状态转换定义（含构建器模式、守卫条件、动作）
  - `src/error.rs`: 错误类型定义（6 种错误类型）
  - `src/history.rs`: 历史记录管理（时间戳、持续时间、过滤查询）
  - `src/hierarchical/`: 层次状态机模块（复合状态、正交区域、深/浅层历史、入口/出口动作）
  - `examples/`: 4 个演示程序（交通灯、文件传输、订单处理、层次状态机）
  - `tests/`: 完整集成测试
  - `README.md`: 中英双语文档（含状态机理论基础）

### 2026-06-25
- ✅ **完成 logic-gates（逻辑门模拟器）** - 从零实现基本逻辑门模拟，包含真值表、加法器电路和交互式模拟器
  - `src/gates.py`: 7 种基本逻辑门（AND, OR, NOT, NAND, NOR, XOR, XNOR）
  - `src/truth_table.py`: 真值表生成工具
  - `src/multi_bit.py`: 多位逻辑运算（按位与/或/非/异或、移位）
  - `src/circuits.py`: 半加器、全加器、4位行波进位加法器
  - `src/visualizer.py`: matplotlib 真值表可视化
  - `examples/`: 5 个演示脚本（真值表、可视化、加法器、4位加法器、交互式模拟器）
  - `tests/`: 完整单元测试

### 2026-06-25
- ✅ **完成 fourier-transform（傅里叶变换实现）** - 从零实现 DFT/FFT 算法，包含频谱分析工具和多个演示示例
  - `src/dft.py`: 离散傅里叶变换实现
  - `src/fft.py`: Cooley-Tukey FFT 算法（递归+迭代）
  - `src/inverse.py`: 逆 FFT 实现
  - `src/spectrum.py`: 频谱分析工具（窗函数、峰值检测、泄漏分析）
  - `examples/`: 4 个演示脚本（信号生成、DFT/FFT 对比、频谱分析、信号分解）
  - `tests/`: 完整单元测试

### 2026-06-25
- ✅ WISHLIST_V4 全部 10 个项目完成
- ✅ 新增 physics-simulation-engine（3D 物理模拟引擎）
- ✅ 新增 timeline-engine（时间线动画引擎）
- ✅ 更新项目索引状态
- ✅ **完整更新 README，纳入所有 190 个项目**
- ✅ 修正各模块项目数量统计
- ✅ 修复重复项（timeline-engine 出现两次）
- ✅ 新增 C++ 特性系列完整列表（14 个项目）
- ✅ 新增控制系统模块（6 个项目）
- ✅ 新增计算机视觉子模块（22 个项目）
- ✅ 新增多媒体 & 图形子模块（17 个项目）
- ✅ 新增金融 & 量化子模块（6 个项目）
- ✅ 新增系统基础设施子项目（48 个项目）
- ✅ 新增 AI & 深度学习子项目（31 个项目）
- ✅ 新增机器学习算法子项目（20 个项目）

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
