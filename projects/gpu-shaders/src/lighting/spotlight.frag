#version 330 core

// Spotlight Fragment Shader
// Simulates a flashlight-like light source that emits a cone of light.
// Features inner and outer cutoff angles for soft edges.

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

uniform vec3 lightPos;
uniform vec3 lightDir;    // Direction the spotlight is pointing
uniform vec3 lightColor;
uniform vec3 objectColor;
uniform vec3 viewPos;
uniform float ambientStrength;
uniform float specularStrength;
uniform float shininess;

// Spotlight parameters
uniform float innerCutoff;  // Cosine of inner cutoff angle
uniform float outerCutoff;  // Cosine of outer cutoff angle

// Attenuation
uniform float constant;
uniform float linear;
uniform float quadratic;

void main()
{
    vec3 norm = normalize(Normal);
    vec3 lightVec = lightPos - FragPos;
    vec3 lightDirNorm = normalize(lightVec);

    // Spotlight intensity based on angle
    float theta = dot(lightDirNorm, normalize(-lightDir));
    float epsilon = innerCutoff - outerCutoff;
    float spotIntensity = clamp((theta - outerCutoff) / epsilon, 0.0, 1.0);

    // Attenuation
    float distance = length(lightVec);
    float attenuation = 1.0 / (constant + linear * distance + quadratic * (distance * distance));

    // Ambient
    vec3 ambient = ambientStrength * lightColor;

    // Diffuse
    float diff = max(dot(norm, lightDirNorm), 0.0);
    vec3 diffuse = diff * lightColor * attenuation * spotIntensity;

    // Specular (Blinn-Phong)
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 halfwayDir = normalize(lightDirNorm + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);
    vec3 specular = specularStrength * spec * lightColor * attenuation * spotIntensity;

    vec3 result = (ambient + diffuse + specular) * objectColor;

    FragColor = vec4(result, 1.0);
}
