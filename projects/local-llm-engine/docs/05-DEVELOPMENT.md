# 开发手册

## 1. 开发环境搭建

### 1.1 系统要求

#### 操作系统
- **Linux**: Ubuntu 20.04+, CentOS 8+, Fedora 32+
- **macOS**: 10.15+ (Catalina 或更新)
- **Windows**: Windows 10+ (需要 WSL2 或 MSYS2)

#### 编译器
- **GCC**: 7.0+ (推荐 9.0+)
- **Clang**: 5.0+ (推荐 10.0+)
- **MSVC**: 2017+ (Visual Studio 2017 或更新)

#### 构建工具
- **CMake**: 3.14+
- **Make**: GNU Make 4.0+ (Linux/macOS)
- **Ninja**: 1.10+ (可选，更快的构建)

### 1.2 环境配置

#### Linux (Ubuntu/Debian)

```bash
# 安装基础工具
sudo apt update
sudo apt install -y build-essential cmake git

# 安装可选依赖
sudo apt install -y libomp-dev  # OpenMP 支持

# 验证安装
gcc --version
cmake --version
git --version
```

#### macOS

```bash
# 安装 Xcode 命令行工具
xcode-select --install

# 安装 Homebrew (如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 CMake
brew install cmake

# 验证安装
clang --version
cmake --version
```

#### Windows (WSL2)

```bash
# 在 WSL2 中安装 Ubuntu
wsl --install -d Ubuntu

# 然后按照 Linux 步骤安装
```

#### Windows (MSYS2)

```bash
# 下载并安装 MSYS2: https://www.msys2.org/

# 在 MSYS2 终端中安装工具链
pacman -S mingw-w64-x86_64-gcc
pacman -S mingw-w64-x86_64-cmake
pacman -S make

# 添加 MinGW 到 PATH
export PATH=/mingw64/bin:$PATH
```

### 1.3 获取代码

```bash
# 克隆项目
git clone <repository-url>
cd projects/local-llm-engine

# 查看目录结构
ls -la
```

### 1.4 构建项目

#### 基本构建

```bash
# 创建构建目录
mkdir build && cd build

# 配置 CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
make -j$(nproc)

# 或者使用 CMake 并行构建
cmake --build . -j$(nproc)
```

#### 调试构建

```bash
# 配置 Debug 模式
cmake .. -DCMAKE_BUILD_TYPE=Debug

# 编译
make -j$(nproc)
```

#### 自定义选项

```bash
# 启用 AVX2 优化
cmake .. -DENABLE_AVX2=ON

# 禁用测试
cmake .. -DBUILD_TESTS=OFF

# 禁用示例
cmake .. -DBUILD_EXAMPLES=OFF
```

### 1.5 运行测试

```bash
# 在 build 目录中
cd build

# 运行所有测试
ctest

# 运行特定测试
./test_tokenizer
./test_kv_cache
./test_sampler

# 详细输出
ctest --verbose
```

## 2. 项目结构详解

### 2.1 目录结构

```
local-llm-engine/
├── CMakeLists.txt          # 构建配置
├── README.md               # 项目说明
├── docs/                   # 文档目录
│   ├── 01-RESEARCH.md     # 市场调研
│   ├── 02-REQUIREMENTS.md # 需求分析
│   ├── 03-DESIGN.md       # 技术设计
│   ├── 04-PRODUCT.md      # 产品思维
│   └── 05-DEVELOPMENT.md  # 开发手册
├── include/                # 头文件目录
│   ├── gguf_loader.h      # GGUF 加载器
│   ├── tokenizer.h        # Tokenizer
│   ├── transformer.h      # Transformer
│   ├── kv_cache.h         # KV Cache
│   ├── sampler.h          # 采样器
│   └── engine.h           # 推理引擎
├── src/                    # 源文件目录
│   ├── gguf_loader.cpp    # GGUF 加载器实现
│   ├── tokenizer.cpp      # Tokenizer 实现
│   ├── transformer.cpp    # Transformer 实现
│   ├── kv_cache.cpp       # KV Cache 实现
│   ├── sampler.cpp        # 采样器实现
│   ├── engine.cpp         # 推理引擎实现
│   └── main.cpp           # 命令行入口
├── tests/                  # 测试目录
│   ├── test_tokenizer.cpp # Tokenizer 测试
│   ├── test_kv_cache.cpp  # KV Cache 测试
│   └── test_sampler.cpp   # 采样器测试
├── examples/               # 示例目录
│   ├── chat.cpp           # 聊天示例
│   └── benchmark.cpp      # 基准测试
└── models/                 # 模型目录（可选）
    └── README.md          # 模型下载说明
```

