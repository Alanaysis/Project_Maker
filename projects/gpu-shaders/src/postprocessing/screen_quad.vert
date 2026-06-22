#version 330 core

// Screen Quad Vertex Shader
// Used for post-processing effects. Renders a full-screen quad
// and passes texture coordinates to the fragment shader.

layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

void main()
{
    TexCoord = aTexCoord;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
