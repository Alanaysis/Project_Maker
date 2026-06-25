#version 450 core
/**
 * Blinn-Phong 光照模型
 *
 * 功能：
 * - 环境光 + 漫反射 + 镜面反射
 * - 多光源支持
 * - 纹理映射
 *
 * 与 Phong 的区别：
 * 使用半程向量 H 替代反射向量 R
 * H = normalize(L + V)
 * I_specular = max(0, N . H)^n
 *
 * 优点：
 * - 计算更快 (避免反射计算)
 * - 当观察方向与光源方向接近时更准确
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// 光源结构
struct Light {
    vec3 position;
    vec3 color;
    float intensity;
    float range;
};

// Uniform
uniform Light uLights[8];
uniform int uNumLights;
uniform vec3 uCameraPos;
uniform vec3 uAmbientColor;
uniform float uAmbientStrength;
uniform vec3 uDiffuseColor;
uniform vec3 uSpecularColor;
uniform float uShininess;
uniform sampler2D uDiffuseMap;
uniform sampler2D uSpecularMap;
uniform sampler2D uNormalMap;
uniform bool uUseTextures;
uniform bool uUseNormalMap;

// 输出
out vec4 FragColor;

vec3 getNormal() {
    vec3 normal = normalize(fs_in.worldNormal);

    if (uUseNormalMap) {
        // 从法线贴图获取法线
        vec3 tangentNormal = texture(uNormalMap, fs_in.texCoord).rgb * 2.0 - 1.0;

        // TBN 矩阵 (简化版，假设切线空间已计算)
        vec3 Q1 = dFdx(fs_in.worldPos);
        vec3 Q2 = dFdy(fs_in.worldPos);
        vec2 st1 = dFdx(fs_in.texCoord);
        vec2 st2 = dFdy(fs_in.texCoord);

        vec3 T = normalize(Q1 * st2.y - Q2 * st1.y);
        vec3 B = -normalize(cross(normal, T));
        mat3 TBN = mat3(T, B, normal);

        normal = normalize(TBN * tangentNormal);
    }

    return normal;
}

vec3 blinnPhong(vec3 lightPos, vec3 lightColor, float lightIntensity,
                vec3 worldPos, vec3 normal, vec3 baseColor, vec3 specColor) {
    vec3 lightDir = normalize(lightPos - worldPos);
    vec3 viewDir = normalize(uCameraPos - worldPos);
    vec3 halfDir = normalize(lightDir + viewDir);

    // 漫反射
    float diff = max(dot(normal, lightDir), 0.0);
    vec3 diffuse = diff * lightColor * baseColor;

    // 镜面反射 (Blinn-Phong)
    float spec = pow(max(dot(normal, halfDir), 0.0), uShininess);
    vec3 specular = spec * lightColor * specColor;

    // 衰减
    float dist = length(lightPos - worldPos);
    float attenuation = 1.0 / (1.0 + 0.09 * dist + 0.032 * dist * dist);

    return (diffuse + specular) * lightIntensity * attenuation;
}

void main() {
    vec3 normal = getNormal();

    // 基础颜色
    vec3 baseColor = uDiffuseColor;
    vec3 specColor = uSpecularColor;

    if (uUseTextures) {
        baseColor *= texture(uDiffuseMap, fs_in.texCoord).rgb;
        specColor *= texture(uSpecularMap, fs_in.texCoord).rgb;
    }

    // 环境光
    vec3 result = uAmbientColor * uAmbientStrength * baseColor;

    // 累加所有光源
    for (int i = 0; i < uNumLights; i++) {
        result += blinnPhong(
            uLights[i].position,
            uLights[i].color,
            uLights[i].intensity,
            fs_in.worldPos,
            normal,
            baseColor,
            specColor
        );
    }

    FragColor = vec4(result, 1.0);
}
