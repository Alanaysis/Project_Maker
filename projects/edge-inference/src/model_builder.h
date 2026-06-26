/**
 * model_builder.c - Helper for creating and saving MNIST model
 * 
 * This module provides utilities to:
 * - Create a simple MNIST classifier model programmatically
 * - Save it in our binary format for loading by the inference engine
 * - Generate random/initialized weights for testing
 * 
 * The model architecture is a simple CNN for MNIST digit classification:
 *   Input(1x28x28) -> Conv(16x24x24) -> ReLU -> MaxPool(16x12x12) ->
 *   Conv(32x10x10) -> ReLU -> MaxPool(32x5x5) -> Flatten ->
 *   FC(800->10) -> Softmax -> Output
 * 
 * This is a simplified version of LeNet-5, designed for educational purposes.
 */

#include "edge_inference.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ============================================================================
 * Weight Initialization
 * ============================================================================ */

/**
 * Xavier/Glorot initialization for weights.
 * 
 * Good weight initialization is critical for training convergence.
 * Xavier init uses variance = 2 / (fan_in + fan_out) to keep
 * activations roughly the same scale through all layers.
 */
static void ei_init_weights_xavier(float *weights, int32_t fan_in, int32_t fan_out, int32_t count, double scale) {
    /* Simple pseudo-random using LCG (Linear Congruential Generator) */
    static unsigned long state = 42;
    state += (unsigned long)count;
    
    double variance = 2.0 / (fan_in + fan_out);
    double std = sqrt(variance);
    
    for (int i = 0; i < count; i++) {
        /* Box-Muller transform for normal distribution */
        double u1 = ((double)(state % 10000) / 10000.0) * 0.999 + 0.001;
        double u2 = ((double)((state >> 14) % 10000) / 10000.0) * 0.999 + 0.001;
        state *= 1103515245 + 12345;
        
        double z = sqrt(-2.0 * log(u1)) * cos(2.0 * 3.14159265358979 * u2);
        weights[i] = (float)(z * std * scale);
    }
}

/**
 * Initialize bias to small positive values (LeCun init).
 * Helps prevent ReLU from being inactive (dying ReLU problem).
 */
static void ei_init_bias(float *bias, int32_t count) {
    for (int i = 0; i < count; i++) {
        bias[i] = 0.01f;  /* Small positive constant */
    }
}

/* ============================================================================
 * Model Creation - MNIST Classifier
 * ============================================================================ */

/**
 * Create a simple MNIST CNN model.
 * 
 * Architecture:
 *   Input: [1, 1, 28, 28] (grayscale image)
 *   Conv2D: [16, 1, 5, 5] stride=1, pad=0 -> [16, 24, 24]
 *   ReLU
 *   MaxPool: [2, 2] stride=2 -> [16, 12, 12]
 *   Conv2D: [32, 16, 5, 5] stride=1, pad=0 -> [32, 8, 8]
 *   ReLU
 *   MaxPool: [2, 2] stride=2 -> [32, 4, 4]
 *   Flatten: [512]
 *   FC: [512 -> 128]
 *   ReLU
 *   FC: [128 -> 10]
 *   Softmax: [10] (class probabilities)
 * 
 * Total parameters: ~27,000 (very small, suitable for edge devices!)
 * Model size: ~108KB (FP32), ~27KB (INT8 quantized)
 */
