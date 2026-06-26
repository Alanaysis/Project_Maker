/**
 * edge_inference.c - Core inference engine implementation
 * 
 * This file implements the core neural network inference operations:
 * - Tensor management (creation, allocation, memory)
 * - Convolution (im2col-based)
 * - Fully connected layers
 * - Activation functions (ReLU, sigmoid, tanh, softmax)
 * - Pooling layers (max pooling, average pooling)
 * - Batch normalization
 * - Model loading and inference
 * 
 * The engine uses a simple approach: each layer takes input tensors,
 * computes output tensors, and passes them to the next layer.
 * This mimics how frameworks like TensorFlow and PyTorch work,
 * but in pure C for educational purposes.
 */

#include "edge_inference.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <float.h>

/* ============================================================================
 * Utility: timing function for benchmarking
 * ============================================================================ */
static double ei_get_time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

/* ============================================================================
 * Tensor API Implementation
 * ============================================================================ */

ei_tensor_t *ei_tensor_create(void) {
    ei_tensor_t *tensor = (ei_tensor_t *)calloc(1, sizeof(ei_tensor_t));
    if (!tensor) return NULL;
    
    tensor->ndims = 0;
    tensor->size = 0;
    tensor->type = EI_TENSOR_FP32;
    tensor->data = NULL;
    tensor->owns_data = false;
    tensor->scale = 1.0f;
    tensor->zero_point = 0;
    
    return tensor;
}

int ei_tensor_init(ei_tensor_t *tensor, int32_t *shape, int32_t ndims, ei_tensor_type_t type) {
    if (!tensor || !shape || ndims > EI_MAX_DIMS) return EI_ERR_SHAPE;
    
    tensor->ndims = ndims;
    tensor->size = 1;
    for (int32_t i = 0; i < ndims; i++) {
        tensor->dims[i] = shape[i];
        tensor->size *= shape[i];
    }
    tensor->type = type;
    tensor->data = NULL;
    tensor->owns_data = false;
    tensor->scale = 1.0f;
    tensor->zero_point = 0;
    
    return EI_OK;
}

int ei_tensor_alloc(ei_tensor_t *tensor, int32_t *shape, int32_t ndims, ei_tensor_type_t type) {
    int ret = ei_tensor_init(tensor, shape, ndims, type);
    if (ret != EI_OK) return ret;
    
    size_t data_size = (size_t)tensor->size * (size_t)ei_tensor_elem_size(type);
    tensor->data = malloc(data_size);
    if (!tensor->data) return EI_ERR_MEM;
    
    tensor->owns_data = true;
    memset(tensor->data, 0, data_size);
    
    return EI_OK;
}

void ei_tensor_free(ei_tensor_t *tensor) {
    if (!tensor) return;
    
    if (tensor->owns_data && tensor->data) {
        free(tensor->data);
        tensor->data = NULL;
    }
    tensor->owns_data = false;
    tensor->size = 0;
    tensor->ndims = 0;
}

int ei_tensor_copy(const ei_tensor_t *src, ei_tensor_t *dst) {
    if (!src || !dst || src->size != dst->size || src->type != dst->type) {
        return EI_ERR_SHAPE;
    }
    
    memcpy(dst->data, src->data, ei_tensor_data_size(src));
    return EI_OK;
}

int32_t ei_tensor_elem_size(ei_tensor_type_t type) {
    switch (type) {
        case EI_TENSOR_FP32:  return sizeof(float);
        case EI_TENSOR_INT8:  return sizeof(int8_t);
        case EI_TENSOR_INT32: return sizeof(int32_t);
        case EI_TENSOR_UINT8: return sizeof(uint8_t);
        default: return sizeof(float);
    }
}

size_t ei_tensor_data_size(const ei_tensor_t *tensor) {
    return (size_t)tensor->size * (size_t)ei_tensor_elem_size(tensor->type);
}

int ei_tensor_set_data(ei_tensor_t *tensor, void *data, bool take_ownership) {
    if (!tensor || !data) return EI_ERR_OP;
    
    if (tensor->owns_data && tensor->data) {
        free(tensor->data);
    }
    
    tensor->data = data;
    tensor->owns_data = take_ownership;
    return EI_OK;
}

void *ei_tensor_get_ptr(ei_tensor_t *tensor, int32_t *indices) {
    if (!tensor || !indices || tensor->ndims != 4) return NULL;
    
    /* Convert 4D indices to flat offset: [n, c, h, w] */
    int32_t offset = indices[0] * tensor->dims[1] * tensor->dims[2] * tensor->dims[3] +
                     indices[1] * tensor->dims[2] * tensor->dims[3] +
                     indices[2] * tensor->dims[3] +
                     indices[3];
    
    /* Handle different data types */
    switch (tensor->type) {
        case EI_TENSOR_FP32:
            return (char *)tensor->data + offset * sizeof(float);
        case EI_TENSOR_INT8:
            return (char *)tensor->data + offset * sizeof(int8_t);
        case EI_TENSOR_INT32:
            return (char *)tensor->data + offset * sizeof(int32_t);
        case EI_TENSOR_UINT8:
            return (char *)tensor->data + offset * sizeof(uint8_t);
        default:
            return NULL;
    }
}

/* ============================================================================
 * Model API Implementation
 * ============================================================================ */

ei_model_t *ei_model_create(void) {
    ei_model_t *model = (ei_model_t *)calloc(1, sizeof(ei_model_t));
    if (!model) return NULL;
    
    memset(model->name, 0, sizeof(model->name));
    memset(model->version, 0, sizeof(model->version));
    model->input_count = 0;
    model->layer_count = 0;
    model->output_count = 0;
    model->quant_type = EI_QUANT_NONE;
    model->model_scale = 1.0f;
    model->model_zero_point = 0;
    model->workspace = NULL;
    model->workspace_size = 0;
    model->temp_tensors = NULL;
    model->num_temp_tensors = 0;
    
    return model;
}

