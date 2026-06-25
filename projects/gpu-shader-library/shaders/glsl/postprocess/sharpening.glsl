#version 450 core
/**
 * 锐化着色器
 *
 * 功能：
 * - Unsharp Mask 锐化
 * - Laplacian 锐化
 * - 自适应锐化
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uInputTexture;
uniform vec2 uTextureSize;
uniform float uSharpness;
uniform int uMethod;  // 0: Unsharp Mask, 1: Laplacian, 2: Adaptive

// 输出
out vec4 FragColor;

// Unsharp Mask
vec3 unsharpMask(vec2 uv) {
    vec3 center = texture(uInputTexture, uv).rgb;
    vec2 texelSize = 1.0 / uTextureSize;

    // 3x3 模糊
    vec3 blurred = vec3(0.0);
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            vec2 offset = vec2(x, y) * texelSize;
            blurred += texture(uInputTexture, uv + offset).rgb;
        }
    }
    blurred /= 9.0;

    // 锐化 = 原始 + (原始 - 模糊) * 强度
    return center + (center - blurred) * uSharpness;
}

// Laplacian 锐化
vec3 laplacianSharpen(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;
    vec3 center = texture(uInputTexture, uv).rgb;

    // Laplacian 核
    float kernel[9] = float[](
        0, -1,  0,
       -1,  5, -1,
        0, -1,  0
    );

    vec3 result = vec3(0.0);
    int idx = 0;
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 offset = vec2(x, y) * texelSize;
            result += texture(uInputTexture, uv + offset).rgb * kernel[idx];
            idx++;
        }
    }

    return mix(center, result, uSharpness);
}

// 自适应锐化
vec3 adaptiveSharpen(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;
    vec3 center = texture(uInputTexture, uv).rgb;

    // 计算局部对比度
    float luminance = dot(center, vec3(0.2126, 0.7152, 0.0722));
    float minLum = luminance;
    float maxLum = luminance;

    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            if (x == 0 && y == 0) continue;
            vec2 offset = vec2(x, y) * texelSize;
            float lum = dot(texture(uInputTexture, uv + offset).rgb, vec3(0.2126, 0.7152, 0.0722));
            minLum = min(minLum, lum);
            maxLum = max(maxLum, lum);
        }
    }

    // 边缘区域锐化更多
    float edgeFactor = smoothstep(0.0, 0.1, maxLum - minLum);
    float adaptiveSharpness = uSharpness * edgeFactor;

    // 应用锐化
    vec3 blurred = vec3(0.0);
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            vec2 offset = vec2(x, y) * texelSize;
            blurred += texture(uInputTexture, uv + offset).rgb;
        }
    }
    blurred /= 9.0;

    return center + (center - blurred) * adaptiveSharpness;
}

void main() {
    vec3 color;

    switch (uMethod) {
        case 0:
            color = unsharpMask(texCoord);
            break;
        case 1:
            color = laplacianSharpen(texCoord);
            break;
        case 2:
            color = adaptiveSharpen(texCoord);
            break;
        default:
            color = unsharpMask(texCoord);
    }

    color = clamp(color, 0.0, 1.0);
    FragColor = vec4(color, 1.0);
}
