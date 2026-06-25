#version 450 core
/**
 * 高斯模糊着色器
 *
 * 功能：
 * - 可分离高斯模糊
 * - 可配置核大小
 * - 双通道 (水平/垂直)
 *
 * 原理：
 * 高斯模糊 = 水平模糊 * 垂直模糊
 * 分离后从 O(n^2) 降到 O(2n)
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uInputTexture;
uniform vec2 uDirection;         // (1,0) 水平, (0,1) 垂直
uniform vec2 uTextureSize;
uniform int uBlurRadius;
uniform float uSigma;            // 高斯标准差

// 输出
out vec4 FragColor;

// 高斯函数
float gaussian(float x, float sigma) {
    return exp(-(x * x) / (2.0 * sigma * sigma)) / (sqrt(2.0 * 3.14159265) * sigma);
}

void main() {
    vec2 texelSize = 1.0 / uTextureSize;
    vec3 result = vec3(0.0);
    float totalWeight = 0.0;

    // 预计算权重
    for (int i = -uBlurRadius; i <= uBlurRadius; i++) {
        float weight = gaussian(float(i), uSigma);
        vec2 offset = uDirection * texelSize * float(i);
        result += texture(uInputTexture, texCoord + offset).rgb * weight;
        totalWeight += weight;
    }

    FragColor = vec4(result / totalWeight, 1.0);
}
