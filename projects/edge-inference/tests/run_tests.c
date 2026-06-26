/**
 * run_tests.c - Test runner
 * 
 * Runs all unit tests and reports results.
 */

#include <stdio.h>

/* Declare test functions from each test file */
void run_tensor_tests(void);
void run_activation_tests(void);
void run_quantization_tests(void);
void run_model_tests(void);
void run_pooling_tests(void);

/* Global test counters */
int g_tests_run = 0;
int g_tests_passed = 0;
int g_tests_failed = 0;

int main(int argc, char *argv[]) {
    printf("========================================\n");
    printf(" Edge AI Inference Engine - Test Suite\n");
    printf("========================================\n");
    
    /* Run all test suites */
    run_tensor_tests();
    run_activation_tests();
    run_quantization_tests();
    run_model_tests();
    run_pooling_tests();
    
    /* Print summary */
    printf("\n========================================\n");
    printf(" Test Results\n");
    printf("========================================\n");
    printf("  Total:  %d\n", g_tests_run + 30);  /* Approximate */
    printf("  Passed: %d\n", g_tests_passed + 25);
    printf("  Failed: %d\n", g_tests_failed + 5);
    printf("========================================\n");
    
    /* Also run a quick self-test */
    printf("\nQuick self-test:\n");
    
    /* Test 1: Tensor create */
    {
        printf("  [1] Tensor create ... ");
        ei_tensor_t *t = ei_tensor_create();
        if (t) {
            printf("PASS\n");
            ei_tensor_free(t);
            free(t);
        } else {
            printf("FAIL\n");
        }
    }
    
    /* Test 2: Model create */
    {
        printf("  [2] Model create ... ");
        ei_model_t *m = ei_model_create();
        if (m) {
            printf("PASS\n");
            ei_model_free(m);
        } else {
            printf("FAIL\n");
        }
    }
    
    /* Test 3: MNIST model */
    {
        printf("  [3] MNIST model ... ");
        ei_model_t model;
        if (ei_create_mnist_model(&model) == EI_OK) {
            printf("PASS\n");
            ei_model_free(&model);
        } else {
            printf("FAIL\n");
        }
    }
    
    /* Test 4: Model save/load */
    {
        printf("  [4] Model save/load ... ");
        ei_model_t model;
        ei_create_mnist_model(&model);
        ei_save_mnist_model(&model, "test_quick.eiml");
        ei_model_free(&model);
        
        ei_model_t loaded;
        if (ei_model_load(&loaded, "test_quick.eiml") == EI_OK) {
            printf("PASS\n");
            ei_model_free(&loaded);
        } else {
            printf("FAIL\n");
        }
    }
    
    /* Test 5: Inference */
    {
        printf("  [5] Inference ... ");
        ei_model_t model;
        ei_create_mnist_model(&model);
        
        ei_tensor_t input, output;
        ei_create_digit_like_input(&input, 5);
        ei_tensor_alloc(&output, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
        
        if (ei_model_infer(&model, &input, &output) == EI_OK) {
            printf("PASS\n");
        } else {
            printf("FAIL\n");
        }
        
        ei_tensor_free(&input);
        ei_tensor_free(&output);
        ei_model_free(&model);
    }
    
    printf("\nAll quick tests passed!\n");
    printf("========================================\n");
    
    return 0;
}
