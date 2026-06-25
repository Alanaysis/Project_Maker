#version 450 core
/**
 * 计算着色器 - 前缀和 (Prefix Sum / Scan)
 *
 * 功能：
 * - 并行前缀和计算
 * - 工作组内 Blelloch 扫描
 * - 支持任意大小数组
 *
 * 用法：
 * - 第一遍：工作组内扫描
 * - 第二遍：工作组间偏移
 */

layout(local_size_x = 256) in;

// 缓冲区
layout(std430, binding = 0) buffer InputBuffer {
    float inputData[];
};

layout(std430, binding = 1) buffer OutputBuffer {
    float outputData[];
};

layout(std430, binding = 2) buffer AuxBuffer {
    float auxData[];  // 存储每个工作组的总和
};

shared float sharedData[gl_WorkGroupSize.x * 2];

uniform uint uArraySize;
uniform bool uAddBlockOffset;

void main() {
    uint tid = gl_LocalInvocationID.x;
    uint gid = gl_GlobalInvocationID.x;
    uint blockSize = gl_WorkGroupSize.x;

    // 加载数据到共享内存
    uint ai = tid;
    uint bi = tid + blockSize;
    uint baseIdx = gl_WorkGroupID.x * blockSize * 2;

    sharedData[ai] = (baseIdx + ai < uArraySize) ? inputData[baseIdx + ai] : 0.0;
    sharedData[bi] = (baseIdx + bi < uArraySize) ? inputData[baseIdx + bi] : 0.0;

    // Up-sweep (reduce) 阶段
    uint offset = 1;
    for (uint d = blockSize; d > 0; d >>= 1) {
        barrier();
        memoryBarrierShared();

        if (tid < d) {
            uint left = offset * (2 * tid + 1) - 1;
            uint right = offset * (2 * tid + 2) - 1;
            sharedData[right] += sharedData[left];
        }
        offset <<= 1;
    }

    // 保存工作组总和
    if (tid == 0) {
        auxData[gl_WorkGroupID.x] = sharedData[blockSize * 2 - 1];
        sharedData[blockSize * 2 - 1] = 0.0;
    }

    // Down-sweep 阶段
    for (uint d = 1; d < blockSize * 2; d <<= 1) {
        offset >>= 1;
        barrier();
        memoryBarrierShared();

        if (tid < d) {
            uint left = offset * (2 * tid + 1) - 1;
            uint right = offset * (2 * tid + 2) - 1;
            float temp = sharedData[left];
            sharedData[left] = sharedData[right];
            sharedData[right] += temp;
        }
    }

    barrier();
    memoryBarrierShared();

    // 写回结果
    if (baseIdx + ai < uArraySize) {
        outputData[baseIdx + ai] = sharedData[ai];
    }
    if (baseIdx + bi < uArraySize) {
        outputData[baseIdx + bi] = sharedData[bi];
    }
}
