#version 450 core
/**
 * 粒子渲染着色器 (几何着色器)
 *
 * 功能：
 * - 将点精灵扩展为四边形
 * - 面向相机 (Billboard)
 * - UV 坐标生成
 */

layout(points) in;
layout(triangle_strip, max_vertices = 4) out;

// 输入
in VS_OUT {
    vec4 color;
    float size;
    float age;
} gs_in[];

// 输出
out GS_OUT {
    vec2 texCoord;
    vec4 color;
    float age;
} gs_out;

// Uniform
uniform mat4 uProjection;
uniform mat4 uView;
uniform vec3 uCameraRight;
uniform vec3 uCameraUp;

void main() {
    vec3 center = gl_in[0].gl_Position.xyz;
    float halfSize = gs_in[0].size * 0.5;

    // 计算四边形顶点
    vec3 vertices[4];
    vertices[0] = center - uCameraRight * halfSize - uCameraUp * halfSize;
    vertices[1] = center + uCameraRight * halfSize - uCameraUp * halfSize;
    vertices[2] = center - uCameraRight * halfSize + uCameraUp * halfSize;
    vertices[3] = center + uCameraRight * halfSize + uCameraUp * halfSize;

    // UV 坐标
    vec2 uvs[4] = vec2[](
        vec2(0.0, 0.0),
        vec2(1.0, 0.0),
        vec2(0.0, 1.0),
        vec2(1.0, 1.0)
    );

    // 发射顶点
    for (int i = 0; i < 4; i++) {
        gl_Position = uProjection * uView * vec4(vertices[i], 1.0);
        gs_out.texCoord = uvs[i];
        gs_out.color = gs_in[0].color;
        gs_out.age = gs_in[0].age;
        EmitVertex();
    }

    EndPrimitive();
}
