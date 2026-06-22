#pragma once

#include <vector>
#include <cstdint>
#include <memory>
#include <cmath>

namespace llm_engine {

// KV Cache for storing key-value pairs during inference
// This is crucial for efficient autoregressive generation
class KVCache {
public:
    KVCache() = default;
    ~KVCache() = default;

    // Initialize cache with dimensions
    bool initialize(uint32_t n_layers, uint32_t n_ctx, uint32_t n_embd, uint32_t n_head);

    // Store key and value for a specific layer and position
    void store(uint32_t layer, uint32_t position,
              const float* key, const float* value);

    // Retrieve key and value for a specific layer
    // Returns pointer to contiguous memory for all positions up to current
    const float* get_keys(uint32_t layer) const;
    const float* get_values(uint32_t layer) const;

    // Get dimensions
    uint32_t n_layers() const { return n_layers_; }
    uint32_t n_ctx() const { return n_ctx_; }
    uint32_t n_embd() const { return n_embd_; }
    uint32_t n_head() const { return n_head_; }

    // Clear cache
    void clear();

    // Get current sequence length (number of stored positions)
    uint32_t current_length() const { return current_pos_; }

    // Advance position
    void advance() { current_pos_++; }

    // Check if cache is full
    bool is_full() const { return current_pos_ >= n_ctx_; }

private:
    // Cache dimensions
    uint32_t n_layers_ = 0;
    uint32_t n_ctx_ = 0;
    uint32_t n_embd_ = 0;
    uint32_t n_head_ = 0;

    // Current position in sequence
    uint32_t current_pos_ = 0;

    // Key-value storage
    // Shape: [n_layers][n_ctx][n_embd]
    std::vector<std::vector<float>> keys_;
    std::vector<std::vector<float>> values_;
};

// Paged KV Cache (inspired by vLLM's PagedAttention)
// More memory efficient for long sequences
class PagedKVCache {
public:
    struct Page {
        static constexpr uint32_t PAGE_SIZE = 16;  // Tokens per page
        std::vector<float> keys;
        std::vector<float> values;
        uint32_t used_slots = 0;

        Page(uint32_t embd_size) : keys(PAGE_SIZE * embd_size, 0.0f),
                                   values(PAGE_SIZE * embd_size, 0.0f) {}
    };

    PagedKVCache() = default;
    ~PagedKVCache() = default;

    // Initialize with dimensions and pool size
    bool initialize(uint32_t n_layers, uint32_t n_embd, uint32_t n_head,
                   uint32_t max_pages = 1024);

    // Allocate a new page for a layer
    Page* allocate_page(uint32_t layer);

    // Store key-value pair
    void store(uint32_t layer, uint32_t position,
              const float* key, const float* value);

    // Get all pages for a layer
    const std::vector<Page*>& get_pages(uint32_t layer) const;

    // Get current sequence length
    uint32_t current_length() const { return current_pos_; }

    // Clear all pages
    void clear();

private:
    uint32_t n_layers_ = 0;
    uint32_t n_embd_ = 0;
    uint32_t n_head_ = 0;
    uint32_t max_pages_ = 0;
    uint32_t current_pos_ = 0;

    // Page pool per layer
    std::vector<std::vector<Page*>> layer_pages_;

    // Free page pool
    std::vector<Page*> free_pages_;

    // All allocated pages (for cleanup)
    std::vector<std::unique_ptr<Page>> all_pages_;
};

// Simple sliding window KV Cache for memory efficiency
class SlidingWindowKVCache {
public:
    SlidingWindowKVCache() = default;
    ~SlidingWindowKVCache() = default;

    // Initialize with window size
    bool initialize(uint32_t n_layers, uint32_t window_size,
                   uint32_t n_embd, uint32_t n_head);

    // Store key-value pair
    void store(uint32_t layer, uint32_t position,
              const float* key, const float* value);

    // Get keys and values within window
    const float* get_keys(uint32_t layer) const;
    const float* get_values(uint32_t layer) const;

    // Get window start position
    uint32_t window_start() const;

    // Get current length
    uint32_t current_length() const { return current_pos_; }

    // Clear cache
    void clear();

private:
    uint32_t n_layers_ = 0;
    uint32_t window_size_ = 0;
    uint32_t n_embd_ = 0;
    uint32_t n_head_ = 0;
    uint32_t current_pos_ = 0;

    // Circular buffers per layer
    std::vector<std::vector<float>> keys_;
    std::vector<std::vector<float>> values_;
};

// Factory function to create KV cache
enum class KVCacheType {
    STANDARD,
    PAGED,
    SLIDING_WINDOW
};

std::unique_ptr<KVCache> create_kv_cache(KVCacheType type, uint32_t n_layers,
                                         uint32_t n_ctx, uint32_t n_embd,
                                         uint32_t n_head);

} // namespace llm_engine
