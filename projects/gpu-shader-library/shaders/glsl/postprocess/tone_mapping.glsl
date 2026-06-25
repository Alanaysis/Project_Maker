#version 450 core
/**
 * 色调映射着色器
 *
 * 功能：
 * - Reinhard 色调映射
 * - ACES 色调映射
 * - Uncharted 2 色调映射
 * - 曝光控制
 * - 白点调整
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uHDRTexture;
uniform float uExposure;
uniform float uGamma;
uniform int uToneMappingMode;  // 0: Reinhard, 1: ACES, 2: Uncharted2
uniform float uWhitePoint;     // 白点值

// 输出
out vec4 FragColor;

// Reinhard 色调映射
vec3 reinhardToneMapping(vec3 color) {
    return color / (1.0 + color);
}

// 带白点的 Reinhard
vec3 reinhardExtendedToneMapping(vec3 color, float white) {
    float numerator = color * (1.0 + color / (white * white));
    return numerator / (1.0 + color);
}

// ACES 色调映射 (Academy Color Encoding System)
vec3 acesToneMapping(vec3 color) {
    // sRGB -> ACES
    color *= 0.6;
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((color * (a * color + b)) / (color * (c * color + d) + e), 0.0, 1.0);
}

// Uncharted 2 色调映射 (John Hable)
vec3 uncharted2ToneMappingCurve(vec3 x) {
    float A = 0.15;
    float B = 0.50;
    float C = 0.10;
    float D = 0.20;
    float E = 0.02;
    float F = 0.30;
    return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - E / F;
}

vec3 uncharted2ToneMapping(vec3 color) {
    float exposureBias = 2.0;
    vec3 curr = uncharted2ToneMappingCurve(exposureBias * color);
    vec3 whiteScale = 1.0 / uncharted2ToneMappingCurve(vec3(uWhitePoint));
    return curr * whiteScale;
}

// Filmic 色调映射
vec3 filmicToneMapping(vec3 color) {
    color = max(vec3(0.0), color - 0.004);
    color = (color * (6.2 * color + 0.5)) / (color * (6.2 * color + 1.7) + 0.06);
    return color;
}

void main() {
    vec3 hdrColor = texture(uHDRTexture, texCoord).rgb;

    // 曝光
    vec3 color = hdrColor * uExposure;

    // 色调映射
    switch (uToneMappingMode) {
        case 0:
            color = reinhardToneMapping(color);
            break;
        case 1:
            color = acesToneMapping(color);
            break;
        case 2:
            color = uncharted2ToneMapping(color);
            break;
        case 3:
            color = filmicToneMapping(color);
            break;
        default:
            color = reinhardExtendedToneMapping(color, uWhitePoint);
    }

    // Gamma 校正
    color = pow(color, vec3(1.0 / uGamma));

    FragColor = vec4(color, 1.0);
}
