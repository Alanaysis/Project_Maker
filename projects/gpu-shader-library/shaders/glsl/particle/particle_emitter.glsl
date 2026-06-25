#version 450 core
/**
 * 粒子发射着色器
 *
 * 功能：
 * - GPU 粒子发射
 * - 随机位置/速度生成
 * - 多种发射形状
 *
 * 使用计算着色器实现
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
uniform vec3 uEmitterPosition;
uniform vec3 uEmitterDirection;
uniform float uEmitRate;
uniform float uParticleLifetime;
uniform float uInitialSpeed;
uniform float uSpread;
uniform vec4 uStartColor;
uniform vec4 uEndColor;
uniform float uStartSize;
uniform float uEndSize;
uniform int uEmitterShape;  // 0: 点, 1: 圆, 2: 球, 3: 锥

// 随机数生成
float random(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

vec3 randomDirection(vec2 seed) {
    float theta = random(seed) * 6.28318;
    float phi = acos(2.0 * random(seed + vec2(1.0)) - 1.0);
    return vec3(
        sin(phi) * cos(theta),
        sin(phi) * sin(theta),
        cos(phi)
    );
}

// 发射形状
vec3 getEmitterPosition(vec2 seed) {
    switch (uEmitterShape) {
        case 0: // 点发射器
            return uEmitterPosition;
        case 1: // 圆形发射器
            float angle = random(seed) * 6.28318;
            float radius = sqrt(random(seed + vec2(1.0)));
            return uEmitterPosition + vec3(cos(angle), 0.0, sin(angle)) * radius;
        case 2: // 球形发射器
            return uEmitterPosition + randomDirection(seed);
        case 3: // 锥形发射器
            float coneAngle = uSpread * 3.14159 / 180.0;
            vec3 dir = mix(uEmitterDirection, randomDirection(seed), coneAngle);
            return uEmitterPosition + normalize(dir);
        default:
            return uEmitterPosition;
    }
}

void main() {
    uint index = gl_GlobalInvocationID.x;

    if (index >= emitCount) return;

    // 生成随机种子
    vec2 seed = vec2(float(index), uDeltaTime * 1000.0);

    // 初始化粒子
    Particle p;
    p.position = vec4(getEmitterPosition(seed), uParticleLifetime);
    p.velocity = vec4(randomDirection(seed + vec2(2.0)) * uInitialSpeed, 0.0);
    p.color = uStartColor;
    p.size = vec4(uStartSize, uStartSize, uEndSize, random(seed));

    particles[index] = p;
}