### 2.2 文件说明

#### 头文件 (include/)

| 文件 | 说明 | 主要类/结构体 |
|------|------|---------------|
| gguf_loader.h | GGUF 格式解析 | GGUFLoader, GGUFModel |
| tokenizer.h | 分词器 | Tokenizer, BPETokenizer |
| transformer.h | Transformer 模型 | Transformer, ModelWeights |
| kv_cache.h | KV Cache 管理 | KVCache, PagedKVCache |
| sampler.h | 采样器 | Sampler, SamplingParams |
| engine.h | 推理引擎 | LLMEngine, EngineConfig |

#### 源文件 (src/)

| 文件 | 说明 | 依赖 |
|------|------|------|
| gguf_loader.cpp | GGUF 解析实现 | 标准库 |
| tokenizer.cpp | 分词算法实现 | 标准库 |
| transformer.cpp | 前向推理实现 | gguf_loader, kv_cache |
| kv_cache.cpp | 缓存管理实现 | 标准库 |
| sampler.cpp | 采样算法实现 | 标准库 |
| engine.cpp | 引擎整合实现 | 所有模块 |
| main.cpp | 命令行工具 | engine |

#### 测试文件 (tests/)

| 文件 | 测试内容 |
|------|----------|
| test_tokenizer.cpp | Tokenizer 编解码 |
| test_kv_cache.cpp | KV Cache 存储检索 |
| test_sampler.cpp | 采样器功能 |

#### 示例文件 (examples/)

| 文件 | 功能 |
|------|------|
| chat.cpp | 交互式聊天 |
| benchmark.cpp | 性能基准测试 |

## 3. 核心模块解析

### 3.1 GGUF Loader 模块

#### 代码位置
- 头文件: `include/gguf_loader.h`
- 源文件: `src/gguf_loader.cpp`

#### 核心类

```cpp
class GGUFLoader {
public:
    // 加载模型
    bool load(const std::string& filepath);

    // 获取模型数据
    const GGUFModel& get_model() const;

    // 获取张量数据
    const uint8_t* get_tensor_data(const std::string& name) const;

    // 获取元数据
    bool get_metadata(const std::string& key, GGUFMetadataValue& value) const;
};
```

#### 实现要点

1. **文件解析流程**:
   ```
   打开文件 → 读取头部 → 读取元数据 → 读取张量信息 → 读取张量数据
   ```

2. **关键代码**:
   ```cpp
   bool GGUFLoader::load(const std::string& filepath) {
       std::ifstream file(filepath, std::ios::binary);

       // 1. 读取头部
       if (!read_header(file)) return false;

       // 2. 验证魔数
       if (model_.header.magic != GGUF_MAGIC) return false;

       // 3. 读取元数据
       if (!read_metadata(file)) return false;

       // 4. 读取张量信息
       if (!read_tensor_infos(file)) return false;

       // 5. 读取张量数据
       if (!read_tensor_data(file)) return false;

       return true;
   }
   ```

3. **二进制读取**:
   ```cpp
   template<typename T>
   bool read_value(std::ifstream& file, T& value) {
       file.read(reinterpret_cast<char*>(&value), sizeof(T));
       return file.good();
   }
   ```

#### 学习要点

- 二进制文件解析
- 内存映射（可选优化）
- 错误处理策略

---

### 3.2 Tokenizer 模块

#### 代码位置
- 头文件: `include/tokenizer.h`
- 源文件: `src/tokenizer.cpp`

#### 核心类

```cpp
// 抽象基类
class Tokenizer {
public:
    virtual std::vector<int32_t> encode(const std::string& text, bool add_bos = true) const = 0;
    virtual std::string decode(const std::vector<int32_t>& tokens, bool skip_special = true) const = 0;
};

// BPE 实现
class BPETokenizer : public Tokenizer {
    // ...
};

// SentencePiece 实现
class SentencePieceTokenizer : public Tokenizer {
    // ...
};
```

