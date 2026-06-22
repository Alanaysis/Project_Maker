#include "sampler.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace llm_engine {

void Sampler::initialize(const SamplingParams& params) {
    params_ = params;
    reset_rng(params.seed);
}

void Sampler::reset_rng(int32_t seed) {
    if (seed < 0) {
        // Random seed
        std::random_device rd;
        rng_.seed(rd());
    } else {
        rng_.seed(static_cast<uint32_t>(seed));
    }
    rng_initialized_ = true;
}

int32_t Sampler::sample(const std::vector<float>& logits) {
    return sample(logits, {});
}

int32_t Sampler::sample(const std::vector<float>& logits,
                        const std::vector<int32_t>& history) {
    // Greedy decoding
    if (!params_.do_sample || params_.temperature == 0.0f) {
        return greedy_select(logits);
    }

    // Copy logits for modification
    std::vector<float> modified_logits = logits;

    // Apply penalties
    if (!history.empty()) {
        if (params_.repetition_penalty != 1.0f) {
            apply_repetition_penalty(modified_logits, history);
        }
        if (params_.frequency_penalty != 0.0f || params_.presence_penalty != 0.0f) {
            apply_frequency_presence_penalty(modified_logits, history);
        }
    }

    // Apply temperature
    apply_temperature(modified_logits);

    // Apply sampling filters
    if (params_.top_k > 0) {
        apply_top_k(modified_logits);
    }

    if (params_.min_p > 0.0f) {
        apply_min_p(modified_logits);
    }

    if (params_.top_p < 1.0f) {
        apply_top_p(modified_logits);
    }

    if (params_.typical_p < 1.0f) {
        apply_typical_p(modified_logits);
    }

    // Convert to probabilities and sample
    std::vector<float> probs = logits_to_probs(modified_logits);
    return sample_from_probs(probs);
}

std::vector<TokenProb> Sampler::get_top_tokens(const std::vector<float>& logits, uint32_t k) {
    std::vector<TokenProb> tokens(logits.size());

    for (size_t i = 0; i < logits.size(); ++i) {
        tokens[i].token_id = static_cast<int32_t>(i);
        tokens[i].logit = logits[i];
    }

    // Sort by logit value (descending)
    std::partial_sort(tokens.begin(), tokens.begin() + k, tokens.end(),
                      [](const TokenProb& a, const TokenProb& b) {
                          return a.logit > b.logit;
                      });

    // Calculate probabilities for top-k
    std::vector<float> top_logits(k);
    for (uint32_t i = 0; i < k; ++i) {
        top_logits[i] = tokens[i].logit;
    }

    std::vector<float> probs = logits_to_probs(top_logits);
    for (uint32_t i = 0; i < k; ++i) {
        tokens[i].probability = probs[i];
    }

    tokens.resize(k);
    return tokens;
}

void Sampler::update_params(const SamplingParams& params) {
    params_ = params;
}

void Sampler::apply_temperature(std::vector<float>& logits) {
    if (params_.temperature <= 0.0f) return;

    float inv_temp = 1.0f / params_.temperature;
    for (auto& logit : logits) {
        logit *= inv_temp;
    }
}

void Sampler::apply_repetition_penalty(std::vector<float>& logits,
                                       const std::vector<int32_t>& history) {
    // Repetition penalty (from CTRL paper)
    // Penalizes tokens that have already appeared

    for (int32_t token_id : history) {
        if (token_id >= 0 && token_id < static_cast<int32_t>(logits.size())) {
            float logit = logits[token_id];
            if (logit > 0) {
                logits[token_id] = logit / params_.repetition_penalty;
            } else {
                logits[token_id] = logit * params_.repetition_penalty;
            }
        }
    }
}

void Sampler::apply_frequency_presence_penalty(std::vector<float>& logits,
                                               const std::vector<int32_t>& history) {
    // Count token frequencies
    std::unordered_map<int32_t, uint32_t> freq;
    for (int32_t token_id : history) {
        freq[token_id]++;
    }

    // Apply penalties
    for (const auto& [token_id, count] : freq) {
        if (token_id >= 0 && token_id < static_cast<int32_t>(logits.size())) {
            logits[token_id] -= params_.frequency_penalty * count;
            logits[token_id] -= params_.presence_penalty;
        }
    }
}

void Sampler::apply_top_k(std::vector<float>& logits) {
    if (params_.top_k >= logits.size()) return;

    // Find the k-th largest logit
    std::vector<float> sorted_logits = logits;
    std::partial_sort(sorted_logits.begin(), sorted_logits.begin() + params_.top_k,
                      sorted_logits.end(), std::greater<float>());

    float threshold = sorted_logits[params_.top_k - 1];

    // Set logits below threshold to -inf
    for (auto& logit : logits) {
        if (logit < threshold) {
            logit = -std::numeric_limits<float>::infinity();
        }
    }
}

