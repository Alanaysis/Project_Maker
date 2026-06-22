#version 450 core

// 从顶点着色器输入
in vec2 TexCoord;

// 输出颜色
out vec4 FragColor;

// Uniform 变量
uniform sampler2D inputTexture;
uniform vec2 distortionCoefficients;  // k1, k2
uniform vec2 centerOffset;
uniform float scale;

void main()
{
    // 计算到中心的距离
    vec2 uv = TexCoord - 0.5 - centerOffset;
    float r2 = dot(uv, uv);
    float r4 = r2 * r2;

    // 应用畸变
    float distortion = 1.0 + distortionCoefficients.x * r2 +
                       distortionCoefficients.y * r4;

    vec2 distortedUV = uv * distortion * scale + 0.5 + centerOffset;

    // 检查边界
    if (distortedUV.x < 0.0 || distortedUV.x > 1.0 ||
        distortedUV.y < 0.0 || distortedUV.y > 1.0) {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        FragColor = texture(inputTexture, distortedUV);
    }
}