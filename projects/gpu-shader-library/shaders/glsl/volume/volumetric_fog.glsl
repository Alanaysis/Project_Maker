#version 450 core
/**
 * 体积雾着色器
 *
 * 功能：
 * - 基于高度的雾
 * - 噪声雾
 * - 光照雾
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uDepthTexture;
uniform sampler3D uNoiseTexture;
uniform vec3 uCameraPos;
uniform vec3 uFogColor;
uniform float uFogDensity;
uniform float uFogStart;
uniform float uFogEnd;
uniform float uFogHeight;
uniform float uFogHeightFalloff;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform float uLightScattering;
uniform float uTime;
uniform float uNoiseScale;
uniform int uNumSteps;
uniform mat4 uInverseViewProjection;

// 输出
out vec4 FragColor;

// 线性化深度
float linearizeDepth(float depth) {
    float near = 0.1;
    float far = 1000.0;
    float z = depth * 2.0 - 1.0;
    return (2.0 * near * far) / (far + near - z * (far - near));
}

// 重建世界位置
vec3 worldPosFromDepth(vec2 uv, float depth) {
    vec4 clipPos = vec4(uv * 2.0 - 1.0, depth * 2.0 - 1.0, 1.0);
    vec4 worldPos = uInverseViewProjection * clipPos;
    return worldPos.xyz / worldPos.w;
}

// 基于高度的雾密度
float heightFog(vec3 pos) {
    float height = pos.y - uFogHeight;
    return exp(-height * uFogHeightFalloff) * uFogDensity;
}

// 噪声雾密度
float noiseFog(vec3 pos) {
    vec3 uvw = pos * uNoiseScale * 0.01;
    uvw.xz += uTime * 0.02;

    float noise = texture(uNoiseTexture, uvw).r;
    noise += texture(uNoiseTexture, uvw * 2.0).r * 0.5;
    noise += texture(uNoiseTexture, uvw * 4.0).r * 0.25;

    return noise / 1.75;
}

// 光照雾 (Mie 散射)
float lightScattering(vec3 viewDir, vec3 lightDir) {
    float cosTheta = dot(viewDir, lightDir);
    // Henyey-Greenstein 相位函数
    float g = 0.8;
    float g2 = g * g;
    return (1.0 - g2) / (4.0 * 3.14159 * pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5));
}

void main() {
    float depth = texture(uDepthTexture, texCoord).r;
    vec3 worldPos = worldPosFromDepth(texCoord, depth);
    vec3 viewDir = normalize(worldPos - uCameraPos);

    float linearDepth = linearizeDepth(depth);
    float distance = length(worldPos - uCameraPos);

    // 距离雾因子
    float distanceFog = smoothstep(uFogStart, uFogEnd, distance);

    // 光线步进采样雾密度
    float fogAmount = 0.0;
    vec3 fogLight = vec3(0.0);
    float stepSize = distance / float(uNumSteps);

    for (int i = 0; i < uNumSteps; i++) {
        float t = (float(i) + 0.5) / float(uNumSteps);
        vec3 samplePos = mix(uCameraPos, worldPos, t);

        // 雾密度
        float density = heightFog(samplePos) * noiseFog(samplePos);
        fogAmount += density * stepSize;

        // 光照散射
        float scattering = lightScattering(viewDir, -uLightDir);
        fogLight += uLightColor * scattering * density * stepSize * uLightScattering;
    }

    fogAmount = 1.0 - exp(-fogAmount);
    fogAmount *= distanceFog;

    // 最终颜色
    vec3 color = mix(uFogColor, uFogColor + fogLight, 0.5);

    FragColor = vec4(color, fogAmount);
}
