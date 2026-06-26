/**
 * example_inference.c - Basic Inference Demo (MNIST Classifier)
 * 
 * This example demonstrates:
 * 1. Creating a model with random weights
 * 2. Running inference on sample inputs
 * 3. Interpreting the output probabilities
 * 
 * Key concepts demonstrated:
 * - Forward pass through a CNN
 * - Understanding layer-by-layer data flow
 * - Reading softmax output as class probabilities
 * 
 * Note: This model has RANDOM weights, so predictions will be random.
 * In practice, you would load a trained model from a file.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "edge_inference.h"
#include "model_builder.h"

/**
 * Print a 28x28 grayscale image as ASCII art.
 * This helps visualize what the model "sees" as input.
 */
static void print_image(const float *data, int height, int width) {
    printf("    Image (28x28 grayscale):\n");
    for (int y = 0; y < height; y++) {
        printf("    |");
        for (int x = 0; x < width; x++) {
            int idx = y * width + x;
            float val = data[idx];
            if (val < 0.1) printf(" ");
            else if (val < 0.3) printf(".");
            else if (val < 0.5) printf(":");
            else if (val < 0.7) printf("*");
            else if (val < 0.9) printf("@");
            else printf("#");
        }
        printf("|\n");
    }
    printf("\n");
}

/**
 * Print layer-by-layer activation visualization.
 * Shows how data flows through the network.
 */
static void print_layer_shapes(ei_model_t *model) {
    printf("    Forward pass shapes:\n");
    printf("      Input:     [%d, %d, %d, %d]\n",
           1, 1, 28, 28);
    
    /* Track shapes through each layer */
    int n = 1, c = 1, h = 28, w = 28;
    
    for (int i = 0; i < model->layer_count; i++) {
        ei_layer_t *layer = &model->layers[i];
        
        switch (layer->type) {
            case EI_LAYER_CONV2D: {
                int kh = layer->params.conv.kernel_h;
                int kw = layer->params.conv.kernel_w;
                int sh = layer->params.conv.stride_h;
                int sw = layer->params.conv.stride_w;
                int ph = layer->params.conv.pad_h;
                int pw = layer->params.conv.pad_w;
                
                int out_channels = layer->weights->dims[0];
                int in_channels = layer->weights->dims[1];
                
                h = (h + 2 * ph - kh) / sh + 1;
                w = (w + 2 * pw - kw) / sw + 1;
                c = out_channels;
                
                printf("      %-15s [%d, %d, %d, %d]\n",
                       layer->name, n, c, h, w);
                break;
            }
            case EI_LAYER_MAX_POOL: {
                int kh = layer->params.pooling.kernel_h;
                int kw = layer->params.pooling.kernel_w;
                int sh = layer->params.pooling.stride_h;
                int sw = layer->params.pooling.stride_w;
                
                h = (h + 2 * layer->params.pooling.pad_h - kh) / sh + 1;
                w = (w + 2 * layer->params.pooling.pad_w - kw) / sw + 1;
                
                printf("      %-15s [%d, %d, %d, %d]\n",
                       layer->name, n, c, h, w);
                break;
            }
            case EI_LAYER_FLATTEN: {
                printf("      %-15s [%d, %d, %d, %d] -> [%d]\n",
                       layer->name, n, c, h, w, c * h * w);
                break;
            }
            case EI_LAYER_FULLY_CONNECTED: {
                int out = layer->params.fc.out_features;
                printf("      %-15s [%d, %d, %d, %d]\n",
                       layer->name, n, 1, 1, out);
                break;
            }
            case EI_LAYER_RELU:
            case EI_LAYER_SIGMOID:
            case EI_LAYER_TANH:
            case EI_LAYER_SOFTMAX:
                printf("      %-15s [%d, %d, %d, %d]\n",
                       layer->name, n, c, h, w);
                break;
            default:
                printf("      %-15s [%d, %d, %d, %d]\n",
                       layer->name, n, c, h, w);
                break;
        }
    }
}

