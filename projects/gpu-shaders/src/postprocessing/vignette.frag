#version 330 core

// Vignette Post-Processing Shader
// Darkens the edges/corners of the screen to draw attention
// to the center. Commonly used in photography and film.

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform float vignetteRadius;    // Where the vignette starts (0.0-1.0)
uniform float vignetteSoftness;  // How soft the vignette edge is
uniform vec3 vignetteColor;      // Color of the vignette (usually black)

void main()
{
    vec4 color = texture(screenTexture, TexCoord);

    // Calculate distance from center
    vec2 center = vec2(0.5);
    float dist = distance(TexCoord, center);

    // Smooth vignette falloff
    float vignette = smoothstep(vignetteRadius, vignetteRadius - vignetteSoftness, dist);

    // Apply vignette
    vec3 result = mix(vignetteColor, color.rgb, vignette);

    FragColor = vec4(result, color.a);
}
