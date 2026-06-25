#version 450 core
/**
 * 体积光着色器 (光轴/上帝之光)
 *
 * 功能：
 * - 光轴效果
 * - 遮挡采样
 * - 散射计算
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uDepthTexture;
uniform sampler2D uShadowMap;
uniform vec3 uLightPos;
uniform vec3 uLightColor;
uniform float uLightIntensity;
uniform vec3 uCameraPos;
uniform float uDensity;
uniform float uDecay;
uniform float uWeight;
uniform float uExposure;
uniform int uNumSamples;
uniform mat4 uLightViewProjection;
uniform vec2 uScreenLightPos;  // 光源屏幕位置

// 输出
out vec4 FragColor;

// 线性化深度
float linearizeDepth(float depth) {
    float near = 0.1;
    float far = 1000.0;
    float z = depth * 2.0 - 1.0;
    return (2.0 * near * far) / (far + near - z * (far - near));
}

// 光轴计算
vec3 volumetricLight(vec2 uv) {
    // 从当前像素到光源的方向
    vec2 deltaTexCoord = (uv - uScreenLightPos);
    deltaTexCoord *= 1.0 / float(uNumSamples) * uDensity;

    vec2 sampleCoord = uv;
    float illumination = 0.0;
    float decay = 1.0;

    for (int i = 0; i < uNumSamples; i++) {
        sampleCoord -= deltaTexCoord;

        // 采样深度
        float depth = texture(uDepthTexture, sampleCoord).r;

        // 阴影测试
        vec4 lightSpacePos = uLightViewProjection * vec4(vec3(sampleCoord, depth), 1.0);
        vec3 shadowCoord = lightSpacePos.xyz / lightSpacePos.w * 0.5 + 0.5;
        float shadowDepth = texture(uShadowMap, shadowCoord.xy).r;
        float shadow = shadowCoord.z > shadowDepth + 0.001 ? 0.0 : 1.0;

        illumination += shadow * decay * uWeight;
        decay *= uDecay;
    }

    illumination /= float(uNumSamples);

    return uLightColor * illumination * uLightIntensity;
}

void main() {
    vec3 light = volumetricLight(texCoord);

    // 曝光
    light *= uExposure;

    FragColor = vec4(light, 1.0);
}
