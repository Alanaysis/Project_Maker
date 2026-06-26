/**
 * edge-inference - Edge AI Inference Engine (边缘推理引擎)
 * 
 * A learning project implementing an embedded AI inference engine in C.
 * Covers model loading, tensor management, quantization, and inference.
 * 
 * Core Loop: 模型加载 → 量化处理 → 推理执行 → 结果输出
 * 
 * Learning Goals:
 * - Understand Edge AI fundamentals
 * - Master model quantization techniques
 * - Learn inference optimization for embedded systems
 */

#ifndef EDGE_INFERENCE_H
#define EDGE_INFERENCE_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* ============================================================================
 * 1. Error Codes
 * ============================================================================ */
#define EI_OK              0
#define EI_ERR_MEM        -1
#define EI_ERR_FORMAT     -2
#define EI_ERR_SHAPE      -3
#define EI_ERR_OP         -4
#define EI_ERR_QUANT      -5
#define EI_ERR_IO         -6
#define EI_ERR_MAGIC      -7

/* ============================================================================
 * 2. Tensor Data Structure
 * 
 * A tensor is the fundamental data structure in neural networks.
 * It holds multi-dimensional arrays of numbers (weights, activations).
 * 
 * For edge AI, we support:
 * - FP32: Full precision (training/reference)
 * - INT8: Quantized (inference, 4x memory reduction)
 * ============================================================================ */
typedef enum {
    EI_TENSOR_FP32 = 0,  /* float32 - reference/quantization source */
    EI_TENSOR_INT8  = 1,  /* int8   - quantized inference */
    EI_TENSOR_INT32 = 2,  /* int32  - accumulator for quantized ops */
    EI_TENSOR_UINT8 = 3,  /* uint8  - unsigned quantization */
} ei_tensor_type_t;

/* Maximum tensor dimensions for edge devices */
#define EI_MAX_DIMS 4

typedef struct {
    int32_t dims[EI_MAX_DIMS];  /* Shape: e.g., [batch, channels, height, width] */
    int32_t ndims;              /* Number of dimensions */
    int32_t size;               /* Total number of elements */
    
    ei_tensor_type_t type;     /* Data type */
    
    void *data;                /* Pointer to tensor data (externally allocated) */
    
    /* Memory management */
    bool owns_data;            /* Should this tensor free data on destroy? */
    
    /* Quantization parameters (for INT8 tensors) */
    float scale;               /* Per-tensor scale factor */
    int32_t zero_point;        /* Zero point for asymmetric quantization */
} ei_tensor_t;

/* ============================================================================
 * 3. Layer Types
 * 
 * Neural network layer types supported by this inference engine.
 * Each layer performs a specific computation on input tensors.
 * ============================================================================ */
typedef enum {
    EI_LAYER_CONV2D    = 0,   /* 2D convolution (im2col based) */
    EI_LAYER_FULLY_CONNECTED = 1,  /* Fully connected / dense layer */
    EI_LAYER_RELU      = 2,   /* Rectified Linear Unit: max(0, x) */
    EI_LAYER_SIGMOID   = 3,   /* Sigmoid: 1 / (1 + exp(-x)) */
    EI_LAYER_TANH      = 4,   /* Hyperbolic tangent */
    EI_LAYER_SOFTMAX   = 5,   /* Softmax: exp(x_i) / sum(exp(x_j)) */
    EI_LAYER_MAX_POOL  = 6,   /* Max pooling */
    EI_LAYER_AVG_POOL  = 7,   /* Average pooling */
    EI_LAYER_ADD       = 8,   /* Element-wise addition (for residuals) */
    EI_LAYER_RESIZE    = 9,   /* Bilinear resize */
    EI_LAYER_FLATTEN   = 10,  /* Flatten tensor to 1D */
    EI_LAYER_BATCH_NORM = 11, /* Batch normalization */
    EI_LAYER_PRELU     = 12,  /* Parametric ReLU */
} ei_layer_type_t;

/* ============================================================================
 * 4. Convolution Layer Parameters
 * 
 * Convolution is the core operation in CNNs. It slides a filter over
 * the input to produce a feature map.
 * 
 * im2col approach: Unfold input into columns, then use matrix multiplication.
 * This converts convolutions to GEMM (General Matrix Multiply), which is
 * highly optimized on embedded CPUs with NEON/SIMD instructions.
 * ============================================================================ */
