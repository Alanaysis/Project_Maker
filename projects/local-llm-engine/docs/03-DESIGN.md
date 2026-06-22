# 技术设计文档

## 1. 架构概述

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      LLMEngine (推理引擎)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Loader   │  │Tokenizer │  │Transformer│  │ Sampler  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↓              ↓              ↓              ↓        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    KV Cache                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      GGUF Model File                         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 数据流

```
输入文本
    ↓
┌─────────────────┐
│   Tokenizer     │  文本 → Token IDs
└─────────────────┘
    ↓
┌─────────────────┐
│   Embedding     │  Token ID → 向量
└─────────────────┘
    ↓
┌─────────────────┐
│   Transformer   │  向量 → 隐藏状态
│   (N layers)    │
└─────────────────┘
    ↓
┌─────────────────┐
│   LM Head       │  隐藏状态 → Logits
└─────────────────┘
    ↓
┌─────────────────┐
│   Sampler       │  Logits → Token ID
└─────────────────┘
    ↓
输出文本
```

## 2. 核心模块设计

### 2.1 GGUF Loader 模块

#### 设计目标
- 高效加载 GGUF 格式模型
- 支持内存映射（mmap）
- 验证模型完整性

#### 数据结构

```cpp
// GGUF 文件头
struct GGUFHeader {
    uint32_t magic;           // 魔数 "GGUF"
    uint32_t version;         // 版本号
    uint64_t tensor_count;    // 张量数量
    uint64_t metadata_count;  // 元数据数量
};

// 张量信息
struct GGUFTensorInfo {
    std::string name;           // 张量名称
    std::vector<uint64_t> dims; // 维度
    GGMLType type;              // 数据类型
    uint64_t offset;            // 数据偏移
};

// 模型数据
struct GGUFModel {
    GGUFHeader header;
    std::unordered_map<std::string, GGUFMetadataValue> metadata;
    std::vector<GGUFTensorInfo> tensor_infos;
    std::vector<uint8_t> tensor_data;
};
```

#### 关键接口

```cpp
class GGUFLoader {
public:
    bool load(const std::string& filepath);
    const GGUFModel& get_model() const;
    const uint8_t* get_tensor_data(const std::string& name) const;
    bool get_metadata(const std::string& key, GGUFMetadataValue& value) const;
};
```

#### 实现要点
1. **二进制解析**: 使用 `ifstream` 读取二进制数据
2. **内存管理**: 使用 `vector<uint8_t>` 存储张量数据
3. **元数据解析**: 支持多种数据类型（字符串、整数、浮点、数组）
4. **错误处理**: 验证魔数、版本号、数据完整性

---

### 2.2 Tokenizer 模块

#### 设计目标
- 支持 BPE 和 SentencePiece 分词
- 高效的编解码
- 正确处理 UTF-8

#### 类层次结构

```
Tokenizer (抽象基类)
    ├── BPETokenizer
    └── SentencePieceTokenizer
```

#### 关键接口

```cpp
class Tokenizer {
public:
    virtual bool initialize(const TokenizerConfig& config,
                          const std::vector<std::string>& vocab,
                          const std::vector<float>& scores = {}) = 0;

    virtual std::vector<int32_t> encode(const std::string& text,
                                       bool add_bos = true) const = 0;

    virtual std::string decode(const std::vector<int32_t>& tokens,
                              bool skip_special = true) const = 0;
};
```

#### BPE 算法流程

```
输入: "hello world"
    ↓
1. 初始分词: ["h", "e", "l", "l", "o", " ", "w", "o", "r", "l", "d"]
    ↓
2. 查找最高频合并: ("l", "l") → "ll"
    ↓
3. 合并: ["h", "e", "ll", "o", " ", "w", "o", "r", "l", "d"]
    ↓
4. 重复直到无法合并
    ↓
5. 查找词汇表得到 token IDs
```

#### SentencePiece 算法流程

```
输入: "hello world"
    ↓
1. 添加特殊前缀: "▁hello▁world"
    ↓
2. Viterbi 分割: 找到最优分割点
    ↓
3. 查找词汇表得到 token IDs
```

---

