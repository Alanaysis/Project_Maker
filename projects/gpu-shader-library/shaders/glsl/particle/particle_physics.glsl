#version 450 core
/**
 * 粒子物理模拟着色器
 *
 * 功能：
 * - 碰撞检测
 * - 碰撞响应
 * - 约束求解
 */

layout(local_size_x = 256) in;

// 粒子结构
struct Particle {
    vec4 position;
    vec4 velocity;
    vec4 color;
    vec4 size;
};

// 缓冲区
layout(std430, binding = 0) buffer ParticleBuffer {
    Particle particles[];
};

layout(std430, binding = 2) buffer CollisionBuffer {
    vec4 planes[];  // 碰撞平面 (xyz: 法线, w: 距离)
};

// Uniform
uniform float uDeltaTime;
uniform uint uNumParticles;
uniform uint uNumPlanes;
uniform float uRestitution;  // 弹性系数
uniform float uFriction;     // 摩擦系数

// 粒子-平面碰撞检测
bool planeCollision(vec3 pos, vec4 plane) {
    float dist = dot(pos, plane.xyz) + plane.w;
    return dist < 0.0;
}

// 碰撞响应
vec3 collisionResponse(vec3 pos, vec3 vel, vec4 plane) {
    float dist = dot(pos, plane.xyz) + plane.w;

    if (dist < 0.0) {
        // 修正位置
        pos -= plane.xyz * dist;

        // 反射速度
        float velDotN = dot(vel, plane.xyz);
        if (velDotN < 0.0) {
            vec3 velNormal = plane.xyz * velDotN;
            vec3 velTangent = vel - velNormal;
            vel = velTangent * uFriction - velNormal * uRestitution;
        }
    }

    return vel;
}

// 粒子-粒子碰撞
void particleCollision(inout Particle p1, inout Particle p2) {
    vec3 diff = p1.position.xyz - p2.position.xyz;
    float dist = length(diff);

    float minDist = (p1.size.x + p2.size.x) * 0.5;

    if (dist < minDist && dist > 0.001) {
        vec3 normal = diff / dist;
        float overlap = minDist - dist;

        // 分离粒子
        p1.position.xyz += normal * overlap * 0.5;
        p2.position.xyz -= normal * overlap * 0.5;

        // 速度交换 (简化弹性碰撞)
        vec3 relVel = p1.velocity.xyz - p2.velocity.xyz;
        float velAlongNormal = dot(relVel, normal);

        if (velAlongNormal > 0.0) return;

        float restitution = uRestitution;
        float j = -(1.0 + restitution) * velAlongNormal / 2.0;

        p1.velocity.xyz += j * normal;
        p2.velocity.xyz -= j * normal;
    }
}

void main() {
    uint index = gl_GlobalInvocationID.x;
    if (index >= uNumParticles) return;

    Particle p = particles[index];

    // 跳过死亡粒子
    if (p.position.w < 0.0) return;

    // 与碰撞平面检测
    for (uint i = 0; i < uNumPlanes; i++) {
        if (planeCollision(p.position.xyz, planes[i])) {
            p.velocity.xyz = collisionResponse(p.position.xyz, p.velocity.xyz, planes[i]);
        }
    }

    // 粒子间碰撞 (简化版 - 仅检查相邻粒子)
    for (uint i = 0; i < uNumParticles; i++) {
        if (i == index) continue;
        if (particles[i].position.w < 0.0) continue;

        particleCollision(p, particles[i]);
    }

    particles[index] = p;
}
