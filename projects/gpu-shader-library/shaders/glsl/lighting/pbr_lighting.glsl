#version 450 core
/**
 * PBR (基于物理的渲染) 着色器
 *
 * 功能：
 * - 微表面理论
 * - Cook-Torrance BRDF
 * - Fresnel (Schlick 近似)
 * - 几何遮蔽 (Smith-GGX)
 * - 法线分布 (GGX/Trowbridge-Reitz)
 *
 * 核心公式：
 * f(l,v) = k_d * f_lambert + k_s * f_cook-torrance
 *
 * f_cook-torrance = D * F * G / (4 * (N.L) * (N.V))
 * D: 法线分布函数
 * F: Fresnel 方程
 * G: 几何函数
 */

// 常量
const float PI = 3.14159265359;
const float EPSILON = 0.0001;

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// PBR 材质参数
uniform vec3 uAlbedo;           // 基础颜色
uniform float uMetallic;        // 金属度
uniform float uRoughness;       // 粗糙度
uniform float uAO;              // 环境光遮蔽

// 纹理
uniform sampler2D uAlbedoMap;
uniform sampler2D uNormalMap;
uniform sampler2D uMetallicRoughnessMap;
uniform sampler2D uAOMap;
uniform sampler2D uEmissiveMap;
uniform samplerCube uIrradianceMap;
uniform samplerCube uPrefilterMap;
uniform sampler2D uBRDFLUT;

// 光源
uniform vec3 uLightPositions[4];
uniform vec3 uLightColors[4];
uniform int uNumLights;
uniform vec3 uCameraPos;
uniform float uExposure;

// 输出
out vec4 FragColor;

// ===================== 法线分布函数 =====================

// GGX/Trowbridge-Reitz 法线分布
float distributionGGX(vec3 N, vec3 H, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;

    float nom = a2;
    float denom = NdotH2 * (a2 - 1.0) + 1.0;
    denom = PI * denom * denom;

    return nom / max(denom, EPSILON);
}

// ===================== 几何函数 =====================

// Schlick-GGX 几何遮蔽
float geometrySchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;

    float nom = NdotV;
    float denom = NdotV * (1.0 - k) + k;

    return nom / denom;
}

// Smith 几何函数
float geometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);

    float ggx1 = geometrySchlickGGX(NdotV, roughness);
    float ggx2 = geometrySchlickGGX(NdotL, roughness);

    return ggx1 * ggx2;
}

// ===================== Fresnel 方程 =====================

// Schlick Fresnel 近似
vec3 fresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

// 带粗糙度的 Fresnel
vec3 fresnelSchlickRoughness(float cosTheta, vec3 F0, float roughness) {
    return F0 + (max(vec3(1.0 - roughness), F0) - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

// ===================== PBR 主计算 =====================

vec3 calculatePBR(vec3 N, vec3 V, vec3 L, vec3 H, vec3 radiance,
                  vec3 albedo, float metallic, float roughness) {
    float NdotL = max(dot(N, L), 0.0);
    float NdotV = max(dot(N, V), 0.0);
    float HdotV = max(dot(H, V), 0.0);

    // 计算 F0 (基础反射率)
    vec3 F0 = mix(vec3(0.04), albedo, metallic);

    // Cook-Torrance BRDF
    float D = distributionGGX(N, H, roughness);
    float G = geometrySmith(N, V, L, roughness);
    vec3 F = fresnelSchlick(HdotV, F0);

    // 镜面反射
    vec3 numerator = D * G * F;
    float denominator = 4.0 * NdotV * NdotL + EPSILON;
    vec3 specular = numerator / denominator;

    // 能量守恒
    vec3 kS = F;
    vec3 kD = vec3(1.0) - kS;
    kD *= 1.0 - metallic;  // 金属无漫反射

    return (kD * albedo / PI + specular) * radiance * NdotL;
}

void main() {
    // 采样材质纹理
    vec3 albedo = uAlbedo * texture(uAlbedoMap, fs_in.texCoord).rgb;
    float metallic = uMetallic * texture(uMetallicRoughnessMap, fs_in.texCoord).b;
    float roughness = uRoughness * texture(uMetallicRoughnessMap, fs_in.texCoord).g;
    float ao = uAO * texture(uAOMap, fs_in.texCoord).r;

    // 法线
    vec3 N = normalize(fs_in.worldNormal);
    vec3 V = normalize(uCameraPos - fs_in.worldPos);

    // F0 计算
    vec3 F0 = mix(vec3(0.04), albedo, metallic);

    // 直接光照
    vec3 Lo = vec3(0.0);
    for (int i = 0; i < uNumLights; i++) {
        vec3 L = normalize(uLightPositions[i] - fs_in.worldPos);
        vec3 H = normalize(V + L);

        float distance = length(uLightPositions[i] - fs_in.worldPos);
        float attenuation = 1.0 / (distance * distance);
        vec3 radiance = uLightColors[i] * attenuation;

        Lo += calculatePBR(N, V, L, H, radiance, albedo, metallic, roughness);
    }

    // 环境光照 (IBL)
    vec3 F = fresnelSchlickRoughness(max(dot(N, V), 0.0), F0, roughness);
    vec3 kS = F;
    vec3 kD = 1.0 - kS;
    kD *= 1.0 - metallic;

    vec3 irradiance = texture(uIrradianceMap, N).rgb;
    vec3 diffuse = irradiance * albedo;

    // 预滤波环境贴图
    vec3 R = reflect(-V, N);
    const float MAX_REFLECTION_LOD = 4.0;
    vec3 prefilteredColor = textureLod(uPrefilterMap, R, roughness * MAX_REFLECTION_LOD).rgb;
    vec2 brdf = texture(uBRDFLUT, vec2(max(dot(N, V), 0.0), roughness)).rg;
    vec3 specular = prefilteredColor * (F * brdf.x + brdf.y);

    vec3 ambient = (kD * diffuse + specular) * ao;

    // 最终颜色
    vec3 color = ambient + Lo;

    // 色调映射 (Reinhard)
    color = color / (color + vec3(1.0));

    // Gamma 校正
    color = pow(color, vec3(1.0 / 2.2));

    FragColor = vec4(color, 1.0);
}
