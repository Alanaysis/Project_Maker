#version 450 core
/**
 * 粒子更新着色器
 *
 * 功能：
 * - 位置更新
 * - 速度更新 (重力、风力)
 * - 生命值更新
 * - 颜色/大小插值
 * - 粒子回收
 */

layout(local_size_x = 256) in;

// 粒子结构
struct Particle {
    vec4 position;      // xyz: 位置, w: 生命值
    vec4 velocity;      // xyz: 速度, w: 年龄
    vec4 color;         // rgba: 颜色
    vec4 size;          // x: 当前大小, y: 初始大小, z: 最大大小, w: 随机种子
};

// 缓冲区
layout(std430, binding = 0) buffer ParticleBuffer {
    Particle particles[];
};

layout(std430, binding = 1) buffer CounterBuffer {
    uint aliveCount;
    uint deadCount;
    uint emitCount;
};

// Uniform
uniform float uDeltaTime;
uniform vec3 uGravity;
uniform vec3 uWind;
uniform float uDrag;
uniform vec4 uStartColor;
uniform vec4 uEndColor;
uniform float uStartSize;
uniform float uEndSize;
uniform float uParticleLifetime;
uniform vec3 uTurbulence;  // 湍流强度

// 随机扰动
vec3 turbulence(vec3 pos, float seed) {
    return vec3(
        sin(pos.x * 10.0 + seed) * cos(pos.z * 10.0 + seed),
        cos(pos.y * 10.0 + seed) * sin(pos.x * 10.0 + seed),
        sin(pos.z * 10.0 + seed) * cos(pos.y * 10.0 + seed)
    ) * uTurbulence;
}

void main() {
    uint index = gl_GlobalInvocationID.x;

    if (index >= aliveCount) return;

    Particle p = particles[index];

    // 更新年龄
    p.velocity.w += uDeltaTime;

    // 计算生命周期 t (0-1)
    float t = p.velocity.w / p.position.w;

    // 粒子死亡检查
    if (t >= 1.0) {
        // 标记为死亡 (移到死亡列表)
        p.position.w = -1.0;
        particles[index] = p;
        return;
    }

    // 物理更新
    // 速度 += (重力 + 风力 + 湍流) * 时间
    vec3 acceleration = uGravity + uWind;
    acceleration += turbulence(p.position.xyz, p.size.w);
    p.velocity.xyz += acceleration * uDeltaTime;

    // 阻尼
    p.velocity.xyz *= (1.0 - uDrag * uDeltaTime);

    // 位置更新
    p.position.xyz += p.velocity.xyz * uDeltaTime;

    // 颜色插值
    p.color = mix(uStartColor, uEndColor, t);

    // 大小插值
    p.size.x = mix(p.size.y, p.size.z, t);

    particles[index] = p;
}
