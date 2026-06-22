#version 330 core

// Texture Fragment Shader
// Samples a 2D texture and applies optional tinting.
// Demonstrates basic texture sampling in GLSL.

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D textureSampler;
uniform vec4 tintColor;
uniform float tintStrength;

void main()
{
    vec4 texColor = texture(textureSampler, TexCoord);

    // Blend texture color with tint color
    FragColor = mix(texColor, tintColor, tintStrength);
}
