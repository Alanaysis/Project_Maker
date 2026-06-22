#include "tokenizer.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <string>

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

// Test BPE Tokenizer
TEST(bpe_tokenizer_init) {
    BPETokenizer tokenizer;

    TokenizerConfig config;
    config.n_vocab = 100;
    config.bos_token_id = 1;
    config.eos_token_id = 2;
    config.unk_token_id = 0;

    std::vector<std::string> vocab = {
        "<unk>", "<s>", "</s>",
        "hello", "world", " ",
        "the", "a", "is", "are",
        "I", "you", "he", "she",
        "good", "bad", "happy", "sad",
        "cat", "dog", "bird", "fish"
    };

    std::vector<float> scores = {
        -10.0f, -5.0f, -5.0f,
        -1.0f, -1.5f, -2.0f,
        -3.0f, -3.5f, -4.0f, -4.5f,
        -5.0f, -5.5f, -6.0f, -6.5f,
        -7.0f, -7.5f, -8.0f, -8.5f,
        -9.0f, -9.5f, -10.0f, -10.5f
    };

    ASSERT_TRUE(tokenizer.initialize(config, vocab, scores));
    ASSERT_EQ(tokenizer.vocab_size(), 22);
}

TEST(bpe_tokenizer_encode_decode) {
    BPETokenizer tokenizer;

    TokenizerConfig config;
    config.n_vocab = 100;
    config.bos_token_id = 1;
    config.eos_token_id = 2;
    config.unk_token_id = 0;

    std::vector<std::string> vocab = {
        "<unk>", "<s>", "</s>",
        "hello", "world", " ",
        "the", "a", "is", "are"
    };

    tokenizer.initialize(config, vocab);

    // Test encoding
    std::vector<int32_t> tokens = tokenizer.encode("hello world", true);

    // Should have BOS token
    ASSERT_EQ(tokens[0], 1);

    // Test decoding
    std::string decoded = tokenizer.decode(tokens, true);
    ASSERT_TRUE(decoded.find("hello") != std::string::npos);
    ASSERT_TRUE(decoded.find("world") != std::string::npos);
}

TEST(bpe_tokenizer_special_tokens) {
    BPETokenizer tokenizer;

    TokenizerConfig config;
    config.n_vocab = 100;
    config.bos_token_id = 1;
    config.eos_token_id = 2;
    config.unk_token_id = 0;

    std::vector<std::string> vocab = {
        "<unk>", "<s>", "</s>", "test"
    };

    tokenizer.initialize(config, vocab);

    // Test special token access
    ASSERT_EQ(tokenizer.bos_token_id(), 1);
    ASSERT_EQ(tokenizer.eos_token_id(), 2);
    ASSERT_EQ(tokenizer.unk_token_id(), 0);

    // Test token lookup
    ASSERT_EQ(tokenizer.text_to_token("<s>"), 1);
    ASSERT_EQ(tokenizer.text_to_token("</s>"), 2);
    ASSERT_EQ(tokenizer.text_to_token("<unk>"), 0);

    // Test unknown token
    ASSERT_EQ(tokenizer.text_to_token("unknown"), 0);
}

// Test SentencePiece Tokenizer
TEST(sentencepiece_tokenizer_init) {
    SentencePieceTokenizer tokenizer;

    TokenizerConfig config;
    config.n_vocab = 100;
    config.bos_token_id = 1;
    config.eos_token_id = 2;
    config.unk_token_id = 0;

    std::vector<std::string> vocab = {
        "<unk>", "<s>", "</s>",
        "▁hello", "▁world", "▁",
        "▁the", "▁a", "▁is", "▁are"
    };

    std::vector<float> scores = {
        -10.0f, -5.0f, -5.0f,
        -1.0f, -1.5f, -2.0f,
        -3.0f, -3.5f, -4.0f, -4.5f
    };

    ASSERT_TRUE(tokenizer.initialize(config, vocab, scores));
    ASSERT_EQ(tokenizer.vocab_size(), 10);
}

TEST(sentencepiece_tokenizer_encode_decode) {
    SentencePieceTokenizer tokenizer;

    TokenizerConfig config;
    config.n_vocab = 100;
    config.bos_token_id = 1;
    config.eos_token_id = 2;
    config.unk_token_id = 0;

    std::vector<std::string> vocab = {
        "<unk>", "<s>", "</s>",
        "▁hello", "▁world", "▁",
        "▁the", "▁a", "▁is", "▁are"
    };

    std::vector<float> scores = {
        -10.0f, -5.0f, -5.0f,
        -1.0f, -1.5f, -2.0f,
        -3.0f, -3.5f, -4.0f, -4.5f
    };

    tokenizer.initialize(config, vocab, scores);

    // Test encoding
    std::vector<int32_t> tokens = tokenizer.encode("hello world", true);

    // Should have BOS token
    ASSERT_EQ(tokens[0], 1);

    // Test decoding
    std::string decoded = tokenizer.decode(tokens, true);
    ASSERT_TRUE(!decoded.empty());
}

// Test tokenizer factory
TEST(tokenizer_factory) {
    auto bpe = create_tokenizer("bpe");
    ASSERT_TRUE(bpe != nullptr);

    auto sp = create_tokenizer("sentencepiece");
    ASSERT_TRUE(sp != nullptr);

    auto gpt2 = create_tokenizer("gpt2");
    ASSERT_TRUE(gpt2 != nullptr);

    auto llama = create_tokenizer("llama");
    ASSERT_TRUE(llama != nullptr);
}

// Test UTF-8 handling
TEST(utf8_handling) {
    BPETokenizer tokenizer;

    TokenizerConfig config;
    config.n_vocab = 100;
    config.bos_token_id = 1;
    config.eos_token_id = 2;
    config.unk_token_id = 0;

    std::vector<std::string> vocab = {
        "<unk>", "<s>", "</s>",
        "你好", "世界", " ",
        "hello", "world"
    };

    tokenizer.initialize(config, vocab);

    // Test Chinese characters
    std::vector<int32_t> tokens = tokenizer.encode("你好世界", true);
    ASSERT_TRUE(tokens.size() > 1);

    std::string decoded = tokenizer.decode(tokens, true);
    ASSERT_TRUE(decoded.find("你好") != std::string::npos);
    ASSERT_TRUE(decoded.find("世界") != std::string::npos);
}

int main() {
    std::cout << "=== Tokenizer Tests ===" << std::endl;

    RUN_TEST(bpe_tokenizer_init);
    RUN_TEST(bpe_tokenizer_encode_decode);
    RUN_TEST(bpe_tokenizer_special_tokens);
    RUN_TEST(sentencepiece_tokenizer_init);
    RUN_TEST(sentencepiece_tokenizer_encode_decode);
    RUN_TEST(tokenizer_factory);
    RUN_TEST(utf8_handling);

    std::cout << "\nAll tokenizer tests passed!" << std::endl;
    return 0;
}
