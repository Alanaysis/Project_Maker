# Local LLM Engine

一个轻量级的本地 LLM 推理引擎，支持 GGUF 模型格式，从零实现 Transformer 推理。

## 🎯 学习目标

通过这个项目，你将深入理解：

- **Transformer 推理原理**：注意力机制、前馈网络、位置编码
- **KV Cache 优化**：如何高效缓存和复用计算结果
- **模型加载和量化推理**：GGUF 格式解析、量化权重处理
- **采样策略**：Temperature、Top-K、Top-P 等采样方法

## 📚 技术栈

| 组件 | 技术 | 学习难度 |
|------|------|----------|
| 主语言 | C++17 | ⭐⭐⭐⭐ |
| 构建系统 | CMake | ⭐⭐ |
| 模型格式 | GGUF | ⭐⭐⭐⭐ |
| 推理框架 | 从零实现 | ⭐⭐⭐⭐⭐ |

## 🏗️ 项目架构

```
local-llm-engine/
├── include/              # 头文件
│   ├── gguf_loader.h    # GGUF 模型加载器
│   ├── tokenizer.h      # Tokenizer 实现
│   ├── transformer.h    # Transformer 模型
│   ├── kv_cache.h       # KV Cache 优化
│   ├── sampler.h        # 采样策略
│   └── engine.h         # 推理引擎
├── src/                  # 源文件
│   ├── gguf_loader.cpp  # GGUF 格式解析
│   ├── tokenizer.cpp    # BPE/SentencePiece 实现
│   ├── transformer.cpp  # Transformer 前向推理
│   ├── kv_cache.cpp     # KV Cache 管理
│   ├── sampler.cpp      # 采样算法
│   ├── engine.cpp       # 推理引擎核心
│   └── main.cpp         # 命令行入口
├── tests/                # 单元测试
├── examples/             # 使用示例
├── docs/                 # 详细文档
└── CMakeLists.txt        # 构建配置
```

## 🚀 快速开始

### 环境要求

- C++17 编译器 (GCC 7+, Clang 5+, MSVC 2017+)
- CMake 3.14+
- 支持 AVX2 的 CPU（可选，用于性能优化）

### 编译

```bash
# 克隆项目
cd projects/local-llm-engine

# 创建构建目录
mkdir build && cd build

# 配置
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
make -j$(nproc)
```

### 运行测试

```bash
# 运行所有测试
ctest

# 运行特定测试
./test_tokenizer
./test_kv_cache
./test_sampler
```

### 使用示例

```bash
# 查看模型信息
./llm_engine info -m /path/to/model.gguf

# 运行推理
./llm_engine infer -m /path/to/model.gguf -p "Hello, how are you?"

# 交互式聊天
./chat -m /path/to/model.gguf

# 性能基准测试
./benchmark -m /path/to/model.gguf -n 128 -r 5
```

## ⭐ 重点难点

### 1. GGUF 格式解析
GGUF 是一种高效的模型存储格式，包含：
- 模型元数据（架构、参数）
- 词汇表
- 量化权重

**难点**：理解二进制格式解析、内存映射、量化类型处理

### 2. KV Cache 优化
KV Cache 是 Transformer 推理的关键优化：
- 缓存已计算的 Key 和 Value
- 避免重复计算
- 支持多种缓存策略（标准、滑动窗口、分页）

**难点**：内存管理、缓存一致性、多层缓存同步

### 3. 位置编码 (RoPE)
Rotary Position Embedding 是现代 LLM 的标准位置编码：
- 基于旋转矩阵
- 支持相对位置编码
- 计算效率高

**难点**：复数运算、频率计算、多头应用

### 4. 注意力机制
多头注意力是 Transformer 的核心：
- Query、Key、Value 投影
- 缩放点积注意力
- 因果掩码（自回归生成）

**难点**：矩阵运算优化、内存效率、数值稳定性

## 💡 值得思考

1. **为什么需要 KV Cache？**
   - 自回归生成时，每个 token 都需要关注之前所有 token
   - 没有 KV Cache，时间复杂度是 O(n²)
   - KV Cache 将其降为 O(n)

2. **量化如何影响推理质量？**
   - FP32 → FP16：几乎无损
   - FP32 → INT8：轻微损失
   - FP32 → INT4：明显损失，但可接受

3. **如何优化推理速度？**
   - 批量处理（Batching）
   - 算子融合（Operator Fusion）
   - 内存预分配
   - SIMD 指令优化

4. **分页注意力（PagedAttention）解决了什么问题？**
   - 传统 KV Cache 需要连续内存
   - 长序列会导致内存碎片
   - 分页管理可以更高效利用内存

## 📖 核心概念

### Transformer 推理流程

```
输入 Token → Embedding → [Layer Norm → Attention → FFN] × N → Output → Logits
                              ↑
                           KV Cache
```

### 采样策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| Greedy | 选择概率最高的 token | 确定性任务 |
| Temperature | 调整概率分布 | 创意生成 |
| Top-K | 只考虑前 K 个 token | 平衡多样性 |
| Top-P | 累积概率阈值 | 动态调整 |
| Min-P | 最小概率阈值 | 高质量生成 |

## 🔧 实现细节

### GGUF 格式

```
[Header]
  Magic: "GGUF"
  Version: 3
  Tensor Count: N
  Metadata Count: M

[Metadata]
  Key-Value pairs...

[Tensor Info]
  Name, Dimensions, Type, Offset

[Tensor Data]
  Raw weights...
```

### KV Cache 结构

```cpp
struct KVCache {
    // Shape: [n_layers][n_ctx][n_embd]
    std::vector<std::vector<float>> keys;
    std::vector<std::vector<float>> values;
    uint32_t current_pos;
};
```

### RoPE 实现

```cpp
// 旋转位置编码
for each head:
    for each dimension pair (2i, 2i+1):
        angle = position * freq[i]
        q'[2i] = q[2i] * cos(angle) - q[2i+1] * sin(angle)
        q'[2i+1] = q[2i] * sin(angle) + q[2i+1] * cos(angle)
```

## 📊 性能指标

典型性能表现（取决于硬件）：

| 指标 | 范围 |
|------|------|
| Prompt 处理速度 | 100-500 tokens/s |
| 生成速度 | 10-50 tokens/s |
| 内存占用 | 取决于模型大小 |

## 🎓 学习路径

### 初级阶段
1. 理解 Transformer 基础架构
2. 学习注意力机制原理
3. 掌握 C++ 基础和内存管理

### 中级阶段
1. 实现 GGUF 格式解析
2. 实现 KV Cache
3. 优化矩阵运算

### 高级阶段
1. 量化推理优化
2. 多线程并行
3. SIMD 指令优化
4. GPU 加速（可选）

## 📚 参考资源

### 论文
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864)
- [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180)

### 开源项目
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - C++ LLM 推理实现
- [vLLM](https://github.com/vllm-project/vllm) - 高性能推理引擎
- [Ollama](https://github.com/ollama/ollama) - 简单易用的 LLM 运行工具

### 教程
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
- [Transformers from Scratch](https://e2eml.school/transformers.html)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

感谢以下项目的启发：
- llama.cpp
- Ollama
- vLLM
- Hugging Face Transformers