### 2.3 Transformer 模块

#### 设计目标
- 实现标准 Transformer 架构
- 支持 LLaMA 风格的变体
- 高效的矩阵运算

#### 模型结构

```
Input Token
    ↓
┌─────────────────────┐
│   Token Embedding   │
└─────────────────────┘
    ↓
┌─────────────────────┐
│   RMSNorm           │  ← Layer Norm
├─────────────────────┤
│   Multi-Head Attn   │  ← 注意力机制
├─────────────────────┤
│   + Residual        │  ← 残差连接
└─────────────────────┘
    ↓
┌─────────────────────┐
│   RMSNorm           │  ← Layer Norm
├─────────────────────┤
│   FFN (SwiGLU)      │  ← 前馈网络
├─────────────────────┤
│   + Residual        │  ← 残差连接
└─────────────────────┘
    ↓
   × N layers
    ↓
┌─────────────────────┐
│   Final RMSNorm     │
├─────────────────────┤
│   Linear (LM Head)  │
└─────────────────────┘
    ↓
Logits
```

#### 注意力机制实现

```cpp
// 多头注意力
void multi_head_attention(
    const float* hidden,    // 输入
    float* output,          // 输出
    uint32_t position,      // 当前位置
    KVCache& cache,         // KV Cache
    const TransformerBlockWeights& layer  // 权重
) {
    // 1. 计算 Q, K, V
    linear(hidden, Q, layer.q_proj);
    linear(hidden, K, layer.k_proj);
    linear(hidden, V, layer.v_proj);

    // 2. 应用 RoPE
    apply_rope(Q, K, position);

    // 3. 存储到 KV Cache
    cache.store(layer, position, K, V);

    // 4. 计算注意力分数
    scores = Q @ K^T / sqrt(head_dim);

    // 5. Softmax
    probs = softmax(scores);

    // 6. 加权求和
    output = probs @ V;
}
```

#### RoPE 实现

```cpp
// 旋转位置编码
void apply_rope(float* query, float* key, uint32_t position) {
    for (uint32_t i = 0; i < head_dim / 2; ++i) {
        float freq = 1.0 / pow(theta, 2 * i / head_dim);
        float angle = position * freq;

        float cos_val = cos(angle);
        float sin_val = sin(angle);

        // 旋转 Q
        float q0 = query[2*i];
        float q1 = query[2*i + 1];
        query[2*i] = q0 * cos_val - q1 * sin_val;
        query[2*i + 1] = q0 * sin_val + q1 * cos_val;

        // 旋转 K
        float k0 = key[2*i];
        float k1 = key[2*i + 1];
        key[2*i] = k0 * cos_val - k1 * sin_val;
        key[2*i + 1] = k0 * sin_val + k1 * cos_val;
    }
}
```

#### SwiGLU FFN 实现

```cpp
// SwiGLU 前馈网络
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

---

### 2.4 KV Cache 模块

#### 设计目标
- 高效存储 Key-Value 对
- 支持多种缓存策略
- 内存友好的实现

#### 缓存策略

##### 标准缓存
```
优点: 简单、随机访问
缺点: 内存固定分配
适用: 短序列、已知最大长度
```

##### 滑动窗口缓存
```
优点: 内存使用固定
缺点: 丢失早期信息
适用: 长对话、流式处理
```

##### 分页缓存（PagedAttention）
```
优点: 内存高效、无碎片
缺点: 实现复杂
适用: 生产环境、长序列
```

#### 数据结构

```cpp
// 标准 KV Cache
struct KVCache {
    // [n_layers][n_ctx][n_embd]
    std::vector<std::vector<float>> keys;
    std::vector<std::vector<float>> values;
    uint32_t current_pos;
};

// 分页 KV Cache
struct PagedKVCache {
    struct Page {
        static constexpr uint32_t PAGE_SIZE = 16;
        std::vector<float> keys;   // [PAGE_SIZE * n_embd]
        std::vector<float> values;
        uint32_t used_slots;
    };

    // 每层的页面列表
    std::vector<std::vector<Page*>> layer_pages;
    // 空闲页面池
    std::vector<Page*> free_pages;
};
```

#### 使用流程

```cpp
// 1. 初始化
KVCache cache;
cache.initialize(n_layers, n_ctx, n_embd, n_head);

