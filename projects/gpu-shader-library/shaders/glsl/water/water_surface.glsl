#version 450 core
/**
 * 水面着色器
 *
 * 功能：
 * - Gerstner 波浪
 * - 法线贴图混合
 * - Fresnel 反射/折射
 * - 深度着色
 * - 泡沫效果
 */

// 常量
const float PI = 3.14159265359;

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec4 clipPos;
} fs_in;

// Uniform
uniform vec3 uCameraPos;
uniform vec3 uLightDir;
uniform vec3 uLightColor;
uniform sampler2D uReflectionTexture;
uniform sampler2D uRefractionTexture;
uniform sampler2D uDepthTexture;
uniform sampler2D uNormalMap1;
uniform sampler2D uNormalMap2;
uniform sampler2D uFoamTexture;
uniform float uTime;
uniform float uWaveSpeed;
uniform float uWaveScale;
uniform vec3 uWaterColor;
uniform vec3 uDeepColor;
uniform float uFresnelPower;
uniform float uRefractionStrength;
uniform float uFoamThreshold;
uniform float uMaxDepth;

// 输出
out vec4 FragColor;

// Gerstner 波浪
vec3 gerstnerWave(vec2 pos, float amplitude, vec2 direction, float frequency, float steepness, float speed) {
    float k = 2.0 * PI * frequency;
    float c = speed;
    float f = k * (dot(direction, pos) - c * uTime);
    float a = amplitude;
    float s = steepness / (k * a);

    return vec3(
        s * a * direction.x * cos(f),
        a * sin(f),
        s * a * direction.y * cos(f)
    );
}

// 多层波浪叠加
vec3 calculateWaves(vec2 pos) {
    vec3 wave = vec3(0.0);

    // 波浪参数: 方向, 振幅, 频率, 陡度, 速度
    wave += gerstnerWave(pos, 0.3, normalize(vec2(1.0, 0.0)), 0.2, 0.5, 1.0);
    wave += gerstnerWave(pos, 0.2, normalize(vec2(0.0, 1.0)), 0.3, 0.4, 1.2);
    wave += gerstnerWave(pos, 0.15, normalize(vec2(1.0, 1.0)), 0.4, 0.3, 0.8);
    wave += gerstnerWave(pos, 0.1, normalize(vec2(-1.0, 0.5)), 0.5, 0.2, 1.5);

    return wave * uWaveScale;
}

// 水面法线计算
vec3 calculateWaterNormal(vec2 pos) {
    float epsilon = 0.01;
    vec3 center = calculateWaves(pos);
    vec3 dx = calculateWaves(pos + vec2(epsilon, 0.0));
    vec3 dz = calculateWaves(pos + vec2(0.0, epsilon));

    vec3 tangent = normalize(dx - center);
    vec3 bitangent = normalize(dz - center);
    return normalize(cross(bitangent, tangent));
}

void main() {
    // 波浪位移
    vec3 waveOffset = calculateWaves(fs_in.texCoord * 10.0);
    vec3 worldPos = fs_in.worldPos + waveOffset;

    // 计算法线
    vec3 waterNormal = calculateWaterNormal(fs_in.texCoord * 10.0);

    // 采样法线贴图 (双层混合)
    vec3 normal1 = texture(uNormalMap1, fs_in.texCoord * 4.0 + uTime * 0.02).rgb * 2.0 - 1.0;
    vec3 normal2 = texture(uNormalMap2, fs_in.texCoord * 8.0 - uTime * 0.015).rgb * 2.0 - 1.0;
    vec3 detailNormal = normalize(normal1 + normal2);

    // 混合法线
    vec3 finalNormal = normalize(waterNormal + detailNormal * 0.3);

    // 屏幕空间坐标
    vec2 screenPos = (fs_in.clipPos.xy / fs_in.clipPos.w) * 0.5 + 0.5;

    // 深度计算
    float depth = texture(uDepthTexture, screenPos).r;
    float floorDepth = linearizeDepth(depth);
    float waterDepth = linearizeDepth(gl_FragCoord.z);
    float relativeDepth = floorDepth - waterDepth;
    float depthFactor = clamp(relativeDepth / uMaxDepth, 0.0, 1.0);

    // Fresnel
    vec3 viewDir = normalize(uCameraPos - worldPos);
    float fresnel = pow(1.0 - max(dot(viewDir, finalNormal), 0.0), uFresnelPower);
    fresnel = clamp(fresnel, 0.0, 1.0);

    // 折射坐标偏移
    vec2 refractionOffset = finalNormal.xz * uRefractionStrength;
    vec2 refractionUV = screenPos + refractionOffset;

    // 反射和折射采样
    vec3 reflection = texture(uReflectionTexture, vec2(screenPos.x, 1.0 - screenPos.y)).rgb;
    vec3 refraction = texture(uRefractionTexture, refractionUV).rgb;

    // 深度颜色混合
    vec3 waterColor = mix(uWaterColor, uDeepColor, depthFactor);
    refraction = mix(refraction, waterColor, depthFactor * 0.5);

    // 反射/折射混合
    vec3 color = mix(refraction, reflection, fresnel);

    // 光照
    vec3 lightDir = normalize(-uLightDir);
    vec3 halfDir = normalize(lightDir + viewDir);
    float specular = pow(max(dot(finalNormal, halfDir), 0.0), 128.0);
    color += uLightColor * specular * 0.8;

    // 泡沫
    float foam = texture(uFoamTexture, fs_in.texCoord * 6.0 + uTime * 0.05).r;
    foam *= smoothstep(uFoamThreshold, uFoamThreshold + 0.1, waveOffset.y);
    color = mix(color, vec3(1.0), foam * 0.6);

    // 焦散 (简化)
    float caustic = texture(uNormalMap1, worldPos.xz * 0.5 + uTime * 0.1).r;
    caustic = pow(caustic, 2.0) * depthFactor;
    color += vec3(0.1, 0.2, 0.15) * caustic * 0.3;

    FragColor = vec4(color, 0.9);
}

// 辅助函数：线性化深度
float linearizeDepth(float depth) {
    float near = 0.1;
    float far = 1000.0;
    float z = depth * 2.0 - 1.0;
    return (2.0 * near * far) / (far + near - z * (far - near));
}
