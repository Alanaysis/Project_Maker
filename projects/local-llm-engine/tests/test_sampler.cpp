#include "sampler.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>
#include <map>

using namespace llm_engine;

// Simple test framework
#define TEST(name) void test_##name()
#define RUN_TEST(name) do { \
    std::cout << "Running " #name "... "; \
    test_##name(); \
    std::cout << "PASSED" << std::endl; \
} while(0)

#define ASSERT_EQ(a, b) do { \
    if ((a) != (b)) { \
        std::cerr << "Assertion failed: " << #a << " != " << #b << std::endl; \
        std::cerr << "  Actual: " << (a) << " vs " << (b) << std::endl; \
        exit(1); \
    } \
} while(0)

#define ASSERT_TRUE(expr) do { \
    if (!(expr)) { \
        std::cerr << "Assertion failed: " << #expr << " is false" << std::endl; \
        exit(1); \
    } \
} while(0)

#define ASSERT_NEAR(a, b, eps) do { \
    if (std::abs((a) - (b)) > (eps)) { \
        std::cerr << "Assertion failed: " << #a << " not near " << #b << std::endl; \
        std::cerr << "  Actual: " << (a) << " vs " << (b) << std::endl; \
        exit(1); \
    } \
} while(0)

// Test greedy sampling
TEST(greedy_sampling) {
    Sampler sampler;

    SamplingParams params;
    params.do_sample = false;
    params.temperature = 0.0f;
    params.seed = 42;

    sampler.initialize(params);

    // Create logits with clear maximum
    std::vector<float> logits = {1.0f, 5.0f, 2.0f, 3.0f, 4.0f};

    // Greedy should select index 1 (highest logit)
    int32_t token = sampler.sample(logits);
    ASSERT_EQ(token, 1);
}

// Test temperature sampling
TEST(temperature_sampling) {
    Sampler sampler;

    SamplingParams params;
    params.do_sample = true;
    params.temperature = 1.0f;
    params.seed = 42;

    sampler.initialize(params);

    // Create logits
    std::vector<float> logits = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};

    // Sample multiple times
    std::map<int32_t, int32_t> counts;
    int32_t num_samples = 1000;

    for (int32_t i = 0; i < num_samples; ++i) {
        int32_t token = sampler.sample(logits);
        counts[token]++;
    }

    // With temperature 1.0, higher logit tokens should be sampled more often
    // Token 4 (highest logit) should be most frequent
    ASSERT_TRUE(counts[4] > counts[0]);
    ASSERT_TRUE(counts[4] > counts[1]);
    ASSERT_TRUE(counts[4] > counts[2]);
    ASSERT_TRUE(counts[4] > counts[3]);
}

// Test low temperature (more deterministic)
TEST(low_temperature) {
    Sampler sampler;

    SamplingParams params;
    params.do_sample = true;
    params.temperature = 0.1f;  // Very low temperature
    params.seed = 42;

    sampler.initialize(params);

    // Create logits with clear difference
    std::vector<float> logits = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};

    // Sample multiple times - should mostly pick the highest
    std::map<int32_t, int32_t> counts;
    int32_t num_samples = 100;

    for (int32_t i = 0; i < num_samples; ++i) {
        int32_t token = sampler.sample(logits);
        counts[token]++;
    }

    // With very low temperature, should almost always pick token 4
    ASSERT_TRUE(counts[4] > 90);  // Should be >90%
}

// Test top-k sampling
TEST(top_k_sampling) {
    Sampler sampler;

    SamplingParams params;
    params.do_sample = true;
    params.temperature = 1.0f;
    params.top_k = 3;  // Only top 3 tokens
    params.seed = 42;

    sampler.initialize(params);

    // Create logits
    std::vector<float> logits = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};

    // Sample multiple times
    std::map<int32_t, int32_t> counts;
    int32_t num_samples = 1000;

    for (int32_t i = 0; i < num_samples; ++i) {
        int32_t token = sampler.sample(logits);
        counts[token]++;
    }

    // Only tokens 2, 3, 4 should be sampled (top 3)
    ASSERT_TRUE(counts.count(0) == 0 || counts[0] == 0);
    ASSERT_TRUE(counts.count(1) == 0 || counts[1] == 0);
    ASSERT_TRUE(counts[2] > 0);
    ASSERT_TRUE(counts[3] > 0);
    ASSERT_TRUE(counts[4] > 0);
}

