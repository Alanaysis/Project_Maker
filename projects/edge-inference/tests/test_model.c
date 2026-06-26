/**
 * test_model.c - Unit tests for model operations
 * 
 * Tests cover:
 * - Model creation and initialization
 * - Model saving and loading
 * - Model inference
 * - Model quantization
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "edge_inference.h"
#include "model_builder.h"

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  Test: %s ... ", name); tests_run++
#define PASS() printf("PASS\n"); tests_passed++
#define FAIL(msg) printf("FAIL: %s\n", msg); tests_failed++

#define FLOAT_EQ(a, b, tol) (fabsf((a) - (b)) < (tol))

/* Test model creation */
static void test_model_create(void) {
    TEST("model_create");
    ei_model_t *model = ei_model_create();
    
    if (model && model->layer_count == 0 && model->input_count == 0) {
        PASS();
        ei_model_free(model);
    } else {
        FAIL("model create failed");
        if (model) ei_model_free(model);
    }
}

/* Test MNIST model creation */
static void test_mnist_model_create(void) {
    TEST("mnist_model_create");
    ei_model_t model;
    int ret = ei_create_mnist_model(&model);
    
    if (ret == EI_OK && model.layer_count == 11 &&
        model.input_count == 1 && model.output_count == 1) {
        PASS();
        ei_model_free(&model);
    } else {
        FAIL("mnist model create failed or wrong structure");
        if (ret == EI_OK) ei_model_free(&model);
    }
}

/* Test model saving */
static void test_model_save(void) {
    TEST("model_save");
    ei_model_t model;
    ei_create_mnist_model(&model);
    
    const char *path = "test_model.eiml";
    int ret = ei_save_mnist_model(&model, path);
    
    if (ret == EI_OK) {
        /* Check file exists and has content */
        FILE *fp = fopen(path, "rb");
        if (fp) {
            fseek(fp, 0, SEEK_END);
            long size = ftell(fp);
            fclose(fp);
            
            if (size > 1000) {  /* Should be at least 1KB */
                PASS();
            } else {
                FAIL("model file too small");
            }
        } else {
            FAIL("cannot open saved model file");
        }
        ei_model_free(&model);
    } else {
        FAIL("model save returned error");
    }
}

/* Test model loading */
static void test_model_load(void) {
    TEST("model_load");
    
    /* First create and save a model */
    ei_model_t model;
    ei_create_mnist_model(&model);
    ei_save_mnist_model(&model, "test_model.eiml");
    ei_model_free(&model);
    
    /* Load it back */
    ei_model_t loaded;
    int ret = ei_model_load(&loaded, "test_model.eiml");
    
    if (ret == EI_OK && loaded.layer_count == 11 &&
        loaded.input_count == 1) {
        PASS();
        ei_model_free(&loaded);
    } else {
        FAIL("model load failed or wrong structure");
        if (ret == EI_OK) ei_model_free(&loaded);
    }
}

/* Test model inference */
static void test_model_inference(void) {
    TEST("model_inference");
    
    ei_model_t model;
    ei_create_mnist_model(&model);
    
    ei_tensor_t input, output;
    ei_create_digit_like_input(&input, 5);
    ei_tensor_alloc(&output, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    int ret = ei_model_infer(&model, &input, &output);
    
    if (ret == EI_OK) {
        /* Check output is valid softmax */
        float *probs = (float *)output.data;
        float sum = 0.0f;
        int valid = 1;
        
        for (int i = 0; i < 10; i++) {
            if (probs[i] < 0.0f || probs[i] > 1.0f) { valid = 0; break; }
            sum += probs[i];
        }
        
        if (valid && FLOAT_EQ(sum, 1.0f, 1e-3)) {
            PASS();
        } else {
            FAIL("output not valid probability distribution");
        }
    } else {
        FAIL("inference returned error");
    }
    
    ei_tensor_free(&input);
    ei_tensor_free(&output);
    ei_model_free(&model);
}

/* Test model quantization */
static void test_model_quantization(void) {
    TEST("model_quantization");
    
    ei_model_t model;
    ei_create_mnist_model(&model);
    
    int ret = ei_model_quantize(&model, EI_QUANT_PER_CHANNEL);
    
    if (ret == EI_OK) {
        /* Check that weights were quantized */
        int quantized_count = 0;
        for (int i = 0; i < model.layer_count; i++) {
            if (model.layers[i].weights_quantized) quantized_count++;
        }
        
        if (quantized_count > 0) {
            PASS();
        } else {
            FAIL("no layers were quantized");
        }
        ei_model_free(&model);
    } else {
        FAIL("quantize returned error");
    }
}

/* Test model inference after quantization */
static void test_quantized_inference(void) {
    TEST("quantized_inference");
    
    ei_model_t model;
    ei_create_mnist_model(&model);
    
    /* Quantize */
    ei_model_quantize(&model, EI_QUANT_PER_CHANNEL);
    
    /* Run inference */
    ei_tensor_t input, output;
    ei_create_digit_like_input(&input, 3);
    ei_tensor_alloc(&output, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    int ret = ei_model_infer(&model, &input, &output);
    
    if (ret == EI_OK) {
        /* Check output is valid */
        float *probs = (float *)output.data;
        float sum = 0.0f;
        int valid = 1;
        
        for (int i = 0; i < 10; i++) {
            if (probs[i] != probs[i]) { valid = 0; break; }  /* NaN check */
            sum += probs[i];
        }
        
        if (valid && FLOAT_EQ(sum, 1.0f, 1e-2)) {
            PASS();
        } else {
            FAIL("quantized output invalid");
        }
    } else {
        FAIL("quantized inference returned error");
    }
    
    ei_tensor_free(&input);
    ei_tensor_free(&output);
    ei_model_free(&model);
}

/* Test batch inference */
static void test_batch_inference(void) {
    TEST("batch_inference");
    
    ei_model_t model;
    ei_create_mnist_model(&model);
    
    int batch_size = 4;
    int32_t in_shape[4] = {batch_size, 1, 28, 28};
    int32_t out_shape[4] = {batch_size, 1, 1, 10};
    
    ei_tensor_t inputs, outputs;
    ei_tensor_alloc(&inputs, in_shape, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&outputs, out_shape, 4, EI_TENSOR_FP32);
    
    /* Fill inputs with data */
    float *in_data = (float *)inputs.data;
    for (int i = 0; i < inputs.size; i++) {
        in_data[i] = (float)(rand() % 1000) / 1000.0f;
    }
    
    int ret = ei_model_batch_infer(&model, &inputs, batch_size, &outputs);
    
    if (ret == EI_OK) {
        /* Check each batch output */
        int valid = 1;
        for (int b = 0; b < batch_size; b++) {
            float *batch_probs = (float *)outputs.data + b * 10;
            float sum = 0.0f;
            for (int i = 0; i < 10; i++) {
                if (batch_probs[i] != batch_probs[i]) { valid = 0; break; }
                sum += batch_probs[i];
            }
            if (!FLOAT_EQ(sum, 1.0f, 1e-2)) { valid = 0; break; }
        }
        
        if (valid) PASS();
        else FAIL("batch output invalid");
    } else {
        FAIL("batch inference returned error");
    }
    
    ei_tensor_free(&inputs);
    ei_tensor_free(&outputs);
    ei_model_free(&model);
}

void run_model_tests(void) {
    printf("\n=== Model Tests ===\n");
    test_model_create();
    test_mnist_model_create();
    test_model_save();
    test_model_load();
    test_model_inference();
    test_model_quantization();
    test_quantized_inference();
    test_batch_inference();
}
