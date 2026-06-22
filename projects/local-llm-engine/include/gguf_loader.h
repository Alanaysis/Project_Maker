#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <fstream>
#include <memory>
#include <unordered_map>

namespace llm_engine {

// GGUF Magic Number
constexpr uint32_t GGUF_MAGIC = 0x46475547; // "GGUF" in little-endian

// GGUF Version
constexpr uint32_t GGUF_VERSION_1 = 1;
constexpr uint32_t GGUF_VERSION_2 = 2;
constexpr uint32_t GGUF_VERSION_3 = 3;

// GGUF Metadata Value Types
enum class GGUFMetadataType : uint32_t {
    UINT8 = 0,
    INT8 = 1,
    UINT16 = 2,
    INT16 = 3,
    UINT32 = 4,
    INT32 = 5,
    FLOAT32 = 6,
    BOOL = 7,
    STRING = 8,
    ARRAY = 9,
    UINT64 = 10,
    INT64 = 11,
    FLOAT64 = 12
};

// GGML Type for tensor quantization
enum class GGMLType : uint32_t {
    F32 = 0,
    F16 = 1,
    Q4_0 = 2,
    Q4_1 = 3,
    Q5_0 = 6,
    Q5_1 = 7,
    Q8_0 = 8,
    Q8_1 = 9,
    Q2_K = 10,
    Q3_K = 11,
    Q4_K = 12,
    Q5_K = 13,
    Q6_K = 14,
    Q8_K = 15,
    IQ2_XXS = 16,
    IQ2_XS = 17,
    IQ3_XXS = 18,
    IQ1_S = 19,
    IQ4_NL = 20,
    IQ3_S = 21,
    IQ2_S = 22,
    IQ4_XS = 23,
    IQ1_M = 24,
    BF16 = 30,
    TQ1_0 = 34,
    TQ2_0 = 35
};

// Get type size in bytes
inline size_t ggml_type_size(GGMLType type) {
    switch (type) {
        case GGMLType::F32: return 4;
        case GGMLType::F16: return 2;
        case GGMLType::BF16: return 2;
        case GGMLType::Q4_0: return 18; // block size 32, 4 bits + scale
        case GGMLType::Q4_1: return 20; // block size 32, 4 bits + scale + min
        case GGMLType::Q5_0: return 22; // block size 32, 5 bits + scale
        case GGMLType::Q5_1: return 24; // block size 32, 5 bits + scale + min
        case GGMLType::Q8_0: return 34; // block size 32, 8 bits + scale
        case GGMLType::Q8_1: return 36; // block size 32, 8 bits + scale + min
        default: return 0;
    }
}

// GGUF Metadata Value
struct GGUFMetadataValue {
    GGUFMetadataType type;
    union {
        uint8_t uint8;
        int8_t int8;
        uint16_t uint16;
        int16_t int16;
        uint32_t uint32;
        int32_t int32;
        uint64_t uint64;
        int64_t int64;
        float float32;
        double float64;
        bool bool_val;
    };
    std::string string_val;
    std::vector<GGUFMetadataValue> array_val;
};

// GGUF Header
struct GGUFHeader {
    uint32_t magic;
    uint32_t version;
    uint64_t tensor_count;
    uint64_t metadata_kv_count;
};

// GGUF Tensor Info
struct GGUFTensorInfo {
    std::string name;
    std::vector<uint64_t> dimensions;
    GGMLType type;
    uint64_t offset;
};

// GGUF Model
struct GGUFModel {
    GGUFHeader header;
    std::unordered_map<std::string, GGUFMetadataValue> metadata;
    std::vector<GGUFTensorInfo> tensor_infos;

    // Model architecture parameters (from metadata)
    uint32_t n_vocab = 0;     // Vocabulary size
    uint32_t n_embd = 0;      // Embedding dimension
    uint32_t n_head = 0;      // Number of attention heads
    uint32_t n_layer = 0;     // Number of transformer layers
    uint32_t n_ctx = 0;       // Context length
    uint32_t n_ff = 0;        // Feed-forward dimension
    uint32_t n_head_kv = 0;   // Number of key-value heads (for GQA)

    // Tensor data storage
    std::vector<uint8_t> tensor_data;
};

// GGUF Loader class
class GGUFLoader {
public:
    GGUFLoader() = default;
    ~GGUFLoader() = default;

    // Load GGUF model from file
    bool load(const std::string& filepath);

    // Get model reference
    const GGUFModel& get_model() const { return model_; }

    // Get tensor data by name
    const uint8_t* get_tensor_data(const std::string& name) const;

    // Get tensor info by name
    const GGUFTensorInfo* get_tensor_info(const std::string& name) const;

    // Get metadata value by key
    bool get_metadata(const std::string& key, GGUFMetadataValue& value) const;

    // Check if model is loaded
    bool is_loaded() const { return loaded_; }

private:
    // Read helpers
    bool read_header(std::ifstream& file);
    bool read_metadata(std::ifstream& file);
    bool read_tensor_infos(std::ifstream& file);
    bool read_tensor_data(std::ifstream& file);

    // Read specific types
    bool read_string(std::ifstream& file, std::string& str);
    bool read_metadata_value(std::ifstream& file, GGUFMetadataValue& value);

    GGUFModel model_;
    bool loaded_ = false;
};

} // namespace llm_engine
