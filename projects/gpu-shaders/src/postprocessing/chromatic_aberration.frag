#version 330 core

// Chromatic Aberration Post-Processing Shader
// Simulates lens distortion by offsetting the red, green, and blue
// channels slightly. This creates a color fringing effect seen
// in cheap or misaligned camera lenses.

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform float aberrationStrength;  // How much to offset channels
uniform vec2 screenCenter;         // Usually (0.5, 0.5)

void main()
{
    vec2 dir = TexCoord - screenCenter;
    float dist = length(dir);

    // Offset increases with distance from center
    vec2 offset = dir * dist * aberrationStrength;

    // Sample each channel with different offsets
    float r = texture(screenTexture, TexCoord + offset).r;
    float g = texture(screenTexture, TexCoord).g;
    float b = texture(screenTexture, TexCoord - offset).b;

    FragColor = vec4(r, g, b, 1.0);
}
