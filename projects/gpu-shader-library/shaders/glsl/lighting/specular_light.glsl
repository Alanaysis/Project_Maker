#version 450 core
/**
 * 镜面反射着色器 (Phong)
 *
 * 功能：
 * - Phong 镜面反射模型
 * - 可调光泽度
 * - 高光贴图支持
 *
 * Phong 公式：
 * I_specular = k_s * I_L * max(0, R . V)^n
 * R: 反射方向
 * V: 观察方向
 * n: 光泽度指数
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// Uniform
uniform vec3 uLightPos;
uniform vec3 uLightColor;
uniform float uLightIntensity;
uniform vec3 uCameraPos;
uniform vec3 uSpecularColor;
uniform float uShininess;
uniform float uSpecularStrength;
uniform sampler2D uSpecularMap;
uniform bool uUseSpecularMap;

// 输出
out vec4 FragColor;

vec3 reflect(vec3 I, vec3 N) {
    return I - 2.0 * dot(N, I) * N;
}

vec3 calculatePhongSpecular(vec3 worldPos, vec3 normal) {
    vec3 lightDir = normalize(uLightPos - worldPos);
    vec3 viewDir = normalize(uCameraPos - worldPos);

    // 反射方向 (Phong)
    vec3 reflectDir = reflect(-lightDir, normal);

    // 高光计算
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), uShininess);

    // 高光贴图
    float specularMap = 1.0;
    if (uUseSpecularMap) {
        specularMap = texture(uSpecularMap, fs_in.texCoord).r;
    }

    return uLightColor * uLightIntensity * spec * uSpecularColor * specularMap * uSpecularStrength;
}

void main() {
    vec3 normal = normalize(fs_in.worldNormal);
    vec3 specular = calculatePhongSpecular(fs_in.worldPos, normal);

    FragColor = vec4(specular, 1.0);
}
