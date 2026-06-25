#version 450 core
/**
 * 环境光着色器
 *
 * 功能：
 * - 全局环境光计算
 * - 环境光遮蔽 (AO) 集成
 * - 天空盒环境光采样
 *
 * 环境光公式：
 * I_ambient = k_a * I_a * AO
 * k_a: 环境光反射系数
 * I_a: 环境光强度
 * AO: 环境光遮蔽因子
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// Uniform
uniform vec3 uAmbientColor;        // 环境光颜色
uniform float uAmbientIntensity;    // 环境光强度
uniform float uAOIntensity;         // AO 强度
uniform sampler2D uAOTexture;       // AO 纹理
uniform samplerCube uEnvMap;        // 环境贴图
uniform bool uUseAO;
uniform bool uUseEnvMap;

// 输出
out vec4 FragColor;

vec3 calculateAmbientLight(vec3 baseColor) {
    vec3 ambient;

    if (uUseEnvMap) {
        // 从天空盒采样环境光
        vec3 envColor = texture(uEnvMap, fs_in.worldNormal).rgb;
        ambient = envColor * baseColor;
    } else {
        // 简单环境光
        ambient = uAmbientColor * uAmbientIntensity * baseColor;
    }

    // 应用环境光遮蔽
    if (uUseAO) {
        float ao = texture(uAOTexture, fs_in.texCoord).r;
        ao = mix(1.0, ao, uAOIntensity);
        ambient *= ao;
    }

    return ambient;
}

void main() {
    vec3 baseColor = vec3(0.8); // 默认基础颜色
    vec3 ambient = calculateAmbientLight(baseColor);
    FragColor = vec4(ambient, 1.0);
}
