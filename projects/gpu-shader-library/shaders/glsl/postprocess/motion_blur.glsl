#version 450 core
/**
 * 运动模糊着色器
 *
 * 功能：
 * - 基于速度缓冲的运动模糊
 * - 可配置模糊强度
 * - 时间抗锯齿 (TAA)
 *
 * 原理：
 * 1. 计算每个像素的运动速度
 * 2. 沿速度方向采样多次
 * 3. 混合采样结果
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uColorTexture;
uniform sampler2D uVelocityTexture;
uniform int uNumSamples;
uniform float uBlurStrength;
uniform float uMaxVelocity;

// 输出
out vec4 FragColor;

void main() {
    vec2 velocity = texture(uVelocityTexture, texCoord).rg;

    // 限制速度
    float speed = length(velocity);
    if (speed > uMaxVelocity) {
        velocity = velocity / speed * uMaxVelocity;
    }

    // 缩放速度
    velocity *= uBlurStrength;

    vec3 color = vec3(0.0);
    float totalWeight = 0.0;

    // 沿速度方向采样
    for (int i = 0; i < uNumSamples; i++) {
        float t = float(i) / float(uNumSamples - 1);
        vec2 sampleCoord = texCoord - velocity * t;

        // 边界检查
        if (sampleCoord.x >= 0.0 && sampleCoord.x <= 1.0 &&
            sampleCoord.y >= 0.0 && sampleCoord.y <= 1.0) {
            color += texture(uColorTexture, sampleCoord).rgb;
            totalWeight += 1.0;
        }
    }

    FragColor = vec4(color / totalWeight, 1.0);
}