typedef struct {
    int32_t kernel_h;      /* Filter height */
    int32_t kernel_w;      /* Filter width */
    int32_t stride_h;      /* Vertical stride */
    int32_t stride_w;      /* Horizontal stride */
    int32_t pad_h;         /* Top/bottom padding */
    int32_t pad_w;         /* Left/right padding */
    int32_t dilation_h;    /* Vertical dilation */
    int32_t dilation_w;    /* Horizontal dilation */
    int32_t groups;        /* Number of groups (1 = standard conv) */
} ei_conv_params_t;

/* ============================================================================
 * 5. Fully Connected Layer Parameters
 * ============================================================================ */
typedef struct {
    int32_t in_features;   /* Input dimension */
    int32_t out_features;  /* Output dimension */
    bool use_bias;         /* Whether to add bias term */
} ei_fc_params_t;

/* ============================================================================
 * 6. Pooling Layer Parameters
 * ============================================================================ */
typedef struct {
    int32_t kernel_h;      /* Pooling window height */
    int32_t kernel_w;      /* Pooling window width */
    int32_t stride_h;      /* Vertical stride */
    int32_t stride_w;      /* Horizontal stride */
    int32_t pad_h;         /* Padding */
    int32_t pad_w;         /* Padding */
} ei_pooling_params_t;

/* ============================================================================
 * 7. Activation Parameters
 * ============================================================================ */
typedef struct {
    float alpha;           /* For PReLU: negative slope */
    float beta;            /* For tanh: scaling factor */
} ei_activation_params_t;

/* ============================================================================
 * 8. Layer Structure
 * 
 * Each layer contains:
 * - Type and name for identification
 * - Parameters specific to the layer type
 * - Weights and biases (stored as tensors)
 * - Quantization info for INT8 inference
 * ============================================================================ */
#define EI_LAYER_NAME_MAX 64

typedef struct {
    ei_layer_type_t type;
    char name[EI_LAYER_NAME_MAX];
    
    /* Parameters (union by layer type) */
    union {
        ei_conv_params_t conv;
        ei_fc_params_t fc;
        ei_pooling_params_t pooling;
        ei_activation_params_t activation;
    } params;
    
    /* Weights and biases */
    ei_tensor_t *weights;      /* Filter weights or weight matrix */
    ei_tensor_t *bias;         /* Optional bias vector */
    
    /* Quantization parameters for this layer */
    bool weights_quantized;    /* Are weights quantized to INT8? */
    float *weight_scales;      /* Per-channel scales for INT8 weights */
    int32_t num_weight_scales; /* Number of scale values (1 = per-tensor, out_channels = per-channel) */
    
    /* Layer metadata */
    int32_t layer_index;
} ei_layer_t;

/* ============================================================================
 * 9. Model Structure
 * 
 * A neural network model consists of:
 * - Metadata (name, version, input shape)
 * - Array of layers
 * - Quantization metadata
 * ============================================================================ */
#define EI_MAX_LAYERS 128
#define EI_MAX_INPUTS 4
#define EI_MAX_OUTPUTS 4

typedef enum {
    EI_QUANT_NONE    = 0,  /* No quantization (FP32) */
    EI_QUANT_PER_TENSOR = 1,  /* Per-tensor quantization (single scale) */
    EI_QUANT_PER_CHANNEL = 2, /* Per-channel quantization (one scale per output channel) */
} ei_quantization_type_t;

typedef struct {
    char name[64];
    char version[16];
    
    /* Input specifications */
    int32_t input_count;
    ei_tensor_t inputs[EI_MAX_INPUTS];
    
    /* Layer definitions */
    int32_t layer_count;
    ei_layer_t layers[EI_MAX_LAYERS];
    
    /* Output specifications */
    int32_t output_count;
    ei_tensor_t outputs[EI_MAX_OUTPUTS];
    
    /* Quantization metadata */
    ei_quantization_type_t quant_type;
    float model_scale;       /* Global scale for per-tensor quantization */
    int32_t model_zero_point; /* Global zero point */
    
    /* Runtime workspace (allocated during init) */
    void *workspace;
    size_t workspace_size;
    
    /* Temporary tensors for intermediate results */
    ei_tensor_t *temp_tensors;
    int32_t num_temp_tensors;
} ei_model_t;

