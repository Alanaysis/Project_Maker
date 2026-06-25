#version 450 core
/**
 * 透明度着色器
 *
 * 功能：
 * - Alpha 混合
 * - Alpha 测试
 * - 加法混合
 * - 顺序无关透明 (OIT)
 */

// 输入
in VS_OUT {
    vec3 worldPos;
    vec3 worldNormal;
    vec2 texCoord;
} fs_in;

// Uniform
uniform vec4 uBaseColor;
uniform sampler2D uDiffuseMap;
uniform sampler2D uAlphaMap;
uniform float uAlphaCutoff;         // Alpha 测试阈值
uniform int uBlendMode;             // 0: Alpha, 1: Additive, 2: Multiply
uniform bool uUseAlphaMap;
uniform bool uDoubleSided;

// 输出
// 对于 OIT，需要多个渲染目标
layout(location = 0) out vec4 FragColor;
layout(location = 1) out float FragAlpha;

void main() {
    // 双面渲染
    vec3 normal = normalize(fs_in.worldNormal);
    if (uDoubleSided && !gl_FrontFacing) {
        normal = -normal;
    }

    // 采样颜色
    vec4 color = uBaseColor * texture(uDiffuseMap, fs_in.texCoord);

    // Alpha 处理
    float alpha = color.a;
    if (uUseAlphaMap) {
        alpha *= texture(uAlphaMap, fs_in.texCoord).r;
    }

    // Alpha 测试
    if (alpha < uAlphaCutoff) {
        discard;
    }

    // 混合模式
    switch (uBlendMode) {
        case 0: // Alpha 混合
            FragColor = vec4(color.rgb * alpha, alpha);
            break;
        case 1: // 加法混合
            FragColor = vec4(color.rgb * alpha, 0.0);
            break;
        case 2: // 乘法混合
            FragColor = vec4(color.rgb, alpha);
            break;
        default:
            FragColor = vec4(color.rgb * alpha, alpha);
    }

    // OIT: 保存 alpha 用于后续混合
    FragAlpha = alpha;
}