int ei_model_load(ei_model_t *model, const char *filepath) {
    FILE *fp = fopen(filepath, "rb");
    if (!fp) {
        fprintf(stderr, "[EI] Error: Cannot open model file: %s\n", filepath);
        return EI_ERR_IO;
    }
    
    /* Read and verify magic number */
    uint32_t magic;
    if (fread(&magic, sizeof(uint32_t), 1, fp) != 1) {
        fprintf(stderr, "[EI] Error: Cannot read magic number\n");
        fclose(fp);
        return EI_ERR_FORMAT;
    }
    
    if (magic != EI_MODEL_MAGIC) {
        fprintf(stderr, "[EI] Error: Invalid model magic: 0x%08X (expected 0x%08X)\n",
                magic, EI_MODEL_MAGIC);
        fclose(fp);
        return EI_ERR_MAGIC;
    }
    
    /* Read version */
    uint32_t version;
    if (fread(&version, sizeof(uint32_t), 1, fp) != 1) {
        fclose(fp);
        return EI_ERR_FORMAT;
    }
    
    /* Read metadata */
    int32_t layer_count;
    if (fread(&layer_count, sizeof(int32_t), 1, fp) != 1) {
        fclose(fp);
        return EI_ERR_FORMAT;
    }
    
    if (layer_count <= 0 || layer_count > EI_MAX_LAYERS) {
        fprintf(stderr, "[EI] Error: Invalid layer count: %d\n", layer_count);
        fclose(fp);
        return EI_ERR_FORMAT;
    }
    
    /* Read model name and version */
    fread(model->name, 64, 1, fp);
    fread(model->version, 16, 1, fp);
    
    /* Read input info */
    if (fread(&model->input_count, sizeof(int32_t), 1, fp) != 1) {
        fclose(fp);
        return EI_ERR_FORMAT;
    }
    
    for (int i = 0; i < model->input_count; i++) {
        for (int j = 0; j < 4; j++) {
            fread(&model->inputs[i].dims[j], sizeof(int32_t), 1, fp);
        }
        model->inputs[i].ndims = 4;
        model->inputs[i].size = 1;
        for (int j = 0; j < 4; j++) {
            model->inputs[i].size *= model->inputs[i].dims[j];
        }
        model->inputs[i].type = EI_TENSOR_FP32;
        model->inputs[i].scale = 1.0f;
        model->inputs[i].zero_point = 0;
    }
    
    /* Read quantization info */
    int32_t quant_type;
    if (fread(&quant_type, sizeof(int32_t), 1, fp) != 1) {
        fclose(fp);
        return EI_ERR_FORMAT;
    }
    model->quant_type = (ei_quantization_type_t)quant_type;
    
    if (quant_type == EI_QUANT_PER_TENSOR) {
        fread(&model->model_scale, sizeof(float), 1, fp);
        fread(&model->model_zero_point, sizeof(int32_t), 1, fp);
    }
    
    /* Read layers */
    model->layer_count = layer_count;
    for (int i = 0; i < layer_count; i++) {
        ei_layer_t *layer = &model->layers[i];
        memset(layer, 0, sizeof(ei_layer_t));
        
        /* Read layer type and name */
        int32_t layer_type;
        if (fread(&layer_type, sizeof(int32_t), 1, fp) != 1) {
            fclose(fp);
            return EI_ERR_FORMAT;
        }
        layer->type = (ei_layer_type_t)layer_type;
        fread(layer->name, EI_LAYER_NAME_MAX, 1, fp);
        layer->layer_index = i;
        
        /* Read parameters (type-specific) */
        int32_t param_size;
        if (fread(&param_size, sizeof(int32_t), 1, fp) != 1) {
            fclose(fp);
            return EI_ERR_FORMAT;
        }
        
        switch (layer->type) {
            case EI_LAYER_CONV2D: {
                fread(&layer->params.conv.kernel_h, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.kernel_w, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.stride_h, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.stride_w, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.pad_h, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.pad_w, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.dilation_h, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.dilation_w, sizeof(int32_t), 1, fp);
                fread(&layer->params.conv.groups, sizeof(int32_t), 1, fp);
                break;
            }
            case EI_LAYER_FULLY_CONNECTED: {
                fread(&layer->params.fc.in_features, sizeof(int32_t), 1, fp);
                fread(&layer->params.fc.out_features, sizeof(int32_t), 1, fp);
                fread(&layer->params.fc.use_bias, sizeof(bool), 1, fp);
                break;
            }
            case EI_LAYER_MAX_POOL:
            case EI_LAYER_AVG_POOL: {
                fread(&layer->params.pooling.kernel_h, sizeof(int32_t), 1, fp);
                fread(&layer->params.pooling.kernel_w, sizeof(int32_t), 1, fp);
                fread(&layer->params.pooling.stride_h, sizeof(int32_t), 1, fp);
                fread(&layer->params.pooling.stride_w, sizeof(int32_t), 1, fp);
                fread(&layer->params.pooling.pad_h, sizeof(int32_t), 1, fp);
                fread(&layer->params.pooling.pad_w, sizeof(int32_t), 1, fp);
                break;
            }
            default:
                /* Skip unknown parameter block */
                fseek(fp, param_size, SEEK_CUR);
                break;
        }
        
        /* Read weights */
        int32_t weight_count, weight_type;
        if (fread(&weight_count, sizeof(int32_t), 1, fp) != 1) {
            fclose(fp);
            return EI_ERR_FORMAT;
        }
        if (fread(&weight_type, sizeof(int32_t), 1, fp) != 1) {
            fclose(fp);
            return EI_ERR_FORMAT;
        }
        
        if (weight_count > 0) {
            layer->weights = ei_tensor_create();
            ei_tensor_type_t w_type = (weight_type == 1) ? EI_TENSOR_INT8 : EI_TENSOR_FP32;
            int32_t w_shape[4] = {1, 1, 1, weight_count};  /* Default shape */
            ei_tensor_alloc(layer->weights, w_shape, 4, w_type);
            size_t w_size = (size_t)weight_count * ei_tensor_elem_size(w_type);
            fread(layer->weights->data, 1, w_size, fp);
            
            /* Store per-channel scales if INT8 */
            if (w_type == EI_TENSOR_INT8) {
                layer->weights_quantized = true;
                if (fread(&layer->num_weight_scales, sizeof(int32_t), 1, fp) != 1) {
                    fclose(fp);
                    return EI_ERR_FORMAT;
                }
                if (layer->num_weight_scales > 0) {
                    layer->weight_scales = (float *)malloc(layer->num_weight_scales * sizeof(float));
                    fread(layer->weight_scales, sizeof(float), layer->num_weight_scales, fp);
                }
            }
        }
        
        /* Read bias */
        int32_t bias_count;
        if (fread(&bias_count, sizeof(int32_t), 1, fp) != 1) {
            fclose(fp);
            return EI_ERR_FORMAT;
        }
        
        if (bias_count > 0) {
            layer->bias = ei_tensor_create();
            int32_t b_shape[4] = {1, 1, 1, bias_count};
            ei_tensor_alloc(layer->bias, b_shape, 4, EI_TENSOR_FP32);
            fread(layer->bias->data, sizeof(float), bias_count, fp);
        }
    }
    
    fclose(fp);
    
    /* Allocate workspace */
    return ei_model_init_workspace(model);
}

int ei_model_init_workspace(ei_model_t *model) {
    if (!model) return EI_ERR_OP;
    
    /* Calculate total workspace needed for intermediate tensors */
    size_t total_size = 0;
    for (int i = 0; i < model->layer_count; i++) {
        total_size += sizeof(ei_tensor_t);  /* For temp tensors */
    }
    
    model->workspace = malloc(total_size);
    if (!model->workspace) return EI_ERR_MEM;
    
    model->workspace_size = total_size;
    model->num_temp_tensors = model->layer_count;
    model->temp_tensors = (ei_tensor_t *)model->workspace;
    
    return EI_OK;
}

