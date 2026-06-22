# 快速开始指南

## 5 分钟快速上手

### 1. 环境准备

确保已安装：
- C++ 编译器 (GCC 7+ 或 Clang 5+)
- CMake 3.14+
- Git

```bash
# Ubuntu/Debian
sudo apt install build-essential cmake git

# macOS
xcode-select --install
brew install cmake

# 验证
g++ --version
cmake --version
```

### 2. 编译项目

```bash
# 进入项目目录
cd projects/local-llm-engine

# 使用 Make 快速构建
make

# 或者手动构建
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### 3. 运行测试

```bash
# 运行所有测试
make test

# 或者手动运行
cd build
ctest
```

### 4. 下载模型

```bash
# 安装 huggingface-cli
pip install huggingface_hub

# 下载 TinyLlama (约 600MB)
huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF \
    tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    --local-dir models/
```

### 5. 运行推理

```bash
# 查看模型信息
./build/llm_engine_cli info -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# 运行推理
./build/llm_engine_cli infer \
    -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
    -p "Hello, how are you?" \
    --max-tokens 100

# 交互式聊天
./build/chat -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

# 性能测试
./build/benchmark -m models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

## 学习路径

### 第一步：理解架构

阅读以下文档：
1. `README.md` - 项目概述
2. `docs/03-DESIGN.md` - 技术设计

### 第二步：阅读代码

从简单到复杂：
1. `include/sampler.h` - 采样器接口
2. `include/kv_cache.h` - KV Cache 接口
3. `include/tokenizer.h` - Tokenizer 接口
4. `include/transformer.h` - Transformer 接口
5. `include/engine.h` - 推理引擎接口

### 第三步：运行测试

```bash
# 运行并观察输出
./build/test_tokenizer
./build/test_kv_cache
./build/test_sampler
```

### 第四步：修改代码

尝试修改：
1. 采样参数（温度、Top-K、Top-P）
2. KV Cache 策略
3. 添加新的采样算法

### 第五步：实现新功能

挑战：
1. 添加新的模型架构支持
2. 实现 GPU 加速
3. 优化矩阵运算

## 常见问题

### Q: 编译失败怎么办？

A: 检查编译器版本：
```bash
g++ --version
# 需要 7.0 或更高版本
```

### Q: 内存不足怎么办？

A: 使用更小的模型或量化版本：
```bash
# 使用 Q2_K 量化（更小）
huggingface-cli download TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF \
    tinyllama-1.1b-chat-v1.0.Q2_K.gguf \
    --local-dir models/
```

### Q: 推理速度慢怎么办？

A: 尝试：
1. 使用 Release 构建：`make release`
2. 启用 AVX2：`cmake .. -DENABLE_AVX2=ON`
3. 减少上下文长度：`-c 512`

## 核心概念速查

### Transformer
```
输入 → Embedding → [Attention + FFN] × N → Output
```

### KV Cache
```
缓存已计算的 Key-Value，避免重复计算
```

### RoPE
```
旋转位置编码，将位置信息编码到 Q, K 中
```

### 采样
```
Logits → Temperature → Top-K → Top-P → Token
```

## 下一步

1. 阅读完整文档
2. 运行所有测试
3. 尝试修改代码
4. 实现新功能
5. 分享学习心得

## 获取帮助

- 查看 `docs/` 目录的详细文档
- 阅读源代码注释
- 运行测试了解行为
- 参考 llama.cpp 实现

祝你学习愉快！
