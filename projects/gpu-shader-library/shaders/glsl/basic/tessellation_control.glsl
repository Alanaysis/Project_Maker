#version 450 core
/**
 * 曲面细分控制着色器
 *
 * 功能：
 * - 控制细分级别
 * - 基于距离的自适应细分
 * - 传递顶点数据
 *
 * 输入：三角形 (3 个控制点)
 * 输出：三角形 (3 个控制点 + 细分因子)
 */

layout(vertices = 3) out;

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec4 clipPos;
} tcs_in[];

// 输出
out TCS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} tcs_out[];

// Uniform
uniform vec3 uCameraPos;
uniform float uTessLevelInner;
uniform float uTessLevelOuter;
uniform float uMinTessLevel;
uniform float uMaxTessLevel;
uniform float uMinDistance;
uniform float uMaxDistance;

float calculateTessLevel(vec3 worldPos) {
    float distance = length(worldPos - uCameraPos);
    float normalizedDistance = clamp(
        (distance - uMinDistance) / (uMaxDistance - uMinDistance),
        0.0, 1.0
    );
    // 距离越远，细分级别越低
    return mix(uMaxTessLevel, uMinTessLevel, normalizedDistance);
}

void main() {
    // 传递控制点数据
    tcs_out[gl_InvocationID].worldPos = tcs_in[gl_InvocationID].worldPos;
    tcs_out[gl_InvocationID].worldNormal = tcs_in[gl_InvocationID].worldNormal;
    tcs_out[gl_InvocationID].texCoord = tcs_in[gl_InvocationID].texCoord;

    // 计算细分因子 (仅第一个 invocation 执行)
    if (gl_InvocationID == 0) {
        // 基于边中点距离计算外部细分因子
        vec3 edgeMid01 = (tcs_in[0].worldPos + tcs_in[1].worldPos) * 0.5;
        vec3 edgeMid12 = (tcs_in[1].worldPos + tcs_in[2].worldPos) * 0.5;
        vec3 edgeMid20 = (tcs_in[2].worldPos + tcs_in[0].worldPos) * 0.5;

        gl_TessLevelOuter[0] = calculateTessLevel(edgeMid12);
        gl_TessLevelOuter[1] = calculateTessLevel(edgeMid20);
        gl_TessLevelOuter[2] = calculateTessLevel(edgeMid01);

        // 内部细分级别取外部的平均值
        gl_TessLevelInner[0] = (
            gl_TessLevelOuter[0] +
            gl_TessLevelOuter[1] +
            gl_TessLevelOuter[2]
        ) / 3.0;
    }
}