int ei_model_infer(ei_model_t *model, ei_tensor_t *input, ei_tensor_t *output) {
    if (!model || !input || !output) return EI_ERR_OP;
    if (model->layer_count <= 0) return EI_ERR_OP;
    
    /* Allocate temp tensors for intermediate results */
    for (int i = 0; i < model->num_temp_tensors; i++) {
        model->temp_tensors[i].owns_data = false;
        model->temp_tensors[i].data = NULL;
    }
    
    /* Set up input tensor */
    ei_tensor_t *current = input;
    
    /* Run each layer sequentially */
    for (int i = 0; i < model->layer_count; i++) {
        ei_layer_t *layer = &model->layers[i];
        int ret = EI_OK;
        
        switch (layer->type) {
            case EI_LAYER_CONV2D:
                ret = ei_run_conv2d(current, &model->temp_tensors[i], layer);
                break;
            case EI_LAYER_FULLY_CONNECTED:
                ret = ei_run_fc(current, &model->temp_tensors[i], layer);
                break;
            case EI_LAYER_RELU:
                ret = ei_run_relu(current, &model->temp_tensors[i]);
                break;
            case EI_LAYER_SIGMOID:
                ret = ei_run_sigmoid(current, &model->temp_tensors[i]);
                break;
            case EI_LAYER_TANH:
                ret = ei_run_tanh(current, &model->temp_tensors[i]);
                break;
            case EI_LAYER_SOFTMAX:
                ret = ei_run_softmax(current, &model->temp_tensors[i]);
                break;
            case EI_LAYER_MAX_POOL:
                ret = ei_run_max_pool(current, &model->temp_tensors[i], layer);
                break;
            case EI_LAYER_AVG_POOL:
                ret = ei_run_avg_pool(current, &model->temp_tensors[i], layer);
                break;
            case EI_LAYER_FLATTEN:
                ret = ei_run_flatten(current, &model->temp_tensors[i]);
                break;
            case EI_LAYER_BATCH_NORM:
                ret = ei_run_batch_norm(current, &model->temp_tensors[i], layer);
                break;
            default:
                fprintf(stderr, "[EI] Warning: Unsupported layer type %d\n", layer->type);
                /* Copy input to output for unsupported layers */
                ei_tensor_copy(current, &model->temp_tensors[i]);
                ret = EI_OK;
                break;
        }
        
        if (ret != EI_OK) {
            fprintf(stderr, "[EI] Error: Layer %d (%s) failed with code %d\n",
                    i, layer->name, ret);
            return ret;
        }
        
        /* Next layer's input is current layer's output */
        current = &model->temp_tensors[i];
    }
    
    /* Copy final output */
    ei_tensor_copy(current, output);
    
    return EI_OK;
}

int ei_model_batch_infer(ei_model_t *model, ei_tensor_t *inputs, int32_t batch_size, ei_tensor_t *outputs) {
    if (!model || !inputs || !outputs || batch_size <= 0) return EI_ERR_OP;
    
    /* Get single input shape (first element of batch) */
    int32_t single_input_size = inputs->size / batch_size;
    
    /* Allocate temp input/output tensors for each batch item */
    ei_tensor_t *batch_inputs = (ei_tensor_t *)malloc(batch_size * sizeof(ei_tensor_t));
    ei_tensor_t *batch_outputs = (ei_tensor_t *)malloc(batch_size * sizeof(ei_tensor_t));
    if (!batch_inputs || !batch_outputs) {
        free(batch_inputs);
        free(batch_outputs);
        return EI_ERR_MEM;
    }
    
    /* Initialize batch tensor descriptors */
    int32_t single_shape[4];
    for (int d = 0; d < 4; d++) {
        single_shape[d] = inputs->dims[d];
    }
    if (batch_size > 1) {
        single_shape[0] = 1;  /* Reset batch dim */
    }
    
    for (int b = 0; b < batch_size; b++) {
        ei_tensor_init(&batch_inputs[b], single_shape, 4, EI_TENSOR_FP32);
        ei_tensor_alloc(&batch_inputs[b], single_shape, 4, EI_TENSOR_FP32);
        
        /* Extract batch item */
        float *src = (float *)inputs->data + b * single_input_size;
        float *dst = (float *)batch_inputs[b].data;
        memcpy(dst, src, single_input_size * sizeof(float));
        
        ei_tensor_init(&batch_outputs[b], single_shape, 4, EI_TENSOR_FP32);
        ei_tensor_alloc(&batch_outputs[b], single_shape, 4, EI_TENSOR_FP32);
    }
    
    /* Run inference on each batch item */
    for (int b = 0; b < batch_size; b++) {
        ei_model_infer(model, &batch_inputs[b], &batch_outputs[b]);
        
        /* Copy result to output buffer */
        float *dst = (float *)outputs->data + b * single_input_size;
        float *src = (float *)batch_outputs[b].data;
        memcpy(dst, src, single_input_size * sizeof(float));
    }
    
    /* Cleanup */
    for (int b = 0; b < batch_size; b++) {
        ei_tensor_free(&batch_inputs[b]);
        ei_tensor_free(&batch_outputs[b]);
    }
    free(batch_inputs);
    free(batch_outputs);
    
    return EI_OK;
}

void ei_model_free(ei_model_t *model) {
    if (!model) return;
    
    /* Free all layers */
    for (int i = 0; i < model->layer_count; i++) {
        ei_layer_t *layer = &model->layers[i];
        if (layer->weights) {
            ei_tensor_free(layer->weights);
            free(layer->weights);
            layer->weights = NULL;
        }
        if (layer->bias) {
            ei_tensor_free(layer->bias);
            free(layer->bias);
            layer->bias = NULL;
        }
        if (layer->weight_scales) {
            free(layer->weight_scales);
            layer->weight_scales = NULL;
        }
    }
    
    /* Free workspace */
    if (model->workspace) {
        free(model->workspace);
        model->workspace = NULL;
    }
    
    free(model);
}

/* ============================================================================
 * Layer API Implementation
 * ============================================================================ */

ei_layer_t *ei_layer_create(void) {
    ei_layer_t *layer = (ei_layer_t *)calloc(1, sizeof(ei_layer_t));
    if (!layer) return NULL;
    
    memset(layer->name, 0, EI_LAYER_NAME_MAX);
    layer->weights_quantized = false;
    layer->num_weight_scales = 0;
    layer->weight_scales = NULL;
    
    return layer;
}

int ei_layer_init_conv(ei_layer_t *layer, const char *name,
                       int32_t kernel_h, int32_t kernel_w,
                       int32_t stride_h, int32_t stride_w,
                       int32_t pad_h, int32_t pad_w,
                       int32_t dilation_h, int32_t dilation_w,
                       int32_t groups) {
    layer->type = EI_LAYER_CONV2D;
    strncpy(layer->name, name ? name : "conv", EI_LAYER_NAME_MAX - 1);
    
    layer->params.conv.kernel_h = kernel_h;
    layer->params.conv.kernel_w = kernel_w;
    layer->params.conv.stride_h = stride_h;
    layer->params.conv.stride_w = stride_w;
    layer->params.conv.pad_h = pad_h;
    layer->params.conv.pad_w = pad_w;
    layer->params.conv.dilation_h = dilation_h;
    layer->params.conv.dilation_w = dilation_w;
    layer->params.conv.groups = groups;
    
    return EI_OK;
}