void Sampler::apply_top_p(std::vector<float>& logits) {
    // Convert to probabilities
    std::vector<float> probs = logits_to_probs(logits);

    // Create indices sorted by probability
    std::vector<size_t> indices(logits.size());
    std::iota(indices.begin(), indices.end(), 0);
    std::sort(indices.begin(), indices.end(),
              [&probs](size_t a, size_t b) { return probs[a] > probs[b]; });

    // Find cumulative probability threshold
    float cumsum = 0.0f;
    size_t cutoff = logits.size();

    for (size_t i = 0; i < indices.size(); ++i) {
        cumsum += probs[indices[i]];
        if (cumsum > params_.top_p) {
            cutoff = i + 1;
            break;
        }
    }

    // Set logits for tokens outside top-p to -inf
    for (size_t i = cutoff; i < indices.size(); ++i) {
        logits[indices[i]] = -std::numeric_limits<float>::infinity();
    }
}

void Sampler::apply_min_p(std::vector<float>& logits) {
    // Min-P sampling: keep tokens with prob >= min_p * max_prob
    std::vector<float> probs = logits_to_probs(logits);

    float max_prob = *std::max_element(probs.begin(), probs.end());
    float threshold = max_prob * params_.min_p;

    for (size_t i = 0; i < logits.size(); ++i) {
        if (probs[i] < threshold) {
            logits[i] = -std::numeric_limits<float>::infinity();
        }
    }
}

void Sampler::apply_typical_p(std::vector<float>& logits) {
    // Typical sampling (from "Locally Typical Sampling" paper)
    // Selects tokens based on information content

    std::vector<float> probs = logits_to_probs(logits);

    // Calculate entropy
    float entropy = 0.0f;
    for (float p : probs) {
        if (p > 0) {
            entropy -= p * std::log2(p);
        }
    }

    // Calculate information content for each token
    std::vector<std::pair<size_t, float>> token_info(logits.size());
    for (size_t i = 0; i < logits.size(); ++i) {
        float info = (probs[i] > 0) ? -std::log2(probs[i]) : 0.0f;
        token_info[i] = {i, std::abs(info - entropy)};
    }

    // Sort by deviation from entropy
    std::sort(token_info.begin(), token_info.end(),
              [](const auto& a, const auto& b) { return a.second < b.second; });

    // Keep tokens until cumulative probability reaches typical_p
    float cumsum = 0.0f;
    size_t cutoff = logits.size();

    for (size_t i = 0; i < token_info.size(); ++i) {
        cumsum += probs[token_info[i].first];
        if (cumsum > params_.typical_p) {
            cutoff = i + 1;
            break;
        }
    }

    // Set logits for tokens outside typical-p to -inf
    for (size_t i = cutoff; i < token_info.size(); ++i) {
        logits[token_info[i].first] = -std::numeric_limits<float>::infinity();
    }
}

std::vector<float> Sampler::logits_to_probs(const std::vector<float>& logits) {
    // Softmax with numerical stability
    float max_logit = *std::max_element(logits.begin(), logits.end());

    std::vector<float> probs(logits.size());
    float sum = 0.0f;

    for (size_t i = 0; i < logits.size(); ++i) {
        if (logits[i] == -std::numeric_limits<float>::infinity()) {
            probs[i] = 0.0f;
        } else {
            probs[i] = std::exp(logits[i] - max_logit);
            sum += probs[i];
        }
    }

    // Normalize
    if (sum > 0) {
        float inv_sum = 1.0f / sum;
        for (auto& p : probs) {
            p *= inv_sum;
        }
    }

    return probs;
}

int32_t Sampler::sample_from_probs(const std::vector<float>& probs) {
    // Categorical sampling
    std::discrete_distribution<int32_t> dist(probs.begin(), probs.end());
    return dist(rng_);
}

int32_t Sampler::greedy_select(const std::vector<float>& logits) {
    return static_cast<int32_t>(
        std::max_element(logits.begin(), logits.end()) - logits.begin());
}

// BeamSearchSampler implementation

void BeamSearchSampler::initialize(uint32_t beam_size, int32_t eos_token_id) {
    beam_size_ = beam_size;
    eos_token_id_ = eos_token_id;
}