/* ============================================================================
 * 10. Model File Format (Simple Binary Format)
 * 
 * Magic number + version + metadata + layer data
 * 
 * Header layout:
 * [4 bytes] Magic: 0x45494D4C ("EIML")
 * [4 bytes] Version: 1
 * [4 bytes] Layer count
 * [64 bytes] Model name
 * [16 bytes] Model version
 * [4 bytes] Input count
 * [4 * 4 bytes] Input shapes (4 dims per input)
 * [4 bytes] Quantization type
 * [4 bytes] Model scale (float)
 * [4 bytes] Model zero point (int32)
 * 
 * Each layer:
 * [4 bytes] Layer type
 * [64 bytes] Layer name
 * [4 bytes] Parameter block size
 * [param block] Parameters (type-specific)
 * [4 bytes] Weight count (elements)
 * [4 bytes] Weight type (0=FP32, 1=INT8)
 * [weight data] Raw weight bytes
 * [4 bytes] Bias count
 * [bias data] Raw bias bytes (if exists)
 * ============================================================================ */
#define EI_MODEL_MAGIC   0x45494D4C  /* "EIML" in ASCII */
#define EI_MODEL_VERSION 1

/* ============================================================================
 * 11. Public API
 * ============================================================================ */

/* --- Tensor API --- */

/** Create a tensor (data must be externally allocated) */
ei_tensor_t *ei_tensor_create(void);

/** Initialize a tensor with shape and type */
int ei_tensor_init(ei_tensor_t *tensor, int32_t *shape, int32_t ndims, ei_tensor_type_t type);

/** Allocate and initialize a tensor with its own data */
int ei_tensor_alloc(ei_tensor_t *tensor, int32_t *shape, int32_t ndims, ei_tensor_type_t type);

/** Free tensor and its data (if owns_data) */
void ei_tensor_free(ei_tensor_t *tensor);

/** Copy one tensor to another */
int ei_tensor_copy(const ei_tensor_t *src, ei_tensor_t *dst);

/** Get element size in bytes */
int32_t ei_tensor_elem_size(ei_tensor_type_t type);

/** Get tensor size in bytes */
size_t ei_tensor_data_size(const ei_tensor_t *tensor);

/** Set tensor data pointer (without taking ownership) */
int ei_tensor_set_data(ei_tensor_t *tensor, void *data, bool take_ownership);

/** Get element pointer at given indices */
void *ei_tensor_get_ptr(ei_tensor_t *tensor, int32_t *indices);

/* --- Model API --- */

/** Create an empty model */
ei_model_t *ei_model_create(void);

/** Load a model from a binary file */
int ei_model_load(ei_model_t *model, const char *filepath);

/** Save a model to a binary file */
int ei_model_save(const ei_model_t *model, const char *filepath);

/** Initialize model workspace */
int ei_model_init_workspace(ei_model_t *model);

/** Run inference on a single input */
int ei_model_infer(ei_model_t *model, ei_tensor_t *input, ei_tensor_t *output);

/** Run batch inference */
int ei_model_batch_infer(ei_model_t *model, ei_tensor_t *inputs, int32_t batch_size, ei_tensor_t *outputs);

/** Free model and all its resources */
void ei_model_free(ei_model_t *model);

/* --- Layer API --- */

/** Create a layer */
ei_layer_t *ei_layer_create(void);

/** Initialize a convolution layer */
int ei_layer_init_conv(ei_layer_t *layer, const char *name,
                       int32_t kernel_h, int32_t kernel_w,
                       int32_t stride_h, int32_t stride_w,
                       int32_t pad_h, int32_t pad_w,
                       int32_t dilation_h, int32_t dilation_w,
                       int32_t groups);

/** Initialize a fully connected layer */
int ei_layer_init_fc(ei_layer_t *layer, const char *name,
                     int32_t in_features, int32_t out_features, bool use_bias);

/** Initialize a pooling layer */
int ei_layer_init_pool(ei_layer_t *layer, const char *name,
                       ei_layer_type_t type,
                       int32_t kernel_h, int32_t kernel_w,
                       int32_t stride_h, int32_t stride_w,
                       int32_t pad_h, int32_t pad_w);

