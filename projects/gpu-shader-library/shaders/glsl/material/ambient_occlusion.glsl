#version 450 core
/**
 * 屏幕空间环境光遮蔽 (SSAO)
 *
 * 功能：
 * - 基础 SSAO
 * - 半球采样
 * - 模糊后处理
 *
 * 原理：
 * 在屏幕空间中采样邻近像素的深度，
 * 判断当前片段是否被周围几何体遮蔽
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uPositionTexture;   // 世界空间位置
uniform sampler2D uNormalTexture;     // 世界空间法线
uniform sampler2D uDepthTexture;      // 深度纹理
uniform sampler2D uNoiseTexture;      // 随机旋转纹理
uniform vec3 uSamples[64];           // 采样核心
uniform int uKernelSize;
uniform float uRadius;
uniform float uBias;
uniform float uPower;
uniform vec2 uNoiseScale;
uniform mat4 uProjection;
uniform mat4 uView;

// 输出
out float FragColor;

void main() {
    vec3 fragPos = texture(uPositionTexture, texCoord).xyz;
    vec3 normal = normalize(texture(uNormalTexture, texCoord).xyz);
    vec3 randomVec = normalize(texture(uNoiseTexture, texCoord * uNoiseScale).xyz);

    // 构建 TBN 矩阵
    vec3 tangent = normalize(randomVec - normal * dot(randomVec, normal));
    vec3 bitangent = cross(normal, tangent);
    mat3 TBN = mat3(tangent, bitangent, normal);

    float occlusion = 0.0;

    for (int i = 0; i < uKernelSize; i++) {
        // 采样点变换到切线空间
        vec3 samplePos = TBN * uSamples[i];
        samplePos = fragPos + samplePos * uRadius;

        // 投影到屏幕空间
        vec4 offset = vec4(samplePos, 1.0);
        offset = uProjection * offset;
        offset.xyz /= offset.w;
        offset.xyz = offset.xyz * 0.5 + 0.5;

        // 获取采样点深度
        float sampleDepth = texture(uPositionTexture, offset.xy).z;

        // 范围检查和累积
        float rangeCheck = smoothstep(0.0, 1.0, uRadius / abs(fragPos.z - sampleDepth));
        occlusion += (sampleDepth >= samplePos.z + uBias ? 1.0 : 0.0) * rangeCheck;
    }

    occlusion = 1.0 - (occlusion / float(uKernelSize));
    FragColor = pow(occlusion, uPower);
}