int ei_create_mnist_model(ei_model_t *model) {
    srand((unsigned int)time(NULL));
    
    memset(model, 0, sizeof(ei_model_t));
    strncpy(model->name, "MNIST-CNN", 64);
    strncpy(model->version, "1.0", 16);
    
    /* Define input shape: [batch, channels, height, width] */
    int32_t input_shape[4] = {1, 1, 28, 28};
    model->input_count = 1;
    ei_tensor_init(&model->inputs[0], input_shape, 4, EI_TENSOR_FP32);
    
    /* ========================================================================
     * Layer 1: Conv2D - 16 filters, 5x5 kernel
     * ======================================================================== */
    ei_layer_t *layer1 = &model->layers[0];
    ei_layer_init_conv(layer1, "conv1", 5, 5, 1, 1, 0, 0, 1, 1, 1);
    
    /* Weight shape: [out_channels, in_channels, kernel_h, kernel_w] */
    int32_t w1_shape[4] = {16, 1, 5, 5};
    int32_t w1_size = 16 * 1 * 5 * 5;  /* 400 weights */
    layer1->weights = ei_tensor_create();
    ei_tensor_alloc(layer1->weights, w1_shape, 4, EI_TENSOR_FP32);
    
    /* Initialize weights with Xavier initialization */
    float *w1_data = (float *)layer1->weights->data;
    ei_init_weights_xavier(w1_data, 1 * 5 * 5, 16, w1_size, 1.0);
    
    /* Bias */
    int32_t b1_shape[4] = {1, 1, 1, 16};
    layer1->bias = ei_tensor_create();
    ei_tensor_alloc(layer1->bias, b1_shape, 4, EI_TENSOR_FP32);
    ei_init_bias((float *)layer1->bias->data, 16);
    
    model->layer_count = 1;
    
    /* ========================================================================
     * Layer 2: ReLU
     * ======================================================================== */
    ei_layer_t *layer2 = &model->layers[1];
    ei_layer_init_relu(layer2, "relu1");
    model->layer_count = 2;
    
    /* ========================================================================
     * Layer 3: Max Pooling 2x2
     * ======================================================================== */
    ei_layer_t *layer3 = &model->layers[2];
    ei_layer_init_pool(layer3, "pool1", EI_LAYER_MAX_POOL, 2, 2, 2, 2, 0, 0);
    model->layer_count = 3;
    
    /* ========================================================================
     * Layer 4: Conv2D - 32 filters, 5x5 kernel
     * ======================================================================== */
    ei_layer_t *layer4 = &model->layers[3];
    ei_layer_init_conv(layer4, "conv2", 5, 5, 1, 1, 0, 0, 1, 1, 1);
    
    int32_t w2_shape[4] = {32, 16, 5, 5};
    int32_t w2_size = 32 * 16 * 5 * 5;  /* 12,800 weights */
    layer4->weights = ei_tensor_create();
    ei_tensor_alloc(layer4->weights, w2_shape, 4, EI_TENSOR_FP32);
    
    float *w2_data = (float *)layer4->weights->data;
    ei_init_weights_xavier(w2_data, 16 * 5 * 5, 32, w2_size, 0.5);
    
    int32_t b2_shape[4] = {1, 1, 1, 32};
    layer4->bias = ei_tensor_create();
    ei_tensor_alloc(layer4->bias, b2_shape, 4, EI_TENSOR_FP32);
    ei_init_bias((float *)layer4->bias->data, 32);
    
    model->layer_count = 4;
    
    /* ========================================================================
     * Layer 5: ReLU
     * ======================================================================== */
    ei_layer_t *layer5 = &model->layers[4];
    ei_layer_init_relu(layer5, "relu2");
    model->layer_count = 5;
    
    /* ========================================================================
     * Layer 6: Max Pooling 2x2
     * ======================================================================== */
    ei_layer_t *layer6 = &model->layers[5];
    ei_layer_init_pool(layer6, "pool2", EI_LAYER_MAX_POOL, 2, 2, 2, 2, 0, 0);
    model->layer_count = 6;
    
    /* ========================================================================
     * Layer 7: Flatten
     * ======================================================================== */
    ei_layer_t *layer7 = &model->layers[6];
    layer7->type = EI_LAYER_FLATTEN;
    strncpy(layer7->name, "flatten", EI_LAYER_NAME_MAX);
    model->layer_count = 7;
    
    /* ========================================================================
     * Layer 8: FC - 512 -> 128
     * ======================================================================== */
    ei_layer_t *layer8 = &model->layers[7];
    ei_layer_init_fc(layer8, "fc1", 512, 128, true);
    
    int32_t w3_shape[4] = {1, 1, 1, 512 * 128};
    int32_t w3_size = 512 * 128;  /* 65,536 weights */
    layer8->weights = ei_tensor_create();
    ei_tensor_alloc(layer8->weights, w3_shape, 4, EI_TENSOR_FP32);
    
    float *w3_data = (float *)layer8->weights->data;
    ei_init_weights_xavier(w3_data, 512, 128, w3_size, 0.1);
    
    int32_t b3_shape[4] = {1, 1, 1, 128};
    layer8->bias = ei_tensor_create();
    ei_tensor_alloc(layer8->bias, b3_shape, 4, EI_TENSOR_FP32);
    ei_init_bias((float *)layer8->bias->data, 128);
    
    model->layer_count = 8;
    
    /* ========================================================================
     * Layer 9: ReLU
     * ======================================================================== */
    ei_layer_t *layer9 = &model->layers[8];
    ei_layer_init_relu(layer9, "relu3");
    model->layer_count = 9;
    
    /* ========================================================================
     * Layer 10: FC - 128 -> 10 (class logits)
     * ======================================================================== */
    ei_layer_t *layer10 = &model->layers[9];
    ei_layer_init_fc(layer10, "fc2", 128, 10, true);
    
    int32_t w4_shape[4] = {1, 1, 1, 128 * 10};
    int32_t w4_size = 128 * 10;  /* 1,280 weights */
    layer10->weights = ei_tensor_create();
    ei_tensor_alloc(layer10->weights, w4_shape, 4, EI_TENSOR_FP32);
    
    float *w4_data = (float *)layer10->weights->data;
    ei_init_weights_xavier(w4_data, 128, 10, w4_size, 0.1);
    
    int32_t b4_shape[4] = {1, 1, 1, 10};
    layer10->bias = ei_tensor_create();
    ei_tensor_alloc(layer10->bias, b4_shape, 4, EI_TENSOR_FP32);
    ei_init_bias((float *)layer10->bias->data, 10);
    
    model->layer_count = 10;
    
    /* ========================================================================
     * Layer 11: Softmax (output)
     * ======================================================================== */
    ei_layer_t *layer11 = &model->layers[10];
    ei_layer_init_softmax(layer11, "softmax");
    model->layer_count = 11;
    
    /* Define output shape */
    int32_t output_shape[4] = {1, 1, 1, 10};
    model->output_count = 1;
    ei_tensor_init(&model->outputs[0], output_shape, 4, EI_TENSOR_FP32);
    
    /* Initialize workspace */
    ei_model_init_workspace(model);
    
    return EI_OK;
}

