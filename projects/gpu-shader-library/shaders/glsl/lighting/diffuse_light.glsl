#version 450 core
/**
 * 漫反射光照着色器 (Lambert)
 *
 * 功能：
 * - Lambert 漫反射模型
 * - 半球光照
 * - 多光源支持
 *
 * Lambert 公式：
 * I_diffuse = k_d * I_L * max(0, N . L)
 * k_d: 漫反射系数
 * I_L: 光源强度
 * N: 表面法线
 * L: 光源方向
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// 光源结构
struct DirectionalLight {
    vec3 direction;
    vec3 color;
    float intensity;
};

struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
    float range;
};

// Uniform
uniform DirectionalLight uDirLight;
uniform PointLight uPointLights[4];
uniform int uNumPointLights;
uniform vec3 uBaseColor;
uniform float uDiffuseStrength;

// 输出
out vec4 FragColor;

// Lambert 漫反射
float lambertDiffuse(vec3 normal, vec3 lightDir) {
    return max(dot(normal, lightDir), 0.0);
}

// 半球光照
vec3 hemisphereLight(vec3 normal, vec3 skyColor, vec3 groundColor) {
    float factor = dot(normal, vec3(0.0, 1.0, 0.0)) * 0.5 + 0.5;
    return mix(groundColor, skyColor, factor);
}

// 衰减计算
float attenuation(float distance, float range) {
    float att = 1.0 - clamp(distance / range, 0.0, 1.0);
    return att * att;
}

vec3 calculateDirectionalLight(DirectionalLight light, vec3 normal) {
    vec3 lightDir = normalize(-light.direction);
    float diff = lambertDiffuse(normal, lightDir);
    return light.color * light.intensity * diff;
}

vec3 calculatePointLight(PointLight light, vec3 worldPos, vec3 normal) {
    vec3 lightVec = light.position - worldPos;
    float dist = length(lightVec);
    vec3 lightDir = normalize(lightVec);

    float att = attenuation(dist, light.range);
    float diff = lambertDiffuse(normal, lightDir);

    return light.color * light.intensity * diff * att;
}

void main() {
    vec3 normal = normalize(fs_in.worldNormal);

    // 方向光
    vec3 diffuse = calculateDirectionalLight(uDirLight, normal);

    // 点光源
    for (int i = 0; i < uNumPointLights; i++) {
        diffuse += calculatePointLight(uPointLights[i], fs_in.worldPos, normal);
    }

    // 半球光照
    vec3 hemi = hemisphereLight(normal, vec3(0.4, 0.5, 0.6), vec3(0.2, 0.15, 0.1));

    diffuse = diffuse * uDiffuseStrength + hemi * 0.2;

    FragColor = vec4(diffuse * uBaseColor, 1.0);
}
