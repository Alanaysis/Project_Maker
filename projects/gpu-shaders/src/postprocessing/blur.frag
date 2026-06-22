#version 330 core

// Gaussian Blur Post-Processing Shader
// Applies a Gaussian blur effect using a kernel convolution.
// Supports configurable blur radius and direction for separable blur.

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform vec2 texelSize;    // 1.0 / textureSize
uniform float blurRadius;
uniform int horizontal;    // 0 = vertical pass, 1 = horizontal pass

// Gaussian weight for a given offset
float gaussianWeight(float x, float sigma) {
    return exp(-(x * x) / (2.0 * sigma * sigma)) / (sqrt(2.0 * 3.14159265) * sigma);
}

void main()
{
    float sigma = blurRadius / 3.0;
    vec3 result = vec3(0.0);
    float totalWeight = 0.0;

    // Sample along the blur direction
    for (float i = -blurRadius; i <= blurRadius; i += 1.0) {
        float weight = gaussianWeight(i, sigma);
        vec2 offset;
        if (horizontal == 1) {
            offset = vec2(i * texelSize.x, 0.0);
        } else {
            offset = vec2(0.0, i * texelSize.y);
        }
        result += texture(screenTexture, TexCoord + offset).rgb * weight;
        totalWeight += weight;
    }

    FragColor = vec4(result / totalWeight, 1.0);
}
