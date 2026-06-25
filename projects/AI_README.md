# 🤖 AI 全栈模块

> 25 个深度学习项目，涵盖量化、微调、训练、推理、部署、强化学习、图像分割、Actor-Critic、Vision Transformer、生成对抗网络、姿态估计、对比学习、超分辨率、风格迁移、点云处理、动作识别、手势识别、文字检测、图像描述、遗传算法、梯度下降、粒子群优化、贝叶斯优化

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [edge-quantized-model](edge-quantized-model/) | 端侧极致量化模型 | Python, C++ | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [finetune-rl-framework](finetune-rl-framework/) | 微调/RL 后训练框架 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [clip](clip/) | CLIP 对比学习模型 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [vit](vit/) | Vision Transformer 图像分类 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [vit-clip-training](vit-clip-training/) | ViT/CLIP 模型训练 | Python, PyTorch | ⭐⭐⭐⭐⭐ | ✅ |
| [industrial-vision-detection](industrial-vision-detection/) | 工业视觉检测 | Python, PyTorch | ⭐⭐⭐⭐⭐ | ✅ |
| [local-llm-engine](local-llm-engine/) | 本地 LLM 推理引擎 | C++ | ⭐⭐⭐⭐⭐⭐⭐ | ✅ |
| [yolo-detection](yolo-detection/) | YOLO 目标检测算法 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [dqn](dqn/) | 深度 Q 网络 | Python, PyTorch, Gym | ⭐⭐⭐⭐ | ✅ |
| [image-segmentation](image-segmentation/) | U-Net 语义分割网络 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [policy-gradient](policy-gradient/) | 策略梯度算法 | Python, PyTorch, Gym | ⭐⭐⭐⭐ | ✅ |
| [actor-critic](actor-critic/) | Actor-Critic 算法 | Python, PyTorch, Gym | ⭐⭐⭐⭐ | ✅ |
| [gan](gan/) | GAN 生成对抗网络 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [pose-estimation](pose-estimation/) | 人体姿态估计 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ | ✅ |
| [super-resolution](super-resolution/) | 图像超分辨率 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [style-transfer](style-transfer/) | 神经风格迁移 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [point-cloud](point-cloud/) | 3D 点云处理 (PointNet) | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [action-recognition](action-recognition/) | 视频动作识别 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ | ✅ |
| [gesture-recognition](gesture-recognition/) | 手势识别 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ | ✅ |
| [text-detection](text-detection/) | 文字检测 | Python, PyTorch, OpenCV | ⭐⭐⭐⭐ | ✅ |
| [image-captioning](image-captioning/) | 图像描述生成 | Python, PyTorch | ⭐⭐⭐⭐ | ✅ |
| [genetic-algorithm](genetic-algorithm/) | 遗传算法优化框架 | Python, matplotlib | ⭐⭐⭐ | ✅ |
| [gradient-descent](gradient-descent/) | 梯度下降优化算法 | Python, numpy | ⭐⭐⭐ | ✅ |
| [simulated-annealing](simulated-annealing/) | 模拟退火优化算法 | Python, matplotlib | ⭐⭐⭐ | ✅ |
| [particle-swarm](particle-swarm/) | 粒子群优化算法 | Python, matplotlib | ⭐⭐⭐ | ✅ |
| [bayesian-optimization](bayesian-optimization/) | 贝叶斯优化（高斯过程） | Python, NumPy, SciPy | ⭐⭐⭐⭐ | ✅ |
| [linear-programming](linear-programming/) | 线性规划（单纯形法、对偶、敏感性分析） | Python, NumPy | ⭐⭐⭐⭐ | ✅ |
| [q-learning](q-learning/) | Q-Learning 强化学习 | Python, NumPy | ⭐⭐⭐ | ✅ |
| [hft-engine](hft-engine/) | 高频交易引擎 | C++17/20 | ⭐⭐⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习路径

```
模型训练 → 模型微调 → 模型量化 → 模型推理 → 模型部署
   ↓          ↓          ↓          ↓          ↓
 ViT/CLIP   LoRA/PPO   INT8/INT4   KV Cache   边缘设备
 对比学习    强化学习    算子融合     采样策略    性能优化
```

### 推荐学习顺序

1. **vit-clip-training** (模型训练)
   - 学习 Vision Transformer 架构
   - 理解对比学习（Contrastive Learning）
   - 掌握多模态对齐

2. **finetune-rl-framework** (模型微调)
   - 学习 LoRA 低秩适配
   - 理解 PPO 强化学习
   - 掌握分布式训练

3. **edge-quantized-model** (模型量化)
   - 学习 INT8/INT4 量化原理
   - 理解算子融合优化
   - 掌握边缘设备部署

4. **local-llm-engine** (模型推理)
   - 学习 Transformer 推理原理
   - 理解 KV Cache 优化
   - 掌握采样策略

5. **industrial-vision-detection** (视觉检测)
   - 学习 YOLO 架构
   - 理解目标检测算法
   - 掌握工业应用

---

## 🔧 技术栈

