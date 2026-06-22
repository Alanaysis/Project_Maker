#include "engine.h"
#include <iostream>
#include <chrono>
#include <vector>
#include <numeric>
#include <algorithm>
#include <cmath>

using namespace llm_engine;

struct BenchmarkResult {
    float prefill_time_ms;
    float decode_time_ms;
    float tokens_per_second;
    uint32_t prompt_tokens;
    uint32_t generated_tokens;
    float memory_mb;
};

BenchmarkResult run_benchmark(LLMEngine& engine, const std::string& prompt,
                              uint32_t num_tokens, const SamplingParams& params) {
    BenchmarkResult result;

    // Tokenize prompt
    auto tokens = engine.tokenize(prompt, true);
    result.prompt_tokens = static_cast<uint32_t>(tokens.size());

    // Measure prefill time
    auto start = std::chrono::steady_clock::now();

    // Generate tokens
    auto gen_result = engine.generate(prompt, params);

    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    result.generated_tokens = gen_result.generated_tokens;
    result.tokens_per_second = gen_result.tokens_per_second;
    result.decode_time_ms = duration.count() / 1000.0f;

    // Estimate prefill time (rough approximation)
    result.prefill_time_ms = result.prompt_tokens * 0.1f;  // Assume 0.1ms per token

    // Estimate memory usage (rough approximation)
    auto info = engine.get_model_info();
    result.memory_mb = (info.n_embd * info.n_layer * 4 * 4) / (1024.0f * 1024.0f);

    return result;
}

void print_results(const std::vector<BenchmarkResult>& results) {
    std::cout << "\n=== Benchmark Results ===" << std::endl;
    std::cout << std::string(80, '-') << std::endl;

    // Calculate averages
    float avg_prefill = 0, avg_decode = 0, avg_tps = 0;
    uint32_t total_prompt = 0, total_generated = 0;

    for (const auto& r : results) {
        avg_prefill += r.prefill_time_ms;
        avg_decode += r.decode_time_ms;
        avg_tps += r.tokens_per_second;
        total_prompt += r.prompt_tokens;
        total_generated += r.generated_tokens;
    }

    avg_prefill /= results.size();
    avg_decode /= results.size();
    avg_tps /= results.size();

    std::cout << "Number of runs: " << results.size() << std::endl;
    std::cout << "Average prompt tokens: " << total_prompt / results.size() << std::endl;
    std::cout << "Average generated tokens: " << total_generated / results.size() << std::endl;
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Average prefill time: " << avg_prefill << " ms" << std::endl;
    std::cout << "Average decode time: " << avg_decode << " ms" << std::endl;
    std::cout << "Average tokens/second: " << avg_tps << std::endl;
    std::cout << "Estimated memory usage: " << results[0].memory_mb << " MB" << std::endl;

    // Calculate percentiles
    std::vector<float> tps_values;
    for (const auto& r : results) {
        tps_values.push_back(r.tokens_per_second);
    }
    std::sort(tps_values.begin(), tps_values.end());

    std::cout << "\nTokens/second percentiles:" << std::endl;
    std::cout << "  P50: " << tps_values[tps_values.size() / 2] << std::endl;
    std::cout << "  P90: " << tps_values[static_cast<size_t>(tps_values.size() * 0.9)] << std::endl;
    std::cout << "  P99: " << tps_values[static_cast<size_t>(tps_values.size() * 0.99)] << std::endl;
}

void print_usage() {
    std::cout << "Usage: benchmark [options]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -m, --model <path>     Path to GGUF model file" << std::endl;
    std::cout << "  -n, --num-tokens <num> Number of tokens to generate (default: 128)" << std::endl;
    std::cout << "  -r, --runs <num>       Number of benchmark runs (default: 5)" << std::endl;
    std::cout << "  -c, --context <size>   Context length (default: 2048)" << std::endl;
    std::cout << "  -t, --threads <num>    Number of threads (default: 4)" << std::endl;
    std::cout << "  --prompt <text>        Custom prompt for benchmark" << std::endl;
    std::cout << "  -h, --help             Show this help message" << std::endl;
}

