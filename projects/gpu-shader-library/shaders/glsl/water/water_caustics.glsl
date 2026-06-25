#version 450 core
/**
 * 焦散着色器
 *
 * 功能：
 * - 基于法线的焦散
 * - 动态焦散图案
 * - 水底投影
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uNormalTexture;
uniform sampler2D uDepthTexture;
uniform float uTime;
uniform float uCausticScale;
uniform float uCausticStrength;
uniform vec3 uWaterSurfacePos;
uniform vec3 uLightDir;

// 输出
out vec4 FragColor;

// 焦散噪声函数
float causticNoise(vec2 uv) {
    vec2 p = uv * 6.28318;
    float t = uTime * 0.5;

    float c = 0.0;
    c += sin(p.x * 3.0 + t) * cos(p.y * 2.0 - t) * 0.5;
    c += sin(p.x * 5.0 - t * 1.3) * cos(p.y * 4.0 + t * 0.7) * 0.25;
    c += sin(p.x * 8.0 + t * 0.8) * cos(p.y * 7.0 - t * 1.1) * 0.125;

    return c * 0.5 + 0.5;
}

// Voronoi 焦散
float voronoiCaustic(vec2 uv) {
    vec2 i = floor(uv);
    vec2 f = fract(uv);

    float minDist = 1.0;
    float secondMinDist = 1.0;

    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            vec2 neighbor = vec2(float(x), float(y));
            vec2 point = vec2(
                fract(sin(dot(i + neighbor, vec2(127.1, 311.7))) * 43758.5453),
                fract(sin(dot(i + neighbor, vec2(269.5, 183.3))) * 43758.5453)
            );

            // 动画
            point = 0.5 + 0.5 * sin(uTime * 0.5 + 6.28318 * point);

            vec2 diff = neighbor + point - f;
            float dist = length(diff);

            if (dist < minDist) {
                secondMinDist = minDist;
                minDist = dist;
            } else if (dist < secondMinDist) {
                secondMinDist = dist;
            }
        }
    }

    // 焦散由两个最近点之间的距离决定
    return secondMinDist - minDist;
}

// 基于法线的焦散
float normalBasedCaustic(vec2 uv) {
    vec3 normal = texture(uNormalTexture, uv).rgb * 2.0 - 1.0;

    // 使用法线偏移 UV 坐标
    vec2 offset1 = normal.xz * 0.1;
    vec2 offset2 = normal.xz * -0.08;

    float c1 = voronoiCaustic((uv + offset1) * uCausticScale);
    float c2 = voronoiCaustic((uv + offset2) * uCausticScale);

    // 干涉图案
    return c1 * c2 * 4.0;
}

void main() {
    // 计算焦散
    float caustic = normalBasedCaustic(texCoord);
    caustic = pow(caustic, 1.5) * uCausticStrength;

    // 基于深度衰减
    float depth = texture(uDepthTexture, texCoord).r;
    float depthFactor = smoothstep(0.0, 0.5, depth);

    caustic *= depthFactor;

    // 焦散颜色 (略微偏绿蓝)
    vec3 causticColor = vec3(0.2, 0.5, 0.4) * caustic;

    FragColor = vec4(causticColor, caustic);
}
