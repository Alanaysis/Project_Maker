# 模型下载指南

## 推荐模型

本项目支持 GGUF 格式的模型。以下是一些推荐的模型：

### 轻量级模型（适合学习和测试）

#### TinyLlama-1.1B
- **大小**: ~600MB (Q4_0)
- **特点**: 轻量级，适合入门学习
- **下载**: [Hugging Face](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)

```bash
# 使用 huggingface-cli 下载
pip install huggingface_hub
huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf --local-dir models/
```

#### Phi-2
- **大小**: ~1.5GB (Q4_0)
- **特点**: 微软出品，性能优秀
- **下载**: [Hugging Face](https://huggingface.co/TheBloke/phi-2-GGUF)

```bash
huggingface-cli download TheBloke/phi-2-GGUF phi-2.Q4_K_M.gguf --local-dir models/
```

### 中等模型（适合实际使用）

#### Llama-2-7B
- **大小**: ~4GB (Q4_0)
- **特点**: Meta 出品，广泛使用
- **下载**: [Hugging Face](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)

```bash
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF llama-2-7b-chat.Q4_K_M.gguf --local-dir models/
```

#### Mistral-7B
- **大小**: ~4GB (Q4_0)
- **特点**: 性能超越 Llama-2-7B
- **下载**: [Hugging Face](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)

```bash
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF mistral-7b-instruct-v0.2.Q4_K_M.gguf --local-dir models/
```

### 量化版本说明

| 量化类型 | 大小 | 质量 | 速度 | 推荐场景 |
|---------|------|------|------|---------|
| Q2_K | 最小 | 较差 | 最快 | 内存受限 |
| Q3_K_M | 小 | 可接受 | 快 | 平衡选择 |
| Q4_K_M | 中等 | 好 | 较快 | **推荐** |
| Q5_K_M | 较大 | 很好 | 中等 | 高质量需求 |
| Q6_K | 大 | 很好 | 较慢 | 接近原始质量 |
| Q8_0 | 最大 | 最好 | 最慢 | 最高质量 |

**推荐**: Q4_K_M 在大小和质量之间有很好的平衡。

## 下载工具

### 方法 1: huggingface-cli (推荐)

```bash
# 安装
pip install huggingface_hub

# 下载单个文件
huggingface-cli download <repo_id> <filename> --local-dir models/

# 示例
huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF \
    tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    --local-dir models/
```

### 方法 2: wget/curl

```bash
# 从 Hugging Face 直接下载
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf -P models/
```

### 方法 3: Git LFS

```bash
# 安装 Git LFS
git lfs install

# 克隆仓库
git clone https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF models/TinyLlama
```

## 模型目录结构

建议的目录结构：

```
models/
├── README.md                 # 本文件
├── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
├── phi-2.Q4_K_M.gguf
├── llama-2-7b-chat.Q4_K_M.gguf
└── mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

## 使用模型

### 查看模型信息

```bash
./build/llm_engine_cli info -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 运行推理

```bash
./build/llm_engine_cli infer \
    -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    -p "Hello, how are you?" \
    --max-tokens 100
```

### 交互式聊天

```bash
./build/chat -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 性能测试

```bash
./build/benchmark \
    -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    -n 128 \
    -r 5
```

## 常见问题

### Q: 下载速度慢怎么办？

A: 尝试使用镜像源：
```bash
# 使用 HF Mirror
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download ...
```

### Q: 内存不足怎么办？

A: 尝试更小的量化版本：
```bash
# 使用 Q2_K 或 Q3_K_M
huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF \
    tinyllama-1.1b-chat-v1.0.Q2_K.gguf \
    --local-dir models/
```

### Q: 如何转换自己的模型？

A: 使用 llama.cpp 的转换工具：
```bash
# 克隆 llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# 转换 Hugging Face 模型
python convert-hf-to-gguf.py /path/to/model --outfile model.gguf

# 量化
./quantize model.gguf model-q4_k_m.gguf Q4_K_M
```

## 参考链接

- [Hugging Face Models](https://huggingface.co/models)
- [TheBloke GGUF Models](https://huggingface.co/TheBloke)
- [llama.cpp Model Conversion](https://github.com/ggerganov/llama.cpp#prepare-and-quantize)

## 注意事项

1. **许可证**: 请遵守各模型的使用许可证
2. **存储空间**: 确保有足够的磁盘空间
3. **内存要求**: 运行模型需要足够的 RAM
4. **网络**: 下载大文件需要稳定的网络连接
