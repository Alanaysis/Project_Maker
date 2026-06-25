#version 450 core
/**
 * 遮挡剔除着色器
 *
 * 功能：
 * - 层次遮挡剔除
 * - GPU 驱动剔除
 * - Hi-Z 缓冲区
 */

layout(local_size_x = 64) in;

// 物体结构
struct ObjectData {
    vec4 boundingSphere;
    vec4 aabbMin;
    vec4 aabbMax;
    uint meshIndex;
    uint visible;
    uint occluded;
    uint _padding;
};

// 缓冲区
layout(std430, binding = 0) buffer ObjectBuffer {
    ObjectData objects[];
};

layout(std430, binding = 1) buffer ResultBuffer {
    uint visibilityResults[];
};

// Hi-Z 深度纹理
uniform sampler2D uHiZTexture;
uniform uint uNumObjects;
uniform mat4 uViewProjection;
uniform vec2 uScreenSize;
uniform int uHiZLevels;

// 屏幕空间包围盒
struct ScreenAABB {
    vec2 min;
    vec2 max;
    float minDepth;
};

// 计算屏幕空间 AABB
ScreenAABB computeScreenAABB(vec4 aabbMin, vec4 aabbMax) {
    // 将 AABB 投影到屏幕空间
    vec4 corners[8];
    corners[0] = uViewProjection * vec4(aabbMin.xyz, 1.0);
    corners[1] = uViewProjection * vec4(aabbMax.x, aabbMin.yz, 1.0);
    corners[2] = uViewProjection * vec4(aabbMin.x, aabbMax.y, aabbMin.z, 1.0);
    corners[3] = uViewProjection * vec4(aabbMax.xy, aabbMin.z, 1.0);
    corners[4] = uViewProjection * vec4(aabbMin.xy, aabbMax.z, 1.0);
    corners[5] = uViewProjection * vec4(aabbMax.x, aabbMin.y, aabbMax.z, 1.0);
    corners[6] = uViewProjection * vec4(aabbMin.x, aabbMax.yz, 1.0);
    corners[7] = uViewProjection * vec4(aabbMax.xyz, 1.0);

    ScreenAABB aabb;
    aabb.min = vec2(1.0);
    aabb.max = vec2(-1.0);
    aabb.minDepth = 1.0;

    for (int i = 0; i < 8; i++) {
        vec3 ndc = corners[i].xyz / corners[i].w;
        aabb.min = min(aabb.min, ndc.xy);
        aabb.max = max(aabb.max, ndc.xy);
        aabb.minDepth = min(aabb.minDepth, ndc.z);
    }

    // 转换到像素坐标
    aabb.min = (aabb.min * 0.5 + 0.5) * uScreenSize;
    aabb.max = (aabb.max * 0.5 + 0.5) * uScreenSize;

    return aabb;
}

// Hi-Z 遮挡测试
bool isOccluded(ScreenAABB aabb) {
    // 选择合适的 mip 级别
    vec2 size = aabb.max - aabb.min;
    float maxDim = max(size.x, size.y);
    int mipLevel = min(int(log2(maxDim)), uHiZLevels - 1);

    // 在 Hi-Z 缓冲区中采样
    vec2 center = (aabb.min + aabb.max) * 0.5 / uScreenSize;
    float depth = textureLod(uHiZTexture, center, float(mipLevel)).r;

    // 比较深度
    return aabb.minDepth > depth;
}

void main() {
    uint index = gl_GlobalInvocationID.x;
    if (index >= uNumObjects) return;

    ObjectData obj = objects[index];

    // 计算屏幕空间 AABB
    ScreenAABB screenAABB = computeScreenAABB(obj.aabbMin, obj.aabbMax);

    // 检查是否在屏幕内
    if (screenAABB.max.x < 0.0 || screenAABB.max.y < 0.0 ||
        screenAABB.min.x > uScreenSize.x || screenAABB.min.y > uScreenSize.y) {
        objects[index].visible = 0;
        objects[index].occluded = 1;
        visibilityResults[index] = 0;
        return;
    }

    // Hi-Z 遮挡测试
    if (isOccluded(screenAABB)) {
        objects[index].visible = 0;
        objects[index].occluded = 1;
        visibilityResults[index] = 0;
        return;
    }

    // 可见
    objects[index].visible = 1;
    objects[index].occluded = 0;
    visibilityResults[index] = 1;
}
