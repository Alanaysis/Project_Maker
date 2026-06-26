/**
 * example_quantization.c - Quantization Accuracy Comparison
 * 
 * This example demonstrates:
 * 1. FP32 model inference (ground truth)
 * 2. Per-tensor INT8 quantization and inference
 * 3. Per-channel INT8 quantization and inference
 * 4. Accuracy comparison between quantization methods
 * 
 * Key concepts:
 * - Quantization reduces model size by 4x (float32 -> int8)
 * - Per-channel quantization is more accurate than per-tensor
 * - INT8 inference is faster on most CPUs (integer ops > float ops)
 * 
 * Quantization formula:
 *   q = round(x / scale) + zero_point
 * 
 * Dequantization formula:
 *   x = (q - zero_point) * scale
 * 
 * The "scale" determines how much we compress the data range.
 * The "zero_point" handles asymmetric ranges (e.g., [-1, 2] -> [0, 255]).
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "edge_inference.h"
#include "model_builder.h"

/* Print top-5 predicted classes */
static void print_top_k(float *probs, int num_classes, int k) {
    /* Simple selection sort for top-k */
    int indices[10];
    for (int i = 0; i < num_classes; i++) indices[i] = i;
    
    for (int i = 0; i < k - 1; i++) {
        for (int j = i + 1; j < num_classes; j++) {
            if (probs[indices[j]] > probs[indices[i]]) {
                int temp = indices[i];
                indices[i] = indices[j];
                indices[j] = temp;
            }
        }
    }
    
    printf("    Top-%d predictions:\n", k);
    for (int i = 0; i < k; i++) {
        printf("      Digit %d: %.4f", indices[i], probs[indices[i]]);
        int bar = (int)(probs[indices[i]] * 30);
        for (int j = 0; j < bar; j++) printf("#");
        printf("\n");
    }
}

/* Compare two probability distributions */
static float compute_accuracy(float *probs_fp32, float *probs_int8, int num_classes) {
    /* Find predicted class for each distribution */
    int pred_fp32 = 0, pred_int8 = 0;
    for (int i = 1; i < num_classes; i++) {
        if (probs_fp32[i] > probs_fp32[pred_fp32]) pred_fp32 = i;
        if (probs_int8[i] > probs_int8[pred_int8]) pred_int8 = i;
    }
    
    return (pred_fp32 == pred_int8) ? 1.0f : 0.0f;
}

/* Compute KL divergence between two distributions */
static float compute_kl_divergence(float *p, float *q, int n) {
    float kl = 0.0f;
    for (int i = 0; i < n; i++) {
        /* Avoid log(0) */
        float pi = fmaxf(p[i], 1e-10f);
        float qi = fmaxf(q[i], 1e-10f);
        kl += pi * logf(pi / qi);
    }
    return kl;
}