// Test top-p (nucleus) sampling
TEST(top_p_sampling) {
    Sampler sampler;

    SamplingParams params;
    params.do_sample = true;
    params.temperature = 1.0f;
    params.top_p = 0.5f;  # Keep tokens until 50% probability
    params.seed = 42;

    sampler.initialize(params);

    // Create logits with one dominant token
    std::vector<float> logits = {1.0f, 10.0f, 1.0f, 1.0f, 1.0f};

    // Sample multiple times
    std::map<int32_t, int32_t> counts;
    int32_t num_samples = 100;

    for (int32_t i = 0; i < num_samples; ++i) {
        int32_t token = sampler.sample(logits);
        counts[token]++;
    }

    // Should mostly pick token 1 (very high logit)
    ASSERT_TRUE(counts[1] > 80);  # Should be >80%
}

// Test repetition penalty
TEST(repetition_penalty) {
    Sampler sampler;

    SamplingParams params;
    params.do_sample = true;
    params.temperature = 1.0f;
    params.repetition_penalty = 2.0f;  # Strong penalty
    params.seed = 42;

    sampler.initialize(params);

    // Create logits
    std::vector<float> logits = {5.0f, 1.0f, 1.0f, 1.0f, 1.0f};

    // History with token 0
    std::vector<int32_t> history = {0};

    // Sample multiple times
    std::map<int32_t, int32_t> counts;
    int32_t num_samples = 100;

    for (int32_t i = 0; i < num_samples; ++i) {
        int32_t token = sampler.sample(logits, history);
        counts[token]++;
    }

    // Token 0 should be penalized, so other tokens should be sampled more
    ASSERT_TRUE(counts[0] < 50);  # Should be less than 50%
}

// Test get_top_tokens
TEST(get_top_tokens) {
    Sampler sampler;

    SamplingParams params;
    params.seed = 42;
    sampler.initialize(params);

    // Create logits
    std::vector<float> logits = {1.0f, 5.0f, 3.0f, 4.0f, 2.0f};

    // Get top 3 tokens
    std::vector<TokenProb> top_tokens = sampler.get_top_tokens(logits, 3);

    ASSERT_EQ(top_tokens.size(), 3);

    // Should be sorted by logit (descending)
    ASSERT_EQ(top_tokens[0].token_id, 1);  // logit 5.0
    ASSERT_EQ(top_tokens[1].token_id, 3);  // logit 4.0
    ASSERT_EQ(top_tokens[2].token_id, 2);  // logit 3.0

    // Probabilities should sum to approximately 1
    float prob_sum = top_tokens[0].probability +
                     top_tokens[1].probability +
                     top_tokens[2].probability;
    ASSERT_NEAR(prob_sum, 1.0f, 0.01f);
}

// Test sampler factory
TEST(sampler_factory) {
    SamplingParams params;
    params.seed = 42;

    // Test different strategies
    auto greedy = create_sampler(SamplingStrategy::GREEDY, params);
    ASSERT_TRUE(greedy != nullptr);

    auto temperature = create_sampler(SamplingStrategy::TEMPERATURE, params);
    ASSERT_TRUE(temperature != nullptr);

    auto top_k = create_sampler(SamplingStrategy::TOP_K, params);
    ASSERT_TRUE(top_k != nullptr);

    auto top_p = create_sampler(SamplingStrategy::TOP_P, params);
    ASSERT_TRUE(top_p != nullptr);

    auto min_p = create_sampler(SamplingStrategy::MIN_P, params);
    ASSERT_TRUE(min_p != nullptr);

    auto typical_p = create_sampler(SamplingStrategy::TYPICAL_P, params);
    ASSERT_TRUE(typical_p != nullptr);
}

// Test BeamSearchSampler
TEST(beam_search) {
    BeamSearchSampler beam_sampler;

    uint32_t beam_size = 3;
    int32_t eos_token_id = 2;

    beam_sampler.initialize(beam_size, eos_token_id);

    // Create initial beam
    BeamSearchSampler::Beam initial_beam;
    initial_beam.tokens = {1};  # Start with some token
    initial_beam.score = 0.0f;
    initial_beam.finished = false;

    std::vector<BeamSearchSampler::Beam> beams = {initial_beam};

    // Create logits
    std::vector<float> logits = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};

    // Step
    auto new_beams = beam_sampler.step(logits, beams);

    // Should have beam_size beams
    ASSERT_EQ(new_beams.size(), beam_size);

    // Beams should be sorted by score
    for (size_t i = 1; i < new_beams.size(); ++i) {
        ASSERT_TRUE(new_beams[i].score <= new_beams[i - 1].score);
    }
}

int main() {
    std::cout << "=== Sampler Tests ===" << std::endl;

    RUN_TEST(greedy_sampling);
    RUN_TEST(temperature_sampling);
    RUN_TEST(low_temperature);
    RUN_TEST(top_k_sampling);
    RUN_TEST(top_p_sampling);
    RUN_TEST(repetition_penalty);
    RUN_TEST(get_top_tokens);
    RUN_TEST(sampler_factory);
    RUN_TEST(beam_search);

    std::cout << "\nAll sampler tests passed!" << std::endl;
    return 0;
}