#### 实现要点

1. **BPE 算法**:
   ```
   输入文本 → 初始分词 → 迭代合并 → 查找词汇表 → 输出 token IDs
   ```

2. **关键代码**:
   ```cpp
   std::vector<int32_t> BPETokenizer::encode(const std::string& text, bool add_bos) const {
       std::vector<int32_t> tokens;

       // 添加 BOS token
       if (add_bos) tokens.push_back(config_.bos_token_id);

       // 分词
       auto words = split_text(text);
       for (const auto& word : words) {
           auto pieces = apply_bpe(word);
           for (const auto& piece : pieces) {
               auto it = token_to_id_.find(piece);
               if (it != token_to_id_.end()) {
                   tokens.push_back(it->second);
               } else {
                   // 字节回退
                   for (char c : piece) {
                       tokens.push_back(byte_to_token_[c]);
                   }
               }
           }
       }

       return tokens;
   }
   ```

3. **UTF-8 处理**:
   ```cpp
   // UTF-8 编码长度
   size_t utf8_char_len(char c) {
       uint8_t byte = static_cast<uint8_t>(c);
       if ((byte & 0x80) == 0) return 1;
       if ((byte & 0xE0) == 0xC0) return 2;
       if ((byte & 0xF0) == 0xE0) return 3;
       if ((byte & 0xF8) == 0xF0) return 4;
       return 1;  // 无效 UTF-8
   }
   ```

#### 学习要点

- BPE 算法原理
- UTF-8 编码处理
- 词汇表管理

---

### 3.3 Transformer 模块

#### 代码位置
- 头文件: `include/transformer.h`
- 源文件: `src/transformer.cpp`

#### 核心类

```cpp
class Transformer {
public:
    // 初始化模型
    bool initialize(const GGUFModel& model);

    // 前向推理
    std::vector<float> forward(int32_t token, uint32_t position);
    std::vector<float> forward_with_cache(int32_t token, uint32_t position, KVCache& cache);
};
```

#### 实现要点

1. **前向推理流程**:
   ```
   Token → Embedding → [LayerNorm → Attention → FFN] × N → LayerNorm → LM Head
   ```

2. **注意力机制**:
   ```cpp
   void multi_head_attention(...) {
       // 1. 计算 Q, K, V
       linear(hidden, Q, layer.q_proj);
       linear(hidden, K, layer.k_proj);
       linear(hidden, V, layer.v_proj);

       // 2. 应用 RoPE
       apply_rope(Q, K, position);

       // 3. 存储到 KV Cache
       cache.store(layer, position, K, V);

       // 4. 计算注意力分数
       for (uint32_t pos = 0; pos <= position; ++pos) {
           float score = dot_product(Q, cached_K[pos]) / sqrt(head_dim);
           scores[pos] = score;
       }

       // 5. Softmax
       softmax(scores, position + 1);

       // 6. 加权求和
       output = zeros();
       for (uint32_t pos = 0; pos <= position; ++pos) {
           output += scores[pos] * cached_V[pos];
       }
   }
   ```

3. **RoPE 实现**:
   ```cpp
   void apply_rope(float* query, float* key, uint32_t position) {
       for (uint32_t i = 0; i < head_dim / 2; ++i) {
           float freq = 1.0 / pow(theta, 2 * i / head_dim);
           float angle = position * freq;

           float cos_val = cos(angle);
           float sin_val = sin(angle);

           // 旋转
           float q0 = query[2*i], q1 = query[2*i + 1];
           query[2*i] = q0 * cos_val - q1 * sin_val;
           query[2*i + 1] = q0 * sin_val + q1 * cos_val;
       }
   }
   ```

4. **SwiGLU FFN**:
   ```cpp
   void feed_forward(const float* input, float* output) {
       // gate = gate_proj(input)
       // up = up_proj(input)
       // intermediate = silu(gate) * up
       // output = down_proj(intermediate)

       linear(input, gate, weights.gate_proj);
       linear(input, up, weights.up_proj);

       for (uint32_t i = 0; i < n_ff; ++i) {
           intermediate[i] = silu(gate[i]) * up[i];
       }

       linear(intermediate, output, weights.down_proj);
   }
   ```

