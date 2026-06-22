#pragma once

#include <vector>
#include <cstdint>
#include <random>
#include <algorithm>
#include <cmath>
#include <functional>

namespace llm_engine {

// Sampling parameters
struct SamplingParams {
    float temperature = 1.0f;      // Sampling temperature
    float top_p = 1.0f;            // Nucleus sampling threshold
    uint32_t top_k = 0;            // Top-K sampling (0 = disabled)
    float min_p = 0.0f;            // Min-P sampling threshold
    float repetition_penalty = 1.0f; // Repetition penalty
    float frequency_penalty = 0.0f;  // Frequency penalty
    float presence_penalty = 0.0f;   // Presence penalty
    uint32_t max_tokens = 256;      // Maximum tokens to generate
    int32_t seed = -1;              // Random seed (-1 = random)
    bool do_sample = true;          // Whether to sample or use greedy
    float typical_p = 1.0f;         // Typical sampling threshold
};

// Token with probability
struct TokenProb {
    int32_t token_id;
    float probability;
    float logit;
};

// Sampler class
class Sampler {
public:
    Sampler() = default;
    ~Sampler() = default;

    // Initialize with parameters
    void initialize(const SamplingParams& params);

    // Sample next token from logits
    int32_t sample(const std::vector<float>& logits);

    // Sample with token history (for repetition penalty)
    int32_t sample(const std::vector<float>& logits,
                  const std::vector<int32_t>& history);

    // Get top-K tokens with probabilities
    std::vector<TokenProb> get_top_tokens(const std::vector<float>& logits,
                                         uint32_t k);

    // Update parameters
    void update_params(const SamplingParams& params);

    // Get current parameters
    const SamplingParams& params() const { return params_; }

    // Reset RNG state
    void reset_rng(int32_t seed = -1);

private:
    // Apply temperature to logits
    void apply_temperature(std::vector<float>& logits);

    // Apply repetition penalty
    void apply_repetition_penalty(std::vector<float>& logits,
                                 const std::vector<int32_t>& history);

    // Apply frequency and presence penalties
    void apply_frequency_presence_penalty(std::vector<float>& logits,
                                         const std::vector<int32_t>& history);

    // Top-K filtering
    void apply_top_k(std::vector<float>& logits);

    // Top-P (nucleus) filtering
    void apply_top_p(std::vector<float>& logits);

    // Min-P filtering
    void apply_min_p(std::vector<float>& logits);

    // Typical sampling filtering
    void apply_typical_p(std::vector<float>& logits);

    // Convert logits to probabilities
    std::vector<float> logits_to_probs(const std::vector<float>& logits);

    // Sample from probability distribution
    int32_t sample_from_probs(const std::vector<float>& probs);

    // Greedy selection
    int32_t greedy_select(const std::vector<float>& logits);

    // Sampling parameters
    SamplingParams params_;

    // Random number generator
    std::mt19937 rng_;
    bool rng_initialized_ = false;
};

// Beam search sampler (alternative to single sampling)
class BeamSearchSampler {
public:
    struct Beam {
        std::vector<int32_t> tokens;
        float score;
        bool finished;
    };

    BeamSearchSampler() = default;
    ~BeamSearchSampler() = default;

    // Initialize with beam size
    void initialize(uint32_t beam_size, int32_t eos_token_id);

    // Generate beams for next step
    std::vector<Beam> step(const std::vector<float>& logits,
                          const std::vector<Beam>& beams);

    // Check if all beams are finished
    bool all_finished(const std::vector<Beam>& beams) const;

    // Get best beam
    const Beam& get_best_beam(const std::vector<Beam>& beams) const;

private:
    uint32_t beam_size_ = 1;
    int32_t eos_token_id_ = 2;
};

// Speculative decoding sampler (for faster inference)
class SpeculativeSampler {
public:
    SpeculativeSampler() = default;
    ~SpeculativeSampler() = default;

    // Initialize with draft model parameters
    void initialize(uint32_t num_speculative_tokens);

    // Verify and accept/reject speculative tokens
    // Returns number of accepted tokens
    uint32_t verify_tokens(const std::vector<float>& target_logits,
                          const std::vector<float>& draft_logits,
                          const std::vector<int32_t>& draft_tokens);

    // Get accepted tokens
    const std::vector<int32_t>& get_accepted_tokens() const { return accepted_tokens_; }

private:
    uint32_t num_speculative_tokens_ = 0;
    std::vector<int32_t> accepted_tokens_;
    std::mt19937 rng_;
};

// Sampling strategy selector
enum class SamplingStrategy {
    GREEDY,
    TEMPERATURE,
    TOP_K,
    TOP_P,
    MIN_P,
    TYPICAL_P,
    BEAM_SEARCH,
    SPECULATIVE
};

// Factory function to create sampler
std::unique_ptr<Sampler> create_sampler(SamplingStrategy strategy,
                                        const SamplingParams& params);

} // namespace llm_engine
