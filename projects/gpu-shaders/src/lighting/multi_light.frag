#version 330 core

// Multi-Light Fragment Shader
// Supports multiple light sources of different types simultaneously.
// Demonstrates how to combine ambient, directional, point, and spot lights.

#define MAX_POINT_LIGHTS 4
#define MAX_SPOT_LIGHTS 2

in vec3 FragPos;
in vec3 Normal;
in vec2 TexCoord;

out vec4 FragColor;

// Material properties
uniform vec3 objectColor;
uniform vec3 viewPos;
uniform float ambientStrength;
uniform float specularStrength;
uniform float shininess;

// Global ambient
uniform vec3 globalAmbient;

// Directional light
struct DirLight {
    vec3 direction;
    vec3 color;
    float intensity;
};

// Point light
struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
    float constant;
    float linear;
    float quadratic;
};

// Spot light
struct SpotLight {
    vec3 position;
    vec3 direction;
    vec3 color;
    float intensity;
    float innerCutoff;
    float outerCutoff;
    float constant;
    float linear;
    float quadratic;
};

uniform DirLight dirLight;
uniform int numPointLights;
uniform PointLight pointLights[MAX_POINT_LIGHTS];
uniform int numSpotLights;
uniform SpotLight spotLights[MAX_SPOT_LIGHTS];

// Calculate directional light contribution
vec3 calcDirLight(DirLight light, vec3 norm, vec3 viewDir)
{
    vec3 lightDir = normalize(-light.direction);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);

    vec3 diffuse = diff * light.color * light.intensity;
    vec3 specular = specularStrength * spec * light.color * light.intensity;

    return diffuse + specular;
}

// Calculate point light contribution
vec3 calcPointLight(PointLight light, vec3 norm, vec3 fragPos, vec3 viewDir)
{
    vec3 lightVec = light.position - fragPos;
    vec3 lightDir = normalize(lightVec);
    float distance = length(lightVec);
    float attenuation = 1.0 / (light.constant + light.linear * distance + light.quadratic * (distance * distance));

    float diff = max(dot(norm, lightDir), 0.0);
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);

    vec3 diffuse = diff * light.color * light.intensity * attenuation;
    vec3 specular = specularStrength * spec * light.color * light.intensity * attenuation;

    return diffuse + specular;
}

// Calculate spot light contribution
vec3 calcSpotLight(SpotLight light, vec3 norm, vec3 fragPos, vec3 viewDir)
{
    vec3 lightVec = light.position - fragPos;
    vec3 lightDir = normalize(lightVec);
    float distance = length(lightVec);
    float attenuation = 1.0 / (light.constant + light.linear * distance + light.quadratic * (distance * distance));

    float theta = dot(lightDir, normalize(-light.direction));
    float epsilon = light.innerCutoff - light.outerCutoff;
    float spotIntensity = clamp((theta - light.outerCutoff) / epsilon, 0.0, 1.0);

    float diff = max(dot(norm, lightDir), 0.0);
    vec3 halfwayDir = normalize(lightDir + viewDir);
    float spec = pow(max(dot(norm, halfwayDir), 0.0), shininess);

    vec3 diffuse = diff * light.color * light.intensity * attenuation * spotIntensity;
    vec3 specular = specularStrength * spec * light.color * light.intensity * attenuation * spotIntensity;

    return diffuse + specular;
}

void main()
{
    vec3 norm = normalize(Normal);
    vec3 viewDir = normalize(viewPos - FragPos);

    // Start with global ambient
    vec3 result = globalAmbient * ambientStrength * objectColor;

    // Add directional light
    result += calcDirLight(dirLight, norm, viewDir) * objectColor;

    // Add point lights
    for (int i = 0; i < numPointLights && i < MAX_POINT_LIGHTS; i++) {
        result += calcPointLight(pointLights[i], norm, FragPos, viewDir) * objectColor;
    }

    // Add spot lights
    for (int i = 0; i < numSpotLights && i < MAX_SPOT_LIGHTS; i++) {
        result += calcSpotLight(spotLights[i], norm, FragPos, viewDir) * objectColor;
    }

    FragColor = vec4(result, 1.0);
}
