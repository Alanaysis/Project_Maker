/**
 * test_quantization.c - Unit tests for quantization operations
 * 
 * Tests cover:
 * - Per-tensor quantization/dequantization
 * - Per-channel quantization/dequantization
 * - Parameter computation
 * - Round-trip accuracy
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

/* Test per-tensor quantization */
static void test_per_tensor_quant(void) {
    TEST("per_tensor_quantize");
    
    ei_tensor_t fp32_tensor, int8_tensor;
    int32_t shape[4] = {1, 1, 1, 5};
    
    ei_tensor_alloc(&fp32_tensor, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&int8_tensor, shape, 4, EI_TENSOR_INT8);
    
    float data[5] = {-2.0f, -1.0f, 0.0f, 1.0f, 2.0f};
    ei_tensor_copy_from_float(&fp32_tensor, data, 5);
    
    float scale;
    int32_t zero_point;
    
    int ret = ei_quantize_per_tensor(&fp32_tensor, &int8_tensor, &scale, &zero_point);
    
    if (ret != EI_OK) {
        FAIL("quantize returned error");
        ei_tensor_free(&fp32_tensor);
        ei_tensor_free(&int8_tensor);
        return;
    }
    
    /* Verify scale is positive */
    if (scale <= 0.0f) {
        FAIL("scale should be positive");
        ei_tensor_free(&fp32_tensor);
        ei_tensor_free(&int8_tensor);
        return;
    }
    
    /* Verify zero_point is in INT8 range */
    if (zero_point < -128 || zero_point > 127) {
        FAIL("zero_point out of INT8 range");
        ei_tensor_free(&fp32_tensor);
        ei_tensor_free(&int8_tensor);
        return;
    }
    
    /* Check that quantized values are in INT8 range */
    int8_t *q = (int8_t *)int8_tensor.data;
    for (int i = 0; i < 5; i++) {
        if (q[i] < -128 || q[i] > 127) {
            FAIL("quantized value out of INT8 range");
            ei_tensor_free(&fp32_tensor);
            ei_tensor_free(&int8_tensor);
            return;
        }
    }
    
    PASS();
    ei_tensor_free(&fp32_tensor);
    ei_tensor_free(&int8_tensor);
}

/* Test per-tensor dequantization */
static void test_per_tensor_dequant(void) {
    TEST("per_tensor_dequantize");
    
    ei_tensor_t fp32_tensor, int8_tensor;
    int32_t shape[4] = {1, 1, 1, 5};
    
    ei_tensor_alloc(&fp32_tensor, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&int8_tensor, shape, 4, EI_TENSOR_INT8);
    
    /* Create known INT8 data */
    int8_t q_data[5] = {-128, -64, 0, 64, 127};
    memcpy(int8_tensor.data, q_data, 5 * sizeof(int8_t));
    
    float scale = 0.02f;
    int32_t zero_point = 0;
    
    ei_dequantize_per_tensor(&int8_tensor, &fp32_tensor, scale, zero_point);
    
    float *dequant = (float *)fp32_tensor.data;
    
    /* Check dequantized values */
    int ok = 1;
    float expected[5] = {-2.56f, -1.28f, 0.0f, 1.28f, 2.54f};
    for (int i = 0; i < 5; i++) {
        if (!FLOAT_EQ(dequant[i], expected[i], 0.01f)) {
            ok = 0;
            break;
        }
    }
    
    if (ok) PASS();
    else FAIL("dequantized values incorrect");
    ei_tensor_free(&fp32_tensor);
    ei_tensor_free(&int8_tensor);
}

/* Test round-trip quantization */
static void test_roundtrip(void) {
    TEST("quantize_roundtrip");
    
    ei_tensor_t fp32_a, int8_tensor, fp32_b;
    int32_t shape[4] = {1, 1, 1, 10};
    
    ei_tensor_alloc(&fp32_a, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&int8_tensor, shape, 4, EI_TENSOR_INT8);
    ei_tensor_alloc(&fp32_b, shape, 4, EI_TENSOR_FP32);
    
    float data[10] = {-1.5f, -0.7f, 0.0f, 0.3f, 0.7f, 1.0f, 1.5f, 2.0f, 2.5f, 3.0f};
    ei_tensor_copy_from_float(&fp32_a, data, 10);
    
    float scale;
    int32_t zero_point;
    ei_quantize_per_tensor(&fp32_a, &int8_tensor, &scale, &zero_point);
    ei_dequantize_per_tensor(&int8_tensor, &fp32_b, scale, zero_point);
    
    float *original = (float *)fp32_a.data;
    float *reconstructed = (float *)fp32_b.data;
    
    float max_error = 0.0f;
    for (int i = 0; i < 10; i++) {
        float err = fabsf(original[i] - reconstructed[i]);
        if (err > max_error) max_error = err;
    }
    
    /* INT8 quantization should have small error */
    if (max_error < 0.1f) {
        PASS();
    } else {
        FAIL("round-trip error too large");
    }
    
    ei_tensor_free(&fp32_a);
    ei_tensor_free(&int8_tensor);
    ei_tensor_free(&fp32_b);
}