int ei_layer_init_fc(ei_layer_t *layer, const char *name,
                     int32_t in_features, int32_t out_features, bool use_bias) {
    layer->type = EI_LAYER_FULLY_CONNECTED;
    strncpy(layer->name, name ? name : "fc", EI_LAYER_NAME_MAX - 1);
    
    layer->params.fc.in_features = in_features;
    layer->params.fc.out_features = out_features;
    layer->params.fc.use_bias = use_bias;
    
    return EI_OK;
}

int ei_layer_init_pool(ei_layer_t *layer, const char *name,
                       ei_layer_type_t type,
                       int32_t kernel_h, int32_t kernel_w,
                       int32_t stride_h, int32_t stride_w,
                       int32_t pad_h, int32_t pad_w) {
    layer->type = type;
    strncpy(layer->name, name ? name : "pool", EI_LAYER_NAME_MAX - 1);
    
    layer->params.pooling.kernel_h = kernel_h;
    layer->params.pooling.kernel_w = kernel_w;
    layer->params.pooling.stride_h = stride_h;
    layer->params.pooling.stride_w = stride_w;
    layer->params.pooling.pad_h = pad_h;
    layer->params.pooling.pad_w = pad_w;
    
    return EI_OK;
}

int ei_layer_init_relu(ei_layer_t *layer, const char *name) {
    layer->type = EI_LAYER_RELU;
    strncpy(layer->name, name ? name : "relu", EI_LAYER_NAME_MAX - 1);
    return EI_OK;
}

int ei_layer_init_sigmoid(ei_layer_t *layer, const char *name) {
    layer->type = EI_LAYER_SIGMOID;
    strncpy(layer->name, name ? name : "sigmoid", EI_LAYER_NAME_MAX - 1);
    return EI_OK;
}

int ei_layer_init_tanh(ei_layer_t *layer, const char *name) {
    layer->type = EI_LAYER_TANH;
    strncpy(layer->name, name ? name : "tanh", EI_LAYER_NAME_MAX - 1);
    return EI_OK;
}

int ei_layer_init_softmax(ei_layer_t *layer, const char *name) {
    layer->type = EI_LAYER_SOFTMAX;
    strncpy(layer->name, name ? name : "softmax", EI_LAYER_NAME_MAX - 1);
    return EI_OK;
}

void ei_layer_free(ei_layer_t *layer) {
    if (!layer) return;
    /* Note: does not free weights/bias - caller manages those */
}

/* ============================================================================
 * Inference Operations
 * 
 * Each operation is implemented as a standalone function that:
 * 1. Takes input and output tensors
 * 2. Performs the computation
 * 3. Returns status code
 * 
 * For embedded systems, we prioritize:
 * - Memory efficiency (minimal temporary allocations)
 * - Cache locality (contiguous memory access patterns)
 * - SIMD friendliness (simple loop structures)
 * ============================================================================ */

/* --- Convolution Layer (im2col based) --- */

/**
 * im2col: Convert convolution to matrix multiplication.
 * 
 * This unfolds the input into columns where each column is a patch
 * that will be multiplied by the filter. The convolution then becomes
 * a simple matrix multiply: output = im2col(input) * weights^T
 * 
 * For embedded CPUs, we can use optimized BLAS or NEON intrinsics
 * for the matrix multiply step.
 */
static int ei_im2col(const float *input, int32_t *col, int32_t channels,
                     int32_t height, int32_t width,
                     int32_t kernel_h, int32_t kernel_w,
                     int32_t stride_h, int32_t stride_w,
                     int32_t pad_h, int32_t pad_w) {
    /* Calculate output dimensions */
    int32_t out_h = (height + 2 * pad_h - kernel_h) / stride_h + 1;
    int32_t out_w = (width + 2 * pad_w - kernel_w) / stride_w + 1;
    
    /* col buffer size */
    int32_t col_size = channels * kernel_h * kernel_w * out_h * out_w;
    
    for (int c = 0; c < channels; c++) {
        for (int kh = 0; kh < kernel_h; kh++) {
            for (int kw = 0; kw < kernel_w; kw++) {
                for (int oh = 0; oh < out_h; oh++) {
                    for (int ow = 0; ow < out_w; ow++) {
                        int32_t ih = oh * stride_h + kh - pad_h;
                        int32_t iw = ow * stride_w + kw - pad_w;
                        
                        float val = 0.0f;
                        if (ih >= 0 && ih < height && iw >= 0 && iw < width) {
                            val = input[c * height * width + ih * width + iw];
                        }
                        col[c * kernel_h * kernel_w * out_h * out_w +
                            kh * kernel_w * out_h * out_w +
                            kw * out_h * out_w +
                            oh * out_w + ow] = val;
                    }
                }
            }
        }
    }
    
    return col_size;
}

int ei_run_conv2d(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer) {
    if (!input || !output || !layer || !layer->weights) return EI_ERR_OP;
    
    const float *in_data = (const float *)input->data;
    float *out_data = (float *)output->data;
    const float *weights = (const float *)layer->weights->data;
    const float *bias = layer->bias ? (const float *)layer->bias->data : NULL;
    
    /* Input shape: [N, C_in, H_in, W_in] */
    int32_t n = input->dims[0];
    int32_t c_in = input->dims[1];
    int32_t h_in = input->dims[2];
    int32_t w_in = input->dims[3];
    
    /* Output shape: [N, C_out, H_out, W_out] */
    int32_t c_out = layer->weights->dims[0];
    int32_t h_out = output->dims[2];
    int32_t w_out = output->dims[3];
    
    /* Filter shape: [C_out, C_in, K_h, K_w] */
    int32_t k_h = layer->params.conv.kernel_h;
    int32_t k_w = layer->params.conv.kernel_w;
    
    /* For INT8 weights, dequantize on the fly */
    const int8_t *int8_weights = NULL;
    const float *w_scales = layer->weight_scales;
    int32_t num_scales = layer->num_weight_scales;
    
    if (layer->weights->type == EI_TENSOR_INT8) {
        int8_weights = (const int8_t *)layer->weights->data;
    }
    
    /* Process each batch item */
    for (int b = 0; b < n; b++) {
        /* im2col: unfold input */
        int32_t col_size = c_in * k_h * k_w * h_out * w_out;
        float *col = (float *)malloc(col_size * sizeof(float));
        if (!col) return EI_ERR_MEM;
        
        ei_im2col(in_data + b * c_in * h_in * w_in,
                  (int32_t *)col, c_in, h_in, w_in,
                  k_h, k_w,
                  layer->params.conv.stride_h, layer->params.conv.stride_w,
                  layer->params.conv.pad_h, layer->params.conv.pad_w);
        
        /* Matrix multiply: output = col * weights^T */
        for (int co = 0; co < c_out; co++) {
            float sum = bias ? bias[co] : 0.0f;
            
            for (int ci = 0; ci < c_in * k_h * k_w; ci++) {
                float w_val;
                if (int8_weights) {
                    /* Per-channel dequantization */
                    w_val = int8_weights[co * (c_in * k_h * k_w) + ci] * w_scales[co];
                } else {
                    w_val = weights[co * (c_in * k_h * k_w) + ci];
                }
                sum += col[ci] * w_val;
            }
            
            out_data[b * c_out * h_out * w_out + co * h_out * w_out] += sum;
        }
        
        free(col);
    }
    
    return EI_OK;
}