// 2. 存储
for (uint32_t pos = 0; pos < seq_len; ++pos) {
    // 计算当前 token 的 K, V
    compute_kv(token[pos], &K, &V);

    // 存储到缓存
    cache.store(layer, pos, K, V);
}

// 3. 检索
const float* cached_keys = cache.get_keys(layer);
const float* cached_values = cache.get_values(layer);

// 4. 计算注意力
for (uint32_t pos = 0; pos <= current_pos; ++pos) {
    float score = dot_product(Q, cached_keys[pos]);
    // ...
}
```

---

### 2.5 Sampler 模块

#### 设计目标
- 支持多种采样策略
- 可组合的采样流水线
- 高效的概率计算

#### 采样策略

##### Greedy 采样
```cpp
int32_t greedy(const std::vector<float>& logits) {
    return argmax(logits);
}
```

##### Temperature 采样
```cpp
void apply_temperature(std::vector<float>& logits, float temp) {
    for (auto& logit : logits) {
        logit /= temp;
    }
}
```

##### Top-K 采样
```cpp
void apply_top_k(std::vector<float>& logits, uint32_t k) {
    // 找到第 k 大的值
    nth_element(logits.begin(), logits.begin() + k, logits.end(), greater<>());
    // 将低于阈值的设为 -inf
    float threshold = logits[k];
    for (auto& logit : logits) {
        if (logit < threshold) logit = -INFINITY;
    }
}
```

##### Top-P (Nucleus) 采样
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

#### 采样流水线

```cpp
int32_t sample(const std::vector<float>& logits,
               const SamplingParams& params) {
    auto modified_logits = logits;

    // 1. 应用重复惩罚
    if (params.repetition_penalty != 1.0) {
        apply_repetition_penalty(modified_logits, history);
    }

    // 2. 应用温度
    if (params.temperature > 0) {
        apply_temperature(modified_logits, params.temperature);
    }

    // 3. 应用 Top-K
    if (params.top_k > 0) {
        apply_top_k(modified_logits, params.top_k);
    }

    // 4. 应用 Top-P
    if (params.top_p < 1.0) {
        apply_top_p(modified_logits, params.top_p);
    }

    // 5. 采样
    auto probs = softmax(modified_logits);
    return multinomial_sample(probs);
}
```

---

## 3. 接口设计

### 3.1 核心接口

```cpp
// 推理引擎接口
class LLMEngine {
public:
    // 初始化
    bool initialize(const EngineConfig& config);
    bool load_model(const std::string& model_path);

    // 推理
    GenerationResult generate(const std::string& prompt,
                             const SamplingParams& params = {});

    GenerationResult generate_stream(const std::string& prompt,
                                    const SamplingParams& params,
                                    StreamCallback callback);

    // 工具方法
    std::vector<int32_t> tokenize(const std::string& text, bool add_bos = true);
    std::string detokenize(const std::vector<int32_t>& tokens);

    // 状态查询
    ModelInfo get_model_info() const;
    uint32_t context_length() const;
    uint32_t vocab_size() const;

    // 重置
    void reset();
};
```

### 3.2 配置接口

```cpp
// 引擎配置
struct EngineConfig {
    std::string model_path;
    uint32_t n_ctx = 2048;
    uint32_t n_batch = 512;
    uint32_t n_threads = 4;
    bool use_mmap = true;
    KVCacheType kv_cache_type = KVCacheType::STANDARD;
};

// 采样参数
struct SamplingParams {
    float temperature = 1.0;
    float top_p = 1.0;
    uint32_t top_k = 0;
    float repetition_penalty = 1.0;
    uint32_t max_tokens = 256;
    bool do_sample = true;
};
```

### 3.3 结果接口

```cpp
// 生成结果
struct GenerationResult {
    std::string text;
    std::vector<int32_t> tokens;
    float tokens_per_second;
    uint32_t prompt_tokens;
    uint32_t generated_tokens;
    bool finished;
    std::string stop_reason;
};
```

---

## 4. 数据结构设计

### 4.1 模型权重

```cpp
// 线性层权重
struct LinearWeights {
    const float* weight;  // [out_features, in_features]
    const float* bias;    // [out_features] (可选)
    uint32_t in_features;
    uint32_t out_features;
};

