#version 450 core
/**
 * 粒子片段着色器
 *
 * 功能：
 * - 纹理采样
 * - 软粒子
 * - 淡入淡出
 * - 混合模式
 */

// 输入
in GS_OUT {
    vec2 texCoord;
    vec4 color;
    float age;
} fs_in;

// Uniform
uniform sampler2D uParticleTexture;
uniform sampler2D uDepthTexture;
uniform float uSoftParticleDistance;
uniform mat4 uProjection;
uniform float uFadeIn;
uniform float uFadeOut;
uniform int uBlendMode;  // 0: Alpha, 1: Additive, 2: Multiplicative

// 输出
out vec4 FragColor;

// 软粒子深度衰减
float softParticleFactor(vec2 screenPos, float particleDepth) {
    float sceneDepth = texture(uDepthTexture, screenPos).r;
    float depthDiff = sceneDepth - particleDepth;
    return smoothstep(0.0, uSoftParticleDistance, depthDiff);
}

void main() {
    // 采样粒子纹理
    vec4 texColor = texture(uParticleTexture, fs_in.texCoord);

    // 粒子颜色
    vec4 particleColor = texColor * fs_in.color;

    // 淡入淡出
    float fadeIn = smoothstep(0.0, uFadeIn, fs_in.age);
    float fadeOut = smoothstep(1.0, uFadeOut, fs_in.age);
    particleColor.a *= fadeIn * fadeOut;

    // 软粒子
    vec2 screenPos = gl_FragCoord.xy / vec2(textureSize(uDepthTexture, 0));
    float softFactor = softParticleFactor(screenPos, gl_FragCoord.z);
    particleColor.a *= softFactor;

    // 混合模式
    switch (uBlendMode) {
        case 0: // Alpha 混合
            FragColor = particleColor;
            break;
        case 1: // 加法混合
            FragColor = vec4(particleColor.rgb * particleColor.a, 0.0);
            break;
        case 2: // 乘法混合
            FragColor = vec4(particleColor.rgb, particleColor.a * 0.5);
            break;
        default:
            FragColor = particleColor;
    }

    // Alpha 测试
    if (FragColor.a < 0.01) discard;
}
