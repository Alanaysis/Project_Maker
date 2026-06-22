#include "gguf_loader.h"
#include <iostream>
#include <cstring>
#include <stdexcept>

namespace llm_engine {

bool GGUFLoader::load(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Failed to open GGUF file: " << filepath << std::endl;
        return false;
    }

    // Read header
    if (!read_header(file)) {
        std::cerr << "Failed to read GGUF header" << std::endl;
        return false;
    }

    // Validate magic number
    if (model_.header.magic != GGUF_MAGIC) {
        std::cerr << "Invalid GGUF magic number: 0x"
                  << std::hex << model_.header.magic << std::endl;
        return false;
    }

    // Validate version
    if (model_.header.version < GGUF_VERSION_1 || model_.header.version > GGUF_VERSION_3) {
        std::cerr << "Unsupported GGUF version: " << model_.header.version << std::endl;
        return false;
    }

    std::cout << "Loading GGUF model v" << model_.header.version << std::endl;
    std::cout << "Tensor count: " << model_.header.tensor_count << std::endl;
    std::cout << "Metadata entries: " << model_.header.metadata_kv_count << std::endl;

    // Read metadata
    if (!read_metadata(file)) {
        std::cerr << "Failed to read GGUF metadata" << std::endl;
        return false;
    }

    // Read tensor infos
    if (!read_tensor_infos(file)) {
        std::cerr << "Failed to read tensor infos" << std::endl;
        return false;
    }

    // Read tensor data
    if (!read_tensor_data(file)) {
        std::cerr << "Failed to read tensor data" << std::endl;
        return false;
    }

    // Extract model parameters from metadata
    GGUFMetadataValue value;

    // Try to get architecture
    if (get_metadata("general.architecture", value)) {
        std::cout << "Architecture: " << value.string_val << std::endl;
    }

    // Get model parameters
    if (get_metadata("llama.embedding_length", value)) {
        model_.n_embd = value.uint32;
    } else if (get_metadata("general.embedding_length", value)) {
        model_.n_embd = value.uint32;
    }

    if (get_metadata("llama.attention.head_count", value)) {
        model_.n_head = value.uint32;
    } else if (get_metadata("general.attention.head_count", value)) {
        model_.n_head = value.uint32;
    }

    if (get_metadata("llama.block_count", value)) {
        model_.n_layer = value.uint32;
    } else if (get_metadata("general.block_count", value)) {
        model_.n_layer = value.uint32;
    }

    if (get_metadata("llama.context_length", value)) {
        model_.n_ctx = value.uint32;
    } else if (get_metadata("general.context_length", value)) {
        model_.n_ctx = value.uint32;
    }

    if (get_metadata("llama.feed_forward_length", value)) {
        model_.n_ff = value.uint32;
    } else if (get_metadata("general.feed_forward_length", value)) {
        model_.n_ff = value.uint32;
    }

    if (get_metadata("llama.attention.head_count_kv", value)) {
        model_.n_head_kv = value.uint32;
    } else if (get_metadata("general.attention.head_count_kv", value)) {
        model_.n_head_kv = value.uint32;
    }

    // Get vocabulary size from tokenizer metadata
    if (get_metadata("tokenizer.ggml.tokens", value)) {
        model_.n_vocab = static_cast<uint32_t>(value.array_val.size());
    }

    std::cout << "Model parameters:" << std::endl;
    std::cout << "  Vocab size: " << model_.n_vocab << std::endl;
    std::cout << "  Embedding dim: " << model_.n_embd << std::endl;
    std::cout << "  Attention heads: " << model_.n_head << std::endl;
    std::cout << "  Layers: " << model_.n_layer << std::endl;
    std::cout << "  Context length: " << model_.n_ctx << std::endl;
    std::cout << "  FFN dim: " << model_.n_ff << std::endl;
    std::cout << "  KV heads: " << model_.n_head_kv << std::endl;

    loaded_ = true;
    return true;
}

bool GGUFLoader::read_header(std::ifstream& file) {
    file.read(reinterpret_cast<char*>(&model_.header.magic), sizeof(uint32_t));
    file.read(reinterpret_cast<char*>(&model_.header.version), sizeof(uint32_t));
    file.read(reinterpret_cast<char*>(&model_.header.tensor_count), sizeof(uint64_t));
    file.read(reinterpret_cast<char*>(&model_.header.metadata_kv_count), sizeof(uint64_t));

    return file.good();
}

bool GGUFLoader::read_metadata(std::ifstream& file) {
    for (uint64_t i = 0; i < model_.header.metadata_kv_count; ++i) {
        std::string key;
        if (!read_string(file, key)) {
            return false;
        }

        GGUFMetadataValue value;
        if (!read_metadata_value(file, value)) {
            return false;
        }

        model_.metadata[key] = value;
    }
    return true;
}

