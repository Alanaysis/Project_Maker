#version 450 core
/**
 * 间接渲染着色器
 *
 * 功能：
 * - GPU 驱动渲染
 * - 间接绘制命令
 * - 可见性剔除
 */

layout(local_size_x = 64) in;

// 间接绘制命令结构
struct DrawCommand {
    uint count;
    uint instanceCount;
    uint firstIndex;
    uint baseVertex;
    uint baseInstance;
};

// 物体结构
struct ObjectData {
    vec4 boundingSphere;  // xyz: 中心, w: 半径
    vec4 color;
    uint indexOffset;
    uint indexCount;
    uint visible;
    uint _padding;
};

// 缓冲区
layout(std430, binding = 0) buffer DrawCommandsBuffer {
    DrawCommand commands[];
};

layout(std430, binding = 1) buffer ObjectBuffer {
    ObjectData objects[];
};

layout(std430, binding = 2) buffer VisibleCountBuffer {
    uint visibleCount;
};

// Uniform
uniform mat4 uViewProjection;
uniform vec4 uFrustumPlanes[6];
uniform uint uNumObjects;
uniform float uLODDistances[4];
uniform uint uLODIndices[4];

// 视锥体剔除
bool isInsideFrustum(vec4 sphere) {
    for (int i = 0; i < 6; i++) {
        float dist = dot(uFrustumPlanes[i].xyz, sphere.xyz) + uFrustumPlanes[i].w;
        if (dist < -sphere.w) {
            return false;
        }
    }
    return true;
}

// LOD 选择
uint selectLOD(float distance) {
    for (int i = 3; i >= 0; i--) {
        if (distance > uLODDistances[i]) {
            return uLODIndices[i];
        }
    }
    return uLODIndices[0];
}

void main() {
    uint index = gl_GlobalInvocationID.x;
    if (index >= uNumObjects) return;

    ObjectData obj = objects[index];

    // 视锥体剔除
    if (!isInsideFrustum(obj.boundingSphere)) {
        objects[index].visible = 0;
        return;
    }

    // 标记为可见
    objects[index].visible = 1;

    // 原子递增可见计数
    uint drawIndex = atomicAdd(visibleCount, 1);

    // 计算 LOD
    vec3 viewPos = (uViewProjection * vec4(obj.boundingSphere.xyz, 1.0)).xyz;
    float distance = length(viewPos);
    uint lod = selectLOD(distance);

    // 填充间接绘制命令
    DrawCommand cmd;
    cmd.count = obj.indexCount;
    cmd.instanceCount = 1;
    cmd.firstIndex = obj.indexOffset;
    cmd.baseVertex = 0;
    cmd.baseInstance = index;

    commands[drawIndex] = cmd;
}
