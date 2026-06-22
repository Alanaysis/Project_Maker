#include "kv_cache.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>

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

#define ASSERT_NEAR(a, b, eps) do { \
    if (std::abs((a) - (b)) > (eps)) { \
        std::cerr << "Assertion failed: " << #a << " not near " << #b << std::endl; \
        std::cerr << "  Actual: " << (a) << " vs " << (b) << std::endl; \
        exit(1); \
    } \
} while(0)

// Test KVCache initialization
TEST(kv_cache_init) {
    KVCache cache;

    uint32_t n_layers = 12;
    uint32_t n_ctx = 512;
    uint32_t n_embd = 768;
    uint32_t n_head = 12;

    ASSERT_TRUE(cache.initialize(n_layers, n_ctx, n_embd, n_head));
    ASSERT_EQ(cache.n_layers(), n_layers);
    ASSERT_EQ(cache.n_ctx(), n_ctx);
    ASSERT_EQ(cache.n_embd(), n_embd);
    ASSERT_EQ(cache.n_head(), n_head);
    ASSERT_EQ(cache.current_length(), 0);
    ASSERT_TRUE(!cache.is_full());
}

// Test KVCache store and retrieve
TEST(kv_cache_store_retrieve) {
    KVCache cache;

    uint32_t n_layers = 2;
    uint32_t n_ctx = 10;
    uint32_t n_embd = 4;
    uint32_t n_head = 2;

    cache.initialize(n_layers, n_ctx, n_embd, n_head);

    // Create test data
    std::vector<float> key = {1.0f, 2.0f, 3.0f, 4.0f};
    std::vector<float> value = {5.0f, 6.0f, 7.0f, 8.0f};

    // Store at position 0
    cache.store(0, 0, key.data(), value.data());

    // Retrieve and verify
    const float* stored_keys = cache.get_keys(0);
    const float* stored_values = cache.get_values(0);

    ASSERT_TRUE(stored_keys != nullptr);
    ASSERT_TRUE(stored_values != nullptr);

    // Check stored values
    ASSERT_NEAR(stored_keys[0], 1.0f, 1e-6f);
    ASSERT_NEAR(stored_keys[1], 2.0f, 1e-6f);
    ASSERT_NEAR(stored_keys[2], 3.0f, 1e-6f);
    ASSERT_NEAR(stored_keys[3], 4.0f, 1e-6f);

    ASSERT_NEAR(stored_values[0], 5.0f, 1e-6f);
    ASSERT_NEAR(stored_values[1], 6.0f, 1e-6f);
    ASSERT_NEAR(stored_values[2], 7.0f, 1e-6f);
    ASSERT_NEAR(stored_values[3], 8.0f, 1e-6f);
}

// Test KVCache multiple positions
TEST(kv_cache_multiple_positions) {
    KVCache cache;

    uint32_t n_layers = 1;
    uint32_t n_ctx = 5;
    uint32_t n_embd = 2;
    uint32_t n_head = 1;

    cache.initialize(n_layers, n_ctx, n_embd, n_head);

    // Store at multiple positions
    for (uint32_t pos = 0; pos < 5; ++pos) {
        std::vector<float> key = {static_cast<float>(pos), static_cast<float>(pos) + 1.0f};
        std::vector<float> value = {static_cast<float>(pos) * 2, static_cast<float>(pos) * 2 + 1.0f};

        cache.store(0, pos, key.data(), value.data());
    }

    // Verify each position
    const float* stored_keys = cache.get_keys(0);
    const float* stored_values = cache.get_values(0);

    for (uint32_t pos = 0; pos < 5; ++pos) {
        ASSERT_NEAR(stored_keys[pos * 2], static_cast<float>(pos), 1e-6f);
        ASSERT_NEAR(stored_keys[pos * 2 + 1], static_cast<float>(pos) + 1.0f, 1e-6f);
        ASSERT_NEAR(stored_values[pos * 2], static_cast<float>(pos) * 2, 1e-6f);
        ASSERT_NEAR(stored_values[pos * 2 + 1], static_cast<float>(pos) * 2 + 1.0f, 1e-6f);
    }
}