// LayerNorm 权重
struct LayerNormWeights {
    const float* weight;  // [normalized_shape]
    const float* bias;    // [normalized_shape] (可选)
    float eps;
};

// Transformer 层权重
struct TransformerBlockWeights {
    // 注意力
    LinearWeights q_proj, k_proj, v_proj, o_proj;

    // FFN
    LinearWeights gate_proj, up_proj, down_proj;

    // Norm
    LayerNormWeights input_norm, post_attention_norm;
};

// 完整模型权重
struct ModelWeights {
    const float* token_embedding;
    std::vector<TransformerBlockWeights> layers;
    LayerNormWeights final_norm;
    LinearWeights lm_head;
};
```

### 4.2 缓存数据

```cpp
// KV Cache
struct KVCache {
    // 存储: [n_layers][n_ctx][n_embd]
    std::vector<std::vector<float>> keys;
    std::vector<std::vector<float>> values;
    uint32_t current_pos;
};

// 分页缓存
struct PagedKVCache {
    struct Page {
        std::vector<float> keys;   // [PAGE_SIZE * n_embd]
        std::vector<float> values;
        uint32_t used_slots;
    };

    std::vector<std::vector<Page*>> layer_pages;
    std::vector<Page*> free_pages;
};
```

---

## 5. 算法设计

### 5.1 矩阵乘法

```cpp
// 简单的矩阵乘法
void matmul(const float* A, const float* B, float* C,
            uint32_t M, uint32_t N, uint32_t K) {
    for (uint32_t i = 0; i < M; ++i) {
        for (uint32_t j = 0; j < N; ++j) {
            float sum = 0;
            for (uint32_t k = 0; k < K; ++k) {
                sum += A[i * K + k] * B[k * N + j];
            }
            C[i * N + j] = sum;
        }
    }
}

// 优化：使用 SIMD 指令
// 优化：循环展开
// 优化：缓存友好的访问模式
```

### 5.2 Softmax

```cpp
// 数值稳定的 Softmax
void softmax(float* data, uint32_t size) {
    // 找最大值（数值稳定）
    float max_val = *max_element(data, data + size);

    // 计算 exp 和 sum
    float sum = 0;
    for (uint32_t i = 0; i < size; ++i) {
        data[i] = exp(data[i] - max_val);
        sum += data[i];
    }

    // 归一化
    for (uint32_t i = 0; i < size; ++i) {
        data[i] /= sum;
    }
}
```

### 5.3 RMSNorm

```cpp
// RMS 归一化
void rms_norm(const float* input, float* output,
              const float* weight, uint32_t size, float eps) {
    // 计算 RMS
    float rms = 0;
    for (uint32_t i = 0; i < size; ++i) {
        rms += input[i] * input[i];
    }
    rms = sqrt(rms / size + eps);

    // 归一化
    float inv_rms = 1.0f / rms;
    for (uint32_t i = 0; i < size; ++i) {
        output[i] = input[i] * inv_rms * weight[i];
    }
}
```

---

## 6. 性能优化设计

### 6.1 内存优化

1. **内存映射 (mmap)**
   - 直接映射模型文件到内存
   - 减少加载时间
   - 共享内存

2. **延迟加载**
   - 只在需要时加载权重
   - 减少初始内存占用

3. **内存池**
   - 预分配计算缓冲区
   - 避免频繁分配释放

### 6.2 计算优化

1. **SIMD 指令**
   - 使用 AVX2/NEON 加速向量运算
   - 矩阵乘法优化

2. **循环展开**
   - 减少循环开销
   - 提高指令级并行

3. **缓存优化**
   - 数据局部性
   - 预取指令

### 6.3 并行优化

1. **多线程**
   - OpenMP 并行
   - 线程池

2. **批处理**
   - 同时处理多个 token
   - 提高吞吐量

---

## 7. 错误处理设计

### 7.1 错误类型

```cpp
enum class ErrorCode {
    SUCCESS = 0,
    FILE_NOT_FOUND,
    INVALID_FORMAT,
    OUT_OF_MEMORY,
    INVALID_PARAM,
    RUNTIME_ERROR
};
```

### 7.2 错误传播

```cpp
// 使用返回值传播错误
bool load_model(const std::string& path) {
    if (!file_exists(path)) {
        std::cerr << "File not found: " << path << std::endl;
        return false;
    }

    if (!parse_gguf(path)) {
        std::cerr << "Invalid GGUF format" << std::endl;
        return false;
    }

    return true;
}
```

### 7.3 日志系统

```cpp
// 简单的日志系统
enum LogLevel { DEBUG, INFO, WARNING, ERROR };

