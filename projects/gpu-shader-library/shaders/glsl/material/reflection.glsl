#version 450 core
/**
 * 反射着色器
 *
 * 功能：
 * - 环境反射 (天空盒)
 * - 平面反射
 * - 屏幕空间反射 (SSR)
 * - 反射探针
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// Uniform
uniform vec3 uCameraPos;
uniform samplerCube uEnvMap;          // 环境贴图
uniform sampler2D uReflectionTexture; // 平面反射纹理
uniform sampler2D uDepthTexture;
uniform sampler2D uNormalTexture;
uniform mat4 uView;
uniform mat4 uProjection;
uniform float uReflectivity;         // 反射率 (0-1)
uniform float uFresnelPower;         // Fresnel 指数
uniform int uReflectionMode;         // 0: 环境贴图, 1: 平面反射, 2: SSR
uniform float uRoughness;

// 输出
out vec4 FragColor;

// Fresnel 近似 (Schlick)
float fresnelSchlick(vec3 viewDir, vec3 normal) {
    float cosTheta = max(dot(viewDir, normal), 0.0);
    return pow(1.0 - cosTheta, uFresnelPower);
}

// 环境贴图反射
vec3 environmentReflection(vec3 reflectDir) {
    // 根据粗糙度选择 mip 级别
    float lod = uRoughness * 4.0;
    return textureLod(uEnvMap, reflectDir, lod).rgb;
}

// 平面反射
vec3 planarReflection(vec2 screenPos) {
    return texture(uReflectionTexture, screenPos).rgb;
}

// 屏幕空间反射 (简化版)
vec3 screenSpaceReflection(vec3 viewPos, vec3 viewDir, vec3 viewNormal) {
    vec3 reflectDir = reflect(viewDir, viewNormal);
    vec3 hitPos = viewPos;

    const int maxSteps = 64;
    const float stepSize = 0.1;

    for (int i = 0; i < maxSteps; i++) {
        hitPos += reflectDir * stepSize;

        // 投影到屏幕空间
        vec4 screenPos = uProjection * vec4(hitPos, 1.0);
        screenPos.xyz /= screenPos.w;
        screenPos.xy = screenPos.xy * 0.5 + 0.5;

        // 检查深度
        float depth = texture(uDepthTexture, screenPos.xy).r;
        if (screenPos.z > depth && screenPos.z < depth + 0.01) {
            return vec3(screenPos.xy, 1.0); // 命中
        }
    }

    return vec3(0.0); // 未命中
}

void main() {
    vec3 normal = normalize(fs_in.worldNormal);
    vec3 viewDir = normalize(uCameraPos - fs_in.worldPos);
    vec3 reflectDir = reflect(-viewDir, normal);

    vec3 reflection;
    float reflectivity = uReflectivity;

    switch (uReflectionMode) {
        case 0: // 环境贴图
            reflection = environmentReflection(reflectDir);
            reflectivity *= fresnelSchlick(viewDir, normal);
            break;
        case 1: // 平面反射
            vec2 screenPos = gl_FragCoord.xy / vec2(textureSize(uReflectionTexture, 0));
            reflection = planarReflection(screenPos);
            break;
        case 2: // SSR
            vec3 viewPos = (uView * vec4(fs_in.worldPos, 1.0)).xyz;
            vec3 viewNormal = normalize(mat3(uView) * normal);
            vec3 viewReflect = reflect(normalize(viewPos), viewNormal);
            vec3 ssr = screenSpaceReflection(viewPos, viewReflect, viewNormal);
            if (ssr.z > 0.0) {
                reflection = vec3(ssr.xy, 0.0); // 使用屏幕坐标采样
            } else {
                reflection = environmentReflection(reflectDir);
            }
            break;
        default:
            reflection = environmentReflection(reflectDir);
    }

    // 基础颜色 (假设)
    vec3 baseColor = vec3(0.5);

    // 混合
    vec3 color = mix(baseColor, reflection, reflectivity);

    FragColor = vec4(color, 1.0);
}
