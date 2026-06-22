#version 330 core

// Diffuse (Lambertian) Lighting Fragment Shader
// Implements Lambertian diffuse reflection model.
// The brightness of a surface depends on the angle between
// the surface normal and the light direction.

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec3 lightPos;
uniform vec3 lightColor;
uniform vec3 objectColor;
uniform vec3 viewPos;
uniform float ambientStrength;

void main()
{
    // Normalize interpolated normal
    vec3 norm = normalize(Normal);

    // Calculate light direction (from fragment to light)
    vec3 lightDir = normalize(lightPos - FragPos);

    // Diffuse shading (Lambert's cosine law)
    float diff = max(dot(norm, lightDir), 0.0);

    // Combine ambient and diffuse
    vec3 ambient = ambientStrength * lightColor;
    vec3 diffuse = diff * lightColor;

    vec3 result = (ambient + diffuse) * objectColor;

    FragColor = vec4(result, 1.0);
}