bool GGUFLoader::read_tensor_infos(std::ifstream& file) {
    model_.tensor_infos.resize(model_.header.tensor_count);

    for (uint64_t i = 0; i < model_.header.tensor_count; ++i) {
        GGUFTensorInfo& info = model_.tensor_infos[i];

        // Read name
        if (!read_string(file, info.name)) {
            return false;
        }

        // Read number of dimensions
        uint32_t n_dims;
        file.read(reinterpret_cast<char*>(&n_dims), sizeof(uint32_t));
        if (!file.good()) return false;

        // Read dimensions
        info.dimensions.resize(n_dims);
        for (uint32_t d = 0; d < n_dims; ++d) {
            file.read(reinterpret_cast<char*>(&info.dimensions[d]), sizeof(uint64_t));
            if (!file.good()) return false;
        }

        // Read type
        uint32_t type;
        file.read(reinterpret_cast<char*>(&type), sizeof(uint32_t));
        info.type = static_cast<GGMLType>(type);

        // Read offset
        file.read(reinterpret_cast<char*>(&info.offset), sizeof(uint64_t));
        if (!file.good()) return false;
    }

    return true;
}

bool GGUFLoader::read_tensor_data(std::ifstream& file) {
    // Calculate total tensor data size
    uint64_t total_size = 0;
    for (const auto& info : model_.tensor_infos) {
        uint64_t tensor_size = 1;
        for (const auto& dim : info.dimensions) {
            tensor_size *= dim;
        }
        tensor_size *= ggml_type_size(info.type);
        total_size = std::max(total_size, info.offset + tensor_size);
    }

    // Read all tensor data
    model_.tensor_data.resize(total_size);
    file.read(reinterpret_cast<char*>(model_.tensor_data.data()), total_size);

    return file.good();
}

bool GGUFLoader::read_string(std::ifstream& file, std::string& str) {
    uint64_t len;
    file.read(reinterpret_cast<char*>(&len), sizeof(uint64_t));
    if (!file.good()) return false;

    str.resize(len);
    file.read(&str[0], len);
    return file.good();
}

bool GGUFLoader::read_metadata_value(std::ifstream& file, GGUFMetadataValue& value) {
    uint32_t type;
    file.read(reinterpret_cast<char*>(&type), sizeof(uint32_t));
    if (!file.good()) return false;

    value.type = static_cast<GGUFMetadataType>(type);

    switch (value.type) {
        case GGUFMetadataType::UINT8:
            file.read(reinterpret_cast<char*>(&value.uint8), sizeof(uint8_t));
            break;
        case GGUFMetadataType::INT8:
            file.read(reinterpret_cast<char*>(&value.int8), sizeof(int8_t));
            break;
        case GGUFMetadataType::UINT16:
            file.read(reinterpret_cast<char*>(&value.uint16), sizeof(uint16_t));
            break;
        case GGUFMetadataType::INT16:
            file.read(reinterpret_cast<char*>(&value.int16), sizeof(int16_t));
            break;
        case GGUFMetadataType::UINT32:
            file.read(reinterpret_cast<char*>(&value.uint32), sizeof(uint32_t));
            break;
        case GGUFMetadataType::INT32:
            file.read(reinterpret_cast<char*>(&value.int32), sizeof(int32_t));
            break;
        case GGUFMetadataType::UINT64:
            file.read(reinterpret_cast<char*>(&value.uint64), sizeof(uint64_t));
            break;
        case GGUFMetadataType::INT64:
            file.read(reinterpret_cast<char*>(&value.int64), sizeof(int64_t));
            break;
        case GGUFMetadataType::FLOAT32:
            file.read(reinterpret_cast<char*>(&value.float32), sizeof(float));
            break;
        case GGUFMetadataType::FLOAT64:
            file.read(reinterpret_cast<char*>(&value.float64), sizeof(double));
            break;
        case GGUFMetadataType::BOOL:
            file.read(reinterpret_cast<char*>(&value.bool_val), sizeof(bool));
            break;
        case GGUFMetadataType::STRING:
            if (!read_string(file, value.string_val)) return false;
            break;
        case GGUFMetadataType::ARRAY: {
            uint32_t array_type;
            uint64_t array_len;
            file.read(reinterpret_cast<char*>(&array_type), sizeof(uint32_t));
            file.read(reinterpret_cast<char*>(&array_len), sizeof(uint64_t));
            if (!file.good()) return false;

            value.array_val.resize(array_len);
            for (uint64_t i = 0; i < array_len; ++i) {
                value.array_val[i].type = static_cast<GGUFMetadataType>(array_type);
                if (!read_metadata_value(file, value.array_val[i])) return false;
            }
            break;
        }
        default:
            std::cerr << "Unknown metadata type: " << type << std::endl;
            return false;
    }

    return file.good();
}

const uint8_t* GGUFLoader::get_tensor_data(const std::string& name) const {
    for (const auto& info : model_.tensor_infos) {
        if (info.name == name) {
            return model_.tensor_data.data() + info.offset;
        }
    }
    return nullptr;
}

const GGUFTensorInfo* GGUFLoader::get_tensor_info(const std::string& name) const {
    for (const auto& info : model_.tensor_infos) {
        if (info.name == name) {
            return &info;
        }
    }
    return nullptr;
}

bool GGUFLoader::get_metadata(const std::string& key, GGUFMetadataValue& value) const {
    auto it = model_.metadata.find(key);
    if (it != model_.metadata.end()) {
        value = it->second;
        return true;
    }
    return false;
}

} // namespace llm_engine