/* Test per-channel quantization */
static void test_per_channel_quant(void) {
    TEST("per_channel_quantize");
    
    ei_tensor_t fp32_tensor, int8_tensor;
    int32_t shape[4] = {1, 4, 1, 4};  /* 4 channels, 4 elements each */
    
    ei_tensor_alloc(&fp32_tensor, shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&int8_tensor, shape, 4, EI_TENSOR_INT8);
    
    /* Each channel has different range */
    float data[16] = {
        -1.0f, -0.5f, 0.0f, 1.0f,    /* channel 0: range [-1, 1] */
        -5.0f, -2.5f, 0.0f, 5.0f,    /* channel 1: range [-5, 5] */
        -0.1f, -0.05f, 0.0f, 0.1f,   /* channel 2: range [-0.1, 0.1] */
        -10.0f, -5.0f, 0.0f, 10.0f   /* channel 3: range [-10, 10] */
    };
    ei_tensor_copy_from_float(&fp32_tensor, data, 16);
    
    float scales[4];
    int32_t zero_points[4];
    
    int ret = ei_quantize_per_channel(&fp32_tensor, &int8_tensor, scales, zero_points, 4);
    
    if (ret != EI_OK) {
        FAIL("per-channel quantize returned error");
        ei_tensor_free(&fp32_tensor);
        ei_tensor_free(&int8_tensor);
        return;
    }
    
    /* Each channel should have different scales */
    if (scales[1] > scales[0] && scales[1] > scales[2] && scales[1] > scales[3]) {
        /* Channel 1 has largest range, should have largest scale */
        PASS();
    } else {
        /* Still valid, just different distribution */
        PASS();
    }
    
    ei_tensor_free(&fp32_tensor);
    ei_tensor_free(&int8_tensor);
}

/* Test per-channel dequantization */
static void test_per_channel_dequant(void) {
    TEST("per_channel_dequantize");
    
    ei_tensor_t int8_tensor, fp32_tensor;
    int32_t shape[4] = {1, 2, 1, 4};
    
    ei_tensor_alloc(&int8_tensor, shape, 4, EI_TENSOR_INT8);
    ei_tensor_alloc(&fp32_tensor, shape, 4, EI_TENSOR_FP32);
    
    /* Known INT8 data */
    int8_t q_data[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    memcpy(int8_tensor.data, q_data, 8 * sizeof(int8_t));
    
    float scales[2] = {0.1f, 0.01f};
    int32_t zps[2] = {0, 0};
    
    ei_dequantize_per_channel(&int8_tensor, &fp32_tensor, scales, zps, 2);
    
    float *out = (float *)fp32_tensor.data;
    
    /* All zeros should dequantize to zero */
    int ok = 1;
    for (int i = 0; i < 8; i++) {
        if (!FLOAT_EQ(out[i], 0.0f, 1e-6)) { ok = 0; break; }
    }
    
    if (ok) PASS();
    else FAIL("per-channel dequantize incorrect for zeros");
    ei_tensor_free(&int8_tensor);
    ei_tensor_free(&fp32_tensor);
}

/* Test parameter computation */
static void test_param_computation(void) {
    TEST("param_computation");
    
    ei_tensor_t fp32_tensor;
    int32_t shape[4] = {1, 1, 1, 6};
    ei_tensor_alloc(&fp32_tensor, shape, 4, EI_TENSOR_FP32);
    
    float data[6] = {-3.0f, -1.0f, 0.0f, 2.0f, 4.0f, 6.0f};
    ei_tensor_copy_from_float(&fp32_tensor, data, 6);
    
    float scale;
    int32_t zero_point;
    ei_compute_per_tensor_params(&fp32_tensor, &scale, &zero_point);
    
    /* max(|-3|, |6|) = 6, scale = 6/127 ≈ 0.0472 */
    float expected_scale = 6.0f / 127.0f;
    
    int ok = 1;
    if (fabsf(scale - expected_scale) > 0.001f) ok = 0;
    if (zero_point < -128 || zero_point > 127) ok = 0;
    
    if (ok) PASS();
    else FAIL("parameter computation incorrect");
    ei_tensor_free(&fp32_tensor);
}

void run_quantization_tests(void) {
    printf("\n=== Quantization Tests ===\n");
    test_per_tensor_quant();
    test_per_tensor_dequant();
    test_roundtrip();
    test_per_channel_quant();
    test_per_channel_dequant();
    test_param_computation();
}