void log(LogLevel level, const std::string& message) {
    const char* level_str[] = {"DEBUG", "INFO", "WARNING", "ERROR"};
    std::cout << "[" << level_str[level] << "] " << message << std::endl;
}
```

---

## 8. 测试设计

### 8.1 单元测试

```cpp
// 测试 Tokenizer
TEST(TokenizerTest, EncodeDecode) {
    BPETokenizer tokenizer;
    tokenizer.initialize(config, vocab);

    auto tokens = tokenizer.encode("hello world");
    auto decoded = tokenizer.decode(tokens);

    ASSERT_EQ(decoded, "hello world");
}

// 测试 KV Cache
TEST(KVCacheTest, StoreRetrieve) {
    KVCache cache;
    cache.initialize(2, 10, 4, 2);

    std::vector<float> key = {1, 2, 3, 4};
    std::vector<float> value = {5, 6, 7, 8};

    cache.store(0, 0, key.data(), value.data());

    auto stored = cache.get_keys(0);
    ASSERT_EQ(stored[0], 1);
    ASSERT_EQ(stored[1], 2);
}
```

### 8.2 集成测试

```cpp
// 测试完整推理流程
TEST(EngineTest, GenerateText) {
    LLMEngine engine;
    engine.initialize(config);
    engine.load_model("test.gguf");

    auto result = engine.generate("Hello");

    ASSERT_FALSE(result.text.empty());
    ASSERT_GT(result.tokens_per_second, 0);
}
```

### 8.3 性能测试

```cpp
// 基准测试
TEST(BenchmarkTest, Throughput) {
    auto start = steady_clock::now();

    for (int i = 0; i < 100; ++i) {
        engine.generate("Test prompt");
    }

    auto duration = duration_cast<milliseconds>(steady_clock::now() - start);
    float tokens_per_second = 100 * 256 / (duration.count() / 1000.0);

    ASSERT_GT(tokens_per_second, 10);  // 至少 10 tokens/s
}
```

---

## 9. 部署设计

### 9.1 构建系统

```cmake
cmake_minimum_required(VERSION 3.14)
project(LocalLLMEngine)

set(CMAKE_CXX_STANDARD 17)

add_library(llm_engine STATIC
    src/gguf_loader.cpp
    src/tokenizer.cpp
    src/transformer.cpp
    src/kv_cache.cpp
    src/sampler.cpp
    src/engine.cpp
)

add_executable(llm_engine_cli src/main.cpp)
target_link_libraries(llm_engine_cli llm_engine)
```

### 9.2 安装布局

```
/usr/local/
├── include/
│   └── llm_engine/
│       ├── gguf_loader.h
│       ├── tokenizer.h
│       ├── transformer.h
│       ├── kv_cache.h
│       ├── sampler.h
│       └── engine.h
├── lib/
│   └── libllm_engine.a
└── bin/
    └── llm_engine
```

---

## 10. 总结

本设计文档详细描述了 Local LLM Engine 的技术架构和实现细节。关键设计决策包括：

1. **模块化设计**: 各组件独立，便于理解和扩展
2. **接口清晰**: 简单易用的 API
3. **性能优先**: 考虑内存和计算优化
4. **可测试性**: 完整的测试覆盖
5. **学习友好**: 详细的注释和文档

通过这个设计，我们实现了一个功能完整、性能合理、易于理解的 LLM 推理引擎。
