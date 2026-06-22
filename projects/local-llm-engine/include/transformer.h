#pragma once

#include <vector>
#include <cstdint>
#include <memory>
#include <cmath>
#include <algorithm>
#include <cstring>

#include "gguf_loader.h"
#include "kv_cache.h"

namespace llm_engine {

// Forward declarations
class KVCache;

// Linear layer weights
struct LinearWeights {
    const float* weight = nullptr;
    const float* bias = nullptr;
    uint32_t in_features = 0;
    uint32_t out_features = 0;
};

// LayerNorm weights
struct LayerNormWeights {
    const float* weight = nullptr;
    const float* bias = nullptr;
    uint32_t normalized_shape = 0;
    float eps = 1e-5f;
};

// Transformer block weights
struct TransformerBlockWeights {
    // Attention weights
    LinearWeights q_proj;
    LinearWeights k_proj;
    LinearWeights v_proj;
    LinearWeights o_proj;

    // FFN weights
    LinearWeights gate_proj;
    LinearWeights up_proj;
    LinearWeights down_proj;

    // Layer norms
    LayerNormWeights input_norm;
    LayerNormWeights post_attention_norm;
};

// Model weights
struct ModelWeights {
    // Token embedding
    const float* token_embedding = nullptr;
    uint32_t vocab_size = 0;
    uint32_t n_embd = 0;

    // Transformer blocks
    std::vector<TransformerBlockWeights> layers;

    // Final layer norm
    LayerNormWeights final_norm;

    // Output projection (lm_head)
    LinearWeights lm_head;

    // RoPE frequencies
    const float* rope_freqs = nullptr;
};

// Model configuration
struct ModelConfig {
    uint32_t vocab_size = 0;
    uint32_t n_embd = 0;
    uint32_t n_head = 0;
    uint32_t n_layer = 0;
    uint32_t n_ctx = 0;
    uint32_t n_ff = 0;
    uint32_t n_head_kv = 0;  // For Grouped Query Attention (GQA)
    float norm_eps = 1e-5f;
    float rope_theta = 10000.0f;
    uint32_t rope_dim = 0;
    bool use_gqa = false;
};

// Transformer model class
class Transformer {
public:
    Transformer() = default;
    ~Transformer() = default;

    // Initialize model from GGUF file
    bool initialize(const GGUFModel& model);

    // Forward pass for a single token
    // Returns logits for next token prediction
    std::vector<float> forward(int32_t token, uint32_t position);

    // Forward pass with KV cache
    std::vector<float> forward_with_cache(int32_t token, uint32_t position, KVCache& cache);

    // Get model configuration
    const ModelConfig& config() const { return config_; }

    // Get vocabulary size
    uint32_t vocab_size() const { return config_.vocab_size; }

    // Get context length
    uint32_t context_length() const { return config_.n_ctx; }

private:
    // Attention computation
    void compute_attention(const float* query, const float* key, const float* value,
                          float* output, uint32_t n_head, uint32_t head_dim,
                          uint32_t seq_len, uint32_t position);

    // Multi-head attention with KV cache
    void multi_head_attention(const float* hidden, float* output,
                            uint32_t position, KVCache& cache,
                            uint32_t layer_index,
                            const TransformerBlockWeights& layer);

    // Feed-forward network
    void feed_forward(const float* input, float* output,
                     const TransformerBlockWeights& layer);

    // Layer normalization
    void layer_norm(const float* input, float* output,
                   const LayerNormWeights& weights, uint32_t size);

    // RMS Normalization (used in LLaMA)
    void rms_norm(const float* input, float* output,
                 const LayerNormWeights& weights, uint32_t size);

    // Rotary Position Embedding (RoPE)
    void apply_rope(float* query, float* key, uint32_t position,
                   uint32_t n_head, uint32_t head_dim);

    // SiLU activation (used in LLaMA FFN)
    float silu(float x) const { return x / (1.0f + std::exp(-x)); }

    // Softmax
    void softmax(float* data, uint32_t size);

    // Linear transformation
    void linear(const float* input, float* output,
               const LinearWeights& weights);

    // Embedding lookup
    void embedding_lookup(int32_t token, float* output,
                         const float* embedding_table, uint32_t n_embd);

    // Model weights
    ModelWeights weights_;
    ModelConfig config_;

    // Temporary buffers for computation
    std::vector<float> hidden_buffer_;
    std::vector<float> attention_buffer_;
    std::vector<float> ffn_buffer_;
    std::vector<float> query_buffer_;
    std::vector<float> key_buffer_;
    std::vector<float> value_buffer_;
};

} // namespace llm_engine
