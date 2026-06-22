# 🤖 AI 全栈模块

> 5 个深度学习项目，涵盖量化、微调、训练、推理、部署

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [edge-quantized-model](edge-quantized-model/) | 端侧极致量化模型 | Python, C++ | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [finetune-rl-framework](finetune-rl-framework/) | 微调/RL 后训练框架 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐ | ✅ |
| [vit-clip-training](vit-clip-training/) | ViT/CLIP 模型训练 | Python, PyTorch | ⭐⭐⭐⭐⭐ | ✅ |
| [industrial-vision-detection](industrial-vision-detection/) | 工业视觉检测 | Python, PyTorch | ⭐⭐⭐⭐⭐ | ✅ |
| [local-llm-engine](local-llm-engine/) | 本地 LLM 推理引擎 | C++ | ⭐⭐⭐⭐⭐⭐⭐ | ✅ |

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

### 1. vit-clip-training (模型训练)

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

### 2. finetune-rl-framework (模型微调)

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

### 3. edge-quantized-model (模型量化)

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

### 4. local-llm-engine (模型推理)

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

### 5. industrial-vision-detection (视觉检测)

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