#### 学习要点

- Transformer 架构
- 注意力机制实现
- 位置编码（RoPE）
- 前馈网络（SwiGLU）

---

### 3.4 KV Cache 模块

#### 代码位置
- 头文件: `include/kv_cache.h`
- 源文件: `src/kv_cache.cpp`

#### 核心类

```cpp
class KVCache {
public:
    bool initialize(uint32_t n_layers, uint32_t n_ctx, uint32_t n_embd, uint32_t n_head);
    void store(uint32_t layer, uint32_t position, const float* key, const float* value);
    const float* get_keys(uint32_t layer) const;
    const float* get_values(uint32_t layer) const;
};
```

#### 实现要点

1. **缓存结构**:
   ```cpp
   struct KVCache {
       // [n_layers][n_ctx][n_embd]
       std::vector<std::vector<float>> keys;
       std::vector<std::vector<float>> values;
       uint32_t current_pos;
   };
   ```

2. **存储操作**:
   ```cpp
   void KVCache::store(uint32_t layer, uint32_t position,
                       const float* key, const float* value) {
       // 计算偏移
       float* key_ptr = keys_[layer].data() + position * n_embd_;
       float* value_ptr = values_[layer].data() + position * n_embd_;

       // 复制数据
       std::memcpy(key_ptr, key, n_embd_ * sizeof(float));
       std::memcpy(value_ptr, value, n_embd_ * sizeof(float));
   }
   ```

3. **检索操作**:
   ```cpp
   const float* KVCache::get_keys(uint32_t layer) const {
       return keys_[layer].data();
   }
   ```

#### 学习要点

- KV Cache 原理
- 内存管理策略
- 缓存优化技巧

---

### 3.5 Sampler 模块

#### 代码位置
- 头文件: `include/sampler.h`
- 源文件: `src/sampler.cpp`

#### 核心类

```cpp
class Sampler {
public:
    void initialize(const SamplingParams& params);
    int32_t sample(const std::vector<float>& logits);
    int32_t sample(const std::vector<float>& logits, const std::vector<int32_t>& history);
};
```

#### 实现要点

1. **采样流程**:
   ```
   Logits → 应用惩罚 → 应用温度 → 应用 Top-K → 应用 Top-P → 采样
   ```

2. **温度采样**:
   ```cpp
   void apply_temperature(std::vector<float>& logits, float temp) {
       for (auto& logit : logits) {
           logit /= temp;
       }
   }
   ```

3. **Top-K 采样**:
   ```cpp
   void apply_top_k(std::vector<float>& logits, uint32_t k) {
       // 找到第 k 大的值
       std::nth_element(logits.begin(), logits.begin() + k, logits.end(),
                        std::greater<>());

       // 将低于阈值的设为 -inf
       float threshold = logits[k];
       for (auto& logit : logits) {
           if (logit < threshold) logit = -INFINITY;
       }
   }
   ```

4. **Top-P 采样**:
   ```cpp
   void apply_top_p(std::vector<float>& logits, float p) {
       // 转换为概率
       auto probs = softmax(logits);

       // 按概率排序
       auto indices = argsort(probs, descending);

       // 累积概率
       float cumsum = 0;
       for (size_t i = 0; i < indices.size(); ++i) {
           cumsum += probs[indices[i]];
           if (cumsum > p) {
               // 将后面的设为 -inf
               for (size_t j = i + 1; j < indices.size(); ++j) {
                   logits[indices[j]] = -INFINITY;
               }
               break;
           }
       }
   }
   ```

5. **重复惩罚**:
   ```cpp
   void apply_repetition_penalty(std::vector<float>& logits,
                                 const std::vector<int32_t>& history) {
       for (int32_t token_id : history) {
           if (token_id >= 0 && token_id < logits.size()) {
               float logit = logits[token_id];
               if (logit > 0) {
                   logits[token_id] = logit / penalty;
               } else {
                   logits[token_id] = logit * penalty;
               }
           }
       }
   }
   ```

#### 学习要点

- 采样策略原理
- 概率分布处理
- 数值稳定性

---

### 3.6 Engine 模块

#### 代码位置
- 头文件: `include/engine.h`
- 源文件: `src/engine.cpp`

