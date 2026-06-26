/**
 * example_benchmark.c - Performance Benchmarking
 * 
 * This example demonstrates:
 * 1. Benchmarking individual layer inference speed
 * 2. Benchmarking full model inference
 * 3. Comparing FP32 vs INT8 inference speed
 * 4. Analyzing throughput (inferences per second)
 * 
 * Key concepts:
 * - Edge AI inference speed depends on layer types
 * - INT8 inference is typically 2-4x faster than FP32 on embedded CPUs
 * - Memory bandwidth is often the bottleneck for large models
 * - Cache efficiency matters more than raw compute on edge devices
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "edge_inference.h"
#include "model_builder.h"

/* Print a human-readable time value */
static void print_time(int64_t us, const char *label) {
    printf("    %-30s %8.1f us  (%.2f ms)\n", label, (double)us, (double)us / 1000.0);
}

/* Print throughput */
static void print_throughput(int64_t us, const char *label) {
    double fps = 1000000.0 / (double)us;
    printf("    %-30s %8.1f fps\n", label, fps);
}

int main(int argc, char *argv[]) {
    printf("=== Edge AI Inference Engine - Performance Benchmarking ===\n\n");
    
    int iterations = 100;
    if (argc > 1) {
        iterations = atoi(argv[1]);
        if (iterations <= 0) iterations = 100;
    }
    printf("[1] Benchmarking with %d iterations per test\n\n", iterations);
    
    /* ========================================================================
     * Test 1: FP32 Model Benchmark
     * ======================================================================== */
    printf("[2] FP32 Model Benchmark:\n");
    
    ei_model_t *model_fp32 = ei_model_create();
    ei_create_mnist_model(model_fp32);
    
    ei_tensor_t input, output;
    ei_create_digit_like_input(&input, 5);
    ei_tensor_alloc(&output, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    /* Benchmark full model */
    int64_t fp32_time = ei_benchmark_model(model_fp32, &input, iterations);
    print_time(fp32_time, "Total inference time");
    print_throughput(fp32_time, "Throughput");
    
    /* Benchmark individual layers */
    printf("\n    Individual layer benchmarks:\n");
    
    for (int i = 0; i < model_fp32->layer_count; i++) {
        ei_layer_t *layer = &model_fp32->layers[i];
        
        /* Skip layers without weights for benchmarking */
        if (!layer->weights && layer->type != EI_LAYER_RELU &&
            layer->type != EI_LAYER_SIGMOID && layer->type != EI_LAYER_TANH &&
            layer->type != EI_LAYER_SOFTMAX) {
            continue;
        }
        
        /* Create appropriate input for this layer */
        ei_tensor_t layer_input, layer_output;
        
        switch (layer->type) {
            case EI_LAYER_CONV2D: {
                int32_t in_shape[4] = {1, 1, 28, 28};
                ei_tensor_alloc(&layer_input, in_shape, 4, EI_TENSOR_FP32);
                int32_t out_shape[4] = {1, 16, 24, 24};
                ei_tensor_alloc(&layer_output, out_shape, 4, EI_TENSOR_FP32);
                break;
            }
            case EI_LAYER_FULLY_CONNECTED: {
                int32_t in_shape[4] = {1, 1, 1, 512};
                ei_tensor_alloc(&layer_input, in_shape, 4, EI_TENSOR_FP32);
                int32_t out_shape[4] = {1, 1, 1, layer->params.fc.out_features};
                ei_tensor_alloc(&layer_output, out_shape, 4, EI_TENSOR_FP32);
                break;
            }
            default: {
                int32_t in_shape[4] = {1, 1, 10, 10};
                ei_tensor_alloc(&layer_input, in_shape, 4, EI_TENSOR_FP32);
                int32_t out_shape[4] = {1, 1, 10, 10};
                ei_tensor_alloc(&layer_output, out_shape, 4, EI_TENSOR_FP32);
                break;
            }
        }
        
        /* Fill input with random data */
        float *in_data = (float *)layer_input.data;
        for (int j = 0; j < layer_input.size; j++) {
            in_data[j] = (float)(rand() % 1000) / 1000.0f;
        }
        
        int64_t layer_time = ei_benchmark_layer(&layer_input, &layer_output, layer, iterations);
        printf("      %-15s %8.1f us\n", layer->name, (double)layer_time);
        
        ei_tensor_free(&layer_input);
        ei_tensor_free(&layer_output);
    }
    
    /* ========================================================================
     * Test 2: INT8 Model Benchmark
     * ======================================================================== */
    printf("\n[3] INT8 Model Benchmark (per-channel):\n");
    
    /* Quantize model */
    ei_model_quantize(model_fp32, EI_QUANT_PER_CHANNEL);
    
    int64_t int8_time = ei_benchmark_model(model_fp32, &input, iterations);
    print_time(int8_time, "Total inference time");
    print_throughput(int8_time, "Throughput");
    
    /* Speedup calculation */
    double speedup = (double)fp32_time / (double)int8_time;
    printf("\n    Speedup: %.2fx\n", speedup);
    
    /* ========================================================================
     * Test 3: Batch Inference Benchmark
     * ======================================================================== */
    printf("\n[4] Batch Inference Benchmark:\n");
    
    /* Restore FP32 model for batch test */
    ei_model_free(model_fp32);
    model_fp32 = ei_model_create();
    ei_create_mnist_model(model_fp32);
    
    int batch_sizes[] = {1, 4, 8, 16};
    for (int bi = 0; bi < 4; bi++) {
        int bs = batch_sizes[bi];
        
        ei_tensor_t batch_input, batch_output;
        int32_t in_shape[4] = {bs, 1, 28, 28};
        ei_tensor_alloc(&batch_input, in_shape, 4, EI_TENSOR_FP32);
        int32_t out_shape[4] = {bs, 1, 1, 10};
        ei_tensor_alloc(&batch_output, out_shape, 4, EI_TENSOR_FP32);
        
        /* Fill batch input */
        float *in_data = (float *)batch_input.data;
        for (int j = 0; j < batch_input.size; j++) {
            in_data[j] = (float)(rand() % 1000) / 1000.0f;
        }
        
        int64_t batch_time = ei_benchmark_model(model_fp32, &batch_input, iterations);
        
        printf("    Batch size %2d: %8.1f us/sample  (%8.1f fps)\n",
               bs, (double)batch_time / bs, 1000000.0 / ((double)batch_time / bs));
        
        ei_tensor_free(&batch_input);
        ei_tensor_free(&batch_output);
    }
    
    /* ========================================================================
     * Summary
     * ======================================================================== */
    printf("\n[5] Summary:\n");
    printf("    +------------------+-----------+-----------+---------+\n");
    printf("    | Configuration    | Latency   | Throughput| Speedup |\n");
    printf("    +------------------+-----------+-----------+---------+\n");
    printf("    | FP32 (1 sample)  | %8.1f us | %8.1f fps|    1.00x|\n",
           (double)fp32_time, 1000000.0 / (double)fp32_time);
    printf("    | INT8 (1 sample)  | %8.1f us | %8.1f fps|   %5.2fx|\n",
           (double)int8_time, 1000000.0 / (double)int8_time, speedup);
    printf("    +------------------+-----------+-----------+---------+\n");
    
    printf("\n    Key insights:\n");
    printf("    - INT8 quantization provides %5.2fx speedup\n", speedup);
    printf("    - Batch inference improves throughput\n");
    printf("    - Convolution layers are the compute bottleneck\n");
    printf("    - FC layers dominate memory bandwidth usage\n");
    printf("    - On ARM NEON: INT8 can be 3-4x faster than FP32\n");
    printf("    - On RISC-V: INT8 can be 5-10x faster than FP32\n");
    
    /* Cleanup */
    ei_tensor_free(&input);
    ei_tensor_free(&output);
    ei_model_free(model_fp32);
    
    printf("\n=== Benchmark complete ===\n");
    return 0;
}
