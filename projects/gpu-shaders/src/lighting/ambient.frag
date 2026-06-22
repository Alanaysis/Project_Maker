#version 330 core

// Ambient Lighting Fragment Shader
// Implements basic ambient lighting - the simplest lighting model.
// Ambient light provides a base illumination that is direction-independent.

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec3 ambientColor;
uniform float ambientStrength;
uniform vec3 objectColor;

void main()
{
    // Ambient contribution = ambient color * ambient strength
    vec3 ambient = ambientStrength * ambientColor;

    // Final color = object color modulated by ambient light
    vec3 result = ambient * objectColor;

    FragColor = vec4(result, 1.0);
}
