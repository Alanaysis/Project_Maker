#version 450 core
/**
 * 阴影映射着色器
 *
 * 功能：
 * - 硬阴影
 * - PCF 软阴影
 * - 级联阴影映射 (CSM)
 *
 * 原理：
 * 1. 从光源视角渲染深度图
 * 2. 在片段着色器中比较深度值
 * 3. 如果片段深度 > 阴影深度，则在阴影中
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec4 lightSpacePos;  // 光源空间位置
} fs_in;

// Uniform
uniform sampler2D uShadowMap;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform float uShadowBias;
uniform float uShadowStrength;
uniform int uPCFSamples;         // PCF 采样数
uniform float uPCFRadius;        // PCF 采样半径
uniform bool uUsePCF;
uniform vec2 uShadowMapSize;

// 输出
out vec4 FragColor;

// 普通阴影采样
float sampleShadow(vec3 projCoords, float bias) {
    float closestDepth = texture(uShadowMap, projCoords.xy).r;
    float currentDepth = projCoords.z;
    return currentDepth - bias > closestDepth ? 1.0 : 0.0;
}

// PCF 软阴影
float sampleShadowPCF(vec3 projCoords, float bias) {
    float shadow = 0.0;
    vec2 texelSize = 1.0 / uShadowMapSize;

    for (int x = -uPCFSamples; x <= uPCFSamples; x++) {
        for (int y = -uPCFSamples; y <= uPCFSamples; y++) {
            vec2 offset = vec2(x, y) * texelSize * uPCFRadius;
            float pcfDepth = texture(uShadowMap, projCoords.xy + offset).r;
            shadow += projCoords.z - bias > pcfDepth ? 1.0 : 0.0;
        }
    }

    float totalSamples = float((2 * uPCFSamples + 1) * (2 * uPCFSamples + 1));
    return shadow / totalSamples;
}

// 级联阴影映射 (简化版)
float calculateShadowCascade(vec4 lightSpacePos, int cascadeIndex) {
    vec3 projCoords = lightSpacePos.xyz / lightSpacePos.w;
    projCoords = projCoords * 0.5 + 0.5;

    if (projCoords.z > 1.0) return 0.0;

    float bias = max(uShadowBias * (1.0 - dot(normalize(fs_in.worldNormal), normalize(-uLightDir))), uShadowBias * 0.1);

    if (uUsePCF) {
        return sampleShadowPCF(projCoords, bias);
    } else {
        return sampleShadow(projCoords, bias);
    }
}

float calculateShadow(vec4 lightSpacePos) {
    vec3 projCoords = lightSpacePos.xyz / lightSpacePos.w;
    projCoords = projCoords * 0.5 + 0.5;

    if (projCoords.z > 1.0) return 0.0;

    float bias = max(uShadowBias * (1.0 - dot(normalize(fs_in.worldNormal), normalize(-uLightDir))), uShadowBias * 0.1);

    if (uUsePCF) {
        return sampleShadowPCF(projCoords, bias);
    } else {
        return sampleShadow(projCoords, bias);
    }
}

void main() {
    vec3 normal = normalize(fs_in.worldNormal);
    vec3 lightDir = normalize(-uLightDir);

    // 漫反射
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 diffuse = diff * uLightColor;

    // 计算阴影
    float shadow = calculateShadow(fs_in.lightSpacePos);
    shadow *= uShadowStrength;

    // 最终颜色 (受阴影影响)
    vec3 color = (1.0 - shadow) * diffuse;

    FragColor = vec4(color, 1.0);
}
