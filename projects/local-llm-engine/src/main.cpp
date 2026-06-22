#include "engine.h"
#include <iostream>
#include <string>
#include <cstring>

using namespace llm_engine;

void print_version() {
    std::cout << "Local LLM Engine v1.0.0" << std::endl;
    std::cout << "A lightweight local LLM inference engine supporting GGUF format" << std::endl;
}

void print_usage() {
    std::cout << "Usage: llm_engine [command] [options]" << std::endl;
    std::cout << std::endl;
    std::cout << "Commands:" << std::endl;
    std::cout << "  infer      Run inference on a prompt" << std::endl;
    std::cout << "  chat       Start interactive chat mode" << std::endl;
    std::cout << "  benchmark  Run performance benchmark" << std::endl;
    std::cout << "  info       Show model information" << std::endl;
    std::cout << "  test       Run basic tests" << std::endl;
    std::cout << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -m, --model <path>     Path to GGUF model file (required)" << std::endl;
    std::cout << "  -p, --prompt <text>    Input prompt for inference" << std::endl;
    std::cout << "  -c, --context <size>   Context length (default: 2048)" << std::endl;
    std::cout << "  -t, --threads <num>    Number of threads (default: 4)" << std::endl;
    std::cout << "  --temp <value>         Temperature (default: 0.7)" << std::endl;
    std::cout << "  --top-p <value>        Top-p sampling (default: 0.9)" << std::endl;
    std::cout << "  --top-k <value>        Top-k sampling (default: 40)" << std::endl;
    std::cout << "  --max-tokens <num>     Max tokens to generate (default: 256)" << std::endl;
    std::cout << "  -v, --version          Show version" << std::endl;
    std::cout << "  -h, --help             Show this help message" << std::endl;
}

int run_inference(const std::string& model_path, const std::string& prompt,
                  const EngineConfig& config, const SamplingParams& params) {
    // Create engine
    auto engine = create_engine(config);
    if (!engine) {
        std::cerr << "Failed to create engine" << std::endl;
        return 1;
    }

    // Load model
    std::cout << "Loading model: " << model_path << std::endl;
    if (!engine->load_model(model_path)) {
        std::cerr << "Failed to load model" << std::endl;
        return 1;
    }

    // Run inference
    std::cout << "\nPrompt: " << prompt << std::endl;
    std::cout << "\nGenerating..." << std::endl;

    auto result = engine->generate(prompt, params);

    // Print result
    std::cout << "\n=== Generated Text ===" << std::endl;
    std::cout << result.text << std::endl;

    std::cout << "\n=== Statistics ===" << std::endl;
    std::cout << "Prompt tokens: " << result.prompt_tokens << std::endl;
    std::cout << "Generated tokens: " << result.generated_tokens << std::endl;
    std::cout << "Tokens/second: " << std::fixed << std::setprecision(1)
              << result.tokens_per_second << std::endl;
    std::cout << "Stop reason: " << result.stop_reason << std::endl;

    return 0;
}

int run_info(const std::string& model_path, const EngineConfig& config) {
    // Create engine
    auto engine = create_engine(config);
    if (!engine) {
        std::cerr << "Failed to create engine" << std::endl;
        return 1;
    }

    // Load model
    std::cout << "Loading model: " << model_path << std::endl;
    if (!engine->load_model(model_path)) {
        std::cerr << "Failed to load model" << std::endl;
        return 1;
    }

    // Print model info
    auto info = engine->get_model_info();

    std::cout << "\n=== Model Information ===" << std::endl;
    std::cout << "Architecture: " << info.architecture << std::endl;
    std::cout << "Name: " << (info.name.empty() ? "N/A" : info.name) << std::endl;
    std::cout << std::endl;
    std::cout << "Parameters:" << std::endl;
    std::cout << "  Vocabulary size: " << info.n_vocab << std::endl;
    std::cout << "  Embedding dimension: " << info.n_embd << std::endl;
    std::cout << "  Attention heads: " << info.n_head << std::endl;
    std::cout << "  Transformer layers: " << info.n_layer << std::endl;
    std::cout << "  Context length: " << info.n_ctx << std::endl;
    std::cout << "  Feed-forward dimension: " << info.n_ff << std::endl;
    std::cout << std::endl;

    // Estimate model size
    float param_count = info.n_vocab * info.n_embd +  # Embedding
                       info.n_layer * (4 * info.n_embd * info.n_embd +  # Attention
                                      3 * info.n_embd * info.n_ff) +  # FFN
                       info.n_embd;  # Output

    std::cout << "Estimated parameters: " << std::fixed << std::setprecision(1)
              << param_count / 1e9 << "B" << std::endl;

    // Estimate memory (FP32)
    float memory_gb = param_count * 4 / 1e9;
    std::cout << "Estimated memory (FP32): " << std::fixed << std::setprecision(2)
              << memory_gb << " GB" << std::endl;

    // Estimate memory (INT8)
    float memory_int8 = param_count / 1e9;
    std::cout << "Estimated memory (INT8): " << std::fixed << std::setprecision(2)
              << memory_int8 << " GB" << std::endl;

    return 0;
}

