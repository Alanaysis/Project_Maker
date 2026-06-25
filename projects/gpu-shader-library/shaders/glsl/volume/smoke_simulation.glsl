#version 450 core
/**
 * 烟雾模拟着色器 (计算着色器)
 *
 * 功能：
 * - Navier-Stokes 流体模拟
 * - 速度场更新
 * - 密度扩散
 * - 压力求解
 */

layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;

// 3D 纹理
layout(binding = 0, rgba32f) uniform image3D uVelocityField;
layout(binding = 1, r32f) uniform image3D uDensityField;
layout(binding = 2, r32f) uniform image3D uPressureField;
layout(binding = 3, r32f) uniform image3D uDivergenceField;

// Uniform
uniform float uDeltaTime;
uniform float uViscosity;         // 粘性
uniform float uDiffusion;         // 扩散率
uniform float uDissipation;       // 消散率
uniform vec3 uSmokeSource;        // 烟雾源位置
uniform float uSmokeRadius;       // 烟雾源半径
uniform float uSmokeAmount;       // 烟雾产生量
uniform vec3 uWindForce;          // 风力
uniform float uBuoyancy;          // 浮力

// 扩散步骤
void diffuse(ivec3 pos, ivec3 size) {
    float center = imageLoad(uDensityField, pos).r;
    float left = imageLoad(uDensityField, max(pos - ivec3(1, 0, 0), ivec3(0))).r;
    float right = imageLoad(uDensityField, min(pos + ivec3(1, 0, 0), size - 1)).r;
    float bottom = imageLoad(uDensityField, max(pos - ivec3(0, 1, 0), ivec3(0))).r;
    float top = imageLoad(uDensityField, min(pos + ivec3(0, 1, 0), size - 1)).r;
    float back = imageLoad(uDensityField, max(pos - ivec3(0, 0, 1), ivec3(0))).r;
    float front = imageLoad(uDensityField, min(pos + ivec3(0, 0, 1), size - 1)).r;

    float laplacian = left + right + bottom + top + back + front - 6.0 * center;
    float newDensity = center + uDiffusion * laplacian * uDeltaTime;

    imageStore(uDensityField, pos, vec4(newDensity));
}

// 平流步骤
void advect(ivec3 pos, ivec3 size) {
    vec3 velocity = imageLoad(uVelocityField, pos).xyz;
    vec3 prevPos = vec3(pos) - velocity * uDeltaTime;

    // 边界约束
    prevPos = clamp(prevPos, vec3(0.0), vec3(size - 1));

    // 三线性插值采样
    ivec3 p0 = ivec3(floor(prevPos));
    ivec3 p1 = min(p0 + 1, size - 1);
    vec3 frac = fract(prevPos);

    float d000 = imageLoad(uDensityField, p0).r;
    float d100 = imageLoad(uDensityField, ivec3(p1.x, p0.y, p0.z)).r;
    float d010 = imageLoad(uDensityField, ivec3(p0.x, p1.y, p0.z)).r;
    float d110 = imageLoad(uDensityField, ivec3(p1.x, p1.y, p0.z)).r;
    float d001 = imageLoad(uDensityField, ivec3(p0.x, p0.y, p1.z)).r;
    float d101 = imageLoad(uDensityField, ivec3(p1.x, p0.y, p1.z)).r;
    float d011 = imageLoad(uDensityField, ivec3(p0.x, p1.y, p1.z)).r;
    float d111 = imageLoad(uDensityField, p1).r;

    float density = mix(
        mix(mix(d000, d100, frac.x), mix(d010, d110, frac.x), frac.y),
        mix(mix(d001, d101, frac.x), mix(d011, d111, frac.x), frac.y),
        frac.z
    );

    density *= (1.0 - uDissipation * uDeltaTime);

    imageStore(uDensityField, pos, vec4(density));
}

// 添加烟雾源
void addSmoke(ivec3 pos) {
    vec3 posVec = vec3(pos);
    float dist = length(posVec - uSmokeSource);

    if (dist < uSmokeRadius) {
        float factor = 1.0 - dist / uSmokeRadius;
        float density = imageLoad(uDensityField, pos).r;
        density += uSmokeAmount * factor * uDeltaTime;
        imageStore(uDensityField, pos, vec4(density));

        // 添加浮力和风力
        vec3 velocity = imageLoad(uVelocityField, pos).xyz;
        velocity += (uWindForce + vec3(0.0, uBuoyancy * factor, 0.0)) * uDeltaTime;
        imageStore(uVelocityField, pos, vec4(velocity, 1.0));
    }
}

void main() {
    ivec3 pos = ivec3(gl_GlobalInvocationID);
    ivec3 size = imageSize(uDensityField);

    if (any(greaterThanEqual(pos, size))) return;

    // 添加烟雾源
    addSmoke(pos);

    // 扩散
    diffuse(pos, size);

    // 平流
    advect(pos, size);
}