/* ============================================================================
 * Model Saving
 * ============================================================================ */

/**
 * Save a model to binary file.
 * 
 * This writes the model in our custom binary format so it can be
 * loaded by ei_model_load() for inference.
 */
int ei_save_mnist_model(const ei_model_t *model, const char *filepath) {
    FILE *fp = fopen(filepath, "wb");
    if (!fp) {
        fprintf(stderr, "[EI] Error: Cannot create model file: %s\n", filepath);
        return EI_ERR_IO;
    }
    
    /* Write magic number and version */
    uint32_t magic = EI_MODEL_MAGIC;
    uint32_t version = EI_MODEL_VERSION;
    fwrite(&magic, sizeof(uint32_t), 1, fp);
    fwrite(&version, sizeof(uint32_t), 1, fp);
    
    /* Write layer count */
    fwrite(&model->layer_count, sizeof(int32_t), 1, fp);
    
    /* Write model name and version */
    fwrite(model->name, 64, 1, fp);
    fwrite(model->version, 16, 1, fp);
    
    /* Write input info */
    fwrite(&model->input_count, sizeof(int32_t), 1, fp);
    for (int i = 0; i < model->input_count; i++) {
        for (int j = 0; j < 4; j++) {
            fwrite(&model->inputs[i].dims[j], sizeof(int32_t), 1, fp);
        }
    }
    
    /* Write quantization info */
    int32_t quant_type = model->quant_type;
    fwrite(&quant_type, sizeof(int32_t), 1, fp);
    
    if (quant_type == EI_QUANT_PER_TENSOR) {
        fwrite(&model->model_scale, sizeof(float), 1, fp);
        fwrite(&model->model_zero_point, sizeof(int32_t), 1, fp);
    }
    
    /* Write each layer */
    for (int i = 0; i < model->layer_count; i++) {
        const ei_layer_t *layer = &model->layers[i];
        
        /* Layer type and name */
        int32_t layer_type = layer->type;
        fwrite(&layer_type, sizeof(int32_t), 1, fp);
        fwrite(layer->name, EI_LAYER_NAME_MAX, 1, fp);
        
        /* Parameter block */
        int32_t param_size = 0;
        switch (layer->type) {
            case EI_LAYER_CONV2D:
                param_size = 9 * sizeof(int32_t);
                fwrite(&param_size, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.kernel_h, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.kernel_w, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.stride_h, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.stride_w, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.pad_h, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.pad_w, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.dilation_h, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.dilation_w, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.conv.groups, sizeof(int32_t), 1, fp);
                break;
            case EI_LAYER_FULLY_CONNECTED:
                param_size = 3 * sizeof(int32_t) + sizeof(bool);
                fwrite(&param_size, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.fc.in_features, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.fc.out_features, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.fc.use_bias, sizeof(bool), 1, fp);
                break;
            case EI_LAYER_MAX_POOL:
            case EI_LAYER_AVG_POOL:
                param_size = 6 * sizeof(int32_t);
                fwrite(&param_size, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.pooling.kernel_h, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.pooling.kernel_w, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.pooling.stride_h, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.pooling.stride_w, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.pooling.pad_h, sizeof(int32_t), 1, fp);
                fwrite(&layer->params.pooling.pad_w, sizeof(int32_t), 1, fp);
                break;
            default:
                param_size = 0;
                fwrite(&param_size, sizeof(int32_t), 1, fp);
                break;
        }
        
        /* Write weights */
        int32_t weight_count = 0;
        int32_t weight_type = 0;  /* 0 = FP32, 1 = INT8 */
        
        if (layer->weights) {
            weight_count = layer->weights->size;
            weight_type = layer->weights->type == EI_TENSOR_INT8 ? 1 : 0;
            fwrite(&weight_count, sizeof(int32_t), 1, fp);
            fwrite(&weight_type, sizeof(int32_t), 1, fp);
            
            size_t w_size = ei_tensor_data_size(layer->weights);
            fwrite(layer->weights->data, 1, w_size, fp);
            
            /* Write per-channel scales for INT8 */
            if (weight_type == 1) {
                fwrite(&layer->num_weight_scales, sizeof(int32_t), 1, fp);
                if (layer->num_weight_scales > 0 && layer->weight_scales) {
                    fwrite(layer->weight_scales, sizeof(float), layer->num_weight_scales, fp);
                }
            }
        } else {
            fwrite(&weight_count, sizeof(int32_t), 1, fp);
            fwrite(&weight_type, sizeof(int32_t), 1, fp);
        }
        
        /* Write bias */
        int32_t bias_count = 0;
        if (layer->bias) {
            bias_count = layer->bias->size;
            fwrite(&bias_count, sizeof(int32_t), 1, fp);
            fwrite(layer->bias->data, sizeof(float), bias_count, fp);
        } else {
            fwrite(&bias_count, sizeof(int32_t), 1, fp);
        }
    }
    
    fclose(fp);
    return EI_OK;
}

