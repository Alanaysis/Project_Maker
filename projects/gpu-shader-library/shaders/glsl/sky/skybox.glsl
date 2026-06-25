#version 450 core
/**
 * 天空盒着色器
 *
 * 功能：
 * - 立方体贴图天空盒
 * - 天空穹
 * - 日出日落效果
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// Uniform
uniform samplerCube uSkyboxTexture;
uniform float uExposure;
uniform float uRotation;
uniform bool uUseSun;
uniform vec3 uSunDirection;
uniform vec3 uSunColor;
uniform float uSunSize;
uniform float uSunHaloSize;
uniform vec3 uSkyColor;
uniform vec3 uHorizonColor;

// 输出
out vec4 FragColor;

// 太阳盘
vec3 sunDisk(vec3 rayDir) {
    float cosAngle = dot(rayDir, -uSunDirection);

    // 太阳盘
    float sunDisk = smoothstep(cos(uSunSize), cos(uSunSize * 0.9), cosAngle);

    // 光晕
    float halo = pow(max(cosAngle, 0.0), uSunHaloSize);

    return uSunColor * (sunDisk + halo * 0.3);
}

// 日出日落渐变
vec3 sunriseSunset(vec3 rayDir) {
    float height = rayDir.y;

    // 天空颜色渐变
    vec3 skyGradient = mix(uHorizonColor, uSkyColor, smoothstep(0.0, 0.5, height));

    // 日出日落染色
    float sunHeight = -uSunDirection.y;
    float sunsetFactor = smoothstep(-0.2, 0.0, sunHeight) * smoothstep(0.2, 0.0, sunHeight);

    vec3 sunsetColor = vec3(1.0, 0.5, 0.2);
    float horizonGlow = pow(max(1.0 - abs(height), 0.0), 4.0);

    skyGradient += sunsetColor * horizonGlow * sunsetFactor;

    return skyGradient;
}

void main() {
    // 归一化方向
    vec3 rayDir = normalize(fs_in.worldPos);

    // 旋转
    float angle = uRotation * 3.14159 / 180.0;
    mat2 rotation = mat2(cos(angle), -sin(angle), sin(angle), cos(angle));
    vec3 rotatedDir = vec3(rotation * rayDir.xz, rayDir.y).xzy;

    // 天空盒采样
    vec3 skyColor = texture(uSkyboxTexture, rotatedDir).rgb;

    // 或者使用程序化天空
    // vec3 skyColor = sunriseSunset(rayDir);

    // 太阳
    if (uUseSun) {
        skyColor += sunDisk(rayDir);
    }

    // 曝光
    skyColor *= uExposure;

    FragColor = vec4(skyColor, 1.0);
}