/** Initialize a ReLU layer */
int ei_layer_init_relu(ei_layer_t *layer, const char *name);

/** Initialize a sigmoid layer */
int ei_layer_init_sigmoid(ei_layer_t *layer, const char *name);

/** Initialize a tanh layer */
int ei_layer_init_tanh(ei_layer_t *layer, const char *name);

/** Initialize a softmax layer */
int ei_layer_init_softmax(ei_layer_t *layer, const char *name);

/** Free a layer (does not free weights/bias tensors) */
void ei_layer_free(ei_layer_t *layer);

/* --- Inference Operations --- */

/** Run a convolution layer */
int ei_run_conv2d(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer);

/** Run a fully connected layer */
int ei_run_fc(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer);

/** Run ReLU activation */
int ei_run_relu(ei_tensor_t *input, ei_tensor_t *output);

/** Run sigmoid activation */
int ei_run_sigmoid(ei_tensor_t *input, ei_tensor_t *output);

/** Run tanh activation */
int ei_run_tanh(ei_tensor_t *input, ei_tensor_t *output);

/** Run softmax activation */
int ei_run_softmax(ei_tensor_t *input, ei_tensor_t *output);

/** Run max pooling */
int ei_run_max_pool(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer);

/** Run average pooling */
int ei_run_avg_pool(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer);

/** Run batch normalization */
int ei_run_batch_norm(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer);

/** Run flatten */
int ei_run_flatten(ei_tensor_t *input, ei_tensor_t *output);

/* --- Quantization API --- */

/** Quantize FP32 tensor to INT8 (per-tensor) */
int ei_quantize_per_tensor(const ei_tensor_t *fp32_tensor, ei_tensor_t *int8_tensor,
                           float *scale, int32_t *zero_point);

/** Dequantize INT8 tensor back to FP32 (per-tensor) */
int ei_dequantize_per_tensor(const ei_tensor_t *int8_tensor, ei_tensor_t *fp32_tensor,
                             float scale, int32_t zero_point);

/** Quantize FP32 tensor to INT8 (per-channel) */
int ei_quantize_per_channel(const ei_tensor_t *fp32_tensor, ei_tensor_t *int8_tensor,
                            float *scales, int32_t *zero_points, int32_t num_channels);

/** Dequantize INT8 tensor back to FP32 (per-channel) */
int ei_dequantize_per_channel(const ei_tensor_t *int8_tensor, ei_tensor_t *fp32_tensor,
                              const float *scales, const int32_t *zero_points, int32_t num_channels);

/** Compute per-tensor quantization parameters (min-max method) */
int ei_compute_per_tensor_params(const ei_tensor_t *fp32_tensor,
                                 float *scale, int32_t *zero_point);

/** Compute per-channel quantization parameters (min-max method) */
int ei_compute_per_channel_params(const ei_tensor_t *fp32_tensor,
                                  float *scales, int32_t *zero_points, int32_t num_channels);

/** Quantize model weights from FP32 to INT8 */
int ei_model_quantize(ei_model_t *model, ei_quantization_type_t quant_type);

/* --- Utility Functions --- */

/** Print tensor info */
void ei_tensor_print(const ei_tensor_t *tensor);

/** Print model info */
void ei_model_print(const ei_model_t *model);

/** Print layer info */
void ei_layer_print(const ei_layer_t *layer);

/** Fill tensor with a value */
int ei_tensor_fill(ei_tensor_t *tensor, float value);

/** Copy FP32 data into tensor */
int ei_tensor_copy_from_float(ei_tensor_t *tensor, const float *data, size_t count);

/** Copy tensor data to FP32 buffer */
int ei_tensor_copy_to_float(const ei_tensor_t *tensor, float *data, size_t count);

/** Compare two tensors for equality (within tolerance) */
int ei_tensor_compare(const ei_tensor_t *a, const ei_tensor_t *b, float tolerance);

/* --- Performance Benchmarking --- */

/** Run a single layer inference and return time in microseconds */
int64_t ei_benchmark_layer(ei_tensor_t *input, ei_tensor_t *output, ei_layer_t *layer, int32_t iterations);

/** Run model inference and return time in microseconds */
int64_t ei_benchmark_model(ei_model_t *model, ei_tensor_t *input, int32_t iterations);

#endif /* EDGE_INFERENCE_H */