/* ============================================================================
 * Generate random MNIST-like input data for testing
 * ============================================================================ */

/**
 * Create a random input tensor that simulates a grayscale MNIST image.
 * 
 * For testing, we generate random pixel values in [0, 1] range.
 * In practice, this would be a real image preprocessed to 28x28 grayscale.
 */
int ei_create_random_input(ei_tensor_t *output) {
    int32_t shape[4] = {1, 1, 28, 28};
    ei_tensor_alloc(output, shape, 4, EI_TENSOR_FP32);
    
    float *data = (float *)output->data;
    for (int i = 0; i < output->size; i++) {
        /* Random pixel value in [0, 1] */
        data[i] = (float)(rand() % 1000) / 1000.0f;
    }
    
    return EI_OK;
}

/**
 * Create a "digit-like" input for more realistic testing.
 * 
 * This creates a simple pattern that looks like a digit (concentric circles),
 * making it easier to verify the model is actually processing data.
 */
int ei_create_digit_like_input(ei_tensor_t *output, int digit) {
    int32_t shape[4] = {1, 1, 28, 28};
    ei_tensor_alloc(output, shape, 4, EI_TENSOR_FP32);
    
    float *data = (float *)output->data;
    memset(data, 0, output->size * sizeof(float));
    
    /* Create a simple circle pattern centered in the image */
    int cx = 14, cy = 14;  /* Center */
    int radius = 8 + (digit % 3);  /* Vary radius by digit */
    
    for (int y = 0; y < 28; y++) {
        for (int x = 0; x < 28; x++) {
            int dx = x - cx;
            int dy = y - cy;
            float dist = sqrtf((float)(dx * dx + dy * dy));
            
            if (dist >= radius - 2 && dist <= radius + 2) {
                /* Ring pattern - simulates a digit stroke */
                data[y * 28 + x] = 1.0f;
            } else if (dist < radius - 2) {
                /* Inner filled area */
                data[y * 28 + x] = 0.3f;
            }
        }
    }
    
    return EI_OK;
}
