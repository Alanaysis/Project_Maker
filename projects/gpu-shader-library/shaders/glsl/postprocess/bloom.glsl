#version 450 core
/**
 * Bloom 效果着色器
 *
 * 功能：
 * - 亮度提取
 * - 高斯模糊
 * - 色调映射
 *
 * 步骤：
 * 1. 提取高亮区域
 * 2. 对高亮区域进行模糊
 * 3. 混合回原始图像
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uHDRTexture;
uniform sampler2D uBlurTexture;
uniform float uBloomThreshold;
uniform float uBloomStrength;
uniform float uExposure;
uniform float uGamma;

// 输出
out vec4 FragColor;

// 亮度计算
float luminance(vec3 color) {
    return dot(color, vec3(0.2126, 0.7152, 0.0722));
}

// 色调映射 (ACES)
vec3 acesToneMapping(vec3 color) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((color * (a * color + b)) / (color * (c * color + d) + e), 0.0, 1.0);
}

void main() {
    vec3 hdrColor = texture(uHDRTexture, texCoord).rgb;
    vec3 blurColor = texture(uBlurTexture, texCoord).rgb;

    // 亮度提取 (用于 bloom)
    float brightness = luminance(hdrColor);
    vec3 brightColor = hdrColor * max(0.0, brightness - uBloomThreshold);

    // 混合 bloom
    vec3 bloomColor = mix(hdrColor, blurColor, uBloomStrength);

    // 色调映射
    vec3 mapped = acesToneMapping(bloomColor * uExposure);

    // Gamma 校正
    mapped = pow(mapped, vec3(1.0 / uGamma));

    FragColor = vec4(mapped, 1.0);
}
