#include "transformer.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <cstring>
#include <iostream>

namespace llm_engine {

bool Transformer::initialize(const GGUFModel& model) {
    // Extract model configuration
    config_.vocab_size = model.n_vocab;
    config_.n_embd = model.n_embd;
    config_.n_head = model.n_head;
    config_.n_layer = model.n_layer;
    config_.n_ctx = model.n_ctx;
    config_.n_ff = model.n_ff;
    config_.n_head_kv = model.n_head_kv;
    config_.use_gqa = (model.n_head_kv > 0 && model.n_head_kv != model.n_head);

    // Load RoPE theta from metadata
    GGUFMetadataValue value;
    if (model.metadata.count("llama.rope.freq_base")) {
        config_.rope_theta = model.metadata.at("llama.rope.freq_base").float32;
    }

    // Calculate RoPE dimension
    config_.rope_dim = config_.n_embd / config_.n_head;

    // Allocate temporary buffers
    hidden_buffer_.resize(config_.n_embd);
    attention_buffer_.resize(config_.n_embd);
    ffn_buffer_.resize(config_.n_ff);
    query_buffer_.resize(config_.n_embd);
    key_buffer_.resize(config_.n_embd);
    value_buffer_.resize(config_.n_embd);

    // Load token embedding
    const uint8_t* embd_data = model.tensor_data.data();
    for (const auto& info : model.tensor_infos) {
        if (info.name == "token_embd.weight") {
            weights_.token_embedding = reinterpret_cast<const float*>(
                model.tensor_data.data() + info.offset);
            break;
        }
    }

    // Load transformer layers
    weights_.layers.resize(config_.n_layer);

    for (uint32_t layer = 0; layer < config_.n_layer; ++layer) {
        TransformerBlockWeights& layer_weights = weights_.layers[layer];

        // Helper lambda to find tensor
        auto find_tensor = [&](const std::string& name) -> const float* {
            for (const auto& info : model.tensor_infos) {
                if (info.name == name) {
                    return reinterpret_cast<const float*>(
                        model.tensor_data.data() + info.offset);
                }
            }
            return nullptr;
        };

        // Load attention weights
        std::string layer_prefix = "blk." + std::to_string(layer) + ".";

        layer_weights.q_proj.weight = find_tensor(layer_prefix + "attn_q.weight");
        layer_weights.k_proj.weight = find_tensor(layer_prefix + "attn_k.weight");
        layer_weights.v_proj.weight = find_tensor(layer_prefix + "attn_v.weight");
        layer_weights.o_proj.weight = find_tensor(layer_prefix + "attn_output.weight");

        // Load FFN weights
        layer_weights.gate_proj.weight = find_tensor(layer_prefix + "ffn_gate.weight");
        layer_weights.up_proj.weight = find_tensor(layer_prefix + "ffn_up.weight");
        layer_weights.down_proj.weight = find_tensor(layer_prefix + "ffn_down.weight");

        // Load layer norms
        layer_weights.input_norm.weight = find_tensor(layer_prefix + "attn_norm.weight");
        layer_weights.post_attention_norm.weight = find_tensor(layer_prefix + "ffn_norm.weight");

        // Set dimensions
        layer_weights.q_proj.in_features = config_.n_embd;
        layer_weights.q_proj.out_features = config_.n_embd;
        layer_weights.k_proj.in_features = config_.n_embd;
        layer_weights.k_proj.out_features = config_.use_gqa ?
            (config_.n_embd / config_.n_head * config_.n_head_kv) : config_.n_embd;
        layer_weights.v_proj.in_features = config_.n_embd;
        layer_weights.v_proj.out_features = layer_weights.k_proj.out_features;
        layer_weights.o_proj.in_features = config_.n_embd;
        layer_weights.o_proj.out_features = config_.n_embd;

        layer_weights.gate_proj.in_features = config_.n_embd;
        layer_weights.gate_proj.out_features = config_.n_ff;
        layer_weights.up_proj.in_features = config_.n_embd;
        layer_weights.up_proj.out_features = config_.n_ff;
        layer_weights.down_proj.in_features = config_.n_ff;
        layer_weights.down_proj.out_features = config_.n_embd;

        layer_weights.input_norm.normalized_shape = config_.n_embd;
        layer_weights.post_attention_norm.normalized_shape = config_.n_embd;
    }

    // Load final layer norm
    weights_.final_norm.weight = nullptr;
    for (const auto& info : model.tensor_infos) {
        if (info.name == "output_norm.weight") {
            weights_.final_norm.weight = reinterpret_cast<const float*>(
                model.tensor_data.data() + info.offset);
            break;
        }
    }
    weights_.final_norm.normalized_shape = config_.n_embd;

    // Load output projection (lm_head)
    for (const auto& info : model.tensor_infos) {
        if (info.name == "output.weight") {
            weights_.lm_head.weight = reinterpret_cast<const float*>(
                model.tensor_data.data() + info.offset);
            break;
        }
    }
    weights_.lm_head.in_features = config_.n_embd;
    weights_.lm_head.out_features = config_.vocab_size;

    // Load RoPE frequencies
    for (const auto& info : model.tensor_infos) {
        if (info.name == "rope_freqs.weight") {
            weights_.rope_freqs = reinterpret_cast<const float*>(
                model.tensor_data.data() + info.offset);
            break;
        }
    }

    std::cout << "Transformer model initialized successfully" << std::endl;
    return true;
}

std::vector<float> Transformer::forward(int32_t token, uint32_t position) {
    // Embedding lookup
    embedding_lookup(token, hidden_buffer_.data(), weights_.token_embedding, config_.n_embd);

    // Process through transformer layers
    for (uint32_t layer = 0; layer < config_.n_layer; ++layer) {
        const TransformerBlockWeights& layer_weights = weights_.layers[layer];

        // Save residual
        std::vector<float> residual(hidden_buffer_);

        // Pre-attention layer norm
        rms_norm(hidden_buffer_.data(), hidden_buffer_.data(),
                layer_weights.input_norm, config_.n_embd);

        // Compute Q, K, V
        linear(hidden_buffer_.data(), query_buffer_.data(), layer_weights.q_proj);
        linear(hidden_buffer_.data(), key_buffer_.data(), layer_weights.k_proj);
        linear(hidden_buffer_.data(), value_buffer_.data(), layer_weights.v_proj);

        // Apply RoPE
        apply_rope(query_buffer_.data(), key_buffer_.data(), position,
                  config_.n_head, config_.rope_dim);

        // Compute attention (simplified - without KV cache)
        compute_attention(query_buffer_.data(), key_buffer_.data(), value_buffer_.data(),
                         attention_buffer_.data(), config_.n_head, config_.rope_dim,
                         1, position);

        // Output projection
        linear(attention_buffer_.data(), hidden_buffer_.data(), layer_weights.o_proj);

        // Residual connection
        for (uint32_t i = 0; i < config_.n_embd; ++i) {
            hidden_buffer_[i] += residual[i];
        }

        // Save residual for FFN
        residual = hidden_buffer_;

        // Post-attention layer norm
        rms_norm(hidden_buffer_.data(), hidden_buffer_.data(),
                layer_weights.post_attention_norm, config_.n_embd);

        // Feed-forward network
        feed_forward(hidden_buffer_.data(), ffn_buffer_.data(), layer_weights);

        // Residual connection
        for (uint32_t i = 0; i < config_.n_embd; ++i) {
            hidden_buffer_[i] = residual[i] + ffn_buffer_[i];
        }
    }

    // Final layer norm
    rms_norm(hidden_buffer_.data(), hidden_buffer_.data(),
            weights_.final_norm, config_.n_embd);

    // Output projection (lm_head)
    std::vector<float> logits(config_.vocab_size);
    linear(hidden_buffer_.data(), logits.data(), weights_.lm_head);

    return logits;
}

std::vector<float> Transformer::forward_with_cache(int32_t token, uint32_t position,
                                                    KVCache& cache) {
    // Embedding lookup
    embedding_lookup(token, hidden_buffer_.data(), weights_.token_embedding, config_.n_embd);

    // Process through transformer layers
    for (uint32_t layer = 0; layer < config_.n_layer; ++layer) {
        const TransformerBlockWeights& layer_weights = weights_.layers[layer];

        // Save residual
        std::vector<float> residual(hidden_buffer_);

        // Pre-attention layer norm
        rms_norm(hidden_buffer_.data(), hidden_buffer_.data(),
                layer_weights.input_norm, config_.n_embd);

        // Compute Q, K, V
        linear(hidden_buffer_.data(), query_buffer_.data(), layer_weights.q_proj);
        linear(hidden_buffer_.data(), key_buffer_.data(), layer_weights.k_proj);
        linear(hidden_buffer_.data(), value_buffer_.data(), layer_weights.v_proj);

        // Apply RoPE
        apply_rope(query_buffer_.data(), key_buffer_.data(), position,
                  config_.n_head, config_.rope_dim);

        // Store K, V in cache
        cache.store(layer, position, key_buffer_.data(), value_buffer_.data());

        // Compute attention with KV cache
        multi_head_attention(hidden_buffer_.data(), attention_buffer_.data(),
                           position, cache, layer, layer_weights);

        // Output projection
        linear(attention_buffer_.data(), hidden_buffer_.data(), layer_weights.o_proj);

        // Residual connection
        for (uint32_t i = 0; i < config_.n_embd; ++i) {
            hidden_buffer_[i] += residual[i];
        }

        // Save residual for FFN
        residual = hidden_buffer_;

        // Post-attention layer norm
        rms_norm(hidden_buffer_.data(), hidden_buffer_.data(),
                layer_weights.post_attention_norm, config_.n_embd);

        // Feed-forward network
        feed_forward(hidden_buffer_.data(), ffn_buffer_.data(), layer_weights);

        // Residual connection
        for (uint32_t i = 0; i < config_.n_embd; ++i) {
            hidden_buffer_[i] = residual[i] + ffn_buffer_[i];
        }
    }

    // Final layer norm
    rms_norm(hidden_buffer_.data(), hidden_buffer_.data(),
            weights_.final_norm, config_.n_embd);

    // Output projection (lm_head)
    std::vector<float> logits(config_.vocab_size);
    linear(hidden_buffer_.data(), logits.data(), weights_.lm_head);

    return logits;
}

void Transformer::compute_attention(const float* query, const float* key, const float* value,
                                     float* output, uint32_t n_head, uint32_t head_dim,
                                     uint32_t seq_len, uint32_t position) {
    // Simplified attention for single token (no KV cache)
    // In a full implementation, this would handle the complete attention computation

    // For now, just copy value as a placeholder
    std::memcpy(output, value, config_.n_embd * sizeof(float));
}

void Transformer::multi_head_attention(const float* hidden, float* output,
                                        uint32_t position, KVCache& cache,
                                        uint32_t layer_index,
                                        const TransformerBlockWeights& layer) {
    uint32_t head_dim = config_.n_embd / config_.n_head;
    uint32_t seq_len = position + 1;

    // For each attention head
    for (uint32_t h = 0; h < config_.n_head; ++h) {
        float* q_head = query_buffer_.data() + h * head_dim;

        // Compute attention scores
        std::vector<float> scores(seq_len);
        const float* k_cache = cache.get_keys(layer_index);
        const float* v_cache = cache.get_values(layer_index);

        for (uint32_t pos = 0; pos < seq_len; ++pos) {
            const float* k_pos = k_cache + pos * config_.n_embd + h * head_dim;

            // Dot product attention score
            float score = 0.0f;
            for (uint32_t d = 0; d < head_dim; ++d) {
                score += q_head[d] * k_pos[d];
            }

            // Scale
            score /= std::sqrt(static_cast<float>(head_dim));
            scores[pos] = score;
        }

        // Softmax
        softmax(scores.data(), seq_len);

        // Weighted sum of values
        float* o_head = output + h * head_dim;
        std::memset(o_head, 0, head_dim * sizeof(float));

        for (uint32_t pos = 0; pos < seq_len; ++pos) {
            const float* v_pos = v_cache + pos * config_.n_embd + h * head_dim;
            float weight = scores[pos];

            for (uint32_t d = 0; d < head_dim; ++d) {
                o_head[d] += weight * v_pos[d];
            }
        }
    }
}

void Transformer::feed_forward(const float* input, float* output,
                               const TransformerBlockWeights& layer) {
    // SwiGLU FFN (used in LLaMA)
    // gate_proj(x) * silu(up_proj(x))

    std::vector<float> gate(config_.n_ff);
    std::vector<float> up(config_.n_ff);

    // Compute gate and up projections
    linear(input, gate.data(), layer.gate_proj);
    linear(input, up.data(), layer.up_proj);

    // Apply SiLU to gate and multiply with up
    std::vector<float> intermediate(config_.n_ff);
    for (uint32_t i = 0; i < config_.n_ff; ++i) {
        intermediate[i] = silu(gate[i]) * up[i];
    }

    // Down projection
    linear(intermediate.data(), output, layer.down_proj);
}

void Transformer::layer_norm(const float* input, float* output,
                             const LayerNormWeights& weights, uint32_t size) {
    // Standard Layer Normalization
    float mean = 0.0f;
    for (uint32_t i = 0; i < size; ++i) {
        mean += input[i];
    }
    mean /= size;

    float variance = 0.0f;
    for (uint32_t i = 0; i < size; ++i) {
        float diff = input[i] - mean;
        variance += diff * diff;
    }
    variance /= size;

    float inv_std = 1.0f / std::sqrt(variance + weights.eps);

    for (uint32_t i = 0; i < size; ++i) {
        float normalized = (input[i] - mean) * inv_std;
        output[i] = normalized * weights.weight[i];
        if (weights.bias) {
            output[i] += weights.bias[i];
        }
    }
}

void Transformer::rms_norm(const float* input, float* output,
                           const LayerNormWeights& weights, uint32_t size) {
    // RMS Normalization (used in LLaMA)
    // More efficient than LayerNorm - no mean subtraction

    float rms = 0.0f;
    for (uint32_t i = 0; i < size; ++i) {
        rms += input[i] * input[i];
    }
    rms = std::sqrt(rms / size + weights.eps);

    float inv_rms = 1.0f / rms;

    for (uint32_t i = 0; i < size; ++i) {
        output[i] = input[i] * inv_rms * weights.weight[i];
    }
}

void Transformer::apply_rope(float* query, float* key, uint32_t position,
                              uint32_t n_head, uint32_t head_dim) {
    // Rotary Position Embedding (RoPE)
    // Applies rotation to query and key based on position

    uint32_t half_dim = head_dim / 2;

    for (uint32_t h = 0; h < n_head; ++h) {
        float* q = query + h * head_dim;
        float* k = key + h * head_dim;

        for (uint32_t i = 0; i < half_dim; ++i) {
            // Calculate rotation angle
            float freq = 1.0f / std::pow(config_.rope_theta,
                                         static_cast<float>(2 * i) / head_dim);
            float angle = position * freq;

            float cos_val = std::cos(angle);
            float sin_val = std::sin(angle);

            // Apply rotation to query
            float q0 = q[2 * i];
            float q1 = q[2 * i + 1];
            q[2 * i] = q0 * cos_val - q1 * sin_val;
            q[2 * i + 1] = q0 * sin_val + q1 * cos_val;

            // Apply rotation to key
            float k0 = k[2 * i];
            float k1 = k[2 * i + 1];
            k[2 * i] = k0 * cos_val - k1 * sin_val;
            k[2 * i + 1] = k0 * sin_val + k1 * cos_val;
        }
    }
}

void Transformer::softmax(float* data, uint32_t size) {
    // Find max for numerical stability
    float max_val = *std::max_element(data, data + size);

    // Compute exp and sum
    float sum = 0.0f;
    for (uint32_t i = 0; i < size; ++i) {
        data[i] = std::exp(data[i] - max_val);
        sum += data[i];
    }

    // Normalize
    float inv_sum = 1.0f / sum;
    for (uint32_t i = 0; i < size; ++i) {
        data[i] *= inv_sum;
    }
}

void Transformer::linear(const float* input, float* output,
                         const LinearWeights& weights) {
    // Matrix multiplication: output = input @ weight^T + bias
    uint32_t in_features = weights.in_features;
    uint32_t out_features = weights.out_features;

    for (uint32_t out = 0; out < out_features; ++out) {
        float sum = 0.0f;
        const float* weight_row = weights.weight + out * in_features;

        for (uint32_t in = 0; in < in_features; ++in) {
            sum += input[in] * weight_row[in];
        }

        if (weights.bias) {
            sum += weights.bias[out];
        }

        output[out] = sum;
    }
}

void Transformer::embedding_lookup(int32_t token, float* output,
                                   const float* embedding_table, uint32_t n_embd) {
    // Validate token is within vocabulary bounds
    if (token < 0 || static_cast<uint32_t>(token) >= config_.vocab_size) {
        std::cerr << "Warning: token " << token
                  << " out of range [0, " << config_.vocab_size
                  << "), using zero embedding" << std::endl;
        std::memset(output, 0, n_embd * sizeof(float));
        return;
    }

    // Embedding lookup
    const float* emb = embedding_table + token * n_embd;
    std::memcpy(output, emb, n_embd * sizeof(float));
}

} // namespace llm_engine