int main(int argc, char *argv[]) {
    printf("=== Edge AI Inference Engine - MNIST Inference Demo ===\n\n");
    
    /* Create model with random weights */
    printf("[1] Creating MNIST CNN model...\n");
    ei_model_t *model = ei_model_create();
    ei_create_mnist_model(model);
    
    /* Save model */
    const char *model_path = "mnist_model.eiml";
    ei_save_mnist_model(model, model_path);
    printf("    Model saved to: %s\n", model_path);
    printf("    Layers: %d\n", model->layer_count);
    printf("    Total parameters: ");
    int total_params = 0;
    for (int i = 0; i < model->layer_count; i++) {
        if (model->layers[i].weights) total_params += model->layers[i].weights->size;
        if (model->layers[i].bias) total_params += model->layers[i].bias->size;
    }
    printf("%d\n", total_params);
    
    /* Print layer shapes */
    print_layer_shapes(model);
    
    /* Create input tensors */
    printf("\n[2] Testing with different inputs:\n\n");
    
    /* Test 1: Random input */
    printf("--- Test 1: Random input ---\n");
    ei_tensor_t input1, output1;
    ei_create_random_input(&input1);
    ei_tensor_alloc(&output1, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    ei_model_infer(model, &input1, &output1);
    
    float *probs1 = (float *)output1.data;
    int max_idx1 = 0;
    for (int i = 1; i < 10; i++) {
        if (probs1[i] > probs1[max_idx1]) max_idx1 = i;
    }
    printf("    Predicted: %d (confidence: %.2f%%)\n\n",
           max_idx1, probs1[max_idx1] * 100.0);
    
    /* Test 2: Digit-like pattern */
    printf("--- Test 2: Digit-like pattern (digit=3) ---\n");
    ei_tensor_t input2, output2;
    ei_create_digit_like_input(&input2, 3);
    ei_tensor_alloc(&output2, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    ei_model_infer(model, &input2, &output2);
    
    float *probs2 = (float *)output2.data;
    int max_idx2 = 0;
    for (int i = 1; i < 10; i++) {
        if (probs2[i] > probs2[max_idx2]) max_idx2 = i;
    }
    printf("    Predicted: %d (confidence: %.2f%%)\n\n",
           max_idx2, probs2[max_idx2] * 100.0);
    
    /* Test 3: Another digit-like pattern */
    printf("--- Test 3: Digit-like pattern (digit=7) ---\n");
    ei_tensor_t input3, output3;
    ei_create_digit_like_input(&input3, 7);
    ei_tensor_alloc(&output3, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    ei_model_infer(model, &input3, &output3);
    
    float *probs3 = (float *)output3.data;
    int max_idx3 = 0;
    for (int i = 1; i < 10; i++) {
        if (probs3[i] > probs3[max_idx3]) max_idx3 = i;
    }
    printf("    Predicted: %d (confidence: %.2f%%)\n\n",
           max_idx3, probs3[max_idx3] * 100.0);
    
    /* Test 4: Load saved model and run inference */
    printf("--- Test 4: Load saved model and run inference ---\n");
    ei_model_free(model);
    
    model = ei_model_create();
    ei_model_load(model, model_path);
    
    ei_tensor_t input4, output4;
    ei_create_digit_like_input(&input4, 5);
    ei_tensor_alloc(&output4, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    ei_model_infer(model, &input4, &output4);
    
    float *probs4 = (float *)output4.data;
    int max_idx4 = 0;
    for (int i = 1; i < 10; i++) {
        if (probs4[i] > probs4[max_idx4]) max_idx4 = i;
    }
    printf("    Predicted: %d (confidence: %.2f%%)\n\n",
           max_idx4, probs4[max_idx4] * 100.0);
    
    /* Print all probabilities for Test 4 */
    printf("    Full output distribution:\n");
    for (int i = 0; i < 10; i++) {
        printf("      Digit %d: %.4f", i, probs4[i]);
        /* Simple bar chart */
        int bar_len = (int)(probs4[i] * 40);
        for (int j = 0; j < bar_len; j++) printf("#");
        printf("\n");
    }
    
    /* Cleanup */
    ei_tensor_free(&input1);
    ei_tensor_free(&output1);
    ei_tensor_free(&input2);
    ei_tensor_free(&output2);
    ei_tensor_free(&input3);
    ei_tensor_free(&output3);
    ei_tensor_free(&input4);
    ei_tensor_free(&output4);
    ei_model_free(model);
    
    printf("\n=== Demo complete ===\n");
    printf("\nNote: This model has RANDOM weights, so predictions are not accurate.\n");
    printf("In practice, load a trained model for real digit recognition.\n");
    
    return 0;
}