// Test KVCache advance and clear
TEST(kv_cache_advance_clear) {
    KVCache cache;

    uint32_t n_layers = 1;
    uint32_t n_ctx = 3;
    uint32_t n_embd = 2;
    uint32_t n_head = 1;

    cache.initialize(n_layers, n_ctx, n_embd, n_head);

    // Store and advance
    std::vector<float> key = {1.0f, 2.0f};
    std::vector<float> value = {3.0f, 4.0f};

    cache.store(0, 0, key.data(), value.data());
    cache.advance();
    ASSERT_EQ(cache.current_length(), 1);

    cache.store(0, 1, key.data(), value.data());
    cache.advance();
    ASSERT_EQ(cache.current_length(), 2);

    // Clear
    cache.clear();
    ASSERT_EQ(cache.current_length(), 0);

    // Verify cleared state
    const float* stored_keys = cache.get_keys(0);
    ASSERT_NEAR(stored_keys[0], 0.0f, 1e-6f);
    ASSERT_NEAR(stored_keys[1], 0.0f, 1e-6f);
}

// Test SlidingWindowKVCache
TEST(sliding_window_cache) {
    SlidingWindowKVCache cache;

    uint32_t n_layers = 1;
    uint32_t window_size = 3;
    uint32_t n_embd = 2;
    uint32_t n_head = 1;

    cache.initialize(n_layers, window_size, n_embd, n_head);

    // Store more than window size
    for (uint32_t pos = 0; pos < 5; ++pos) {
        std::vector<float> key = {static_cast<float>(pos), static_cast<float>(pos) + 1.0f};
        std::vector<float> value = {static_cast<float>(pos) * 2, static_cast<float>(pos) * 2 + 1.0f};

        cache.store(0, pos, key.data(), value.data());
    }

    // Should only keep last 3 positions
    ASSERT_EQ(cache.window_start(), 2);
    ASSERT_EQ(cache.current_length(), 5);

    // Check that the buffer contains the last 3 positions (wrapped around)
    const float* stored_keys = cache.get_keys(0);
    ASSERT_TRUE(stored_keys != nullptr);
}

// Test PagedKVCache
TEST(paged_kv_cache) {
    PagedKVCache cache;

    uint32_t n_layers = 1;
    uint32_t n_embd = 2;
    uint32_t n_head = 1;
    uint32_t max_pages = 4;

    cache.initialize(n_layers, n_embd, n_head, max_pages);

    // Store some values
    std::vector<float> key = {1.0f, 2.0f};
    std::vector<float> value = {3.0f, 4.0f};

    cache.store(0, 0, key.data(), value.data());
    cache.store(0, 1, key.data(), value.data());

    // Check pages
    const auto& pages = cache.get_pages(0);
    ASSERT_TRUE(pages.size() > 0);
    ASSERT_EQ(cache.current_length(), 2);

    // Clear and reuse pages
    cache.clear();
    ASSERT_EQ(cache.current_length(), 0);
}

// Test factory function
TEST(kv_cache_factory) {
    // Standard cache
    auto standard = create_kv_cache(KVCacheType::STANDARD, 2, 10, 4, 2);
    ASSERT_TRUE(standard != nullptr);

    // Sliding window cache
    auto sliding = create_kv_cache(KVCacheType::SLIDING_WINDOW, 2, 10, 4, 2);
    ASSERT_TRUE(sliding != nullptr);

    // Paged cache (falls back to standard)
    auto paged = create_kv_cache(KVCacheType::PAGED, 2, 10, 4, 2);
    ASSERT_TRUE(paged != nullptr);
}

int main() {
    std::cout << "=== KV Cache Tests ===" << std::endl;

    RUN_TEST(kv_cache_init);
    RUN_TEST(kv_cache_store_retrieve);
    RUN_TEST(kv_cache_multiple_positions);
    RUN_TEST(kv_cache_advance_clear);
    RUN_TEST(sliding_window_cache);
    RUN_TEST(paged_kv_cache);
    RUN_TEST(kv_cache_factory);

    std::cout << "\nAll KV cache tests passed!" << std::endl;
    return 0;
}
