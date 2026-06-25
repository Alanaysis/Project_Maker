#version 450 core
/**
 * 几何着色器 - 直通模式
 *
 * 功能：
 * - 将输入图元直接传递到下一阶段
 * - 可选法线可视化
 * - 支持点、线、三角形
 *
 * 输入布局：triangles
 * 输出布局：triangle_strip
 */

layout(triangles) in;
layout(triangle_strip, max_vertices = 3) out;

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec4 clipPos;
} gs_in[];

// 输出
out GS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec3 barycentric;  // 重心坐标 (用于线框渲染)
} gs_out;

// Uniform
uniform bool uShowNormals;
uniform float uNormalLength;

void emitVertex(int index, vec3 bary) {
    gl_Position = gl_in[index].gl_Position;
    gs_out.worldPos = gs_in[index].worldPos;
    gs_out.worldNormal = gs_in[index].worldNormal;
    gs_out.texCoord = gs_in[index].texCoord;
    gs_out.barycentric = bary;
    EmitVertex();
}

void main() {
    // 传递三角形，附加重心坐标
    emitVertex(0, vec3(1.0, 0.0, 0.0));
    emitVertex(1, vec3(0.0, 1.0, 0.0));
    emitVertex(2, vec3(0.0, 0.0, 1.0));
    EndPrimitive();
}
