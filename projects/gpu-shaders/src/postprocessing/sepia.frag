#version 330 core

// Sepia Post-Processing Shader
// Applies a sepia tone effect to simulate old photographs.
// First converts to grayscale, then applies a warm brown tint.

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform float intensity;  // 0.0 = original, 1.0 = full sepia

void main()
{
    vec4 color = texture(screenTexture, TexCoord);

    // Sepia transformation matrix
    vec3 sepia;
    sepia.r = dot(color.rgb, vec3(0.393, 0.769, 0.189));
    sepia.g = dot(color.rgb, vec3(0.349, 0.686, 0.168));
    sepia.b = dot(color.rgb, vec3(0.272, 0.534, 0.131));

    FragColor = vec4(mix(color.rgb, sepia, intensity), color.a);
}
