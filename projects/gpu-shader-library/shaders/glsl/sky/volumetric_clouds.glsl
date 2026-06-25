#version 450 core
/**
 * 体积云着色器
 *
 * 功能：
 * - 噪声云层
 * - 光线步进
 * - 云层光照
 * - 动态形状
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler3D uNoiseTexture;
uniform sampler2D uDepthTexture;
uniform vec3 uCameraPos;
uniform vec3 uCameraDir;
uniform vec3 uSunDirection;
uniform vec3 uSunColor;
uniform float uTime;
uniform float uCloudSpeed;
uniform float uCloudScale;
uniform float uCloudHeight;
uniform float uCloudThickness;
uniform float uCloudDensity;
uniform float uCloudAbsorption;
uniform int uNumSteps;
uniform int uNumLightSteps;
uniform float uStepSize;

// 输出
out vec4 FragColor;

// 噪声采样
float sampleNoise(vec3 pos) {
    vec3 uvw = pos * uCloudScale * 0.001;
    uvw.xz += uTime * uCloudSpeed * 0.01;

    // 分形噪声
    float noise = 0.0;
    float amplitude = 1.0;
    float frequency = 1.0;

    for (int i = 0; i < 4; i++) {
        noise += texture(uNoiseTexture, uvw * frequency).r * amplitude;
        amplitude *= 0.5;
        frequency *= 2.0;
    }

    return noise;
}

// 云密度函数
float cloudDensity(vec3 pos) {
    // 基础形状
    float height = pos.y - uCloudHeight;
    float heightGradient = smoothstep(0.0, uCloudThickness * 0.3, height) *
                           smoothstep(uCloudThickness, uCloudThickness * 0.7, height);

    // 噪声
    float noise = sampleNoise(pos);

    // 密度
    float density = noise * heightGradient * uCloudDensity;

    return max(density, 0.0);
}

// 云层光照
float cloudLighting(vec3 pos, vec3 lightDir) {
    float density = 0.0;
    float stepSize = 20.0;

    for (int i = 0; i < uNumLightSteps; i++) {
        pos += lightDir * stepSize;
        density += cloudDensity(pos);
    }

    // Beer 定律
    float transmittance = exp(-density * uCloudAbsorption);

    // 粉色散射 (Henyey-Greenstein)
    float cosTheta = dot(lightDir, normalize(uCameraPos - pos));
    float phase = (1.0 - 0.5 * 0.5) / (4.0 * 3.14159 * pow(1.0 + 0.5 * 0.5 - 2.0 * 0.5 * cosTheta, 1.5));

    return transmittance * phase;
}

// 光线步进
vec4 raymarchClouds(vec3 rayOrigin, vec3 rayDir, float maxDist) {
    vec3 color = vec3(0.0);
    float transmittance = 1.0;

    // 确定步进范围
    float t = 0.0;

    for (int i = 0; i < uNumSteps; i++) {
        vec3 pos = rayOrigin + rayDir * t;

        float density = cloudDensity(pos);

        if (density > 0.001) {
            // 光照
            float light = cloudLighting(pos, -uSunDirection);

            // 累积颜色
            vec3 luminance = uSunColor * light;
            color += transmittance * density * luminance * uStepSize;

            // 透射率
            transmittance *= exp(-density * uCloudAbsorption * uStepSize);

            if (transmittance < 0.01) break;
        }

        t += uStepSize;
        if (t > maxDist) break;
    }

    return vec4(color, 1.0 - transmittance);
}

void main() {
    // 重建射线
    vec2 uv = texCoord * 2.0 - 1.0;
    vec3 rayDir = normalize(vec3(uv, -1.0));  // 简化投影

    // 深度测试
    float depth = texture(uDepthTexture, texCoord).r;
    float maxDist = 1000.0;
    if (depth < 1.0) {
        maxDist = depth * 1000.0;
    }

    // 射线步进
    vec4 cloudColor = raymarchClouds(uCameraPos, rayDir, maxDist);

    FragColor = cloudColor;
}