/* --- Fully Connected Layer --- */

/**
 * Fully connected (dense) layer: y = x * W^T + b
 * 
 * This is essentially a matrix multiplication where every input
 * neuron connects to every output neuron. For embedded systems,
 * this is the most compute-intensive layer.
 * 
 * INT8 inference: x (FP32) * W (INT8) -> accumulator (INT32) -> output (FP32)
 * The INT32 accumulator prevents overflow during multiply-accumulate.
 */
int ei_run_fc(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer) {
    if (!input || !output || !layer || !layer->weights) return EI_ERR_OP;
    
    const float *in_data = (const float *)input->data;
    float *out_data = (float *)output->data;
    const float *weights = (const float *)layer->weights->data;
    const float *bias = layer->bias ? (const float *)layer->bias->data : NULL;
    
    int32_t n = input->dims[0];
    int32_t m = layer->params.fc.in_features;
    int32_t k = layer->params.fc.out_features;
    
    /* For INT8 weights */
    const int8_t *int8_weights = NULL;
    const float *w_scales = layer->weight_scales;
    int32_t num_scales = layer->num_weight_scales;
    
    if (layer->weights->type == EI_TENSOR_INT8) {
        int8_weights = (const int8_t *)layer->weights->data;
    }
    
    /* Matrix multiply: out = in * weights^T + bias */
    for (int i = 0; i < n * m; i += m) {
        float *row_out = out_data + (i / m) * k;
        
        for (int j = 0; j < k; j++) {
            float sum = bias ? bias[j] : 0.0f;
            
            for (int l = 0; l < m; l++) {
                float w_val;
                if (int8_weights) {
                    w_val = int8_weights[j * m + l] * w_scales[j];
                } else {
                    w_val = weights[j * m + l];
                }
                sum += in_data[i + l] * w_val;
            }
            
            row_out[j] = sum;
        }
    }
    
    return EI_OK;
}

/* --- Activation Functions --- */

/**
 * ReLU: f(x) = max(0, x)
 * 
 * The simplest activation function. It introduces non-linearity
 * by zeroing out negative values. Very common in hidden layers.
 * 
 * Edge AI benefit: No exponentials or divisions needed.
 */
int ei_run_relu(ei_tensor_t *input, ei_tensor_t *output) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    
    for (int i = 0; i < input->size; i++) {
        out[i] = in[i] > 0.0f ? in[i] : 0.0f;
    }
    
    return EI_OK;
}

/**
 * Sigmoid: f(x) = 1 / (1 + e^(-x))
 * 
 * Maps any input to (0, 1). Used for binary classification outputs.
 * 
 * Edge AI concern: exp() is expensive on embedded CPUs without FPU.
 * Consider lookup tables or approximations for deployment.
 */
int ei_run_sigmoid(ei_tensor_t *input, ei_tensor_t *output) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    
    for (int i = 0; i < input->size; i++) {
        out[i] = 1.0f / (1.0f + expf(-in[i]));
    }
    
    return EI_OK;
}

/**
 * Tanh: f(x) = (e^x - e^(-x)) / (e^x + e^(-x))
 * 
 * Maps any input to (-1, 1). Zero-centered, unlike ReLU.
 * Often used in RNNs and regression outputs.
 */
int ei_run_tanh(ei_tensor_t *input, ei_tensor_t *output) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    
    for (int i = 0; i < input->size; i++) {
        out[i] = tanhf(in[i]);
    }
    
    return EI_OK;
}

/**
 * Softmax: f(x_i) = e^(x_i) / sum(e^(x_j))
 * 
 * Converts logits to probabilities. Used in multi-class classification.
 * 
 * Numerical stability: Subtract max(x) before exp to avoid overflow.
 * This is critical for edge deployment where inputs may have large values.
 */
int ei_run_softmax(ei_tensor_t *input, ei_tensor_t *output) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    int32_t n = input->size;
    
    /* Find max for numerical stability */
    float max_val = in[0];
    for (int i = 1; i < n; i++) {
        if (in[i] > max_val) max_val = in[i];
    }
    
    /* Compute exp(x - max) and sum */
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        out[i] = expf(in[i] - max_val);
        sum += out[i];
    }
    
    /* Normalize */
    for (int i = 0; i < n; i++) {
        out[i] /= sum;
    }
    
    return EI_OK;
}

/* --- Pooling Layers --- */

/**
 * Max Pooling: f(x) = max(patch)
 * 
 * Reduces spatial dimensions by taking the maximum value in each
 * pooling window. Provides translation invariance and reduces
 * computation for subsequent layers.
 * 
 * Edge AI benefit: Reduces model size and computation.
 * Commonly used after convolution layers.
 */
int ei_run_max_pool(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    
    int32_t n = input->dims[0];
    int32_t c = input->dims[1];
    int32_t h_in = input->dims[2];
    int32_t w_in = input->dims[3];
    int32_t h_out = output->dims[2];
    int32_t w_out = output->dims[3];
    int32_t k_h = layer->params.pooling.kernel_h;
    int32_t k_w = layer->params.pooling.kernel_w;
    int32_t s_h = layer->params.pooling.stride_h;
    int32_t s_w = layer->params.pooling.stride_w;
    int32_t p_h = layer->params.pooling.pad_h;
    int32_t p_w = layer->params.pooling.pad_w;
    
    for (int b = 0; b < n; b++) {
        for (int ch = 0; ch < c; ch++) {
            for (int oh = 0; oh < h_out; oh++) {
                for (int ow = 0; ow < w_out; ow++) {
                    float max_val = -FLT_MAX;
                    
                    for (int kh = 0; kh < k_h; kh++) {
                        for (int kw = 0; kw < k_w; kw++) {
                            int32_t ih = oh * s_h + kh - p_h;
                            int32_t iw = ow * s_w + kw - p_w;
                            
                            if (ih >= 0 && ih < h_in && iw >= 0 && iw < w_in) {
                                float val = in[(b * c + ch) * h_in * w_in + ih * w_in + iw];
                                if (val > max_val) max_val = val;
                            }
                        }
                    }
                    
                    out[(b * c + ch) * h_out * w_out + oh * w_out + ow] = max_val;
                }
            }
        }
    }
    
    return EI_OK;
}

/**
 * Average Pooling: f(x) = mean(patch)
 * 
 * Similar to max pooling but takes the average. Less common than
 * max pooling but can be useful for global average pooling (GAP)
 * before classification layers.
 * 
 * Edge AI benefit: GAP replaces fully connected layers,
 * dramatically reducing model size.
 */
