#version 450 core
/**
 * 基础片段着色器 - 颜色输出
 *
 * 功能：
 * - 基础颜色采样
 * - Gamma 校正
 * - Alpha 测试
 *
 * 输入：
 * - worldPos: 世界空间位置
 * - worldNormal: 世界空间法线
 * - texCoord: 纹理坐标
 *
 * Uniform 变量：
 * - uBaseColor: 基础颜色
 * - uTexture: 基础纹理
 * - uGamma: Gamma 值
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec4 clipPos;
} fs_in;

// Uniform 变量
uniform vec4 uBaseColor;
uniform sampler2D uTexture;
uniform float uGamma;
uniform bool uUseTexture;

// 输出
out vec4 FragColor;

void main() {
    // 获取基础颜色
    vec4 color;
    if (uUseTexture) {
        color = texture(uTexture, fs_in.texCoord) * uBaseColor;
    } else {
        color = uBaseColor;
    }

    // Alpha 测试
    if (color.a < 0.01) {
        discard;
    }

    // Gamma 校正 (线性空间 -> sRGB)
    color.rgb = pow(color.rgb, vec3(1.0 / uGamma));

    FragColor = color;
}
