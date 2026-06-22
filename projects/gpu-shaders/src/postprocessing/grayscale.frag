#version 330 core

// Grayscale Post-Processing Shader
// Converts the scene to grayscale using luminance weights.
// Uses the standard luminance formula: 0.2126*R + 0.7152*G + 0.0722*B

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform float intensity;  // 0.0 = full color, 1.0 = full grayscale

void main()
{
    vec4 color = texture(screenTexture, TexCoord);

    // Calculate luminance using perceptual weights
    float luminance = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));

    // Mix between original color and grayscale based on intensity
    vec3 gray = vec3(luminance);
    FragColor = vec4(mix(color.rgb, gray, intensity), color.a);
}