std::vector<BeamSearchSampler::Beam> BeamSearchSampler::step(
    const std::vector<float>& logits,
    const std::vector<Beam>& beams) {

    std::vector<Beam> candidates;

    for (const auto& beam : beams) {
        if (beam.finished) {
            candidates.push_back(beam);
            continue;
        }

        // Get top-k tokens for this beam
        std::vector<std::pair<float, int32_t>> token_scores(logits.size());
        for (size_t i = 0; i < logits.size(); ++i) {
            token_scores[i] = {logits[i], static_cast<int32_t>(i)};
        }

        std::partial_sort(token_scores.begin(),
                         token_scores.begin() + beam_size_,
                         token_scores.end(),
                         std::greater<>());

        // Create new beams
        for (uint32_t i = 0; i < beam_size_; ++i) {
            Beam new_beam = beam;
            new_beam.tokens.push_back(token_scores[i].second);
            new_beam.score += token_scores[i].first;

            if (token_scores[i].second == eos_token_id_) {
                new_beam.finished = true;
            }

            candidates.push_back(std::move(new_beam));
        }
    }

    // Keep top beams
    std::partial_sort(candidates.begin(),
                     candidates.begin() + beam_size_,
                     candidates.end(),
                     [](const Beam& a, const Beam& b) {
                         return a.score > b.score;
                     });

    candidates.resize(beam_size_);
    return candidates;
}

bool BeamSearchSampler::all_finished(const std::vector<Beam>& beams) const {
    return std::all_of(beams.begin(), beams.end(),
                       [](const Beam& b) { return b.finished; });
}

const BeamSearchSampler::Beam& BeamSearchSampler::get_best_beam(
    const std::vector<Beam>& beams) const {
    return *std::max_element(beams.begin(), beams.end(),
                            [](const Beam& a, const Beam& b) {
                                return a.score < b.score;
                            });
}

// SpeculativeSampler implementation

void SpeculativeSampler::initialize(uint32_t num_speculative_tokens) {
    num_speculative_tokens_ = num_speculative_tokens;
}

uint32_t SpeculativeSampler::verify_tokens(
    const std::vector<float>& target_logits,
    const std::vector<float>& draft_logits,
    const std::vector<int32_t>& draft_tokens) {

    accepted_tokens_.clear();
    uint32_t accepted = 0;

    for (size_t i = 0; i < draft_tokens.size(); ++i) {
        int32_t draft_token = draft_tokens[i];

        // Get target probability for draft token
        float target_prob = 0.0f;
        if (draft_token >= 0 && draft_token < static_cast<int32_t>(target_logits.size())) {
            // Simple softmax for single token
            float max_logit = *std::max_element(target_logits.begin(), target_logits.end());
            target_prob = std::exp(target_logits[draft_token] - max_logit);
            float sum = 0.0f;
            for (float l : target_logits) {
                sum += std::exp(l - max_logit);
            }
            target_prob /= sum;
        }

        // Get draft probability
        float draft_prob = 0.0f;
        if (draft_token >= 0 && draft_token < static_cast<int32_t>(draft_logits.size())) {
            float max_logit = *std::max_element(draft_logits.begin(), draft_logits.end());
            draft_prob = std::exp(draft_logits[draft_token] - max_logit);
            float sum = 0.0f;
            for (float l : draft_logits) {
                sum += std::exp(l - max_logit);
            }
            draft_prob /= sum;
        }

        // Acceptance criterion
        float acceptance_prob = std::min(1.0f, target_prob / (draft_prob + 1e-10f));

        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        if (dist(rng_) < acceptance_prob) {
            accepted_tokens_.push_back(draft_token);
            accepted++;
        } else {
            break;
        }
    }

    return accepted;
}

// Factory function
std::unique_ptr<Sampler> create_sampler(SamplingStrategy strategy,
                                        const SamplingParams& params) {
    auto sampler = std::make_unique<Sampler>();

    SamplingParams modified_params = params;

    // Modify params based on strategy
    switch (strategy) {
        case SamplingStrategy::GREEDY:
            modified_params.do_sample = false;
            modified_params.temperature = 0.0f;
            break;
        case SamplingStrategy::TEMPERATURE:
            modified_params.do_sample = true;
            break;
        case SamplingStrategy::TOP_K:
            modified_params.do_sample = true;
            modified_params.top_k = 40;
            break;
        case SamplingStrategy::TOP_P:
            modified_params.do_sample = true;
            modified_params.top_p = 0.9f;
            break;
        case SamplingStrategy::MIN_P:
            modified_params.do_sample = true;
            modified_params.min_p = 0.05f;
            break;
        case SamplingStrategy::TYPICAL_P:
            modified_params.do_sample = true;
            modified_params.typical_p = 0.95f;
            break;
        default:
            break;
    }

    sampler->initialize(modified_params);
    return sampler;
}

} // namespace llm_engine
