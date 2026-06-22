#include "engine.h"
#include <iostream>
#include <chrono>
#include <sstream>
#include <iomanip>

namespace llm_engine {

LLMEngine::LLMEngine() = default;
LLMEngine::~LLMEngine() = default;

bool LLMEngine::initialize(const EngineConfig& config) {
    config_ = config;

    // Create components
    loader_ = std::make_unique<GGUFLoader>();
    transformer_ = std::make_unique<Transformer>();

    return true;
}

bool LLMEngine::load_model(const std::string& model_path) {
    if (!loader_) {
        std::cerr << "Engine not initialized" << std::endl;
        return false;
    }

    std::cout << "Loading model: " << model_path << std::endl;
    start_time_ = std::chrono::steady_clock::now();

    // Load GGUF model
    if (!loader_->load(model_path)) {
        std::cerr << "Failed to load GGUF model" << std::endl;
        return false;
    }

    const auto& model = loader_->get_model();

    // Initialize transformer
    if (!transformer_->initialize(model)) {
        std::cerr << "Failed to initialize transformer" << std::endl;
        return false;
    }

    // Initialize KV cache
    kv_cache_ = create_kv_cache(config_.kv_cache_type,
                                 model.n_layer,
                                 config_.n_ctx > 0 ? config_.n_ctx : model.n_ctx,
                                 model.n_embd,
                                 model.n_head);

    if (!kv_cache_) {
        std::cerr << "Failed to initialize KV cache" << std::endl;
        return false;
    }

    // Initialize tokenizer
    // Extract tokenizer type from metadata
    GGUFMetadataValue value;
    std::string tokenizer_type = "bpe";

    if (loader_->get_metadata("tokenizer.ggml.model", value)) {
        tokenizer_type = value.string_val;
    }

    tokenizer_ = create_tokenizer(tokenizer_type);

    // Load vocabulary from metadata
    std::vector<std::string> vocab;
    std::vector<float> scores;

    if (loader_->get_metadata("tokenizer.ggml.tokens", value)) {
        vocab.reserve(value.array_val.size());
        for (const auto& token : value.array_val) {
            vocab.push_back(token.string_val);
        }
    }

    if (loader_->get_metadata("tokenizer.ggml.scores", value)) {
        scores.reserve(value.array_val.size());
        for (const auto& score : value.array_val) {
            scores.push_back(score.float32);
        }
    }

    // Configure tokenizer
    TokenizerConfig tok_config;
    tok_config.n_vocab = model.n_vocab;
    tok_config.model_type = tokenizer_type;

    // Get special token IDs
    if (loader_->get_metadata("tokenizer.ggml.bos_token_id", value)) {
        tok_config.bos_token_id = value.uint32;
    }
    if (loader_->get_metadata("tokenizer.ggml.eos_token_id", value)) {
        tok_config.eos_token_id = value.uint32;
    }

    if (!tokenizer_->initialize(tok_config, vocab, scores)) {
        std::cerr << "Failed to initialize tokenizer" << std::endl;
        return false;
    }

    // Initialize sampler with default parameters
    sampler_ = std::make_unique<Sampler>();
    SamplingParams default_params;
    sampler_->initialize(default_params);

    // Store model info
    model_info_.n_vocab = model.n_vocab;
    model_info_.n_embd = model.n_embd;
    model_info_.n_head = model.n_head;
    model_info_.n_layer = model.n_layer;
    model_info_.n_ctx = config_.n_ctx > 0 ? config_.n_ctx : model.n_ctx;
    model_info_.n_ff = model.n_ff;

    if (loader_->get_metadata("general.architecture", value)) {
        model_info_.architecture = value.string_val;
    }
    if (loader_->get_metadata("general.name", value)) {
        model_info_.name = value.string_val;
    }

    auto end_time = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time_);

    std::cout << "Model loaded successfully in " << duration.count() << "ms" << std::endl;
    std::cout << "Architecture: " << model_info_.architecture << std::endl;
    std::cout << "Vocab size: " << model_info_.n_vocab << std::endl;
    std::cout << "Context length: " << model_info_.n_ctx << std::endl;

    initialized_ = true;
    return true;
}

GenerationResult LLMEngine::generate(const std::string& prompt,
                                     const SamplingParams& params) {
    return generate_stream(prompt, params, nullptr);
}

