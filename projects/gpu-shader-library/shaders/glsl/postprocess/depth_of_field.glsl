#version 450 core
/**
 * 景深着色器
 *
 * 功能：
 * - 焦点距离可调
 * - 光圈大小控制
 * - 散景形状
 * - 远景/近景模糊
 *
 * 原理：
 * 模拟相机景深效果，焦点处清晰，远近处模糊
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uColorTexture;
uniform sampler2D uDepthTexture;
uniform float uFocalDistance;      // 焦点距离
uniform float uFocalRange;        // 焦点范围
uniform float uAperture;          // 光圈大小
uniform float uMaxBlurSize;
uniform vec2 uTextureSize;
uniform mat4 uProjection;
uniform float uNear;
uniform float uFar;

// 输出
out vec4 FragColor;

// 线性化深度
float linearizeDepth(float depth) {
    float z = depth * 2.0 - 1.0;
    return (2.0 * uNear * uFar) / (uFar + uNear - z * (uFar - uNear));
}

// 计算模糊因子
float calculateBlurFactor(float depth) {
    float linearDepth = linearizeDepth(depth);
    float focalDiff = abs(linearDepth - uFocalDistance);
    return smoothstep(0.0, uFocalRange, focalDiff) * uAperture;
}

// 圆形散景采样
vec3 bokehSample(vec2 uv, float blur) {
    vec3 color = vec3(0.0);
    float totalWeight = 0.0;

    const int samples = 16;
    float angleStep = 6.28318 / float(samples);
    float radiusStep = blur * uMaxBlurSize / float(samples);

    for (int i = 0; i < samples; i++) {
        float angle = angleStep * float(i);
        for (int j = 1; j <= 4; j++) {
            float radius = radiusStep * float(j);
            vec2 offset = vec2(cos(angle), sin(angle)) * radius / uTextureSize;
            color += texture(uColorTexture, uv + offset).rgb;
            totalWeight += 1.0;
        }
    }

    return color / totalWeight;
}

void main() {
    float depth = texture(uDepthTexture, texCoord).r;
    float blur = calculateBlurFactor(depth);

    vec3 color;
    if (blur > 0.01) {
        color = bokehSample(texCoord, blur);
    } else {
        color = texture(uColorTexture, texCoord).rgb;
    }

    FragColor = vec4(color, 1.0);
}