int main(int argc, char *argv[]) {
    printf("=== Edge AI Inference Engine - Quantization Accuracy Comparison ===\n\n");
    
    /* Create model */
    printf("[1] Creating MNIST model...\n");
    ei_model_t *model = ei_model_create();
    ei_create_mnist_model(model);
    
    /* Create test input */
    printf("[2] Creating test inputs...\n");
    ei_tensor_t input, output_fp32, output_int8;
    ei_create_digit_like_input(&input, 7);
    ei_tensor_alloc(&output_fp32, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    ei_tensor_alloc(&output_int8, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    /* ========================================================================
     * Test 1: FP32 inference (ground truth)
     * ======================================================================== */
    printf("\n[3] FP32 inference (ground truth):\n");
    ei_model_infer(model, &input, &output_fp32);
    float *probs_fp32 = (float *)output_fp32.data;
    print_top_k(probs_fp32, 10, 5);
    
    /* ========================================================================
     * Test 2: Per-tensor INT8 quantization
     * 
     * Per-tensor uses a SINGLE scale factor for the entire tensor.
     * Simplest approach but less accurate for layers with wide dynamic range.
     * ======================================================================== */
    printf("\n[4] Quantizing model (per-tensor INT8)...\n");
    ei_model_quantize(model, EI_QUANT_PER_TENSOR);
    printf("    Model scale: %.6f\n", model->model_scale);
    printf("    Model zero point: %d\n", model->model_zero_point);
    
    /* Count quantized layers */
    int quantized_layers = 0;
    for (int i = 0; i < model->layer_count; i++) {
        if (model->layers[i].weights_quantized) quantized_layers++;
    }
    printf("    Quantized layers: %d/%d\n", quantized_layers, model->layer_count);
    
    printf("\n[5] INT8 inference (per-tensor):\n");
    ei_model_infer(model, &input, &output_int8);
    float *probs_int8_pt = (float *)output_int8.data;
    print_top_k(probs_int8_pt, 10, 5);
    
    float accuracy_pt = compute_accuracy(probs_fp32, probs_int8_pt, 10);
    float kl_pt = compute_kl_divergence(probs_fp32, probs_int8_pt, 10);
    printf("    Accuracy match: %.0f%%\n", accuracy_pt * 100.0);
    printf("    KL divergence: %.6f\n", kl_pt);
    
    /* ========================================================================
     * Test 3: Per-channel INT8 quantization
     * 
     * Per-channel uses DIFFERENT scale factors for each output channel.
     * More accurate than per-tensor, especially for layers with varying
     * activation ranges across channels.
     * 
     * Trade-off: More metadata (scales) to store, but better accuracy.
     * ======================================================================== */
    printf("\n[6] Quantizing model (per-channel INT8)...\n");
    
    /* First, restore FP32 weights */
    ei_model_free(model);
    model = ei_model_create();
    ei_create_mnist_model(model);
    
    ei_model_quantize(model, EI_QUANT_PER_CHANNEL);
    
    /* Count quantized layers */
    quantized_layers = 0;
    for (int i = 0; i < model->layer_count; i++) {
        if (model->layers[i].weights_quantized) quantized_layers++;
    }
    printf("    Quantized layers: %d/%d\n", quantized_layers, model->layer_count);
    
    printf("\n[7] INT8 inference (per-channel):\n");
    ei_model_infer(model, &input, &output_int8);
    float *probs_int8_pc = (float *)output_int8.data;
    print_top_k(probs_int8_pc, 10, 5);
    
    float accuracy_pc = compute_accuracy(probs_fp32, probs_int8_pc, 10);
    float kl_pc = compute_kl_divergence(probs_fp32, probs_int8_pc, 10);
    printf("    Accuracy match: %.0f%%\n", accuracy_pc * 100.0);
    printf("    KL divergence: %.6f\n", kl_pc);
    
    /* ========================================================================
     * Summary
     * ======================================================================== */
    printf("\n[8] Summary:\n");
    printf("    +------------------+----------------+----------------+\n");
    printf("    | Method           | Accuracy       | KL Divergence  |\n");
    printf("    +------------------+----------------+----------------+\n");
    printf("    | FP32 (baseline)  | N/A            | 0.000000       |\n");
    printf("    | Per-tensor INT8  | %.0f%%        | %.6f         |\n",
           accuracy_pt * 100.0, kl_pt);
    printf("    | Per-channel INT8 | %.0f%%        | %.6f         |\n",
           accuracy_pc * 100.0, kl_pc);
    printf("    +------------------+----------------+----------------+\n");
    
    printf("\n    Key insights:\n");
    printf("    - Per-channel is typically more accurate (lower KL divergence)\n");
    printf("    - Both methods achieve 4x memory reduction (INT8 vs FP32)\n");
    printf("    - Per-channel stores more metadata (scales per channel)\n");
    printf("    - Choose per-channel for accuracy-critical apps\n");
    printf("    - Choose per-tensor for simplicity and smaller metadata\n");
    
    /* Cleanup */
    ei_tensor_free(&input);
    ei_tensor_free(&output_fp32);
    ei_tensor_free(&output_int8);
    ei_model_free(model);
    
    printf("\n=== Demo complete ===\n");
    return 0;
}
