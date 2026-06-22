#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <cstdint>

namespace llm_engine {

// Token types
enum class TokenType {
    NORMAL,
    CONTROL,
    USER_DEFINED,
    BYTE,
    UNKNOWN
};

// Token structure
struct Token {
    int32_t id;
    std::string text;
    TokenType type;
    float score;  // For BPE merges
};

// Tokenizer configuration from GGUF metadata
struct TokenizerConfig {
    uint32_t n_vocab = 0;
    std::string model_type;  // "llama", "gpt2", etc.
    std::string bos_token = "<s>";
    std::string eos_token = "</s>";
    std::string unk_token = "<unk>";
    int32_t bos_token_id = 1;
    int32_t eos_token_id = 2;
    int32_t unk_token_id = 0;
};

// Tokenizer base class
class Tokenizer {
public:
    Tokenizer() = default;
    virtual ~Tokenizer() = default;

    // Initialize tokenizer from GGUF metadata
    virtual bool initialize(const TokenizerConfig& config,
                          const std::vector<std::string>& vocab,
                          const std::vector<float>& scores = {}) = 0;

    // Encode text to token IDs
    virtual std::vector<int32_t> encode(const std::string& text, bool add_bos = true) const = 0;

    // Decode token IDs to text
    virtual std::string decode(const std::vector<int32_t>& tokens, bool skip_special = true) const = 0;

    // Get vocabulary size
    virtual uint32_t vocab_size() const = 0;

    // Get token text by ID
    virtual std::string token_to_text(int32_t token_id) const = 0;

    // Get token ID by text
    virtual int32_t text_to_token(const std::string& text) const = 0;

    // Special tokens
    int32_t bos_token_id() const { return config_.bos_token_id; }
    int32_t eos_token_id() const { return config_.eos_token_id; }
    int32_t unk_token_id() const { return config_.unk_token_id; }

protected:
    TokenizerConfig config_;
};

// Simple BPE Tokenizer implementation
class BPETokenizer : public Tokenizer {
public:
    BPETokenizer() = default;
    ~BPETokenizer() override = default;

    bool initialize(const TokenizerConfig& config,
                   const std::vector<std::string>& vocab,
                   const std::vector<float>& scores = {}) override;

    std::vector<int32_t> encode(const std::string& text, bool add_bos = true) const override;

    std::string decode(const std::vector<int32_t>& tokens, bool skip_special = true) const override;

    uint32_t vocab_size() const override { return static_cast<uint32_t>(vocab_.size()); }

    std::string token_to_text(int32_t token_id) const override;

    int32_t text_to_token(const std::string& text) const override;

private:
    // BPE merge operations
    struct Merge {
        std::string left;
        std::string right;
        std::string merged;
        float priority;
    };

    // Apply BPE to a word
    std::vector<std::string> apply_bpe(const std::string& word) const;

    // Split text into words
    std::vector<std::string> split_text(const std::string& text) const;

    // UTF-8 helpers
    static std::vector<uint32_t> utf8_to_unicode(const std::string& str);
    static std::string unicode_to_utf8(uint32_t codepoint);

    // Vocabulary
    std::vector<Token> vocab_;
    std::unordered_map<std::string, int32_t> token_to_id_;
    std::unordered_map<int32_t, std::string> id_to_token_;

    // BPE merges
    std::vector<Merge> merges_;
    std::unordered_map<std::string, int32_t> merge_ranks_;

    // Byte fallback mapping
    std::unordered_map<uint8_t, int32_t> byte_to_token_;
};

// SentencePiece Tokenizer (for LLaMA models)
class SentencePieceTokenizer : public Tokenizer {
public:
    SentencePieceTokenizer() = default;
    ~SentencePieceTokenizer() override = default;

    bool initialize(const TokenizerConfig& config,
                   const std::vector<std::string>& vocab,
                   const std::vector<float>& scores = {}) override;

    std::vector<int32_t> encode(const std::string& text, bool add_bos = true) const override;

    std::string decode(const std::vector<int32_t>& tokens, bool skip_special = true) const override;

    uint32_t vocab_size() const override { return static_cast<uint32_t>(vocab_.size()); }

    std::string token_to_text(int32_t token_id) const override;

    int32_t text_to_token(const std::string& text) const override;

private:
    // SentencePiece model type
    enum class ModelType {
        UNIGRAM,
        BPE
    };

    // Unigram piece
    struct UnigramPiece {
        std::string piece;
        float score;
    };

    // Viterbi segmentation
    std::vector<int32_t> viterbi_segment(const std::string& text) const;

    // Model type
    ModelType model_type_ = ModelType::UNIGRAM;

    // Vocabulary
    std::vector<UnigramPiece> vocab_;
    std::unordered_map<std::string, int32_t> token_to_id_;
    std::unordered_map<int32_t, std::string> id_to_token_;

    // Character coverage
    float character_coverage_ = 0.9995f;
};

// Factory function to create tokenizer
std::unique_ptr<Tokenizer> create_tokenizer(const std::string& type);

} // namespace llm_engine
