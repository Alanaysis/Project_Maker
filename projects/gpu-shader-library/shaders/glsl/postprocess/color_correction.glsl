#version 450 core
/**
 * 色彩校正着色器
 *
 * 功能：
 * - 亮度/对比度调整
 * - 饱和度调整
 * - 色相旋转
 * - 色温调整
 * - LUT (查找表) 颜色分级
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uInputTexture;
uniform sampler3D uLUTTexture;
uniform float uBrightness;
uniform float uContrast;
uniform float uSaturation;
uniform float uHue;
uniform float uTemperature;
uniform float uTint;
uniform bool uUseLUT;
uniform float uLUTStrength;

// 输出
out vec4 FragColor;

// RGB -> HSV
vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// HSV -> RGB
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// 亮度对比度调整
vec3 adjustBrightnessContrast(vec3 color) {
    // 对比度
    color = (color - 0.5) * uContrast + 0.5;
    // 亮度
    color += uBrightness;
    return color;
}

// 饱和度调整
vec3 adjustSaturation(vec3 color) {
    float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
    return mix(vec3(luminance), color, uSaturation);
}

// 色相旋转
vec3 adjustHue(vec3 color) {
    vec3 hsv = rgb2hsv(color);
    hsv.x = fract(hsv.x + uHue);
    return hsv2rgb(hsv);
}

// 色温调整
vec3 adjustTemperature(vec3 color) {
    // 简单色温模拟
    color.r += uTemperature * 0.1;
    color.b -= uTemperature * 0.1;
    color.g += uTint * 0.05;
    return color;
}

// LUT 颜色分级
vec3 applyLUT(vec3 color) {
    // 假设 LUT 是 16x16x16
    vec3 lutCoord = color * 15.0 / 16.0 + 0.5 / 16.0;
    vec3 lutColor = texture(uLUTTexture, lutCoord).rgb;
    return mix(color, lutColor, uLUTStrength);
}

void main() {
    vec3 color = texture(uInputTexture, texCoord).rgb;

    // 色彩校正管线
    color = adjustBrightnessContrast(color);
    color = adjustSaturation(color);
    color = adjustHue(color);
    color = adjustTemperature(color);

    // LUT 应用
    if (uUseLUT) {
        color = applyLUT(color);
    }

    // 裁剪
    color = clamp(color, 0.0, 1.0);

    FragColor = vec4(color, 1.0);
}