#### 核心类

```cpp
class LLMEngine {
public:
    bool initialize(const EngineConfig& config);
    bool load_model(const std::string& model_path);
    GenerationResult generate(const std::string& prompt, const SamplingParams& params);
    GenerationResult generate_stream(const std::string& prompt,
                                    const SamplingParams& params,
                                    StreamCallback callback);
};
```

#### 实现要点

1. **初始化流程**:
   ```cpp
   bool LLMEngine::initialize(const EngineConfig& config) {
       // 创建组件
       loader_ = std::make_unique<GGUFLoader>();
       transformer_ = std::make_unique<Transformer>();

       return true;
   }
   ```

2. **模型加载**:
   ```cpp
   bool LLMEngine::load_model(const std::string& model_path) {
       // 1. 加载 GGUF
       if (!loader_->load(model_path)) return false;

       // 2. 初始化 Transformer
       if (!transformer_->initialize(loader_->get_model())) return false;

       // 3. 初始化 KV Cache
       kv_cache_ = create_kv_cache(...);

       // 4. 初始化 Tokenizer
       tokenizer_ = create_tokenizer(...);

       // 5. 初始化采样器
       sampler_ = std::make_unique<Sampler>();

       return true;
   }
   ```

3. **推理流程**:
   ```cpp
   GenerationResult LLMEngine::generate(const std::string& prompt,
                                        const SamplingParams& params) {
       // 1. Tokenize
       auto tokens = tokenize(prompt);

       // 2. Prefill (处理 prompt)
       for (size_t i = 0; i < tokens.size(); ++i) {
           transformer_->forward_with_cache(tokens[i], i, *kv_cache_);
       }

       // 3. Decode (生成 token)
       std::vector<int32_t> generated;
       for (uint32_t i = 0; i < params.max_tokens; ++i) {
           auto logits = transformer_->forward_with_cache(...);
           int32_t next_token = sampler_->sample(logits);

           if (next_token == eos_token_id) break;
           generated.push_back(next_token);
       }

       // 4. Detokenize
       std::string text = detokenize(generated);

       return {text, generated, ...};
   }
   ```

#### 学习要点

- 组件整合
- 推理流程管理
- 错误处理

## 4. 开发流程

### 4.1 代码风格

#### 命名规范

```cpp
// 类名: PascalCase
class GGUFLoader { };

// 函数名: snake_case
bool load_model(const std::string& path);

// 变量名: snake_case
uint32_t n_layers;

// 常量: UPPER_SNAKE_CASE
constexpr uint32_t MAX_CONTEXT = 2048;

// 成员变量: snake_case_ (带下划线后缀)
std::vector<float> keys_;
```

#### 注释规范

```cpp
/**
 * @brief 加载 GGUF 模型文件
 * @param filepath 模型文件路径
 * @return 加载是否成功
 *
 * 这个函数会解析 GGUF 格式，加载所有元数据和张量数据。
 */
bool load(const std::string& filepath);

// 单行注释
float rms = 0.0f;  // 计算 RMS 值
```

#### 代码组织

```cpp
// 1. 头文件包含
#include "gguf_loader.h"
#include <iostream>
#include <vector>

// 2. 命名空间
namespace llm_engine {

// 3. 类定义
class MyClass {
public:
    // 公共接口
private:
    // 私有成员
};

// 4. 实现
bool MyClass::method() {
    // 实现代码
}

}  // namespace llm_engine
```

### 4.2 Git 工作流

#### 分支策略

```
main (主分支)
├── develop (开发分支)
│   ├── feature/xxx (功能分支)
│   └── bugfix/xxx (修复分支)
└── release/x.x.x (发布分支)
```

#### 提交规范

```
类型(范围): 描述

类型:
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 杂项

示例:
feat(tokenizer): 添加 SentencePiece 支持
fix(kv-cache): 修复内存泄漏
docs(readme): 更新使用说明
```

### 4.3 测试策略

#### 单元测试

```cpp
// 测试单个函数或类
TEST(TokenizerTest, EncodeDecode) {
    BPETokenizer tokenizer;
    tokenizer.initialize(config, vocab);

    auto tokens = tokenizer.encode("hello world");
    auto decoded = tokenizer.decode(tokens);

    ASSERT_EQ(decoded, "hello world");
}
```

