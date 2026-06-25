#version 450 core
/**
 * 基础顶点着色器 - 顶点变换
 *
 * 功能：
 * - 模型空间 -> 世界空间 -> 观察空间 -> 裁剪空间变换
 * - 法线变换
 * - 纹理坐标传递
 *
 * 输入属性：
 * - aPosition: 顶点位置 (vec3)
 * - aNormal: 顶点法线 (vec3)
 * - aTexCoord: 纹理坐标 (vec2)
 *
 * Uniform 变量：
 * - uModel: 模型矩阵
 * - uView: 观察矩阵
 * - uProjection: 投影矩阵
 * - uNormalMatrix: 法线矩阵 (逆转置)
 */

// 顶点输入
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

// Uniform 变量
uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;
uniform mat3 uNormalMatrix;

// 输出到片段着色器
out VS_OUT {
    vec3 worldPos;      // 世界空间位置
    vec3 worldNormal;   // 世界空间法线
    vec2 texCoord;      // 纹理坐标
    vec4 clipPos;       // 裁剪空间位置
} vs_out;

void main() {
    // 模型空间 -> 世界空间
    vec4 worldPos = uModel * vec4(aPosition, 1.0);
    vs_out.worldPos = worldPos.xyz;

    // 法线变换 (使用法线矩阵保持正交性)
    vs_out.worldNormal = normalize(uNormalMatrix * aNormal);

    // 传递纹理坐标
    vs_out.texCoord = aTexCoord;

    // 世界空间 -> 观察空间 -> 裁剪空间
    vs_out.clipPos = uProjection * uView * worldPos;
    gl_Position = vs_out.clipPos;
}