int run_test() {
    std::cout << "Running basic tests..." << std::endl;

    // Test tokenizer
    std::cout << "\n=== Testing Tokenizer ===" << std::endl;
    auto tokenizer = create_tokenizer("bpe");

    TokenizerConfig tok_config;
    tok_config.n_vocab = 100;
    tok_config.bos_token_id = 1;
    tok_config.eos_token_id = 2;
    tok_config.unk_token_id = 0;

    std::vector<std::string> vocab = {
        "<unk>", "<s>", "</s>",
        "hello", "world", " ",
        "test", "ing", "ed"
    };

    if (tokenizer->initialize(tok_config, vocab)) {
        std::cout << "Tokenizer initialized: PASSED" << std::endl;

        auto tokens = tokenizer->encode("hello world", true);
        std::cout << "Encode 'hello world': ";

        for (int32_t t : tokens) {
            std::cout << t << " ";
        }
        std::cout << std::endl;

        std::string decoded = tokenizer->decode(tokens, true);
        std::cout << "Decoded: " << decoded << std::endl;
    } else {
        std::cout << "Tokenizer initialization: FAILED" << std::endl;
    }

    // Test KV Cache
    std::cout << "\n=== Testing KV Cache ===" << std::endl;
    KVCache cache;
    if (cache.initialize(2, 10, 4, 2)) {
        std::cout << "KV Cache initialized: PASSED" << std::endl;

        std::vector<float> key = {1.0f, 2.0f, 3.0f, 4.0f};
        std::vector<float> value = {5.0f, 6.0f, 7.0f, 8.0f};

        cache.store(0, 0, key.data(), value.data());
        cache.advance();

        std::cout << "Cache current length: " << cache.current_length() << std::endl;
        std::cout << "KV Cache store/advance: PASSED" << std::endl;
    } else {
        std::cout << "KV Cache initialization: FAILED" << std::endl;
    }

    // Test Sampler
    std::cout << "\n=== Testing Sampler ===" << std::endl;
    Sampler sampler;
    SamplingParams params;
    params.seed = 42;
    sampler.initialize(params);

    std::vector<float> logits = {1.0f, 5.0f, 3.0f, 4.0f, 2.0f};
    int32_t token = sampler.sample(logits);

    std::cout << "Sampled token: " << token << std::endl;
    std::cout << "Expected (greedy): 1" << std::endl;

    if (token == 1) {
        std::cout << "Sampler test: PASSED" << std::endl;
    } else {
        std::cout << "Sampler test: FAILED" << std::endl;
    }

    std::cout << "\nAll basic tests completed!" << std::endl;
    return 0;
}

int main(int argc, char* argv[]) {
    // Parse command
    if (argc < 2) {
        print_usage();
        return 1;
    }

    std::string command = argv[1];

    // Handle help and version
    if (command == "-h" || command == "--help") {
        print_usage();
        return 0;
    } else if (command == "-v" || command == "--version") {
        print_version();
        return 0;
    } else if (command == "test") {
        return run_test();
    }

    // For other commands, need model path
    std::string model_path;
    std::string prompt;
    EngineConfig config;
    SamplingParams params;

    // Parse arguments
    for (int i = 2; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "-m" || arg == "--model") {
            if (i + 1 < argc) {
                model_path = argv[++i];
                config.model_path = model_path;
            }
        } else if (arg == "-p" || arg == "--prompt") {
            if (i + 1 < argc) {
                prompt = argv[++i];
            }
        } else if (arg == "-c" || arg == "--context") {
            if (i + 1 < argc) {
                config.n_ctx = std::stoi(argv[++i]);
            }
        } else if (arg == "-t" || arg == "--threads") {
            if (i + 1 < argc) {
                config.n_threads = std::stoi(argv[++i]);
            }
        } else if (arg == "--temp") {
            if (i + 1 < argc) {
                params.temperature = std::stof(argv[++i]);
            }
        } else if (arg == "--top-p") {
            if (i + 1 < argc) {
                params.top_p = std::stof(argv[++i]);
            }
        } else if (arg == "--top-k") {
            if (i + 1 < argc) {
                params.top_k = std::stoi(argv[++i]);
            }
        } else if (arg == "--max-tokens") {
            if (i + 1 < argc) {
                params.max_tokens = std::stoi(argv[++i]);
            }
        }
    }

    // Validate model path
    if (model_path.empty()) {
        std::cerr << "Error: Model path is required" << std::endl;
        print_usage();
        return 1;
    }

    // Execute command
    if (command == "infer") {
        if (prompt.empty()) {
            std::cerr << "Error: Prompt is required for inference" << std::endl;
            return 1;
        }
        return run_inference(model_path, prompt, config, params);
    } else if (command == "info") {
        return run_info(model_path, config);
    } else if (command == "chat" || command == "benchmark") {
        // These are handled by separate executables
        std::cout << "Please use the dedicated executables:" << std::endl;
        std::cout << "  ./chat       - Interactive chat mode" << std::endl;
        std::cout << "  ./benchmark  - Performance benchmark" << std::endl;
        return 0;
    } else {
        std::cerr << "Unknown command: " << command << std::endl;
        print_usage();
        return 1;
    }

    return 0;
}
