#version 330 core

// HDR Tone Mapping Post-Processing Shader
// Converts High Dynamic Range (HDR) colors to Low Dynamic Range (LDR)
// for display on standard monitors. Supports multiple tone mapping operators.

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D screenTexture;
uniform float exposure;
uniform int tonemapOperator;  // 0=Reinhard, 1=ACES, 2=Uncharted2

// Reinhard tone mapping
vec3 reinhard(vec3 color) {
    return color / (color + vec3(1.0));
}

// ACES filmic tone mapping (used in many games)
vec3 aces(vec3 x) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// Uncharted 2 tone mapping (filmic look)
vec3 uncharted2_tonemap_partial(vec3 x) {
    float A = 0.15;
    float B = 0.50;
    float C = 0.10;
    float D = 0.20;
    float E = 0.02;
    float F = 0.30;
    return ((x*(A*x+C*B)+D*E)/(x*(A*x+B)+D*F))-E/F;
}

vec3 uncharted2(vec3 color) {
    float W = 11.2;
    vec3 curr = uncharted2_tonemap_partial(color * 2.0);
    vec3 white_scale = vec3(1.0) / uncharted2_tonemap_partial(vec3(W));
    return curr * white_scale;
}

void main()
{
    vec4 color = texture(screenTexture, TexCoord);

    // Apply exposure
    vec3 mapped = color.rgb * exposure;

    // Apply selected tone mapping operator
    if (tonemapOperator == 0) {
        mapped = reinhard(mapped);
    } else if (tonemapOperator == 1) {
        mapped = aces(mapped);
    } else {
        mapped = uncharted2(mapped);
    }

    FragColor = vec4(mapped, color.a);
}
