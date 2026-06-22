#version 330 core

// Edge Detection Post-Processing Shader
// Uses the Sobel operator to detect edges in the scene.
// The Sobel operator applies two 3x3 kernels (horizontal and vertical)
// to detect intensity changes.

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform vec2 texelSize;
uniform float edgeStrength;
uniform vec3 edgeColor;
uniform vec3 backgroundColor;

void main()
{
    // Sobel kernels
    // Horizontal kernel:     Vertical kernel:
    // -1 -2 -1              -1  0  1
    //  0  0  0              -2  0  2
    //  1  2  1              -1  0  1

    // Sample the 3x3 neighborhood
    float tl = dot(texture(screenTexture, TexCoord + vec2(-texelSize.x, texelSize.y)).rgb, vec3(0.2126, 0.7152, 0.0722));
    float t  = dot(texture(screenTexture, TexCoord + vec2(0.0, texelSize.y)).rgb, vec3(0.2126, 0.7152, 0.0722));
    float tr = dot(texture(screenTexture, TexCoord + vec2(texelSize.x, texelSize.y)).rgb, vec3(0.2126, 0.7152, 0.0722));
    float l  = dot(texture(screenTexture, TexCoord + vec2(-texelSize.x, 0.0)).rgb, vec3(0.2126, 0.7152, 0.0722));
    float r  = dot(texture(screenTexture, TexCoord + vec2(texelSize.x, 0.0)).rgb, vec3(0.2126, 0.7152, 0.0722));
    float bl = dot(texture(screenTexture, TexCoord + vec2(-texelSize.x, -texelSize.y)).rgb, vec3(0.2126, 0.7152, 0.0722));
    float b  = dot(texture(screenTexture, TexCoord + vec2(0.0, -texelSize.y)).rgb, vec3(0.2126, 0.7152, 0.0722));
    float br = dot(texture(screenTexture, TexCoord + vec2(texelSize.x, -texelSize.y)).rgb, vec3(0.2126, 0.7152, 0.0722));

    // Apply Sobel kernels
    float edgeX = (-tl - 2.0*l - bl) + (tr + 2.0*r + br);
    float edgeY = (-tl - 2.0*t - tr) + (bl + 2.0*b + br);

    // Calculate edge magnitude
    float edge = sqrt(edgeX * edgeX + edgeY * edgeY) * edgeStrength;
    edge = clamp(edge, 0.0, 1.0);

    // Mix background with edge color
    vec3 result = mix(backgroundColor, edgeColor, edge);

    FragColor = vec4(result, 1.0);
}
