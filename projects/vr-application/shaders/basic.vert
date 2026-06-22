#version 450 core

// 顶点属性
layout (location = 0) in vec3 aPos;      // 顶点位置
layout (location = 1) in vec3 aNormal;   // 法线
layout (location = 2) in vec2 aTexCoord; // 纹理坐标

// 输出到片段着色器
out VS_OUT {
    vec3 FragPos;    // 世界空间位置
    vec3 Normal;     // 世界空间法线
    vec2 TexCoord;   // 纹理坐标
} vs_out;

// Uniform 变量
uniform mat4 model;       // 模型矩阵
uniform mat4 view;        // 视图矩阵
uniform mat4 projection;  // 投影矩阵

void main()
{
    // 计算世界空间位置
    vs_out.FragPos = vec3(model * vec4(aPos, 1.0));

    // 计算法线矩阵（处理非均匀缩放）
    vs_out.Normal = mat3(transpose(inverse(model))) * aNormal;

    // 传递纹理坐标
    vs_out.TexCoord = aTexCoord;

    // 计算裁剪空间位置
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}