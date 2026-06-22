#include "kv_cache.h"
#include <cstring>
#include <algorithm>

namespace llm_engine {

// Standard KVCache implementation

bool KVCache::initialize(uint32_t n_layers, uint32_t n_ctx, uint32_t n_embd, uint32_t n_head) {
    n_layers_ = n_layers;
    n_ctx_ = n_ctx;
    n_embd_ = n_embd;
    n_head_ = n_head;
    current_pos_ = 0;

    // Allocate key and value storage
    keys_.resize(n_layers);
    values_.resize(n_layers);

    for (uint32_t layer = 0; layer < n_layers; ++layer) {
        keys_[layer].resize(n_ctx * n_embd, 0.0f);
        values_[layer].resize(n_ctx * n_embd, 0.0f);
    }

    return true;
}

void KVCache::store(uint32_t layer, uint32_t position,
                    const float* key, const float* value) {
    if (layer >= n_layers_ || position >= n_ctx_) {
        return;
    }

    // Store key
    float* key_ptr = keys_[layer].data() + position * n_embd_;
    std::memcpy(key_ptr, key, n_embd_ * sizeof(float));

    // Store value
    float* value_ptr = values_[layer].data() + position * n_embd_;
    std::memcpy(value_ptr, value, n_embd_ * sizeof(float));
}

const float* KVCache::get_keys(uint32_t layer) const {
    if (layer >= n_layers_) {
        return nullptr;
    }
    return keys_[layer].data();
}

const float* KVCache::get_values(uint32_t layer) const {
    if (layer >= n_layers_) {
        return nullptr;
    }
    return values_[layer].data();
}

void KVCache::clear() {
    current_pos_ = 0;
    for (auto& layer_keys : keys_) {
        std::fill(layer_keys.begin(), layer_keys.end(), 0.0f);
    }
    for (auto& layer_values : values_) {
        std::fill(layer_values.begin(), layer_values.end(), 0.0f);
    }
}

// PagedKVCache implementation

bool PagedKVCache::initialize(uint32_t n_layers, uint32_t n_embd, uint32_t n_head,
                               uint32_t max_pages) {
    n_layers_ = n_layers;
    n_embd_ = n_embd;
    n_head_ = n_head;
    max_pages_ = max_pages;
    current_pos_ = 0;

    // Initialize page pools for each layer
    layer_pages_.resize(n_layers);

    // Pre-allocate pages for the pool
    for (uint32_t i = 0; i < max_pages; ++i) {
        auto page = std::make_unique<Page>(n_embd);
        free_pages_.push_back(page.get());
        all_pages_.push_back(std::move(page));
    }

    return true;
}

PagedKVCache::Page* PagedKVCache::allocate_page(uint32_t layer) {
    if (free_pages_.empty()) {
        return nullptr;  // Out of memory
    }

    Page* page = free_pages_.back();
    free_pages_.pop_back();

    // Reset page state
    page->used_slots = 0;
    std::fill(page->keys.begin(), page->keys.end(), 0.0f);
    std::fill(page->values.begin(), page->values.end(), 0.0f);

    layer_pages_[layer].push_back(page);
    return page;
}

void PagedKVCache::store(uint32_t layer, uint32_t position,
                         const float* key, const float* value) {
    if (layer >= n_layers_) return;

    // Calculate which page and slot to use
    uint32_t page_idx = position / Page::PAGE_SIZE;
    uint32_t slot_idx = position % Page::PAGE_SIZE;

    // Allocate pages as needed
    while (layer_pages_[layer].size() <= page_idx) {
        if (!allocate_page(layer)) {
            return;  // Out of memory
        }
    }

    Page* page = layer_pages_[layer][page_idx];

    // Store key
    float* key_ptr = page->keys.data() + slot_idx * n_embd_;
    std::memcpy(key_ptr, key, n_embd_ * sizeof(float));

    // Store value
    float* value_ptr = page->values.data() + slot_idx * n_embd_;
    std::memcpy(value_ptr, value, n_embd_ * sizeof(float));

    // Update used slots
    page->used_slots = std::max(page->used_slots, slot_idx + 1);

    current_pos_ = std::max(current_pos_, position + 1);
}

const std::vector<PagedKVCache::Page*>& PagedKVCache::get_pages(uint32_t layer) const {
    return layer_pages_[layer];
}

void PagedKVCache::clear() {
    current_pos_ = 0;

    // Return all pages to free pool
    for (auto& pages : layer_pages_) {
        for (Page* page : pages) {
            free_pages_.push_back(page);
        }
        pages.clear();
    }
}

// SlidingWindowKVCache implementation

bool SlidingWindowKVCache::initialize(uint32_t n_layers, uint32_t window_size,
                                      uint32_t n_embd, uint32_t n_head) {
    n_layers_ = n_layers;
    window_size_ = window_size;
    n_embd_ = n_embd;
    n_head_ = n_head;
    current_pos_ = 0;

    // Allocate circular buffers
    keys_.resize(n_layers);
    values_.resize(n_layers);

    for (uint32_t layer = 0; layer < n_layers; ++layer) {
        keys_[layer].resize(window_size * n_embd, 0.0f);
        values_[layer].resize(window_size * n_embd, 0.0f);
    }

    return true;
}

void SlidingWindowKVCache::store(uint32_t layer, uint32_t position,
                                 const float* key, const float* value) {
    if (layer >= n_layers_) return;

    // Use circular indexing
    uint32_t idx = position % window_size_;

    // Store key
    float* key_ptr = keys_[layer].data() + idx * n_embd_;
    std::memcpy(key_ptr, key, n_embd_ * sizeof(float));

    // Store value
    float* value_ptr = values_[layer].data() + idx * n_embd_;
    std::memcpy(value_ptr, value, n_embd_ * sizeof(float));

    current_pos_ = std::max(current_pos_, position + 1);
}

const float* SlidingWindowKVCache::get_keys(uint32_t layer) const {
    if (layer >= n_layers_) {
        return nullptr;
    }
    return keys_[layer].data();
}

const float* SlidingWindowKVCache::get_values(uint32_t layer) const {
    if (layer >= n_layers_) {
        return nullptr;
    }
    return values_[layer].data();
}

uint32_t SlidingWindowKVCache::window_start() const {
    if (current_pos_ <= window_size_) {
        return 0;
    }
    return current_pos_ - window_size_;
}

void SlidingWindowKVCache::clear() {
    current_pos_ = 0;
    for (auto& layer_keys : keys_) {
        std::fill(layer_keys.begin(), layer_keys.end(), 0.0f);
    }
    for (auto& layer_values : values_) {
        std::fill(layer_values.begin(), layer_values.end(), 0.0f);
    }
}

// Factory function
std::unique_ptr<KVCache> create_kv_cache(KVCacheType type, uint32_t n_layers,
                                         uint32_t n_ctx, uint32_t n_embd,
                                         uint32_t n_head) {
    switch (type) {
        case KVCacheType::STANDARD: {
            auto cache = std::make_unique<KVCache>();
            cache->initialize(n_layers, n_ctx, n_embd, n_head);
            return cache;
        }
        case KVCacheType::SLIDING_WINDOW: {
            auto cache = std::make_unique<SlidingWindowKVCache>();
            cache->initialize(n_layers, n_ctx / 2, n_embd, n_head);
            return cache;
        }
        case KVCacheType::PAGED:
        default:
            // PagedKVCache is not a KVCache subclass, handle separately
            // For now, return standard cache
            auto cache = std::make_unique<KVCache>();
            cache->initialize(n_layers, n_ctx, n_embd, n_head);
            return cache;
    }
}

} // namespace llm_engine