int main(int argc, char* argv[]) {
    // Parse command line arguments
    std::string model_path;
    uint32_t num_tokens = 128;
    uint32_t num_runs = 5;
    uint32_t n_ctx = 2048;
    uint32_t n_threads = 4;
    std::string custom_prompt;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help") {
            print_usage();
            return 0;
        } else if (arg == "-m" || arg == "--model") {
            if (i + 1 < argc) {
                model_path = argv[++i];
            }
        } else if (arg == "-n" || arg == "--num-tokens") {
            if (i + 1 < argc) {
                num_tokens = std::stoi(argv[++i]);
            }
        } else if (arg == "-r" || arg == "--runs") {
            if (i + 1 < argc) {
                num_runs = std::stoi(argv[++i]);
            }
        } else if (arg == "-c" || arg == "--context") {
            if (i + 1 < argc) {
                n_ctx = std::stoi(argv[++i]);
            }
        } else if (arg == "-t" || arg == "--threads") {
            if (i + 1 < argc) {
                n_threads = std::stoi(argv[++i]);
            }
        } else if (arg == "--prompt") {
            if (i + 1 < argc) {
                custom_prompt = argv[++i];
            }
        }
    }

    // Validate model path
    if (model_path.empty()) {
        std::cerr << "Error: Model path is required" << std::endl;
        print_usage();
        return 1;
    }

    // Configure engine
    EngineConfig config;
    config.model_path = model_path;
    config.n_ctx = n_ctx;
    config.n_threads = n_threads;

    // Create and initialize engine
    std::cout << "Initializing LLM Engine for benchmark..." << std::endl;
    auto engine = create_engine(config);

    if (!engine) {
        std::cerr << "Failed to create engine" << std::endl;
        return 1;
    }

    if (!engine->load_model(model_path)) {
        std::cerr << "Failed to load model" << std::endl;
        return 1;
    }

    // Print model info
    auto info = engine->get_model_info();
    std::cout << "\n=== Model Info ===" << std::endl;
    std::cout << "Architecture: " << info.architecture << std::endl;
    std::cout << "Vocab size: " << info.n_vocab << std::endl;
    std::cout << "Context length: " << info.n_ctx << std::endl;
    std::cout << "Layers: " << info.n_layer << std::endl;

    // Configure sampling parameters
    SamplingParams params;
    params.temperature = 0.0f;  # Greedy for benchmark
    params.do_sample = false;
    params.max_tokens = num_tokens;

    // Default prompts for benchmark
    std::vector<std::string> default_prompts = {
        "Explain the theory of relativity in simple terms.",
        "Write a short story about a robot learning to love.",
        "What are the key principles of object-oriented programming?",
        "Describe the process of photosynthesis.",
        "How does the human immune system work?"
    };

    // Use custom prompt or default prompts
    std::vector<std::string> prompts;
    if (!custom_prompt.empty()) {
        prompts.push_back(custom_prompt);
    } else {
        prompts = default_prompts;
    }

    // Run benchmark
    std::cout << "\nRunning benchmark with " << num_runs << " runs..." << std::endl;
    std::cout << "Generating " << num_tokens << " tokens per run" << std::endl;

    std::vector<BenchmarkResult> results;

    for (uint32_t run = 0; run < num_runs; ++run) {
        std::cout << "Run " << (run + 1) << "/" << num_runs << "... ";
        std::cout.flush();

        // Select prompt (rotate through prompts)
        const std::string& prompt = prompts[run % prompts.size()];

        // Run benchmark
        BenchmarkResult result = run_benchmark(*engine, prompt, num_tokens, params);
        results.push_back(result);

        std::cout << result.tokens_per_second << " tokens/s" << std::endl;

        // Reset engine state between runs
        engine->reset();
    }

    // Print results
    print_results(results);

    // Throughput test
    std::cout << "\n=== Throughput Test ===" << std::endl;
    std::cout << "Testing with increasing context lengths..." << std::endl;

    std::vector<uint32_t> context_lengths = {128, 256, 512, 1024};

    for (uint32_t ctx_len : context_lengths) {
        if (ctx_len > n_ctx) continue;

        // Create a prompt of approximate length
        std::string prompt = "Hello, how are you? ";
        while (prompt.size() < ctx_len * 4) {  # Rough estimate
            prompt += "This is a test. ";
        }

        // Adjust context length in params
        params.max_tokens = 32;  # Fewer tokens for throughput test

        std::cout << "Context length ~" << ctx_len << ": ";
        std::cout.flush();

        auto result = run_benchmark(*engine, prompt, params.max_tokens, params);
        std::cout << result.tokens_per_second << " tokens/s" << std::endl;

        engine->reset();
    }

    std::cout << "\nBenchmark complete!" << std::endl;
    return 0;
}