GenerationResult LLMEngine::generate_stream(const std::string& prompt,
                                            const SamplingParams& params,
                                            StreamCallback callback) {
    GenerationResult result;

    if (!initialized_) {
        result.stop_reason = "engine_not_initialized";
        return result;
    }

    // Update sampler parameters
    sampler_->update_params(params);

    // Tokenize prompt
    std::vector<int32_t> prompt_tokens = tokenize(prompt, true);
    result.prompt_tokens = static_cast<uint32_t>(prompt_tokens.size());

    std::cout << "Prompt tokens: " << prompt_tokens.size() << std::endl;

    // Process prompt (prefill phase)
    auto start_time = std::chrono::steady_clock::now();

    if (!process_prompt(prompt_tokens)) {
        result.stop_reason = "prefill_failed";
        return result;
    }

    // Generate tokens (decode phase)
    std::vector<int32_t> generated_tokens;
    std::string generated_text;

    // Set last_generated_token_ to the last prompt token for the first decode step
    if (!prompt_tokens.empty()) {
        last_generated_token_ = prompt_tokens.back();
    }

    for (uint32_t i = 0; i < params.max_tokens; ++i) {
        // Generate next token
        int32_t next_token = generate_token(prompt_tokens.size() + i);

        // Check for EOS
        if (next_token == tokenizer_->eos_token_id()) {
            result.stop_reason = "eos";
            break;
        }

        generated_tokens.push_back(next_token);
        last_generated_token_ = next_token;

        // Decode token
        std::string token_text = tokenizer_->detokenize({next_token});
        generated_text += token_text;

        // Call streaming callback
        if (callback) {
            bool should_continue = callback(token_text, false);
            if (!should_continue) {
                result.stop_reason = "user_stop";
                break;
            }
        }

        // Update KV cache
        update_cache(prompt_tokens.size() + i);
    }

    // Final callback
    if (callback) {
        callback("", true);
    }

    auto end_time = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time_);

    result.text = generated_text;
    result.tokens = generated_tokens;
    result.generated_tokens = static_cast<uint32_t>(generated_tokens.size());
    result.finished = true;

    if (result.stop_reason.empty()) {
        result.stop_reason = "max_tokens";
    }

    // Calculate tokens per second
    float duration_sec = duration.count() / 1000.0f;
    if (duration_sec > 0) {
        result.tokens_per_second = generated_tokens.size() / duration_sec;
    }

    std::cout << "Generated " << generated_tokens.size() << " tokens in "
              << duration.count() << "ms ("
              << std::fixed << std::setprecision(1)
              << result.tokens_per_second << " tokens/s)" << std::endl;

    return result;
}

std::vector<int32_t> LLMEngine::tokenize(const std::string& text, bool add_bos) {
    if (!tokenizer_) {
        return {};
    }
    return tokenizer_->encode(text, add_bos);
}

std::string LLMEngine::detokenize(const std::vector<int32_t>& tokens) {
    if (!tokenizer_) {
        return "";
    }
    return tokenizer_->decode(tokens);
}

LLMEngine::ModelInfo LLMEngine::get_model_info() const {
    return model_info_;
}

uint32_t LLMEngine::context_length() const {
    return model_info_.n_ctx;
}

uint32_t LLMEngine::vocab_size() const {
    return model_info_.n_vocab;
}

void LLMEngine::reset() {
    if (kv_cache_) {
        kv_cache_->clear();
    }
}

bool LLMEngine::process_prompt(const std::vector<int32_t>& tokens) {
    // Prefill phase: process all prompt tokens
    // This is more efficient than processing one token at a time

    for (size_t i = 0; i < tokens.size(); ++i) {
        // Forward pass
        std::vector<float> logits = transformer_->forward_with_cache(
            tokens[i], static_cast<uint32_t>(i), *kv_cache_);

        // Update cache
        kv_cache_->advance();

        // Check for context overflow
        if (kv_cache_->is_full()) {
            std::cerr << "Context length exceeded during prefill" << std::endl;
            return false;
        }
    }

    return true;
}

int32_t LLMEngine::generate_token(uint32_t position) {
    // Forward pass
    std::vector<float> logits = transformer_->forward_with_cache(
        last_generated_token_, position, *kv_cache_);

    // Sample next token
    return sampler_->sample(logits);
}

void LLMEngine::update_cache(uint32_t position) {
    // KV cache is already updated in forward_with_cache
    // This method could handle additional cache management
}

// BatchLLMEngine implementation

bool BatchLLMEngine::initialize(const EngineConfig& config, uint32_t max_batch_size) {
    max_batch_size_ = max_batch_size;
    engine_ = std::make_unique<LLMEngine>();

    if (!engine_->initialize(config)) {
        return false;
    }

    if (!engine_->load_model(config.model_path)) {
        return false;
    }

    return true;
}

