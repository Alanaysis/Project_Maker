/**
 * test_pooling.c - Unit tests for pooling operations
 * 
 * Tests cover:
 * - Max pooling
 * - Average pooling
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "edge_inference.h"

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  Test: %s ... ", name); tests_run++
#define PASS() printf("PASS\n"); tests_passed++
#define FAIL(msg) printf("FAIL: %s\n", msg); tests_failed++

#define FLOAT_EQ(a, b, tol) (fabsf((a) - (b)) < (tol))

/* Test max pooling */
static void test_max_pool(void) {
    TEST("max_pool");
    
    ei_tensor_t input, output;
    int32_t in_shape[4] = {1, 1, 4, 4};
    int32_t out_shape[4] = {1, 1, 2, 2};
    
    ei_tensor_alloc(&input, in_shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, out_shape, 4, EI_TENSOR_FP32);
    
    /* 4x4 input with known values */
    float in_data[16] = {
        1.0f, 3.0f, 0.0f, 2.0f,
        5.0f, 0.0f, 4.0f, 1.0f,
        2.0f, 6.0f, 3.0f, 0.0f,
        1.0f, 2.0f, 5.0f, 4.0f
    };
    ei_tensor_copy_from_float(&input, in_data, 16);
    
    /* Create pooling layer */
    ei_layer_t pool_layer;
    memset(&pool_layer, 0, sizeof(ei_layer_t));
    ei_layer_init_pool(&pool_layer, "test_pool", EI_LAYER_MAX_POOL, 2, 2, 2, 2, 0, 0);
    
    ei_run_max_pool(&input, &output, &pool_layer);
    
    /* Expected output (max of each 2x2 window):
     * [3, 4]
     * [6, 5]
     */
    float *out = (float *)output.data;
    float expected[4] = {3.0f, 4.0f, 6.0f, 5.0f};
    
    int ok = 1;
    for (int i = 0; i < 4; i++) {
        if (!FLOAT_EQ(out[i], expected[i], 1e-5)) {
            ok = 0;
            break;
        }
    }
    
    if (ok) PASS();
    else FAIL("max pool output incorrect");
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

/* Test average pooling */
static void test_avg_pool(void) {
    TEST("avg_pool");
    
    ei_tensor_t input, output;
    int32_t in_shape[4] = {1, 1, 4, 4};
    int32_t out_shape[4] = {1, 1, 2, 2};
    
    ei_tensor_alloc(&input, in_shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, out_shape, 4, EI_TENSOR_FP32);
    
    float in_data[16] = {
        1.0f, 2.0f, 3.0f, 4.0f,
        5.0f, 6.0f, 7.0f, 8.0f,
        9.0f, 10.0f, 11.0f, 12.0f,
        13.0f, 14.0f, 15.0f, 16.0f
    };
    ei_tensor_copy_from_float(&input, in_data, 16);
    
    ei_layer_t pool_layer;
    memset(&pool_layer, 0, sizeof(ei_layer_t));
    ei_layer_init_pool(&pool_layer, "test_pool", EI_LAYER_AVG_POOL, 2, 2, 2, 2, 0, 0);
    
    ei_run_avg_pool(&input, &output, &pool_layer);
    
    /* Expected output (average of each 2x2 window):
     * [3.5, 5.5]
     * [11.5, 13.5]
     */
    float *out = (float *)output.data;
    float expected[4] = {3.5f, 5.5f, 11.5f, 13.5f};
    
    int ok = 1;
    for (int i = 0; i < 4; i++) {
        if (!FLOAT_EQ(out[i], expected[i], 1e-5)) {
            ok = 0;
            break;
        }
    }
    
    if (ok) PASS();
    else FAIL("avg pool output incorrect");
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

/* Test max pooling with batch dimension */
static void test_max_pool_batch(void) {
    TEST("max_pool_batch");
    
    ei_tensor_t input, output;
    int32_t in_shape[4] = {2, 1, 4, 4};
    int32_t out_shape[4] = {2, 1, 2, 2};
    
    ei_tensor_alloc(&input, in_shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, out_shape, 4, EI_TENSOR_FP32);
    
    float in_data[32];
    for (int i = 0; i < 32; i++) {
        in_data[i] = (float)(i % 16);
    }
    ei_tensor_copy_from_float(&input, in_data, 32);
    
    ei_layer_t pool_layer;
    memset(&pool_layer, 0, sizeof(ei_layer_t));
    ei_layer_init_pool(&pool_layer, "test_pool", EI_LAYER_MAX_POOL, 2, 2, 2, 2, 0, 0);
    
    int ret = ei_run_max_pool(&input, &output, &pool_layer);
    
    if (ret == EI_OK) {
        PASS();
    } else {
        FAIL("max pool batch returned error");
    }
    
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

void run_pooling_tests(void) {
    printf("\n=== Pooling Tests ===\n");
    test_max_pool();
    test_avg_pool();
    test_max_pool_batch();
}
