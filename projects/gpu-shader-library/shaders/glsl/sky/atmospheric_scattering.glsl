#version 450 core
/**
 * 大气散射着色器
 *
 * 功能：
 * - Rayleigh 散射
 * - Mie 散射
 * - 太阳盘
 * - 地平线效果
 *
 * 基于 Sean O'Neil 的 GPU Gems 2 实现
 */

// 常量
const float PI = 3.14159265359;

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// Uniform
uniform vec3 uCameraPos;
uniform vec3 uSunDirection;
uniform vec3 uSunColor;
uniform float uSunIntensity;
uniform float uPlanetRadius;        // 地球半径
uniform float uAtmosphereRadius;    // 大气层半径
uniform vec3 uRayleighScattering;   // Rayleigh 散射系数
uniform float uMieScattering;       // Mie 散射系数
uniform float uRayleighScaleHeight; // Rayleigh 标高
uniform float uMieScaleHeight;      // Mie 标高
uniform float uMiePreferredDir;     // Mie 散射方向
uniform int uNumSamples;
uniform int uNumLightSamples;

// 输出
out vec4 FragColor;

// 光线-球体相交
vec2 raySphereIntersect(vec3 rayOrigin, vec3 rayDir, float radius) {
    float a = dot(rayDir, rayDir);
    float b = 2.0 * dot(rayOrigin, rayDir);
    float c = dot(rayOrigin, rayOrigin) - radius * radius;
    float discriminant = b * b - 4.0 * a * c;

    if (discriminant < 0.0) {
        return vec2(-1.0);
    }

    float sqrtDisc = sqrt(discriminant);
    return vec2(-b - sqrtDisc, -b + sqrtDisc) / (2.0 * a);
}

// Rayleigh 相位函数
float rayleighPhase(float cosTheta) {
    return 3.0 / (16.0 * PI) * (1.0 + cosTheta * cosTheta);
}

// Mie 相位函数 (Henyey-Greenstein)
float miePhase(float cosTheta, float g) {
    float g2 = g * g;
    float denom = 1.0 + g2 - 2.0 * g * cosTheta;
    return (1.0 - g2) / (4.0 * PI * denom * sqrt(denom));
}

// 大气散射计算
void calculateAtmosphere(vec3 rayOrigin, vec3 rayDir, float maxDist,
                         out vec3 rayleigh, out vec3 mie) {
    rayleigh = vec3(0.0);
    mie = vec3(0.0);

    // 步长
    float stepSize = maxDist / float(uNumSamples);

    // 光学深度
    float opticalDepthR = 0.0;
    float opticalDepthM = 0.0;

    for (int i = 0; i < uNumSamples; i++) {
        // 当前采样点
        vec3 samplePos = rayOrigin + rayDir * (float(i) + 0.5) * stepSize;
        float height = length(samplePos) - uPlanetRadius;

        // 密度
        float hr = exp(-height / uRayleighScaleHeight) * stepSize;
        float hm = exp(-height / uMieScaleHeight) * stepSize;

        opticalDepthR += hr;
        opticalDepthM += hm;

        // 到太阳的光学深度
        vec2 sunIntersect = raySphereIntersect(samplePos, uSunDirection, uAtmosphereRadius);
        float sunStepSize = sunIntersect.y / float(uNumLightSamples);
        float sunOpticalDepthR = 0.0;
        float sunOpticalDepthM = 0.0;

        for (int j = 0; j < uNumLightSamples; j++) {
            vec3 sunSamplePos = samplePos + uSunDirection * (float(j) + 0.5) * sunStepSize;
            float sunHeight = length(sunSamplePos) - uPlanetRadius;
            sunOpticalDepthR += exp(-sunHeight / uRayleighScaleHeight) * sunStepSize;
            sunOpticalDepthM += exp(-sunHeight / uMieScaleHeight) * sunStepSize;
        }

        // 散射
        vec3 tau = uRayleighScattering * (opticalDepthR + sunOpticalDepthR) +
                   uMieScattering * 1.1 * (opticalDepthM + sunOpticalDepthM);
        vec3 attenuation = exp(-tau);

        rayleigh += hr * attenuation;
        mie += hm * attenuation;
    }

    rayleigh *= uRayleighScattering;
    mie *= uMieScattering;
}

void main() {
    vec3 rayDir = normalize(fs_in.worldPos - uCameraPos);
    float maxDist = length(fs_in.worldPos - uCameraPos);

    // 确保光线指向大气层
    vec2 atmosphereIntersect = raySphereIntersect(uCameraPos, rayDir, uAtmosphereRadius);
    if (atmosphereIntersect.x > 0.0) {
        maxDist = min(maxDist, atmosphereIntersect.y);
    }

    vec3 rayleigh, mie;
    calculateAtmosphere(uCameraPos, rayDir, maxDist, rayleigh, mie);

    // 相位函数
    float cosTheta = dot(rayDir, -uSunDirection);
    float rayleighPhaseValue = rayleighPhase(cosTheta);
    float miePhaseValue = miePhase(cosTheta, uMiePreferredDir);

    // 最终颜色
    vec3 color = rayleigh * rayleighPhaseValue + mie * miePhaseValue;

    // 太阳盘
    float sunDisk = smoothstep(0.999, 0.9999, cosTheta);
    color += uSunColor * uSunIntensity * sunDisk;

    // 色调映射
    color = 1.0 - exp(-color * 2.0);

    FragColor = vec4(color, 1.0);
}
