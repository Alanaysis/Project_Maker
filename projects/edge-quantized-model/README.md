# 端侧极致量化模型（车载）

> 实现一个极致量化的模型部署框架，支持 INT8/INT4 量化，优化车载场景推理

## 学习目标

- 理解模型量化原理（INT8、INT4、混合精度）
- 掌握推理优化技术（算子融合、内存优化）
- 学会边缘设备部署和性能调优

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| C++ | 推理引擎核心 | ⭐⭐⭐⭐ |
| Python | 量化工具链、训练 | ⭐⭐⭐ |
| PyTorch | 模型训练、量化感知训练 | ⭐⭐⭐ |
| ONNX | 模型中间表示 | ⭐⭐ |
| TensorRT | NVIDIA GPU 推理优化 | ⭐⭐⭐⭐ |
| OpenVINO | Intel 设备推理优化 | ⭐⭐⭐ |
| NCNN | 移动端推理框架 | ⭐⭐⭐ |

## 项目结构

```
edge-quantized-model/
├── README.md
├── LEARNING_NOTES.md
├── docs/
│   ├── 01-RESEARCH.md      # 市场调研
│   ├── 02-REQUIREMENTS.md   # 需求分析
│   ├── 03-DESIGN.md         # 技术设计
│   ├── 04-PRODUCT.md        # 产品思维
│   └── 05-DEVELOPMENT.md    # 开发手册
├── src/
│   ├── quantization/        # 量化算法实现
│   ├── inference/           # 推理引擎
│   ├── operators/           # 算子实现
│   └── utils/               # 工具函数
├── tests/                   # 单元测试
├── examples/
│   └── automotive/          # 车载场景示例
├── configs/                 # 配置文件
├── scripts/                 # 脚本工具
└── benchmarks/              # 性能基准测试
```

## 快速开始

### 环境要求

- Python 3.8+
- PyTorch 2.0+
- ONNX 1.14+
- CMake 3.16+ (C++ 推理引擎)
- GCC 9+ 或 Clang 12+

### 安装

```bash
# 克隆项目
cd projects/edge-quantized-model

# 安装 Python 依赖
pip install -r requirements.txt

# 编译 C++ 推理引擎（可选）
mkdir build && cd build
cmake ..
make -j4
```

### 运行示例

```bash
# 运行量化示例
python examples/automotive/object_detection_demo.py

# 运行基准测试
python benchmarks/run_benchmark.py
```

## 核心循环

```
浮点模型 → 量化校准 → 量化模型 → 算子融合 → 引擎构建 → 边缘推理
```

## 重点难点

### ⭐ 重点

1. **量化原理理解**
   - 对称量化 vs 非对称量化
   - 逐通道量化 vs 逐层量化
   - 量化感知训练（QAT）vs 训练后量化（PTQ）

2. **算子融合技术**
   - Conv + BN + ReLU 融合
   - 注意力机制融合
   - 自定义算子优化

3. **内存优化**
   - 内存池管理
   - 张量生命周期管理
   - 零拷贝技术

### ⭐ 难点

1. **混合精度策略**
   - 敏感层识别
   - 精度-性能权衡
   - 自动混合精度算法

2. **边缘设备适配**
   - ARM NEON 优化
   - GPU 着色器优化
   - NPU 指令集利用

3. **实时性保证**
   - 延迟优化
   - 吞吐量优化
   - 功耗控制

## 💡 值得思考

1. **为什么 INT8 量化能保持精度？**
   - 神经网络具有鲁棒性
   - 权重和激活值分布特点
   - 校准数据集的作用

2. **INT4 量化的挑战是什么？**
   - 精度损失更大
   - 需要更复杂的量化策略
   - 混合精度的必要性

3. **车载场景的特殊需求？**
   - 实时性要求（< 100ms）
   - 功耗限制
   - 安全性要求（功能安全）

## 参考资源

### 开源项目

- [TensorRT](https://github.com/NVIDIA/TensorRT) - NVIDIA 推理优化
- [ONNX Runtime](https://github.com/microsoft/onnxruntime) - 微软推理引擎
- [NCNN](https://github.com/Tencent/ncnn) - 腾讯移动端推理
- [MNN](https://github.com/alibaba/MNN) - 阿里移动端推理
- [OpenVINO](https://github.com/openvinotoolkit/openvino) - Intel 推理优化
- [TFLite](https://github.com/tensorflow/tensorflow/tree/master/tensorflow/lite) - TensorFlow 移动端

### 学习资源

- [量化感知训练教程](https://pytorch.org/docs/stable/quantization.html)
- [ONNX 量化工具](https://github.com/microsoft/onnxruntime/tree/main/onnxruntime/python/tools/quantization)
- [TensorRT 开发者指南](https://docs.nvidia.com/deeplearning/tensorrt/developer-guide/)

### 论文

- [Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference](https://arxiv.org/abs/1712.05877)
- [Mixed Precision Training](https://arxiv.org/abs/1710.03740)
- [Quantizing deep convolutional networks for efficient inference: A whitepaper](https://arxiv.org/abs/1806.08342)

## 许可证

MIT License
