#pragma once

#include "Common.h"
#include <string>
#include <unordered_map>

namespace vr {

// 着色器类型
enum class ShaderType {
    Vertex,
    Fragment,
    Geometry,
    Compute
};

// 着色器源码
struct ShaderSource {
    std::string vertexCode;
    std::string fragmentCode;
    std::string geometryCode;
    std::string computeCode;
};

// 着色器类
class Shader {
public:
    Shader();
    ~Shader();

    // 禁用拷贝
    Shader(const Shader&) = delete;
    Shader& operator=(const Shader&) = delete;

    // 移动语义
    Shader(Shader&& other) noexcept;
    Shader& operator=(Shader&& other) noexcept;

    // 加载着色器
    bool LoadFromFile(const std::string& vertexPath, const std::string& fragmentPath);
    bool LoadFromSource(const std::string& vertexSource, const std::string& fragmentSource);
    bool LoadFromSource(const ShaderSource& source);

    // 编译着色器
    bool Compile();

    // 使用着色器
    void Use() const;
    void Unuse() const;

    // 获取程序 ID
    GLuint GetProgramID() const { return m_programID; }

    // 设置 Uniform 变量
    void SetBool(const std::string& name, bool value);
    void SetInt(const std::string& name, int value);
    void SetFloat(const std::string& name, float value);
    void SetVec2(const std::string& name, const Vec2& value);
    void SetVec3(const std::string& name, const Vec3& value);
    void SetVec4(const std::string& name, const Vec4& value);
    void SetMat3(const std::string& name, const Mat3& value);
    void SetMat4(const std::string& name, const Mat4& value);

    // 批量设置
    void SetVec3Array(const std::string& name, const Vec3* values, int count);
    void SetMat4Array(const std::string& name, const Mat4* values, int count);

    // 获取 Uniform 位置
    GLint GetUniformLocation(const std::string& name);

    // 检查状态
    bool IsCompiled() const { return m_isCompiled; }
    bool IsValid() const { return m_programID != 0; }

    // 销毁着色器
    void Destroy();

private:
    // 编译单个着色器
    GLuint CompileShader(ShaderType type, const std::string& source);

    // 链接程序
    bool LinkProgram();

    // 检查错误
    bool CheckCompileError(GLuint shader, ShaderType type);
    bool CheckLinkError(GLuint program);

    // 成员变量
    GLuint m_programID = 0;
    GLuint m_vertexShader = 0;
    GLuint m_fragmentShader = 0;
    GLuint m_geometryShader = 0;
    GLuint m_computeShader = 0;

    bool m_isCompiled = false;

    // Uniform 位置缓存
    std::unordered_map<std::string, GLint> m_uniformLocationCache;

    // 着色器源码
    ShaderSource m_source;
};

// 着色器管理器
class ShaderManager {
public:
    static ShaderManager& GetInstance();

    // 加载着色器
    SharedPtr<Shader> LoadShader(const std::string& name,
                                  const std::string& vertexPath,
                                  const std::string& fragmentPath);

    // 获取着色器
    SharedPtr<Shader> GetShader(const std::string& name);

    // 创建内置着色器
    SharedPtr<Shader> CreateBuiltinShader(const std::string& name);

    // 清理
    void Clear();

private:
    ShaderManager() = default;

    std::unordered_map<std::string, SharedPtr<Shader>> m_shaders;
};

// 内置着色器源码
namespace BuiltinShaders {

// 基础顶点着色器
constexpr const char* BASIC_VERTEX = R"(
#version 450 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoord;

out VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoord;
} vs_out;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    vs_out.FragPos = vec3(model * vec4(aPos, 1.0));
    vs_out.Normal = mat3(transpose(inverse(model))) * aNormal;
    vs_out.TexCoord = aTexCoord;

    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
)";

// 基础片段着色器
constexpr const char* BASIC_FRAGMENT = R"(
#version 450 core

in VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoord;
} fs_in;

out vec4 FragColor;

// 材质
struct Material {
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float shininess;
    bool useTexture;
    sampler2D diffuseTexture;
};

// 方向光
struct DirectionalLight {
    vec3 direction;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};

// 点光源
struct PointLight {
    vec3 position;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
    float constant;
    float linear;
    float quadratic;
};

uniform Material material;
uniform DirectionalLight dirLight;
uniform PointLight pointLights[4];
uniform int numPointLights;
uniform vec3 viewPos;

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
    vec3 normal = normalize(fs_in.Normal);
    vec3 viewDir = normalize(viewPos - fs_in.FragPos);

    // 纹理颜色
    vec3 texColor = vec3(1.0);
    if (material.useTexture) {
        texColor = texture(material.diffuseTexture, fs_in.TexCoord).rgb;
    }

    // 计算光照
    vec3 result = CalcDirectionalLight(dirLight, normal, viewDir);

    for (int i = 0; i < numPointLights && i < 4; i++) {
        result += CalcPointLight(pointLights[i], normal, fs_in.FragPos, viewDir);
    }

    // 应用纹理
    result *= texColor;

    FragColor = vec4(result, 1.0);
}
)";

// 线框着色器
constexpr const char* WIREFRAME_VERTEX = R"(
#version 450 core

layout (location = 0) in vec3 aPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
)";

constexpr const char* WIREFRAME_FRAGMENT = R"(
#version 450 core

out vec4 FragColor;
uniform vec4 lineColor;

void main()
{
    FragColor = lineColor;
}
)";

// 畸变校正着色器（VR 用）
constexpr const char* DISTORTION_VERTEX = R"(
#version 450 core

layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

void main()
{
    TexCoord = aTexCoord;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
)";

constexpr const char* DISTORTION_FRAGMENT = R"(
#version 450 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D inputTexture;
uniform vec2 distortionCoefficients;
uniform vec2 centerOffset;
uniform float scale;

void main()
{
    // 计算到中心的距离
    vec2 uv = TexCoord - 0.5 - centerOffset;
    float r2 = dot(uv, uv);
    float r4 = r2 * r2;

    // 应用畸变
    float distortion = 1.0 + distortionCoefficients.x * r2 +
                       distortionCoefficients.y * r4;

    vec2 distortedUV = uv * distortion * scale + 0.5 + centerOffset;

    // 检查边界
    if (distortedUV.x < 0.0 || distortedUV.x > 1.0 ||
        distortedUV.y < 0.0 || distortedUV.y > 1.0) {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        FragColor = texture(inputTexture, distortedUV);
    }
}
)";

}  // namespace BuiltinShaders

}  // namespace vr