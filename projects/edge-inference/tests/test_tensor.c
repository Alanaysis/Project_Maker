/**
 * test_tensor.c - Unit tests for tensor operations
 * 
 * Tests cover:
 * - Tensor creation and initialization
 * - Memory allocation
 * - Copy operations
 * - Data access
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

/* Test 1: Tensor creation */
static void test_create(void) {
    TEST("tensor_create");
    ei_tensor_t *t = ei_tensor_create();
    if (t && t->ndims == 0 && t->size == 0 && t->data == NULL) {
        PASS();
        ei_tensor_free(t);
        free(t);
    } else {
        FAIL("invalid state after create");
        if (t) { free(t); }
    }
}

/* Test 2: Tensor initialization */
static void test_init(void) {
    TEST("tensor_init");
    ei_tensor_t t;
    int32_t shape[4] = {2, 3, 4, 5};
    int ret = ei_tensor_init(&t, shape, 4, EI_TENSOR_FP32);
    
    if (ret == EI_OK && t.ndims == 4 && t.size == 120 && t.type == EI_TENSOR_FP32) {
        PASS();
    } else {
        FAIL("init failed or invalid shape/size");
    }
}

/* Test 3: Tensor allocation */
static void test_alloc(void) {
    TEST("tensor_alloc");
    ei_tensor_t t;
    int32_t shape[4] = {2, 3, 4, 5};
    int ret = ei_tensor_alloc(&t, shape, 4, EI_TENSOR_FP32);
    
    if (ret == EI_OK && t.data != NULL && t.owns_data == true) {
        PASS();
        ei_tensor_free(&t);
    } else {
        FAIL("alloc failed or invalid state");
    }
}

/* Test 4: Tensor fill */
static void test_fill(void) {
    TEST("tensor_fill");
    ei_tensor_t t;
    int32_t shape[4] = {1, 1, 2, 3};
    ei_tensor_alloc(&t, shape, 4, EI_TENSOR_FP32);
    
    ei_tensor_fill(&t, 3.14f);
    
    float *data = (float *)t.data;
    int ok = 1;
    for (int i = 0; i < t.size; i++) {
        if (!FLOAT_EQ(data[i], 3.14f, 1e-6)) { ok = 0; break; }
    }
    
    if (ok) PASS();
    else FAIL("fill values incorrect");
    ei_tensor_free(&t);
}

/* Test 5: Tensor copy from float */
static void test_copy_from_float(void) {
    TEST("copy_from_float");
    ei_tensor_t t;
    int32_t shape[4] = {1, 1, 2, 3};
    ei_tensor_alloc(&t, shape, 4, EI_TENSOR_FP32);
    
    float src[6] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f, 6.0f};
    ei_tensor_copy_from_float(&t, src, 6);
    
    float *data = (float *)t.data;
    int ok = 1;
    for (int i = 0; i < 6; i++) {
        if (!FLOAT_EQ(data[i], src[i], 1e-6)) { ok = 0; break; }
    }
    
    if (ok) PASS();
    else FAIL("copy values incorrect");
    ei_tensor_free(&t);
}

/* Test 6: Tensor copy to float */
static void test_copy_to_float(void) {
    TEST("copy_to_float");
    ei_tensor_t t;
    int32_t shape[4] = {1, 1, 2, 3};
    ei_tensor_alloc(&t, shape, 4, EI_TENSOR_FP32);
    
    float src[6] = {10.0f, 20.0f, 30.0f, 40.0f, 50.0f, 60.0f};
    ei_tensor_copy_from_float(&t, src, 6);
    
    float dst[6];
    ei_tensor_copy_to_float(&t, dst, 6);
    
    int ok = 1;
    for (int i = 0; i < 6; i++) {
        if (!FLOAT_EQ(dst[i], src[i], 1e-6)) { ok = 0; break; }
    }
    
    if (ok) PASS();
    else FAIL("copy values mismatch");
    ei_tensor_free(&t);
}

/* Test 7: Tensor element size */
static void test_elem_size(void) {
    TEST("tensor_elem_size");
    if (ei_tensor_elem_size(EI_TENSOR_FP32) == sizeof(float) &&
        ei_tensor_elem_size(EI_TENSOR_INT8) == sizeof(int8_t) &&
        ei_tensor_elem_size(EI_TENSOR_INT32) == sizeof(int32_t) &&
        ei_tensor_elem_size(EI_TENSOR_UINT8) == sizeof(uint8_t)) {
        PASS();
    } else {
        FAIL("element sizes incorrect");
    }
}

/* Test 8: Tensor data size */
static void test_data_size(void) {
    TEST("tensor_data_size");
    ei_tensor_t t;
    int32_t shape[4] = {2, 3, 4, 5};
    ei_tensor_init(&t, shape, 4, EI_TENSOR_FP32);
    
    size_t expected = 120 * sizeof(float);
    if (ei_tensor_data_size(&t) == expected) {
        PASS();
    } else {
        FAIL("data size incorrect");
    }
}

void run_tensor_tests(void) {
    printf("\n=== Tensor Tests ===\n");
    test_create();
    test_init();
    test_alloc();
    test_fill();
    test_copy_from_float();
    test_copy_to_float();
    test_elem_size();
    test_data_size();
}
