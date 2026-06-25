#version 450 core
/**
 * 折射着色器
 *
 * 功能：
 * - Snell 定律折射
 * - 色散效果
 * - Fresnel 反射/折射混合
 * - 透明材质
 *
 * Snell 定律：
 * n1 * sin(theta1) = n2 * sin(theta2)
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// Uniform
uniform vec3 uCameraPos;
uniform samplerCube uEnvMap;
uniform float uIOR;                  // 折射率 (Index of Refraction)
uniform float uFresnelPower;
uniform vec3 uRefractionTint;        // 折射颜色染色
uniform float uOpacity;
uniform bool uUseDispersion;         // 色散
uniform float uDispersionStrength;
uniform float uThickness;            // 材质厚度

// 输出
out vec4 FragColor;

// 折射计算
vec3 refract(vec3 I, vec3 N, float eta) {
    float k = 1.0 - eta * eta * (1.0 - dot(N, I) * dot(N, I));
    if (k < 0.0) {
        return vec3(0.0); // 全内反射
    }
    return eta * I - (eta * dot(N, I) + sqrt(k)) * N;
}

// Fresnel (Schlick)
float fresnelSchlick(vec3 viewDir, vec3 normal, float ior) {
    float cosTheta = max(dot(viewDir, normal), 0.0);
    float r0 = pow((1.0 - ior) / (1.0 + ior), 2.0);
    return r0 + (1.0 - r0) * pow(1.0 - cosTheta, 5.0);
}

// 色散折射
vec3 dispersedRefraction(vec3 I, vec3 N) {
    // 不同波长不同折射率
    float iorR = uIOR - uDispersionStrength;
    float iorG = uIOR;
    float iorB = uIOR + uDispersionStrength;

    vec3 refractR = refract(I, N, 1.0 / iorR);
    vec3 refractG = refract(I, N, 1.0 / iorG);
    vec3 refractB = refract(I, N, 1.0 / iorB);

    float r = texture(uEnvMap, refractR).r;
    float g = texture(uEnvMap, refractG).g;
    float b = texture(uEnvMap, refractB).b;

    return vec3(r, g, b);
}

void main() {
    vec3 normal = normalize(fs_in.worldNormal);
    vec3 viewDir = normalize(uCameraPos - fs_in.worldPos);

    // 折射
    vec3 refractDir = refract(-viewDir, normal, 1.0 / uIOR);

    vec3 refractionColor;
    if (uUseDispersion) {
        refractionColor = dispersedRefraction(-viewDir, normal);
    } else {
        refractionColor = texture(uEnvMap, refractDir).rgb;
    }

    // 应用颜色染色 (模拟材质吸收)
    vec3 absorbance = exp(-uRefractionTint * uThickness);
    refractionColor *= absorbance;

    // 反射
    vec3 reflectDir = reflect(-viewDir, normal);
    vec3 reflectionColor = texture(uEnvMap, reflectDir).rgb;

    // Fresnel 混合
    float fresnel = fresnelSchlick(viewDir, normal, uIOR);

    vec3 color = mix(refractionColor, reflectionColor, fresnel);

    FragColor = vec4(color, uOpacity);
}