int ei_run_avg_pool(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    
    int32_t n = input->dims[0];
    int32_t c = input->dims[1];
    int32_t h_in = input->dims[2];
    int32_t w_in = input->dims[3];
    int32_t h_out = output->dims[2];
    int32_t w_out = output->dims[3];
    int32_t k_h = layer->params.pooling.kernel_h;
    int32_t k_w = layer->params.pooling.kernel_w;
    int32_t s_h = layer->params.pooling.stride_h;
    int32_t s_w = layer->params.pooling.stride_w;
    int32_t p_h = layer->params.pooling.pad_h;
    int32_t p_w = layer->params.pooling.pad_w;
    
    int32_t pool_size = k_h * k_w;
    
    for (int b = 0; b < n; b++) {
        for (int ch = 0; ch < c; ch++) {
            for (int oh = 0; oh < h_out; oh++) {
                for (int ow = 0; ow < w_out; ow++) {
                    float sum = 0.0f;
                    
                    for (int kh = 0; kh < k_h; kh++) {
                        for (int kw = 0; kw < k_w; kw++) {
                            int32_t ih = oh * s_h + kh - p_h;
                            int32_t iw = ow * s_w + kw - p_w;
                            
                            if (ih >= 0 && ih < h_in && iw >= 0 && iw < w_in) {
                                sum += in[(b * c + ch) * h_in * w_in + ih * w_in + iw];
                            }
                        }
                    }
                    
                    out[(b * c + ch) * h_out * w_out + oh * w_out + ow] = sum / pool_size;
                }
            }
        }
    }
    
    return EI_OK;
}

/* --- Batch Normalization --- */

/**
 * Batch Normalization: y = (x - mean) / sqrt(var + eps) * gamma + beta
 * 
 * Normalizes layer inputs to have zero mean and unit variance.
 * This stabilizes training and allows higher learning rates.
 * 
 * At inference time, we use running mean/variance (stored in bias/weights).
 * For this learning project, we use the layer's bias as gamma and
 * weights as the running statistics.
 */
int ei_run_batch_norm(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    
    int32_t n = input->dims[0];
    int32_t c = input->dims[1];
    int32_t h = input->dims[2];
    int32_t w = input->dims[3];
    int32_t spatial_size = h * w;
    int32_t batch_size = n * spatial_size;
    
    /* Use layer weights as gamma (scale) and bias as beta (shift) */
    const float *gamma = layer->weights ? (const float *)layer->weights->data : NULL;
    const float *beta = layer->bias ? (const float *)layer->bias->data : NULL;
    
    if (!gamma || !beta) {
        /* Fallback: just copy input */
        memcpy(out, in, input->size * sizeof(float));
        return EI_OK;
    }
    
    /* Compute running mean and variance per channel */
    float *mean = (float *)calloc(c, sizeof(float));
    float *var = (float *)calloc(c, sizeof(float));
    if (!mean || !var) {
        free(mean);
        free(var);
        return EI_ERR_MEM;
    }
    
    for (int b = 0; b < n; b++) {
        for (int ch = 0; ch < c; ch++) {
            float ch_sum = 0.0f;
            for (int s = 0; s < spatial_size; s++) {
                ch_sum += in[b * c * spatial_size + ch * spatial_size + s];
            }
            mean[ch] = ch_sum / batch_size;
        }
    }
    
    for (int ch = 0; ch < c; ch++) {
        float var_sum = 0.0f;
        for (int b = 0; b < n; b++) {
            for (int s = 0; s < spatial_size; s++) {
                float diff = in[b * c * spatial_size + ch * spatial_size + s] - mean[ch];
                var_sum += diff * diff;
            }
        }
        var[ch] = var_sum / batch_size + 1e-5;  /* eps = 1e-5 */
    }
    
    /* Normalize: y = (x - mean) / sqrt(var) * gamma + beta */
    for (int b = 0; b < n; b++) {
        for (int ch = 0; ch < c; ch++) {
            float inv_std = 1.0f / sqrtf(var[ch]);
            for (int s = 0; s < spatial_size; s++) {
                int idx = b * c * spatial_size + ch * spatial_size + s;
                out[idx] = (in[idx] - mean[ch]) * inv_std * gamma[ch] + beta[ch];
            }
        }
    }
    
    free(mean);
    free(var);
    
    return EI_OK;
}

/* --- Flatten --- */

int ei_run_flatten(ei_tensor_t *input, ei_tensor_t *output) {
    const float *in = (const float *)input->data;
    float *out = (float *)output->data;
    
    /* Just copy data - shape changes but memory layout stays the same */
    memcpy(out, in, input->size * sizeof(float));
    
    return EI_OK;
}

/* ============================================================================
 * Quantization API
 * 
 * Quantization converts FP32 (float) values to INT8 (integer) values.
 * This is the key technique for deploying AI models on edge devices.
 * 
 * Why quantize?
 * - 4x memory reduction (4 bytes -> 1 byte)
 * - 2-4x faster inference (integer ops > float ops on most CPUs)
 * - Lower power consumption (integer math is more energy efficient)
 * 
 * Quantization formula:
 *   q = round(x / scale) + zero_point
 * 
 * Dequantization formula:
 *   x = (q - zero_point) * scale
 * 
 * Per-tensor: Single scale and zero_point for entire tensor
 * Per-channel: One scale and zero_point per output channel (more accurate)
 * ============================================================================ */

int ei_quantize_per_tensor(const ei_tensor_t *fp32_tensor, ei_tensor_t *int8_tensor,
                           float *scale, int32_t *zero_point) {
    if (!fp32_tensor || !int8_tensor || !scale || !zero_point) return EI_ERR_OP;
    
    const float *in = (const float *)fp32_tensor->data;
    int8_t *out = (int8_t *)int8_tensor->data;
    
    /* Find min and max for scale calculation */
    float min_val = in[0], max_val = in[0];
    for (int i = 1; i < fp32_tensor->size; i++) {
        if (in[i] < min_val) min_val = in[i];
        if (in[i] > max_val) max_val = in[i];
    }
    
    /* Calculate scale and zero point */
    /* INT8 range: [-128, 127], symmetric quantization preferred */
    float abs_max = fmaxf(fabsf(min_val), fabsf(max_val));
    *scale = abs_max / 127.0f;
    
    /* Asymmetric quantization with zero_point */
    *zero_point = (int32_t)roundf((0.0f - min_val) / *scale);
    *zero_point = fmaxf(-128, fminf(127, *zero_point));  /* Clamp to INT8 range */
    
    /* Quantize */
    for (int i = 0; i < fp32_tensor->size; i++) {
        int32_t q = (int32_t)roundf(in[i] / *scale) + *zero_point;
        out[i] = (int8_t)fmaxf(-128, fminf(127, (float)q));
    }
    
    return EI_OK;
}