#### 集成测试

```cpp
// 测试多个组件协作
TEST(EngineTest, GenerateText) {
    LLMEngine engine;
    engine.initialize(config);
    engine.load_model("test.gguf");

    auto result = engine.generate("Hello");
    ASSERT_FALSE(result.text.empty());
}
```

#### 性能测试

```cpp
// 测试性能指标
TEST(BenchmarkTest, Throughput) {
    auto start = steady_clock::now();

    for (int i = 0; i < 100; ++i) {
        engine.generate("Test");
    }

    auto duration = duration_cast<milliseconds>(steady_clock::now() - start);
    float tps = 100 * 256 / (duration.count() / 1000.0);

    ASSERT_GT(tps, 10);  // 至少 10 tokens/s
}
```

### 4.4 调试技巧

#### 使用 GDB

```bash
# 编译 Debug 版本
cmake .. -DCMAKE_BUILD_TYPE=Debug
make

# 运行 GDB
gdb ./llm_engine

# 常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行
(gdb) next                # 下一行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
```

#### 使用 Valgrind

```bash
# 检查内存泄漏
valgrind --leak-check=full ./llm_engine

# 检查未初始化内存
valgrind --tool=memcheck ./llm_engine
```

#### 日志调试

```cpp
// 简单的日志宏
#define LOG_DEBUG(msg) std::cout << "[DEBUG] " << msg << std::endl
#define LOG_INFO(msg)  std::cout << "[INFO] " << msg << std::endl
#define LOG_ERROR(msg) std::cerr << "[ERROR] " << msg << std::endl

// 使用
LOG_INFO("Loading model: " << path);
LOG_DEBUG("Tensor count: " << count);
LOG_ERROR("Failed to open file");
```

## 5. 常见问题

### 5.1 编译问题

**问题**: 找不到 CMake
```bash
# 解决: 安装 CMake
sudo apt install cmake  # Linux
brew install cmake      # macOS
```

**问题**: C++17 不支持
```bash
# 解决: 使用更新的编译器
sudo apt install g++-9
export CXX=g++-9
```

### 5.2 运行问题

**问题**: 模型加载失败
```
# 检查:
1. 文件路径是否正确
2. 文件是否损坏
3. 是否是有效的 GGUF 文件
```

**问题**: 内存不足
```
# 解决:
1. 使用更小的模型
2. 使用量化版本
3. 减小上下文长度
```

### 5.3 性能问题

**问题**: 推理速度慢
```
# 优化:
1. 启用 AVX2: cmake .. -DENABLE_AVX2=ON
2. 使用 Release 模式: cmake .. -DCMAKE_BUILD_TYPE=Release
3. 减少上下文长度
4. 使用更小的模型
```

## 6. 扩展开发

### 6.1 添加新模型架构

1. 在 `transformer.h` 中添加新的权重结构
2. 在 `transformer.cpp` 中实现新的前向推理
3. 在 `gguf_loader.cpp` 中添加新的元数据解析

### 6.2 添加新采样策略

1. 在 `sampler.h` 中添加新的策略枚举
2. 在 `sampler.cpp` 中实现新的采样算法
3. 在 `engine.cpp` 中集成新策略

### 6.3 添加 GPU 支持

1. 添加 CUDA/Metal 后端
2. 实现 GPU 内存管理
3. 修改计算流程支持 GPU

## 7. 最佳实践

### 7.1 代码质量

- 保持函数简短（< 50 行）
- 单一职责原则
- 适当的错误处理
- 充分的测试覆盖

### 7.2 性能优化

- 先测量，再优化
- 关注热点代码
- 使用性能分析工具
- 避免过早优化

### 7.3 文档维护

- 代码和文档同步更新
- 使用清晰的示例
- 保持文档简洁
- 定期审查和更新

## 8. 总结

本开发手册提供了完整的开发环境搭建、项目结构解析、核心模块详解和开发流程指导。

**关键要点**：
1. 遵循代码规范
2. 编写充分的测试
3. 保持文档更新
4. 持续重构优化

通过这个项目，你将掌握：
- C++ 项目开发流程
- AI 推理引擎实现
- 性能优化技巧
- 开源项目管理

祝你开发愉快！
