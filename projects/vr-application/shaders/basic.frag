#version 450 core

// 从顶点着色器输入
in VS_OUT {
    vec3 FragPos;    // 世界空间位置
    vec3 Normal;     // 世界空间法线
    vec2 TexCoord;   // 纹理坐标
} fs_in;

// 输出颜色
out vec4 FragColor;

// 材质结构体
struct Material {
    vec3 ambient;      // 环境光反射系数
    vec3 diffuse;      // 漫反射系数
    vec3 specular;     // 镜面反射系数
    float shininess;   // 光泽度
    bool useTexture;   // 是否使用纹理
    sampler2D diffuseTexture;  // 漫反射纹理
};

// 方向光结构体
struct DirectionalLight {
    vec3 direction;    // 光照方向
    vec3 ambient;      // 环境光颜色
    vec3 diffuse;      // 漫反射颜色
    vec3 specular;     // 镜面反射颜色
};

// 点光源结构体
struct PointLight {
    vec3 position;     // 光源位置
    vec3 ambient;      // 环境光颜色
    vec3 diffuse;      // 漫反射颜色
    vec3 specular;     // 镜面反射颜色
    float constant;    // 常数衰减
    float linear;      // 线性衰减
    float quadratic;   // 二次衰减
};

// Uniform 变量
uniform Material material;
uniform DirectionalLight dirLight;
uniform PointLight pointLights[4];  // 最多支持 4 个点光源
uniform int numPointLights;
uniform vec3 viewPos;  // 相机位置

// 计算方向光
vec3 CalcDirectionalLight(DirectionalLight light, vec3 normal, vec3 viewDir)
{
    vec3 lightDir = normalize(-light.direction);

    // 漫反射
    float diff = max(dot(normal, lightDir), 0.0);

    // 镜面反射
    vec3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);

    // 合成
    vec3 ambient = light.ambient * material.ambient;
    vec3 diffuse = light.diffuse * diff * material.diffuse;
    vec3 specular = light.specular * spec * material.specular;

    return ambient + diffuse + specular;
}

// 计算点光源
vec3 CalcPointLight(PointLight light, vec3 normal, vec3 fragPos, vec3 viewDir)
{
    vec3 lightDir = normalize(light.position - fragPos);

    // 漫反射
    float diff = max(dot(normal, lightDir), 0.0);

    // 镜面反射
    vec3 reflectDir = reflect(-lightDir, normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), material.shininess);

    // 衰减
    float distance = length(light.position - fragPos);
    float attenuation = 1.0 / (light.constant + light.linear * distance +
                                light.quadratic * (distance * distance));

    // 合成
    vec3 ambient = light.ambient * material.ambient * attenuation;
    vec3 diffuse = light.diffuse * diff * material.diffuse * attenuation;
    vec3 specular = light.specular * spec * material.specular * attenuation;

    return ambient + diffuse + specular;
}

void main()
{
    // 归一化法线
    vec3 normal = normalize(fs_in.Normal);
    vec3 viewDir = normalize(viewPos - fs_in.FragPos);

    // 纹理颜色
    vec3 texColor = vec3(1.0);
    if (material.useTexture) {
        texColor = texture(material.diffuseTexture, fs_in.TexCoord).rgb;
    }

    // 计算方向光
    vec3 result = CalcDirectionalLight(dirLight, normal, viewDir);

    // 计算点光源
    for (int i = 0; i < numPointLights && i < 4; i++) {
        result += CalcPointLight(pointLights[i], normal, fs_in.FragPos, viewDir);
    }

    // 应用纹理
    result *= texColor;

    // Gamma 校正
    float gamma = 2.2;
    result = pow(result, vec3(1.0 / gamma));

    FragColor = vec4(result, 1.0);
}