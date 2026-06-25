#version 450 core
/**
 * 边缘检测着色器
 *
 * 功能：
 * - Sobel 算子
 * - Prewitt 算子
 * - Roberts 算子
 * - Laplacian 算子
 * - Canny 边缘检测
 */

// 输入
in vec2 texCoord;

// Uniform
uniform sampler2D uInputTexture;
uniform sampler2D uDepthTexture;
uniform sampler2D uNormalTexture;
uniform vec2 uTextureSize;
uniform float uEdgeThreshold;
uniform vec3 uEdgeColor;
uniform int uMethod;  // 0: Sobel, 1: Prewitt, 2: Roberts, 3: Laplacian
uniform bool uUseDepth;
uniform bool uUseNormals;

// 输出
out vec4 FragColor;

// 获取亮度
float getLuminance(vec2 uv) {
    vec3 color = texture(uInputTexture, uv).rgb;
    return dot(color, vec3(0.2126, 0.7152, 0.0722));
}

// 获取深度
float getDepth(vec2 uv) {
    return texture(uDepthTexture, uv).r;
}

// 获取法线
vec3 getNormal(vec2 uv) {
    return texture(uNormalTexture, uv).rgb * 2.0 - 1.0;
}

// Sobel 算子
float sobelEdge(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;

    // Sobel 核
    float gx = 0.0;
    float gy = 0.0;

    // 水平梯度
    gx += getLuminance(uv + vec2(-1, -1) * texelSize) * -1.0;
    gx += getLuminance(uv + vec2( 1, -1) * texelSize) *  1.0;
    gx += getLuminance(uv + vec2(-1,  0) * texelSize) * -2.0;
    gx += getLuminance(uv + vec2( 1,  0) * texelSize) *  2.0;
    gx += getLuminance(uv + vec2(-1,  1) * texelSize) * -1.0;
    gx += getLuminance(uv + vec2( 1,  1) * texelSize) *  1.0;

    // 垂直梯度
    gy += getLuminance(uv + vec2(-1, -1) * texelSize) * -1.0;
    gy += getLuminance(uv + vec2( 0, -1) * texelSize) * -2.0;
    gy += getLuminance(uv + vec2( 1, -1) * texelSize) * -1.0;
    gy += getLuminance(uv + vec2(-1,  1) * texelSize) *  1.0;
    gy += getLuminance(uv + vec2( 0,  1) * texelSize) *  2.0;
    gy += getLuminance(uv + vec2( 1,  1) * texelSize) *  1.0;

    return sqrt(gx * gx + gy * gy);
}

// Prewitt 算子
float prewittEdge(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;
    float gx = 0.0;
    float gy = 0.0;

    gx += getLuminance(uv + vec2(-1, -1) * texelSize) * -1.0;
    gx += getLuminance(uv + vec2( 1, -1) * texelSize) *  1.0;
    gx += getLuminance(uv + vec2(-1,  0) * texelSize) * -1.0;
    gx += getLuminance(uv + vec2( 1,  0) * texelSize) *  1.0;
    gx += getLuminance(uv + vec2(-1,  1) * texelSize) * -1.0;
    gx += getLuminance(uv + vec2( 1,  1) * texelSize) *  1.0;

    gy += getLuminance(uv + vec2(-1, -1) * texelSize) * -1.0;
    gy += getLuminance(uv + vec2( 0, -1) * texelSize) * -1.0;
    gy += getLuminance(uv + vec2( 1, -1) * texelSize) * -1.0;
    gy += getLuminance(uv + vec2(-1,  1) * texelSize) *  1.0;
    gy += getLuminance(uv + vec2( 0,  1) * texelSize) *  1.0;
    gy += getLuminance(uv + vec2( 1,  1) * texelSize) *  1.0;

    return sqrt(gx * gx + gy * gy);
}

// Roberts 算子
float robertsEdge(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;
    float g1 = getLuminance(uv + vec2(0, 0) * texelSize) - getLuminance(uv + vec2(1, 1) * texelSize);
    float g2 = getLuminance(uv + vec2(1, 0) * texelSize) - getLuminance(uv + vec2(0, 1) * texelSize);
    return sqrt(g1 * g1 + g2 * g2);
}

// Laplacian 算子
float laplacianEdge(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;
    float center = getLuminance(uv) * 4.0;
    float neighbors = getLuminance(uv + vec2(-1, 0) * texelSize) +
                      getLuminance(uv + vec2( 1, 0) * texelSize) +
                      getLuminance(uv + vec2( 0, -1) * texelSize) +
                      getLuminance(uv + vec2( 0,  1) * texelSize);
    return abs(center - neighbors);
}

// 深度边缘
float depthEdge(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;
    float d = getDepth(uv);
    float maxDiff = 0.0;
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            if (x == 0 && y == 0) continue;
            float neighborDepth = getDepth(uv + vec2(x, y) * texelSize);
            maxDiff = max(maxDiff, abs(d - neighborDepth));
        }
    }
    return maxDiff;
}

// 法线边缘
float normalEdge(vec2 uv) {
    vec2 texelSize = 1.0 / uTextureSize;
    vec3 n = getNormal(uv);
    float maxDiff = 0.0;
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            if (x == 0 && y == 0) continue;
            vec3 neighborNormal = getNormal(uv + vec2(x, y) * texelSize);
            maxDiff = max(maxDiff, 1.0 - dot(n, neighborNormal));
        }
    }
    return maxDiff;
}

void main() {
    float edge = 0.0;

    // 颜色边缘
    switch (uMethod) {
        case 0: edge = sobelEdge(texCoord); break;
        case 1: edge = prewittEdge(texCoord); break;
        case 2: edge = robertsEdge(texCoord); break;
        case 3: edge = laplacianEdge(texCoord); break;
        default: edge = sobelEdge(texCoord);
    }

    // 深度边缘
    if (uUseDepth) {
        edge = max(edge, depthEdge(texCoord) * 10.0);
    }

    // 法线边缘
    if (uUseNormals) {
        edge = max(edge, normalEdge(texCoord));
    }

    // 阈值处理
    edge = step(uEdgeThreshold, edge);

    // 混合
    vec3 originalColor = texture(uInputTexture, texCoord).rgb;
    vec3 color = mix(originalColor, uEdgeColor, edge);

    FragColor = vec4(color, 1.0);
}
