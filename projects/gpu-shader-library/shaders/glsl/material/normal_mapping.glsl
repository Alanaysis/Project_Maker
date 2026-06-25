#version 450 core
/**
 * 法线贴图着色器
 *
 * 功能：
 * - 切线空间法线贴图
 * - TBN 矩阵计算
 * - 与 Blinn-Phong 集成
 *
 * 原理：
 * 1. 将法线贴图中的法线从切线空间转换到世界空间
 * 2. 使用变换后的法线进行光照计算
 * 3. 实现表面细节凹凸效果
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
uniform sampler2D uSpecularMap;
uniform vec3 uLightPos;
uniform vec3 uCameraPos;
uniform vec3 uLightColor;
uniform float uShininess;
uniform bool uFlipNormalY;

// 输出
out vec4 FragColor;

// 构建 TBN 矩阵
mat3 buildTBN() {
    vec3 N = normalize(fs_in.worldNormal);
    vec3 T = normalize(fs_in.worldTangent);
    vec3 B = normalize(fs_in.worldBitangent);

    // 正交化 (Gram-Schmidt)
    T = normalize(T - dot(T, N) * N);

    // 重建 B (确保正交)
    vec3 correctedB = cross(N, T);

    return mat3(T, correctedB, N);
}

// 从法线贴图获取法线
vec3 getNormalFromMap() {
    // 采样法线贴图
    vec3 tangentNormal = texture(uNormalMap, fs_in.texCoord).xyz * 2.0 - 1.0;

    // 可选翻转 Y 轴 (OpenGL vs DirectX)
    if (uFlipNormalY) {
        tangentNormal.y = -tangentNormal.y;
    }

    // TBN 变换
    mat3 TBN = buildTBN();
    return normalize(TBN * tangentNormal);
}

vec3 blinnPhong(vec3 normal, vec3 worldPos) {
    vec3 lightDir = normalize(uLightPos - worldPos);
    vec3 viewDir = normalize(uCameraPos - worldPos);
    vec3 halfDir = normalize(lightDir + viewDir);

    // 漫反射
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 diffuse = diff * uLightColor;

    // 镜面反射
    float spec = pow(max(dot(normal, halfDir), 0.0), uShininess);
    vec3 specular = spec * uLightColor;

    // 衰减
    float distance = length(uLightPos - worldPos);
    float attenuation = 1.0 / (1.0 + 0.09 * distance + 0.032 * distance * distance);

    return (diffuse + specular) * attenuation;
}

void main() {
    // 获取法线
    vec3 normal = getNormalFromMap();

    // 采样纹理
    vec3 diffuseColor = texture(uDiffuseMap, fs_in.texCoord).rgb;
    float specularStrength = texture(uSpecularMap, fs_in.texCoord).r;

    // 光照计算
    vec3 lighting = blinnPhong(normal, fs_in.worldPos);

    // 环境光
    vec3 ambient = vec3(0.1) * diffuseColor;

    vec3 color = ambient + lighting * diffuseColor;

    FragColor = vec4(color, 1.0);
}
