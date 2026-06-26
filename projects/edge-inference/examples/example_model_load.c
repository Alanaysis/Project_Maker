/**
 * example_model_load.c - Model Loading and Verification Demo
 * 
 * This example demonstrates:
 * 1. Creating a model programmatically (MNIST CNN)
 * 2. Saving it to a binary file
 * 3. Loading it back from the file
 * 4. Verifying the model structure
 * 
 * This mirrors the real-world workflow:
 * - Train model in Python (PyTorch/TensorFlow)
 * - Export to binary format
 * - Load and run on edge device
 */

#include <stdio.h>
#include <stdlib.h>
#include "edge_inference.h"
#include "model_builder.h"

int main(int argc, char *argv[]) {
    printf("=== Edge AI Inference Engine - Model Loading Demo ===\n\n");
    
    const char *model_path = "mnist_model.eiml";
    if (argc > 1) {
        model_path = argv[1];
    }
    
    /* Step 1: Create model programmatically */
    printf("[1] Creating MNIST model...\n");
    ei_model_t *model = ei_model_create();
    if (!model) {
        fprintf(stderr, "Failed to create model\n");
        return 1;
    }
    
    ei_create_mnist_model(model);
    printf("    Model name: %s\n", model->name);
    printf("    Layers: %d\n", model->layer_count);
    printf("    Input shape: [%d, %d, %d, %d]\n",
           model->inputs[0].dims[0], model->inputs[0].dims[1],
           model->inputs[0].dims[2], model->inputs[0].dims[3]);
    
    /* Step 2: Save model to binary file */
    printf("\n[2] Saving model to: %s\n", model_path);
    int ret = ei_save_mnist_model(model, model_path);
    if (ret != EI_OK) {
        fprintf(stderr, "Failed to save model (error %d)\n", ret);
        ei_model_free(model);
        return 1;
    }
    
    /* Check file size */
    FILE *fp = fopen(model_path, "rb");
    if (fp) {
        fseek(fp, 0, SEEK_END);
        long size = ftell(fp);
        fclose(fp);
        printf("    Model file size: %ld bytes (%.1f KB)\n", size, size / 1024.0);
    }
    
    /* Step 3: Free the original model */
    printf("\n[3] Freeing original model...\n");
    ei_model_free(model);
    
    /* Step 4: Load model from file */
    printf("\n[4] Loading model from: %s\n", model_path);
    ei_model_t *loaded_model = ei_model_create();
    if (!loaded_model) {
        fprintf(stderr, "Failed to create model\n");
        return 1;
    }
    
    ret = ei_model_load(loaded_model, model_path);
    if (ret != EI_OK) {
        fprintf(stderr, "Failed to load model (error %d)\n", ret);
        ei_model_free(loaded_model);
        return 1;
    }
    
    /* Step 5: Verify loaded model */
    printf("\n[5] Model verification:\n");
    printf("    Name: %s\n", loaded_model->name);
    printf("    Version: %s\n", loaded_model->version);
    printf("    Layers: %d\n", loaded_model->layer_count);
    printf("    Quantization: ");
    switch (loaded_model->quant_type) {
        case EI_QUANT_NONE: printf("None (FP32)\n"); break;
        case EI_QUANT_PER_TENSOR: printf("Per-tensor INT8\n"); break;
        case EI_QUANT_PER_CHANNEL: printf("Per-channel INT8\n"); break;
    }
    
    /* Print layer details */
    printf("\n    Layer details:\n");
    for (int i = 0; i < loaded_model->layer_count; i++) {
        ei_layer_t *layer = &loaded_model->layers[i];
        const char *type_str;
        switch (layer->type) {
            case EI_LAYER_CONV2D:         type_str = "Conv2D"; break;
            case EI_LAYER_FULLY_CONNECTED: type_str = "FC"; break;
            case EI_LAYER_RELU:           type_str = "ReLU"; break;
            case EI_LAYER_SIGMOID:        type_str = "Sigmoid"; break;
            case EI_LAYER_TANH:           type_str = "Tanh"; break;
            case EI_LAYER_SOFTMAX:        type_str = "Softmax"; break;
            case EI_LAYER_MAX_POOL:       type_str = "MaxPool"; break;
            case EI_LAYER_AVG_POOL:       type_str = "AvgPool"; break;
            case EI_LAYER_FLATTEN:        type_str = "Flatten"; break;
            default:                      type_str = "Unknown"; break;
        }
        
        printf("      [%2d] %-15s (%s)", i, layer->name, type_str);
        
        if (layer->weights) {
            printf(", weights=%d", layer->weights->size);
            if (layer->weights_quantized) {
                printf(" [INT8]");
            }
        }
        
        if (layer->bias) {
            printf(", bias=%d", layer->bias->size);
        }
        
        printf("\n");
    }
    
    /* Step 6: Run inference */
    printf("\n[6] Running inference...\n");
    ei_tensor_t input, output;
    ei_create_digit_like_input(&input, 3);
    ei_tensor_alloc(&output, (int32_t[]){1, 1, 1, 10}, 4, EI_TENSOR_FP32);
    
    ret = ei_model_infer(loaded_model, &input, &output);
    if (ret != EI_OK) {
        fprintf(stderr, "Inference failed (error %d)\n", ret);
        ei_tensor_free(&input);
        ei_tensor_free(&output);
        ei_model_free(loaded_model);
        return 1;
    }
    
    /* Print output probabilities */
    float *probs = (float *)output.data;
    int max_idx = 0;
    float max_prob = probs[0];
    
    printf("    Output probabilities:\n");
    for (int i = 0; i < 10; i++) {
        printf("      Digit %d: %.4f %s\n", i, probs[i],
               probs[i] == max_prob ? " <-- MAX" : "");
        if (probs[i] > max_prob) {
            max_prob = probs[i];
            max_idx = i;
        }
    }
    
    printf("\n    Predicted digit: %d (confidence: %.2f%%)\n",
           max_idx, max_prob * 100.0);
    
    /* Cleanup */
    ei_tensor_free(&input);
    ei_tensor_free(&output);
    ei_model_free(loaded_model);
    
    printf("\n=== Demo complete ===\n");
    return 0;
}