int ei_dequantize_per_tensor(const ei_tensor_t *int8_tensor, ei_tensor_t *fp32_tensor,
                             float scale, int32_t zero_point) {
    if (!int8_tensor || !fp32_tensor) return EI_ERR_OP;
    
    const int8_t *in = (const int8_t *)int8_tensor->data;
    float *out = (float *)fp32_tensor->data;
    
    for (int i = 0; i < int8_tensor->size; i++) {
        out[i] = ((float)in[i] - (float)zero_point) * scale;
    }
    
    return EI_OK;
}

int ei_quantize_per_channel(const ei_tensor_t *fp32_tensor, ei_tensor_t *int8_tensor,
                            float *scales, int32_t *zero_points, int32_t num_channels) {
    if (!fp32_tensor || !int8_tensor || !scales || !zero_points || num_channels <= 0) {
        return EI_ERR_OP;
    }
    
    const float *in = (const float *)fp32_tensor->data;
    int8_t *out = (int8_t *)int8_tensor->data;
    
    int32_t elements_per_channel = fp32_tensor->size / num_channels;
    
    for (int ch = 0; ch < num_channels; ch++) {
        float min_val = in[ch * elements_per_channel];
        float max_val = in[ch * elements_per_channel];
        
        for (int i = 1; i < elements_per_channel; i++) {
            int idx = ch * elements_per_channel + i;
            if (in[idx] < min_val) min_val = in[idx];
            if (in[idx] > max_val) max_val = in[idx];
        }
        
        float abs_max = fmaxf(fabsf(min_val), fabsf(max_val));
        scales[ch] = abs_max / 127.0f;
        
        zero_points[ch] = (int32_t)roundf((0.0f - min_val) / scales[ch]);
        zero_points[ch] = fmaxf(-128, fminf(127, zero_points[ch]));
        
        for (int i = 0; i < elements_per_channel; i++) {
            int idx = ch * elements_per_channel + i;
            int32_t q = (int32_t)roundf(in[idx] / scales[ch]) + zero_points[ch];
            out[idx] = (int8_t)fmaxf(-128, fminf(127, (float)q));
        }
    }
    
    return EI_OK;
}

int ei_dequantize_per_channel(const ei_tensor_t *int8_tensor, ei_tensor_t *fp32_tensor,
                              const float *scales, const int32_t *zero_points, int32_t num_channels) {
    if (!int8_tensor || !fp32_tensor || !scales || !zero_points) return EI_ERR_OP;
    
    const int8_t *in = (const int8_t *)int8_tensor->data;
    float *out = (float *)fp32_tensor->data;
    
    int32_t elements_per_channel = int8_tensor->size / num_channels;
    
    for (int ch = 0; ch < num_channels; ch++) {
        for (int i = 0; i < elements_per_channel; i++) {
            int idx = ch * elements_per_channel + i;
            out[idx] = ((float)in[idx] - (float)zero_points[ch]) * scales[ch];
        }
    }
    
    return EI_OK;
}

int ei_compute_per_tensor_params(const ei_tensor_t *fp32_tensor,
                                 float *scale, int32_t *zero_point) {
    if (!fp32_tensor || !scale || !zero_point) return EI_ERR_OP;
    
    const float *data = (const float *)fp32_tensor->data;
    
    float min_val = data[0], max_val = data[0];
    for (int i = 1; i < fp32_tensor->size; i++) {
        if (data[i] < min_val) min_val = data[i];
        if (data[i] > max_val) max_val = data[i];
    }
    
    float abs_max = fmaxf(fabsf(min_val), fabsf(max_val));
    *scale = abs_max / 127.0f;
    *zero_point = (int32_t)roundf((0.0f - min_val) / *scale);
    *zero_point = fmaxf(-128, fminf(127, *zero_point));
    
    return EI_OK;
}

int ei_compute_per_channel_params(const ei_tensor_t *fp32_tensor,
                                  float *scales, int32_t *zero_points, int32_t num_channels) {
    if (!fp32_tensor || !scales || !zero_points || num_channels <= 0) return EI_ERR_OP;
    
    const float *data = (const float *)fp32_tensor->data;
    int32_t elements_per_channel = fp32_tensor->size / num_channels;
    
    for (int ch = 0; ch < num_channels; ch++) {
        float min_val = data[ch * elements_per_channel];
        float max_val = data[ch * elements_per_channel];
        
        for (int i = 1; i < elements_per_channel; i++) {
            int idx = ch * elements_per_channel + i;
            if (data[idx] < min_val) min_val = data[idx];
            if (data[idx] > max_val) max_val = data[idx];
        }
        
        float abs_max = fmaxf(fabsf(min_val), fabsf(max_val));
        scales[ch] = abs_max / 127.0f;
        
        zero_points[ch] = (int32_t)roundf((0.0f - min_val) / scales[ch]);
        zero_points[ch] = fmaxf(-128, fminf(127, zero_points[ch]));
    }
    
    return EI_OK;
}

int ei_model_quantize(ei_model_t *model, ei_quantization_type_t quant_type) {
    if (!model) return EI_ERR_OP;
    
    model->quant_type = quant_type;
    
    /* Allocate quantization buffers */
    float *fp32_buffer = (float *)malloc(model->inputs[0].size * sizeof(float));
    int8_t *int8_buffer = (int8_t *)malloc(model->inputs[0].size * sizeof(int8_t));
    if (!fp32_buffer || !int8_buffer) {
        free(fp32_buffer);
        free(int8_buffer);
        return EI_ERR_MEM;
    }
    
    /* Quantize each layer's weights */
    for (int i = 0; i < model->layer_count; i++) {
        ei_layer_t *layer = &model->layers[i];
        
        if (!layer->weights) continue;
        
        if (layer->weights->type == EI_TENSOR_FP32) {
            /* Allocate INT8 weight tensor */
            int32_t w_shape[4];
            for (int d = 0; d < 4; d++) w_shape[d] = layer->weights->dims[d];
            
            layer->weights = (ei_tensor_t *)realloc(layer->weights, sizeof(ei_tensor_t));
            ei_tensor_alloc(layer->weights, w_shape, 4, EI_TENSOR_INT8);
            
            if (quant_type == EI_QUANT_PER_TENSOR) {
                ei_quantize_per_tensor(layer->weights, layer->weights,
                                       &model->model_scale, &model->model_zero_point);
                layer->num_weight_scales = 1;
                layer->weight_scales = (float *)malloc(sizeof(float));
                layer->weight_scales[0] = model->model_scale;
            } else {
                /* Per-channel: one scale per output channel */
                int32_t out_channels = layer->weights->dims[0];
                layer->num_weight_scales = out_channels;
                layer->weight_scales = (float *)malloc(out_channels * sizeof(float));
                
                int8_t *tmp_int8 = (int8_t *)malloc(layer->weights->size * sizeof(int8_t));
                int32_t *tmp_zp = (int32_t *)malloc(out_channels * sizeof(int32_t));
                
                ei_quantize_per_channel(layer->weights,
                                        (ei_tensor_t){.data = tmp_int8, .size = layer->weights->size},
                                        layer->weight_scales, tmp_zp, out_channels);
                
                free(tmp_int8);
                free(tmp_zp);
            }
            
            layer->weights_quantized = true;
        }
    }
    
    free(fp32_buffer);
    free(int8_buffer);
    
    return EI_OK;
}