| 技术 | 用途 | 学习资源 |
|------|------|----------|
| **Python** | 主语言 | [Python 官方文档](https://docs.python.org/3/) |
| **PyTorch** | 深度学习框架 | [PyTorch 官方文档](https://pytorch.org/docs/stable/) |
| **C++** | 推理引擎 | [C++ 官方文档](https://en.cppreference.com/) |
| **ONNX** | 模型格式 | [ONNX 官方文档](https://onnx.ai/onnx/) |
| **TensorRT** | 推理优化 | [TensorRT 文档](https://developer.nvidia.com/tensorrt) |

---

## 📊 项目详情

### 1. vit (Vision Transformer 图像分类)

**核心功能**：
- Patch Embedding：图像分割 + 线性投影
- Multi-Head Self-Attention：多头自注意力机制
- Transformer Encoder：Pre-LN 架构的 Transformer 编码器
- 完整 ViT 模型：支持 ViT-Tiny/Small/Base 配置
- 训练器：AdamW + Cosine Annealing + Label Smoothing
- 注意力可视化：注意力热力图和 Attention Rollout

**代码量**：约 1500 行

**快速开始**：
```bash
cd vit
pip install -r requirements.txt
python demo.py
python train.py --epochs 5 --model tiny
```

---

### 2. vit-clip-training (模型训练)

**核心功能**：
- Vision Transformer (ViT) 实现
- 文本编码器（因果掩码 Transformer）
- CLIP 双编码器架构
- 4 种损失函数（CLIP、Contrastive、SupCon、NTXent）
- 完整训练循环（混合精度、学习率调度）

**代码量**：约 2500 行

**快速开始**：
```bash
cd vit-clip-training
pip install -r requirements.txt
python examples/train_clip.py
```

---

### 3. finetune-rl-framework (模型微调)

**核心功能**：
- LoRA 低秩适配实现
- PPO 强化学习训练
- 分布式训练支持
- 评估指标

**代码量**：约 3000 行

**快速开始**：
```bash
cd finetune-rl-framework
pip install -r requirements.txt
python examples/lora_finetune_example.py
```

---

### 4. edge-quantized-model (模型量化)

**核心功能**：
- INT8/INT4 量化
- 算子融合优化
- 推理引擎
- 车载场景 Demo

**代码量**：约 4000 行

**快速开始**：
```bash
cd edge-quantized-model
pip install -r requirements.txt
python examples/basic/simple_quantize.py
```

---

### 5. local-llm-engine (模型推理)

**核心功能**：
- GGUF 模型加载
- BPE Tokenizer
- Transformer 推理
- KV Cache 优化
- 6 种采样策略

**代码量**：约 4700 行

**快速开始**：
```bash
cd local-llm-engine
mkdir build && cd build
cmake ..
make
./llm_engine_cli --model model.gguf --prompt "Hello"
```

---

### 6. industrial-vision-detection (视觉检测)

**核心功能**：
- CSPDarknet 骨干网络
- PANet 特征融合
- 解耦检测头
- 数据增强（Mosaic、MixUp）
- ONNX 导出

**代码量**：约 3500 行

**快速开始**：
```bash
cd industrial-vision-detection
pip install -r requirements.txt
python examples/train_demo.py
```

---

### 7. dqn (深度 Q 网络)

**核心功能**：
- DQN 算法实现
- 经验回放缓冲区
- 目标网络
- CartPole 环境训练
- Double DQN 支持

**代码量**：约 500 行

**快速开始**：
```bash
cd dqn
pip install torch gymnasium numpy
python src/train.py
```

---

### 8. policy-gradient (策略梯度)

**核心功能**：
- REINFORCE 算法实现
- 策略网络
- 基线减法（移动平均、价值网络）
- CartPole 环境训练
- 熵正则化

**代码量**：约 800 行

**快速开始**：
```bash
cd policy-gradient
pip install -r requirements.txt
pytest tests/
```

---

### 9. image-segmentation (图像分割)

**核心功能**：
- U-Net 编码器-解码器架构
- 跳跃连接（Skip Connections）
- 双线性插值 / 转置卷积上采样
- Dice Loss + BCE 组合损失
- 合成数据生成和训练循环

**代码量**：约 600 行

**快速开始**：
```bash
cd image-segmentation
pip install torch numpy pytest
pytest tests/ -v
```

---

### 10. actor-critic (Actor-Critic 算法)

**核心功能**：
- Actor-Critic 算法实现
- Actor 策略网络
- Critic 价值网络
- 优势函数计算（支持 GAE）
- CartPole 环境训练

**代码量**：约 800 行

**快速开始**：
```bash
cd actor-critic
pip install -e .
python scripts/train.py
pytest tests/ -v
```

---

### 12. pose-estimation (人体姿态估计)

**核心功能**：
- 轻量级骨干网络（类似简化版 ResNet）
- 热力图预测头（反卷积上采样）
- 高斯热力图生成与处理
- MSE 损失 + OHKM 在线困难关键点挖掘
- COCO 17 关键点定义和骨骼连接
- 关键点提取（argmax / soft-argmax / 亚像素精度）
- PCK 和 OKS 评估指标
- 合成数据集和可视化

**代码量**：约 1500 行

**快速开始**：
```bash
cd pose-estimation
pip install torch torchvision numpy opencv-python pytest
pytest tests/ -v
python examples/demo.py
```

---

## 📚 学习资源

### 书籍
- 《深度学习》
- 《动手学深度学习》
- 《PyTorch 深度学习实战》

### 课程
- [Stanford CS231n](http://cs231n.stanford.edu/)
- [Fast.ai](https://www.fast.ai/)

### 开源项目
- [Hugging Face Transformers](https://github.com/huggingface/transformers)
- [OpenMMLab](https://github.com/open-mmlab)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [学习路径图](../LEARNING_PATHS.md)
- [项目索引](../PROJECT_INDEX.md)
