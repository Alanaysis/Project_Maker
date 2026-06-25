#version 450 core
/**
 * 实例化渲染着色器
 *
 * 功能：
 * - 硬件实例化
 * - 实例属性 (位置、旋转、缩放)
 * - 实例颜色
 */

// 顶点属性
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

// 实例属性
layout(location = 3) in vec3 aInstancePos;      // 实例位置
layout(location = 4) in vec4 aInstanceRotation;  // 实例旋转 (四元数)
layout(location = 5) in vec3 aInstanceScale;     // 实例缩放
layout(location = 6) in vec4 aInstanceColor;     // 实例颜色

// Uniform
uniform mat4 uView;
uniform mat4 uProjection;
uniform mat3 uNormalMatrix;

// 输出
out VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
    vec4 instanceColor;
} vs_out;

// 四元数旋转
vec3 rotateByQuaternion(vec4 q, vec3 v) {
    vec3 t = 2.0 * cross(q.xyz, v);
    return v + q.w * t + cross(q.xyz, t);
}

void main() {
    // 应用实例变换
    vec3 scaledPos = aPosition * aInstanceScale;
    vec3 rotatedPos = rotateByQuaternion(aInstanceRotation, scaledPos);
    vec3 worldPos = rotatedPos + aInstancePos;

    // 法线变换
    vec3 rotatedNormal = rotateByQuaternion(aInstanceRotation, aNormal);

    vs_out.worldPos = worldPos;
    vs_out.worldNormal = normalize(rotatedNormal);
    vs_out.texCoord = aTexCoord;
    vs_out.instanceColor = aInstanceColor;

    gl_Position = uProjection * uView * vec4(worldPos, 1.0);
}