/* ============================================================================
 * Utility Functions
 * ============================================================================ */

void ei_tensor_print(const ei_tensor_t *tensor) {
    if (!tensor) {
        printf("  [Tensor] NULL\n");
        return;
    }
    
    const char *type_str;
    switch (tensor->type) {
        case EI_TENSOR_FP32:  type_str = "FP32"; break;
        case EI_TENSOR_INT8:  type_str = "INT8"; break;
        case EI_TENSOR_INT32: type_str = "INT32"; break;
        case EI_TENSOR_UINT8: type_str = "UINT8"; break;
        default: type_str = "UNKNOWN"; break;
    }
    
    printf("  [Tensor] type=%s, shape=[", type_str);
    for (int i = 0; i < tensor->ndims; i++) {
        printf("%d", tensor->dims[i]);
        if (i < tensor->ndims - 1) printf(", ");
    }
    printf("], size=%d", tensor->size);
    
    if (tensor->type == EI_TENSOR_INT8) {
        printf(", scale=%.6f, zp=%d", tensor->scale, tensor->zero_point);
    }
    
    printf("\n");
}

void ei_model_print(const ei_model_t *model) {
    if (!model) return;
    
    printf("=== Model: %s (v%s) ===\n", model->name, model->version);
    printf("  Layers: %d\n", model->layer_count);
    printf("  Quantization: ");
    switch (model->quant_type) {
        case EI_QUANT_NONE: printf("None (FP32)\n"); break;
        case EI_QUANT_PER_TENSOR: printf("Per-tensor INT8\n"); break;
        case EI_QUANT_PER_CHANNEL: printf("Per-channel INT8\n"); break;
    }
    
    if (model->input_count > 0) {
        printf("  Input shape: [");
        for (int i = 0; i < 4; i++) {
            printf("%d", model->inputs[0].dims[i]);
            if (i < 3) printf(", ");
        }
        printf("]\n");
    }
    
    printf("\n  Layers:\n");
    for (int i = 0; i < model->layer_count; i++) {
        ei_layer_print(&model->layers[i]);
    }
    printf("\n");
}

void ei_layer_print(const ei_layer_t *layer) {
    if (!layer) return;
    
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
        case EI_LAYER_BATCH_NORM:     type_str = "BatchNorm"; break;
        case EI_LAYER_FLATTEN:        type_str = "Flatten"; break;
        default:                      type_str = "Unknown"; break;
    }
    
    printf("    [%d] %s (%s)", layer->layer_index, layer->name, type_str);
    
    if (layer->weights) {
        printf(", weights=%d", layer->weights->size);
        if (layer->weights_quantized) {
            printf(" [INT8, channels=%d]", layer->num_weight_scales);
        }
    }
    
    if (layer->bias) {
        printf(", bias=%d", layer->bias->size);
    }
    
    printf("\n");
}

int ei_tensor_fill(ei_tensor_t *tensor, float value) {
    if (!tensor || !tensor->data) return EI_ERR_OP;
    
    float *data = (float *)tensor->data;
    for (int i = 0; i < tensor->size; i++) {
        data[i] = value;
    }
    
    return EI_OK;
}

int ei_tensor_copy_from_float(ei_tensor_t *tensor, const float *data, size_t count) {
    if (!tensor || !data || !tensor->data) return EI_ERR_OP;
    if (count > (size_t)tensor->size) return EI_ERR_SHAPE;
    
    float *target = (float *)tensor->data;
    memcpy(target, data, count * sizeof(float));
    
    return EI_OK;
}

int ei_tensor_copy_to_float(const ei_tensor_t *tensor, float *data, size_t count) {
    if (!tensor || !data || !tensor->data) return EI_ERR_OP;
    if (count > (size_t)tensor->size) return EI_ERR_SHAPE;
    
    const float *source = (const float *)tensor->data;
    memcpy(data, source, count * sizeof(float));
    
    return EI_OK;
}

int ei_tensor_compare(const ei_tensor_t *a, const ei_tensor_t *b, float tolerance) {
    if (!a || !b || a->size != b->size || a->type != b->type) {
        return -1;
    }
    
    const float *fa = (const float *)a->data;
    const float *fb = (const float *)b->data;
    
    int max_diff_idx = 0;
    float max_diff = 0.0f;
    
    for (int i = 0; i < a->size; i++) {
        float diff = fabsf(fa[i] - fb[i]);
        if (diff > max_diff) {
            max_diff = diff;
            max_diff_idx = i;
        }
        if (diff > tolerance) {
            printf("  [Compare] Mismatch at index %d: %.6f vs %.6f (diff=%.6f)\n",
                   i, fa[i], fb[i], diff);
        }
    }
    
    if (max_diff > tolerance) {
        printf("  [Compare] Max diff: %.6f at index %d (tolerance: %.6f)\n",
               max_diff, max_diff_idx, tolerance);
        return -1;
    }
    
    printf("  [Compare] OK (max diff: %.6e)\n", max_diff);
    return 1;
}

/* ============================================================================
 * Benchmarking
 * ============================================================================ */

int64_t ei_benchmark_layer(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer, int32_t iterations) {
    if (!layer || iterations <= 0) return -1;
    
    double total_ms = 0.0;
    
    for (int i = 0; i < iterations; i++) {
        double start = ei_get_time_ms();
        
        switch (layer->type) {
            case EI_LAYER_CONV2D:
                ei_run_conv2d(input, output, layer);
                break;
            case EI_LAYER_FULLY_CONNECTED:
                ei_run_fc(input, output, layer);
                break;
            case EI_LAYER_RELU:
                ei_run_relu(input, output);
                break;
            case EI_LAYER_SIGMOID:
                ei_run_sigmoid(input, output);
                break;
            case EI_LAYER_TANH:
                ei_run_tanh(input, output);
                break;
            case EI_LAYER_SOFTMAX:
                ei_run_softmax(input, output);
                break;
            case EI_LAYER_MAX_POOL:
                ei_run_max_pool(input, output, layer);
                break;
            case EI_LAYER_AVG_POOL:
                ei_run_avg_pool(input, output, layer);
                break;
            default:
                break;
        }
        
        double end = ei_get_time_ms();
        total_ms += (end - start);
    }
    
    return (int64_t)(total_ms / iterations * 1000);  /* Return microseconds */
}

int64_t ei_benchmark_model(ei_model_t *model, ei_tensor_t *input, int32_t iterations) {
    if (!model || !input || iterations <= 0) return -1;
    
    double total_ms = 0.0;
    
    for (int i = 0; i < iterations; i++) {
        double start = ei_get_time_ms();
        ei_model_infer(model, input, input);  /* Use input as output buffer */
        double end = ei_get_time_ms();
        total_ms += (end - start);
    }
    
    return (int64_t)(total_ms / iterations * 1000);
}
