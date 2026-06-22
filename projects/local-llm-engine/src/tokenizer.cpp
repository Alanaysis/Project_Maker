#include "tokenizer.h"
#include <iostream>
#include <algorithm>
#include <sstream>
#include <regex>
#include <cstring>

namespace llm_engine {

// BPETokenizer implementation

bool BPETokenizer::initialize(const TokenizerConfig& config,
                              const std::vector<std::string>& vocab,
                              const std::vector<float>& scores) {
    config_ = config;

    // Initialize vocabulary
    vocab_.resize(vocab.size());
    for (size_t i = 0; i < vocab.size(); ++i) {
        vocab_[i].id = static_cast<int32_t>(i);
        vocab_[i].text = vocab[i];
        vocab_[i].type = TokenType::NORMAL;
        vocab_[i].score = (i < scores.size()) ? scores[i] : 0.0f;

        token_to_id_[vocab[i]] = static_cast<int32_t>(i);
        id_to_token_[static_cast<int32_t>(i)] = vocab[i];
    }

    // Initialize byte fallback mapping
    for (int i = 0; i < 256; ++i) {
        std::string byte_str = "<0x" + std::string(1, "0123456789ABCDEF"[i >> 4]) +
                               std::string(1, "0123456789ABCDEF"[i & 0xF]) + ">";
        auto it = token_to_id_.find(byte_str);
        if (it != token_to_id_.end()) {
            byte_to_token_[static_cast<uint8_t>(i)] = it->second;
        }
    }

    return true;
}

std::vector<int32_t> BPETokenizer::encode(const std::string& text, bool add_bos) const {
    std::vector<int32_t> tokens;

    // Add BOS token if requested
    if (add_bos && config_.bos_token_id >= 0) {
        tokens.push_back(config_.bos_token_id);
    }

    // Split text into words
    std::vector<std::string> words = split_text(text);

    // Apply BPE to each word
    for (const auto& word : words) {
        std::vector<std::string> pieces = apply_bpe(word);

        for (const auto& piece : pieces) {
            auto it = token_to_id_.find(piece);
            if (it != token_to_id_.end()) {
                tokens.push_back(it->second);
            } else {
                // Try byte fallback
                for (char c : piece) {
                    auto byte_it = byte_to_token_.find(static_cast<uint8_t>(c));
                    if (byte_it != byte_to_token_.end()) {
                        tokens.push_back(byte_it->second);
                    } else {
                        tokens.push_back(config_.unk_token_id);
                    }
                }
            }
        }
    }

    return tokens;
}

std::string BPETokenizer::decode(const std::vector<int32_t>& tokens, bool skip_special) const {
    std::string result;

    for (int32_t token_id : tokens) {
        // Skip special tokens if requested
        if (skip_special) {
            if (token_id == config_.bos_token_id || token_id == config_.eos_token_id) {
                continue;
            }
        }

        auto it = id_to_token_.find(token_id);
        if (it != id_to_token_.end()) {
            std::string token_text = it->second;

            // Handle byte tokens
            if (token_text.size() == 6 && token_text.substr(0, 3) == "<0x" &&
                token_text.back() == '>') {
                // Convert hex to byte
                try {
                    uint8_t byte = static_cast<uint8_t>(
                        std::stoi(token_text.substr(3, 2), nullptr, 16));
                    result += static_cast<char>(byte);
                } catch (...) {
                    result += token_text;
                }
            } else {
                result += token_text;
            }
        } else {
            result += "<unk>";
        }
    }

    return result;
}

std::string BPETokenizer::token_to_text(int32_t token_id) const {
    auto it = id_to_token_.find(token_id);
    if (it != id_to_token_.end()) {
        return it->second;
    }
    return "<unk>";
}

int32_t BPETokenizer::text_to_token(const std::string& text) const {
    auto it = token_to_id_.find(text);
    if (it != token_to_id_.end()) {
        return it->second;
    }
    return config_.unk_token_id;
}

std::vector<std::string> BPETokenizer::apply_bpe(const std::string& word) const {
    // Simple BPE implementation
    // In a real implementation, this would use pre-computed merge rules

    if (word.empty()) return {};

    // For now, just split into characters as a fallback
    std::vector<std::string> pieces;
    for (size_t i = 0; i < word.size(); ) {
        // Check for UTF-8 multi-byte characters
        uint8_t c = static_cast<uint8_t>(word[i]);
        size_t char_len = 1;

        if ((c & 0x80) == 0) {
            char_len = 1;
        } else if ((c & 0xE0) == 0xC0) {
            char_len = 2;
        } else if ((c & 0xF0) == 0xE0) {
            char_len = 3;
        } else if ((c & 0xF8) == 0xF0) {
            char_len = 4;
        }

        // Check if this piece exists in vocabulary
        std::string piece = word.substr(i, char_len);
        if (token_to_id_.count(piece)) {
            pieces.push_back(piece);
        } else {
            // Try to find larger piece
            bool found = false;
            for (size_t len = char_len + 1; len <= std::min(word.size() - i, (size_t)32); ++len) {
                std::string candidate = word.substr(i, len);
                if (token_to_id_.count(candidate)) {
                    pieces.push_back(candidate);
                    i += len;
                    found = true;
                    break;
                }
            }

            if (!found) {
                pieces.push_back(piece);
            }
        }

        i += char_len;
    }

    return pieces;
}

std::vector<std::string> BPETokenizer::split_text(const std::string& text) const {
    // Simple word splitting
    // In a real implementation, this would handle punctuation, whitespace, etc.
    std::vector<std::string> words;
    std::string current_word;

    for (size_t i = 0; i < text.size(); ++i) {
        char c = text[i];

        // Split on whitespace
        if (std::isspace(c)) {
            if (!current_word.empty()) {
                words.push_back(current_word);
                current_word.clear();
            }
            // Add space as separate token if it exists in vocab
            std::string space(1, c);
            if (token_to_id_.count(space)) {
                words.push_back(space);
            }
        } else {
            current_word += c;
        }
    }

    if (!current_word.empty()) {
        words.push_back(current_word);
    }

    return words;
}

std::vector<uint32_t> BPETokenizer::utf8_to_unicode(const std::string& str) {
    std::vector<uint32_t> result;
    size_t i = 0;

    while (i < str.size()) {
        uint32_t codepoint;
        uint8_t c = static_cast<uint8_t>(str[i]);

        if ((c & 0x80) == 0) {
            codepoint = c;
            i += 1;
        } else if ((c & 0xE0) == 0xC0) {
            if (i + 1 >= str.size()) { i += 1; continue; }
            codepoint = (c & 0x1F) << 6;
            codepoint |= (static_cast<uint8_t>(str[i + 1]) & 0x3F);
            i += 2;
        } else if ((c & 0xF0) == 0xE0) {
            if (i + 2 >= str.size()) { i += 1; continue; }
            codepoint = (c & 0x0F) << 12;
            codepoint |= (static_cast<uint8_t>(str[i + 1]) & 0x3F) << 6;
            codepoint |= (static_cast<uint8_t>(str[i + 2]) & 0x3F);
            i += 3;
        } else if ((c & 0xF8) == 0xF0) {
            if (i + 3 >= str.size()) { i += 1; continue; }
            codepoint = (c & 0x07) << 18;
            codepoint |= (static_cast<uint8_t>(str[i + 1]) & 0x3F) << 12;
            codepoint |= (static_cast<uint8_t>(str[i + 2]) & 0x3F) << 6;
            codepoint |= (static_cast<uint8_t>(str[i + 3]) & 0x3F);
            i += 4;
        } else {
            // Invalid UTF-8, skip
            i += 1;
            continue;
        }

        result.push_back(codepoint);
    }

    return result;
}

std::string BPETokenizer::unicode_to_utf8(uint32_t codepoint) {
    std::string result;

    if (codepoint <= 0x7F) {
        result += static_cast<char>(codepoint);
    } else if (codepoint <= 0x7FF) {
        result += static_cast<char>(0xC0 | (codepoint >> 6));
        result += static_cast<char>(0x80 | (codepoint & 0x3F));
    } else if (codepoint <= 0xFFFF) {
        result += static_cast<char>(0xE0 | (codepoint >> 12));
        result += static_cast<char>(0x80 | ((codepoint >> 6) & 0x3F));
        result += static_cast<char>(0x80 | (codepoint & 0x3F));
    } else if (codepoint <= 0x10FFFF) {
        result += static_cast<char>(0xF0 | (codepoint >> 18));
        result += static_cast<char>(0x80 | ((codepoint >> 12) & 0x3F));
        result += static_cast<char>(0x80 | ((codepoint >> 6) & 0x3F));
        result += static_cast<char>(0x80 | (codepoint & 0x3F));
    }

    return result;
}

// SentencePieceTokenizer implementation

bool SentencePieceTokenizer::initialize(const TokenizerConfig& config,
                                        const std::vector<std::string>& vocab,
                                        const std::vector<float>& scores) {
    config_ = config;

    // Initialize vocabulary
    vocab_.resize(vocab.size());
    for (size_t i = 0; i < vocab.size(); ++i) {
        vocab_[i].piece = vocab[i];
        vocab_[i].score = (i < scores.size()) ? scores[i] : 0.0f;

        token_to_id_[vocab[i]] = static_cast<int32_t>(i);
        id_to_token_[static_cast<int32_t>(i)] = vocab[i];
    }

    return true;
}

std::vector<int32_t> SentencePieceTokenizer::encode(const std::string& text, bool add_bos) const {
    std::vector<int32_t> tokens;

    // Add BOS token if requested
    if (add_bos && config_.bos_token_id >= 0) {
        tokens.push_back(config_.bos_token_id);
    }

    // Use Viterbi segmentation for SentencePiece
    std::vector<int32_t> segmented = viterbi_segment(text);
    tokens.insert(tokens.end(), segmented.begin(), segmented.end());

    return tokens;
}

std::string SentencePieceTokenizer::decode(const std::vector<int32_t>& tokens, bool skip_special) const {
    std::string result;

    for (int32_t token_id : tokens) {
        // Skip special tokens if requested
        if (skip_special) {
            if (token_id == config_.bos_token_id || token_id == config_.eos_token_id) {
                continue;
            }
        }

        auto it = id_to_token_.find(token_id);
        if (it != id_to_token_.end()) {
            std::string piece = it->second;

            // Handle SentencePiece whitespace encoding (U+2581 = ▁)
            // Replace ▁ with space
            size_t pos = 0;
            while ((pos = piece.find("\xe2\x96\x81", pos)) != std::string::npos) {
                piece.replace(pos, 3, " ");
                pos += 1;
            }

            result += piece;
        } else {
            result += "<unk>";
        }
    }

    // Remove leading space if present
    if (!result.empty() && result[0] == ' ') {
        result = result.substr(1);
    }

    return result;
}

std::string SentencePieceTokenizer::token_to_text(int32_t token_id) const {
    auto it = id_to_token_.find(token_id);
    if (it != id_to_token_.end()) {
        return it->second;
    }
    return "<unk>";
}

int32_t SentencePieceTokenizer::text_to_token(const std::string& text) const {
    auto it = token_to_id_.find(text);
    if (it != token_to_id_.end()) {
        return it->second;
    }
    return config_.unk_token_id;
}

std::vector<int32_t> SentencePieceTokenizer::viterbi_segment(const std::string& text) const {
    // SentencePiece Viterbi segmentation
    // This is a simplified version - real implementation would be more complex

    // Add SentencePiece whitespace marker
    std::string processed_text = "\xe2\x96\x81" + text;  // ▁ prefix

    size_t len = processed_text.size();
    std::vector<float> best_score(len + 1, -1e10f);
    std::vector<int32_t> best_token(len + 1, -1);
    std::vector<int32_t> best_prev(len + 1, -1);

    best_score[0] = 0.0f;

    // Dynamic programming
    for (size_t i = 0; i < len; ++i) {
        if (best_score[i] < -1e9f) continue;

        // Try all possible token lengths
        for (size_t token_len = 1; token_len <= std::min(len - i, (size_t)16); ++token_len) {
            std::string piece = processed_text.substr(i, token_len);

            auto it = token_to_id_.find(piece);
            if (it != token_to_id_.end()) {
                float score = best_score[i] + vocab_[it->second].score;
                if (score > best_score[i + token_len]) {
                    best_score[i + token_len] = score;
                    best_token[i + token_len] = it->second;
                    best_prev[i + token_len] = static_cast<int32_t>(i);
                }
            }
        }
    }

    // Backtrack to find best segmentation
    std::vector<int32_t> tokens;
    int32_t pos = static_cast<int32_t>(len);

    while (pos > 0) {
        int32_t token = best_token[pos];
        if (token < 0) {
            // Fallback to character-by-character
            tokens.clear();
            for (size_t i = 0; i < text.size(); ++i) {
                auto it = token_to_id_.find(std::string(1, text[i]));
                if (it != token_to_id_.end()) {
                    tokens.push_back(it->second);
                } else {
                    tokens.push_back(config_.unk_token_id);
                }
            }
            break;
        }

        tokens.push_back(token);
        pos = best_prev[pos];
    }

    std::reverse(tokens.begin(), tokens.end());
    return tokens;
}

// Factory function
std::unique_ptr<Tokenizer> create_tokenizer(const std::string& type) {
    if (type == "bpe" || type == "gpt2") {
        return std::make_unique<BPETokenizer>();
    } else if (type == "sentencepiece" || type == "llama") {
        return std::make_unique<SentencePieceTokenizer>();
    }

    // Default to BPE
    return std::make_unique<BPETokenizer>();
}

} // namespace llm_engine
