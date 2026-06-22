#version 330 core

// Bloom Post-Processing Shader (Bright Pass + Combine)
// Bloom makes bright areas glow by:
// 1. Extracting bright pixels (bright pass)
// 2. Blurring them (done externally with blur shader)
// 3. Combining the blurred bright pixels with the original scene
//
// This shader handles both the bright pass and the combine step.

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform sampler2D bloomTexture;  // Blurred bright pixels
uniform int passType;            // 0 = bright pass, 1 = combine
uniform float bloomThreshold;
uniform float bloomIntensity;

// Calculate perceived brightness
float luminance(vec3 color) {
    return dot(color, vec3(0.2126, 0.7152, 0.0722));
}

void main()
{
    vec4 color = texture(screenTexture, TexCoord);

    if (passType == 0) {
        // Bright pass: extract pixels above threshold
        float brightness = luminance(color.rgb);
        float contribution = max(brightness - bloomThreshold, 0.0);
        FragColor = vec4(color.rgb * contribution, 1.0);
    } else {
        // Combine: add blurred bloom to original scene
        vec3 bloom = texture(bloomTexture, TexCoord).rgb;
        vec3 result = color.rgb + bloom * bloomIntensity;

        // Reinhard tone mapping to prevent over-brightness
        result = result / (result + vec3(1.0));

        FragColor = vec4(result, color.a);
    }
}
