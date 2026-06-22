#version 330 core

// Gradient Fragment Shader
// Creates various gradient patterns based on texture coordinates.
// Supports linear, radial, and angular gradient types.

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec4 colorStart;
uniform vec4 colorEnd;
uniform int gradientType;  // 0=linear, 1=radial, 2=angular
uniform vec2 gradientDir;  // Direction for linear gradient (normalized)

void main()
{
    float t = 0.0;

    if (gradientType == 0) {
        // Linear gradient along specified direction
        t = dot(TexCoord - vec2(0.5), normalize(gradientDir)) + 0.5;
    } else if (gradientType == 1) {
        // Radial gradient from center
        t = length(TexCoord - vec2(0.5)) * 2.0;
    } else {
        // Angular gradient
        vec2 centered = TexCoord - vec2(0.5);
        t = atan(centered.y, centered.x) / (2.0 * 3.14159265) + 0.5;
    }

    t = clamp(t, 0.0, 1.0);
    FragColor = mix(colorStart, colorEnd, t);
}
