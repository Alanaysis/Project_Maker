#version 450 core
/**
 * 曲面细分求值着色器
 *
 * 功能：
 * - 执行实际的细分计算
 * - Phong 曲面细分
 * - 置换贴图
 *
 * 输入：细分后的控制点
 * 输出：细分后的顶点
 */

layout(triangles, equal_spacing, ccw) in;

// 输入
in TCS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} tes_in[];

// 输出
out TES_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec3 displacement;
} tes_out;

// Uniform
uniform sampler2D uDisplacementMap;
uniform float uDisplacementScale;
uniform bool uUseDisplacement;
uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;

vec2 interpolateVec2(vec2 v0, vec2 v1, vec2 v2) {
    return v0 * gl_TessCoord.x +
           v1 * gl_TessCoord.y +
           v2 * gl_TessCoord.z;
}

vec3 interpolateVec3(vec3 v0, vec3 v1, vec3 v2) {
    return v0 * gl_TessCoord.x +
           v1 * gl_TessCoord.y +
           v2 * gl_TessCoord.z;
}

void main() {
    // 插值纹理坐标
    vec2 texCoord = interpolateVec2(
        tes_in[0].texCoord,
        tes_in[1].texCoord,
        tes_in[2].texCoord
    );

    // 插值世界位置
    vec3 worldPos = interpolateVec3(
        tes_in[0].worldPos,
        tes_in[1].worldPos,
        tes_in[2].worldPos
    );

    // 插值法线
    vec3 worldNormal = normalize(interpolateVec3(
        tes_in[0].worldNormal,
        tes_in[1].worldNormal,
        tes_in[2].worldNormal
    ));

    // 置换贴图偏移
    vec3 displacement = vec3(0.0);
    if (uUseDisplacement) {
        float height = texture(uDisplacementMap, texCoord).r;
        displacement = worldNormal * height * uDisplacementScale;
        worldPos += displacement;
    }

    tes_out.worldPos = worldPos;
    tes_out.worldNormal = worldNormal;
    tes_out.texCoord = texCoord;
    tes_out.displacement = displacement;

    gl_Position = uProjection * uView * vec4(worldPos, 1.0);
}
