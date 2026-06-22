#version 330 core

// Solid Color Fragment Shader
// Outputs a uniform solid color for all fragments.
// Useful for debugging, wireframe rendering, or simple overlays.

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec4 color;

void main()
{
    FragColor = color;
}
