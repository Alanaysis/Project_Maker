#version 330 core

// Point Light Fragment Shader
// Simulates a light source that emits light in all directions from a point.
// Light intensity decreases with distance (attenuation).
//
// Attenuation formula: 1.0 / (constant + linear*d + quadratic*d^2)

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec3 lightPos;
uniform vec3 lightColor;
uniform vec3 objectColor;
uniform vec3 viewPos;
uniform float ambientStrength;
uniform float specularStrength;
uniform float shininess;

// Attenuation parameters
uniform float constant;
uniform float linear;
uniform float quadratic;

void main()
{
    vec3 norm = normalize(Normal);

    // Calculate distance for attenuation
    vec3 lightVec = lightPos - FragPos;
    float distance = length(lightVec);
    float attenuation = 1.0 / (constant + linear * distance + quadratic * (distance * distance));

    // Ambient (not affected by attenuation)
    vec3 ambient = ambientStrength * lightColor;

    // Diffuse
    vec3 lightDir = normalize(lightVec);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * lightColor * attenuation;

    // Specular (Blinn-Phong)
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);
    vec3 specular = specularStrength * spec * lightColor * attenuation;

    vec3 result = (ambient + diffuse + specular) * objectColor;

    FragColor = vec4(result, 1.0);
}
