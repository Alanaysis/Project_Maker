#version 450 core
/**
 * LOD 计算着色器
 *
 * 功能：
 * - 基于距离的 LOD 选择
 * - 屏幕空间误差计算
 * - 自动 LOD 生成
 */

layout(local_size_x = 64) in;

// 网格 LOD 数据
struct MeshLOD {
    uint indexOffset;
    uint indexCount;
    float minDistance;
    float maxDistance;
    float screenSpaceError;
};

// 物体数据
struct ObjectData {
    vec4 boundingSphere;
    uint meshIndex;
    uint currentLOD;
    uint targetLOD;
    float lodTransition;
};

// 缓冲区
layout(std430, binding = 0) buffer ObjectBuffer {
    ObjectData objects[];
};

layout(std430, binding = 1) buffer LODBuffer {
    MeshLOD meshLODs[];
};

layout(std430, binding = 2) buffer DrawCommandBuffer {
    uint drawIndexCounts[];
};

// Uniform
uniform uint uNumObjects;
uniform uint uMaxLODLevels;
uniform vec3 uCameraPos;
uniform float uFOV;
uniform float uScreenHeight;
uniform float uLODBias;
uniform float uTransitionSpeed;

// 计算屏幕空间像素误差
float screenSpaceError(float worldSpaceError, float distance) {
    // 基于 FOV 的投影
    float pixelError = (worldSpaceError * uScreenHeight) / (2.0 * distance * tan(uFOV * 0.5));
    return pixelError;
}

// 选择最佳 LOD
uint selectBestLOD(uint meshIndex, float distance) {
    uint bestLOD = 0;

    for (uint lod = 0; lod < uMaxLODLevels; lod++) {
        uint lodIndex = meshIndex * uMaxLODLevels + lod;
        MeshLOD meshLOD = meshLODs[lodIndex];

        // 计算屏幕空间误差
        float sse = screenSpaceError(meshLOD.screenSpaceError, distance);

        // 如果误差可接受且在距离范围内
        if (sse < 1.0 && distance >= meshLOD.minDistance && distance <= meshLOD.maxDistance) {
            bestLOD = lod;
            break;
        }
    }

    return bestLOD;
}

void main() {
    uint index = gl_GlobalInvocationID.x;
    if (index >= uNumObjects) return;

    ObjectData obj = objects[index];

    // 计算距离
    float distance = length(obj.boundingSphere.xyz - uCameraPos) - obj.boundingSphere.w;
    distance = max(distance, 0.01);

    // 应用 LOD 偏差
    distance *= uLODBias;

    // 选择目标 LOD
    uint targetLOD = selectBestLOD(obj.meshIndex, distance);

    // LOD 过渡
    if (targetLOD != obj.currentLOD) {
        obj.lodTransition += uTransitionSpeed;
        if (obj.lodTransition >= 1.0) {
            obj.currentLOD = targetLOD;
            obj.lodTransition = 0.0;
        }
    } else {
        obj.lodTransition = 0.0;
    }

    obj.targetLOD = targetLOD;

    // 更新绘制命令
    uint lodIndex = obj.meshIndex * uMaxLODLevels + obj.currentLOD;
    drawIndexCounts[index] = meshLODs[lodIndex].indexCount;

    objects[index] = obj;
}
