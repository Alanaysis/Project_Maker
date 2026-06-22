#pragma once

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <thread>
#include <atomic>
#include <queue>
#include <mutex>
#include <condition_variable>

#include "gguf_loader.h"
#include "tokenizer.h"
#include "transformer.h"
#include "kv_cache.h"
#include "sampler.h"

namespace llm_engine {

// Generation result
struct GenerationResult {
    std::string text;
    std::vector<int32_t> tokens;
    float tokens_per_second = 0.0f;
    uint32_t prompt_tokens = 0;
    uint32_t generated_tokens = 0;
    bool finished = false;
    std::string stop_reason;  // "eos", "max_tokens", "user_stop"
};

// Streaming callback
using StreamCallback = std::function<bool(const std::string& token_text, bool is_last)>;

// Engine configuration
struct EngineConfig {
    std::string model_path;
    uint32_t n_ctx = 2048;           // Context length
    uint32_t n_batch = 512;          // Batch size for prompt processing
    uint32_t n_threads = 4;          // Number of threads
    bool use_mmap = true;            // Use memory mapping
    bool use_mlock = false;          // Lock memory
    KVCacheType kv_cache_type = KVCacheType::STANDARD;
    uint32_t n_gpu_layers = 0;       // Layers to offload to GPU (not implemented)
    float rope_freq_scale = 1.0f;    // RoPE frequency scaling
};

// Main inference engine class
class LLMEngine {
public:
    LLMEngine();
    ~LLMEngine();

    // Initialize engine with configuration
    bool initialize(const EngineConfig& config);

    // Load model from GGUF file
    bool load_model(const std::string& model_path);

    // Generate text from prompt
    GenerationResult generate(const std::string& prompt,
                             const SamplingParams& params = {});

    // Generate text with streaming callback
    GenerationResult generate_stream(const std::string& prompt,
                                    const SamplingParams& params,
                                    StreamCallback callback);

    // Tokenize text
    std::vector<int32_t> tokenize(const std::string& text, bool add_bos = true);

    // Detokenize tokens
    std::string detokenize(const std::vector<int32_t>& tokens);

    // Get model info
    struct ModelInfo {
        std::string architecture;
        std::string name;
        uint32_t n_vocab;
        uint32_t n_embd;
        uint32_t n_head;
        uint32_t n_layer;
        uint32_t n_ctx;
        uint32_t n_ff;
        float rope_theta;
    };

    ModelInfo get_model_info() const;

    // Check if engine is ready
    bool is_ready() const { return initialized_; }

    // Get context length
    uint32_t context_length() const;

    // Get vocabulary size
    uint32_t vocab_size() const;

    // Reset engine state
    void reset();

private:
    // Process prompt tokens (prefill phase)
    bool process_prompt(const std::vector<int32_t>& tokens);

    // Generate single token (decode phase)
    int32_t generate_token(uint32_t position);

    // Update KV cache
    void update_cache(uint32_t position);

    // Components
    std::unique_ptr<GGUFLoader> loader_;
    std::unique_ptr<Tokenizer> tokenizer_;
    std::unique_ptr<Transformer> transformer_;
    std::unique_ptr<KVCache> kv_cache_;
    std::unique_ptr<Sampler> sampler_;

    // Model state
    bool initialized_ = false;
    EngineConfig config_;
    ModelInfo model_info_;
    int32_t last_generated_token_ = 0;

    // Timing
    std::chrono::steady_clock::time_point start_time_;
};

// Batch inference engine (for multiple sequences)
class BatchLLMEngine {
public:
    BatchLLMEngine() = default;
    ~BatchLLMEngine() = default;

    // Initialize with engine configuration
    bool initialize(const EngineConfig& config, uint32_t max_batch_size);

    // Add sequence to batch
    int32_t add_sequence(const std::string& prompt, const SamplingParams& params);

    // Process one step for all sequences
    // Returns completed sequence IDs
    std::vector<int32_t> step();

    // Get generation result for a sequence
    GenerationResult get_result(int32_t sequence_id) const;

    // Remove completed sequence
    void remove_sequence(int32_t sequence_id);

    // Get number of active sequences
    uint32_t active_sequences() const;

    // Get max batch size
    uint32_t max_batch_size() const { return max_batch_size_; }

private:
    struct Sequence {
        int32_t id;
        std::vector<int32_t> tokens;
        SamplingParams params;
        bool finished;
        GenerationResult result;
    };

    std::unique_ptr<LLMEngine> engine_;
    std::vector<Sequence> sequences_;
    uint32_t max_batch_size_ = 1;
    int32_t next_id_ = 0;
};

// Continuous batching server (for production use)
class ContinuousBatchServer {
public:
    ContinuousBatchServer() = default;
    ~ContinuousBatchServer() = default;

    // Initialize server
    bool initialize(const EngineConfig& config, uint32_t max_batch_size);

    // Submit generation request
    int32_t submit_request(const std::string& prompt, const SamplingParams& params);

    // Cancel request
    void cancel_request(int32_t request_id);

    // Get completed requests
    std::vector<std::pair<int32_t, GenerationResult>> get_completed();

    // Start processing thread
    void start();

    // Stop processing
    void stop();

    // Get server status
    struct Status {
        uint32_t active_requests;
        uint32_t waiting_requests;
        uint32_t completed_requests;
        float avg_tokens_per_second;
    };

    Status get_status() const;

private:
    void processing_loop();

    std::unique_ptr<BatchLLMEngine> batch_engine_;
    std::thread processing_thread_;
    std::atomic<bool> running_{false};

    std::queue<std::pair<int32_t, std::pair<std::string, SamplingParams>>> request_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;

    std::queue<std::pair<int32_t, GenerationResult>> completed_queue_;
    std::mutex completed_mutex_;

    Status status_;
    std::mutex status_mutex_;
};

// Factory function to create engine
std::unique_ptr<LLMEngine> create_engine(const EngineConfig& config);

} // namespace llm_engine
