/**
 * test_activation.c - Unit tests for activation functions
 * 
 * Tests cover:
 * - ReLU (max(0, x))
 * - Sigmoid (1 / (1 + exp(-x)))
 * - Tanh (hyperbolic tangent)
 * - Softmax (exp(x_i) / sum(exp(x_j)))
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

/* Test ReLU */
static void test_relu(void) {
    TEST("relu");
    ei_tensor_t input, output;
    int32_t shape[4] = {1, 1, 1, 6};
    ei_tensor_alloc(&input, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, shape, 4, EI_TENSOR_FP32);
    
    float data[6] = {-2.0f, -1.0f, 0.0f, 1.0f, 2.0f, 3.0f};
    ei_tensor_copy_from_float(&input, data, 6);
    
    ei_run_relu(&input, &output);
    
    float *out = (float *)output.data;
    float expected[6] = {0.0f, 0.0f, 0.0f, 1.0f, 2.0f, 3.0f};
    
    int ok = 1;
    for (int i = 0; i < 6; i++) {
        if (!FLOAT_EQ(out[i], expected[i], 1e-5)) { ok = 0; break; }
    }
    
    if (ok) PASS();
    else FAIL("relu output incorrect");
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

/* Test Sigmoid */
static void test_sigmoid(void) {
    TEST("sigmoid");
    ei_tensor_t input, output;
    int32_t shape[4] = {1, 1, 1, 5};
    ei_tensor_alloc(&input, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, shape, 4, EI_TENSOR_FP32);
    
    float data[5] = {-5.0f, 0.0f, 1.0f, 5.0f, 10.0f};
    ei_tensor_copy_from_float(&input, data, 5);
    
    ei_run_sigmoid(&input, &output);
    
    float *out = (float *)output.data;
    
    /* Check key properties: sigmoid(0) = 0.5, sigmoid(inf) ~ 1, sigmoid(-inf) ~ 0 */
    int ok = 1;
    if (!FLOAT_EQ(out[1], 0.5f, 1e-3)) ok = 0;       /* sigmoid(0) = 0.5 */
    if (out[0] > 0.01f) ok = 0;                         /* sigmoid(-5) ~ 0 */
    if (out[3] < 0.99f) ok = 0;                         /* sigmoid(5) ~ 1 */
    if (out[4] < 0.999f) ok = 0;                        /* sigmoid(10) ~ 1 */
    if (out[2] < 0.7f || out[2] > 0.75f) ok = 0;      /* sigmoid(1) ~ 0.731 */
    
    if (ok) PASS();
    else FAIL("sigmoid output incorrect");
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

/* Test Tanh */
static void test_tanh(void) {
    TEST("tanh");
    ei_tensor_t input, output;
    int32_t shape[4] = {1, 1, 1, 4};
    ei_tensor_alloc(&input, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, shape, 4, EI_TENSOR_FP32);
    
    float data[4] = {-3.0f, -1.0f, 0.0f, 3.0f};
    ei_tensor_copy_from_float(&input, data, 4);
    
    ei_run_tanh(&input, &output);
    
    float *out = (float *)output.data;
    
    int ok = 1;
    if (!FLOAT_EQ(out[2], 0.0f, 1e-5)) ok = 0;         /* tanh(0) = 0 */
    if (out[0] < -0.99f) ok = 0;                        /* tanh(-3) ~ -1 */
    if (out[3] > 0.99f) ok = 0;                         /* tanh(3) ~ 1 */
    if (!FLOAT_EQ(out[1], -0.7616f, 1e-3)) ok = 0;     /* tanh(-1) ~ -0.7616 */
    
    if (ok) PASS();
    else FAIL("tanh output incorrect");
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

/* Test Softmax */
static void test_softmax(void) {
    TEST("softmax");
    ei_tensor_t input, output;
    int32_t shape[4] = {1, 1, 1, 5};
    ei_tensor_alloc(&input, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, shape, 4, EI_TENSOR_FP32);
    
    float data[5] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    ei_tensor_copy_from_float(&input, data, 5);
    
    ei_run_softmax(&input, &output);
    
    float *out = (float *)output.data;
    
    /* Key properties: all positive, sums to 1, largest input -> largest output */
    float sum = 0.0f;
    int ok = 1;
    for (int i = 0; i < 5; i++) {
        if (out[i] <= 0.0f) { ok = 0; break; }
        sum += out[i];
    }
    if (!FLOAT_EQ(sum, 1.0f, 1e-4)) ok = 0;             /* sums to 1 */
    if (out[4] < out[3] || out[3] < out[2]) ok = 0;     /* preserves order */
    
    if (ok) PASS();
    else FAIL("softmax output incorrect");
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

/* Test Softmax numerical stability (large values) */
static void test_softmax_stability(void) {
    TEST("softmax_numerical_stability");
    ei_tensor_t input, output;
    int32_t shape[4] = {1, 1, 1, 3};
    ei_tensor_alloc(&input, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output, shape, 4, EI_TENSOR_FP32);
    
    float data[3] = {1000.0f, 1001.0f, 999.0f};
    ei_tensor_copy_from_float(&input, data, 3);
    
    ei_run_softmax(&input, &output);
    
    float *out = (float *)output.data;
    
    int ok = 1;
    float sum = 0.0f;
    for (int i = 0; i < 3; i++) {
        if (out[i] != out[i]) { ok = 0; break; }  /* NaN check */
        if (out[i] < 0.0f || out[i] > 1.0f) { ok = 0; break; }
        sum += out[i];
    }
    if (!FLOAT_EQ(sum, 1.0f, 1e-4)) ok = 0;
    
    if (ok) PASS();
    else FAIL("softmax overflow or NaN");
    ei_tensor_free(&input);
    ei_tensor_free(&output);
}

void run_activation_tests(void) {
    printf("\n=== Activation Function Tests ===\n");
    test_relu();
    test_sigmoid();
    test_tanh();
    test_softmax();
    test_softmax_stability();
}
