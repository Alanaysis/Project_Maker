#include "engine.h"
#include <iostream>
#include <string>
#include <sstream>

using namespace llm_engine;

void print_usage() {
    std::cout << "Usage: chat [options]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -m, --model <path>     Path to GGUF model file" << std::endl;
    std::cout << "  -c, --context <size>   Context length (default: 2048)" << std::endl;
    std::cout << "  -t, --threads <num>    Number of threads (default: 4)" << std::endl;
    std::cout << "  --temp <value>         Temperature (default: 0.7)" << std::endl;
    std::cout << "  --top-p <value>        Top-p sampling (default: 0.9)" << std::endl;
    std::cout << "  --top-k <value>        Top-k sampling (default: 40)" << std::endl;
    std::cout << "  --max-tokens <num>     Max tokens to generate (default: 256)" << std::endl;
    std::cout << "  -h, --help             Show this help message" << std::endl;
}

int main(int argc, char* argv[]) {
    // Parse command line arguments
    std::string model_path;
    uint32_t n_ctx = 2048;
    uint32_t n_threads = 4;
    float temperature = 0.7f;
    float top_p = 0.9f;
    uint32_t top_k = 40;
    uint32_t max_tokens = 256;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help") {
            print_usage();
            return 0;
        } else if (arg == "-m" || arg == "--model") {
            if (i + 1 < argc) {
                model_path = argv[++i];
            }
        } else if (arg == "-c" || arg == "--context") {
            if (i + 1 < argc) {
                n_ctx = std::stoi(argv[++i]);
            }
        } else if (arg == "-t" || arg == "--threads") {
            if (i + 1 < argc) {
                n_threads = std::stoi(argv[++i]);
            }
        } else if (arg == "--temp") {
            if (i + 1 < argc) {
                temperature = std::stof(argv[++i]);
            }
        } else if (arg == "--top-p") {
            if (i + 1 < argc) {
                top_p = std::stof(argv[++i]);
            }
        } else if (arg == "--top-k") {
            if (i + 1 < argc) {
                top_k = std::stoi(argv[++i]);
            }
        } else if (arg == "--max-tokens") {
            if (i + 1 < argc) {
                max_tokens = std::stoi(argv[++i]);
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
    std::cout << "Initializing LLM Engine..." << std::endl;
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
    std::cout << "Embedding dim: " << info.n_embd << std::endl;
    std::cout << "Attention heads: " << info.n_head << std::endl;

    // Configure sampling parameters
    SamplingParams params;
    params.temperature = temperature;
    params.top_p = top_p;
    params.top_k = top_k;
    params.max_tokens = max_tokens;
    params.do_sample = true;

    // Chat loop
    std::cout << "\n=== Chat Interface ===" << std::endl;
    std::cout << "Type your message and press Enter. Type 'quit' to exit." << std::endl;
    std::cout << "Type 'clear' to clear conversation history." << std::endl;
    std::cout << "Type 'params' to show current parameters." << std::endl;
    std::cout << std::endl;

    std::string conversation_history;

    while (true) {
        std::cout << "\nUser: ";
        std::string user_input;
        std::getline(std::cin, user_input);

        // Handle special commands
        if (user_input == "quit" || user_input == "exit") {
            std::cout << "Goodbye!" << std::endl;
            break;
        } else if (user_input == "clear") {
            conversation_history.clear();
            engine->reset();
            std::cout << "Conversation cleared." << std::endl;
            continue;
        } else if (user_input == "params") {
            std::cout << "\nCurrent parameters:" << std::endl;
            std::cout << "  Temperature: " << params.temperature << std::endl;
            std::cout << "  Top-p: " << params.top_p << std::endl;
            std::cout << "  Top-k: " << params.top_k << std::endl;
            std::cout << "  Max tokens: " << params.max_tokens << std::endl;
            continue;
        } else if (user_input.empty()) {
            continue;
        }

        // Add user message to conversation
        conversation_history += "User: " + user_input + "\nAssistant: ";

        // Generate response with streaming
        std::cout << "\nAssistant: ";
        std::cout.flush();

        auto result = engine->generate_stream(
            conversation_history,
            params,
            [](const std::string& token, bool is_last) -> bool {
                if (!token.empty()) {
                    std::cout << token;
                    std::cout.flush();
                }
                if (is_last) {
                    std::cout << std::endl;
                }
                return true;  // Continue generation
            }
        );

        // Add assistant response to conversation
        conversation_history += result.text + "\n";

        // Print statistics
        std::cout << "\n[Generated " << result.generated_tokens << " tokens, "
                  << std::fixed << std::setprecision(1)
                  << result.tokens_per_second << " tokens/s, "
                  << "Stop reason: " << result.stop_reason << "]" << std::endl;
    }

    return 0;
}