int32_t BatchLLMEngine::add_sequence(const std::string& prompt,
                                     const SamplingParams& params) {
    if (sequences_.size() >= max_batch_size_) {
        return -1;  // Batch full
    }

    Sequence seq;
    seq.id = next_id_++;
    seq.params = params;
    seq.finished = false;

    // Tokenize prompt
    seq.tokens = engine_->tokenize(prompt, true);

    sequences_.push_back(std::move(seq));
    return sequences_.back().id;
}

std::vector<int32_t> BatchLLMEngine::step() {
    std::vector<int32_t> completed_ids;

    // Process each sequence
    for (auto& seq : sequences_) {
        if (seq.finished) continue;

        // Generate next token
        // This is simplified - real implementation would batch the computation
        GenerationResult result = engine_->generate("", seq.params);

        if (result.finished) {
            seq.finished = true;
            seq.result = result;
            completed_ids.push_back(seq.id);
        }
    }

    return completed_ids;
}

GenerationResult BatchLLMEngine::get_result(int32_t sequence_id) const {
    for (const auto& seq : sequences_) {
        if (seq.id == sequence_id) {
            return seq.result;
        }
    }
    return {};
}

void BatchLLMEngine::remove_sequence(int32_t sequence_id) {
    sequences_.erase(
        std::remove_if(sequences_.begin(), sequences_.end(),
                       [sequence_id](const Sequence& s) { return s.id == sequence_id; }),
        sequences_.end());
}

uint32_t BatchLLMEngine::active_sequences() const {
    return static_cast<uint32_t>(
        std::count_if(sequences_.begin(), sequences_.end(),
                      [](const Sequence& s) { return !s.finished; }));
}

// ContinuousBatchServer implementation

bool ContinuousBatchServer::initialize(const EngineConfig& config, uint32_t max_batch_size) {
    batch_engine_ = std::make_unique<BatchLLMEngine>();
    return batch_engine_->initialize(config, max_batch_size);
}

int32_t ContinuousBatchServer::submit_request(const std::string& prompt,
                                              const SamplingParams& params) {
    int32_t request_id = -1;

    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        request_id = static_cast<int32_t>(request_queue_.size());
        request_queue_.push({request_id, {prompt, params}});
    }

    queue_cv_.notify_one();
    return request_id;
}

void ContinuousBatchServer::cancel_request(int32_t request_id) {
    // In a real implementation, this would cancel the request
    // For now, just a placeholder
}

std::vector<std::pair<int32_t, GenerationResult>> ContinuousBatchServer::get_completed() {
    std::vector<std::pair<int32_t, GenerationResult>> results;

    {
        std::lock_guard<std::mutex> lock(completed_mutex_);
        while (!completed_queue_.empty()) {
            results.push_back(completed_queue_.front());
            completed_queue_.pop();
        }
    }

    return results;
}

void ContinuousBatchServer::start() {
    running_ = true;
    processing_thread_ = std::thread(&ContinuousBatchServer::processing_loop, this);
}

void ContinuousBatchServer::stop() {
    running_ = false;
    queue_cv_.notify_all();

    if (processing_thread_.joinable()) {
        processing_thread_.join();
    }
}

ContinuousBatchServer::Status ContinuousBatchServer::get_status() const {
    std::lock_guard<std::mutex> lock(status_mutex_);
    return status_;
}

void ContinuousBatchServer::processing_loop() {
    while (running_) {
        // Check for new requests
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            queue_cv_.wait(lock, [this] {
                return !request_queue_.empty() || !running_;
            });

            if (!running_) break;

            // Add requests to batch
            while (!request_queue_.empty() &&
                   batch_engine_->active_sequences() < batch_engine_->max_batch_size()) {
                auto [id, req] = request_queue_.front();
                request_queue_.pop();
                batch_engine_->add_sequence(req.first, req.second);
            }
        }

        // Process batch
        auto completed = batch_engine_->step();

        // Move completed requests to output queue
        {
            std::lock_guard<std::mutex> lock(completed_mutex_);
            for (int32_t id : completed) {
                completed_queue_.push({id, batch_engine_->get_result(id)});
                batch_engine_->remove_sequence(id);
            }
        }

        // Update status
        {
            std::lock_guard<std::mutex> lock(status_mutex_);
            status_.active_requests = batch_engine_->active_sequences();
        }
    }
}

// Factory function
std::unique_ptr<LLMEngine> create_engine(const EngineConfig& config) {
    auto engine = std::make_unique<LLMEngine>();
    if (engine->initialize(config)) {
        return engine;
    }
    return nullptr;
}

} // namespace llm_engine
