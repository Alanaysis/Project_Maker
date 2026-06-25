#version 450 core
/**
 * 视差贴图着色器
 *
 * 功能：
 * - 基础视差贴图
 * - 陡峭视差贴图 (Steep Parallax)
 * - 视差遮蔽映射 (Parallax Occlusion Mapping)
 *
 * 原理：
 * 通过在片段着色器中偏移纹理坐标，模拟表面凹凸深度
 * 比法线贴图更真实，但计算成本更高
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec3 worldTangent;
    vec3 worldBitangent;
} fs_in;

// Uniform
uniform sampler2D uDiffuseMap;
uniform sampler2D uNormalMap;
uniform sampler2D uDepthMap;
uniform vec3 uLightPos;
uniform vec3 uCameraPos;
uniform vec3 uLightColor;
uniform float uHeightScale;       // 高度缩放 (0.0 - 0.1)
uniform int uMinLayers;           // 最小层数
uniform int uMaxLayers;           // 最大层数
uniform int uParallaxMode;        // 0: 基础, 1: 陡峭, 2: 遮蔽

// 输出
out vec4 FragColor;

// TBN 矩阵
mat3 getTBN() {
    vec3 N = normalize(fs_in.worldNormal);
    vec3 T = normalize(fs_in.worldTangent);
    vec3 B = normalize(fs_in.worldBitangent);
    return mat3(T, B, N);
}

// 基础视差贴图
vec2 parallaxBasic(vec2 texCoords, vec3 viewDirTangent) {
    float height = texture(uDepthMap, texCoords).r;
    vec2 p = viewDirTangent.xy / viewDirTangent.z * (height * uHeightScale);
    return texCoords - p;
}

// 陡峭视差贴图
vec2 parallaxSteep(vec2 texCoords, vec3 viewDirTangent) {
    float layerDepth = 1.0 / float(uMaxLayers);
    float currentLayerDepth = 0.0;
    vec2 deltaTexCoords = viewDirTangent.xy / viewDirTangent.z * uHeightScale / float(uMaxLayers);

    vec2 currentTexCoords = texCoords;
    float currentDepthMapValue = texture(uDepthMap, currentTexCoords).r;

    while (currentLayerDepth < currentDepthMapValue) {
        currentTexCoords -= deltaTexCoords;
        currentDepthMapValue = texture(uDepthMap, currentTexCoords).r;
        currentLayerDepth += layerDepth;
    }

    return currentTexCoords;
}

// 视差遮蔽映射
vec2 parallaxOcclusionMapping(vec2 texCoords, vec3 viewDirTangent) {
    float layerDepth = 1.0 / float(uMaxLayers);
    float currentLayerDepth = 0.0;
    vec2 deltaTexCoords = viewDirTangent.xy / viewDirTangent.z * uHeightScale / float(uMaxLayers);

    vec2 currentTexCoords = texCoords;
    float currentDepthMapValue = texture(uDepthMap, currentTexCoords).r;

    // 陡峭视差阶段
    while (currentLayerDepth < currentDepthMapValue) {
        currentTexCoords -= deltaTexCoords;
        currentDepthMapValue = texture(uDepthMap, currentTexCoords).r;
        currentLayerDepth += layerDepth;
    }

    // 遮蔽插值
    vec2 prevTexCoords = currentTexCoords + deltaTexCoords;
    float afterDepth = currentDepthMapValue - currentLayerDepth;
    float beforeDepth = texture(uDepthMap, prevTexCoords).r - currentLayerDepth + layerDepth;
    float weight = afterDepth / (afterDepth - beforeDepth);
    vec2 finalTexCoords = prevTexCoords * weight + currentTexCoords * (1.0 - weight);

    return finalTexCoords;
}

vec3 getParallaxTexCoords(vec2 texCoords, vec3 viewDirTangent) {
    vec2 parallaxTexCoords;
    switch (uParallaxMode) {
        case 0:
            parallaxTexCoords = parallaxBasic(texCoords, viewDirTangent);
            break;
        case 1:
            parallaxTexCoords = parallaxSteep(texCoords, viewDirTangent);
            break;
        default:
            parallaxTexCoords = parallaxOcclusionMapping(texCoords, viewDirTangent);
            break;
    }

    // 裁剪超出范围的坐标
    if (parallaxTexCoords.x > 1.0 || parallaxTexCoords.y > 1.0 ||
        parallaxTexCoords.x < 0.0 || parallaxTexCoords.y < 0.0) {
        discard;
    }

    return vec3(parallaxTexCoords, 0.0);
}

void main() {
    mat3 TBN = getTBN();
    vec3 viewDir = normalize(uCameraPos - fs_in.worldPos);
    vec3 viewDirTangent = normalize(transpose(TBN) * viewDir);

    // 计算视差纹理坐标
    vec2 texCoords = getParallaxTexCoords(fs_in.texCoord, viewDirTangent).xy;

    // 采样
    vec3 diffuseColor = texture(uDiffuseMap, texCoords).rgb;
    vec3 normal = texture(uNormalMap, texCoords).rgb * 2.0 - 1.0;
    normal = normalize(TBN * normal);

    // 简单光照
    vec3 lightDir = normalize(uLightPos - fs_in.worldPos);
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 color = diffuseColor * diff * uLightColor;

    FragColor = vec4(color, 1.0);
}
