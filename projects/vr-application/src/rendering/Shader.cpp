#include "rendering/Shader.h"
#include <fstream>
#include <sstream>
#include <iostream>

namespace vr {

Shader::Shader() = default;

Shader::~Shader() {
    Destroy();
}

Shader::Shader(Shader&& other) noexcept
    : m_programID(other.m_programID)
    , m_vertexShader(other.m_vertexShader)
    , m_fragmentShader(other.m_fragmentShader)
    , m_geometryShader(other.m_geometryShader)
    , m_computeShader(other.m_computeShader)
    , m_isCompiled(other.m_isCompiled)
    , m_uniformLocationCache(std::move(other.m_uniformLocationCache))
    , m_source(std::move(other.m_source)) {
    other.m_programID = 0;
    other.m_vertexShader = 0;
    other.m_fragmentShader = 0;
    other.m_geometryShader = 0;
    other.m_computeShader = 0;
    other.m_isCompiled = false;
}

Shader& Shader::operator=(Shader&& other) noexcept {
    if (this != &other) {
        Destroy();

        m_programID = other.m_programID;
        m_vertexShader = other.m_vertexShader;
        m_fragmentShader = other.m_fragmentShader;
        m_geometryShader = other.m_geometryShader;
        m_computeShader = other.m_computeShader;
        m_isCompiled = other.m_isCompiled;
        m_uniformLocationCache = std::move(other.m_uniformLocationCache);
        m_source = std::move(other.m_source);

        other.m_programID = 0;
        other.m_vertexShader = 0;
        other.m_fragmentShader = 0;
        other.m_geometryShader = 0;
        other.m_computeShader = 0;
        other.m_isCompiled = false;
    }
    return *this;
}

bool Shader::LoadFromFile(const std::string& vertexPath, const std::string& fragmentPath) {
    // 读取顶点着色器文件
    std::ifstream vertexFile(vertexPath);
    if (!vertexFile.is_open()) {
        VR_ERROR("Failed to open vertex shader file: " + vertexPath);
        return false;
    }
    std::stringstream vertexStream;
    vertexStream << vertexFile.rdbuf();
    m_source.vertexCode = vertexStream.str();

    // 读取片段着色器文件
    std::ifstream fragmentFile(fragmentPath);
    if (!fragmentFile.is_open()) {
        VR_ERROR("Failed to open fragment shader file: " + fragmentPath);
        return false;
    }
    std::stringstream fragmentStream;
    fragmentStream << fragmentFile.rdbuf();
    m_source.fragmentCode = fragmentStream.str();

    return Compile();
}

bool Shader::LoadFromSource(const std::string& vertexSource, const std::string& fragmentSource) {
    m_source.vertexCode = vertexSource;
    m_source.fragmentCode = fragmentSource;
    return Compile();
}

bool Shader::LoadFromSource(const ShaderSource& source) {
    m_source = source;
    return Compile();
}

bool Shader::Compile() {
    // 删除旧的着色器
    if (m_programID) {
        glDeleteProgram(m_programID);
        m_programID = 0;
    }

    // 编译顶点着色器
    if (!m_source.vertexCode.empty()) {
        m_vertexShader = CompileShader(ShaderType::Vertex, m_source.vertexCode);
        if (m_vertexShader == 0) {
            return false;
        }
    }

    // 编译片段着色器
    if (!m_source.fragmentCode.empty()) {
        m_fragmentShader = CompileShader(ShaderType::Fragment, m_source.fragmentCode);
        if (m_fragmentShader == 0) {
            return false;
        }
    }

    // 编译几何着色器（可选）
    if (!m_source.geometryCode.empty()) {
        m_geometryShader = CompileShader(ShaderType::Geometry, m_source.geometryCode);
        if (m_geometryShader == 0) {
            return false;
        }
    }

    // 链接程序
    if (!LinkProgram()) {
        return false;
    }

    m_isCompiled = true;
    return true;
}

GLuint Shader::CompileShader(ShaderType type, const std::string& source) {
    GLenum glType;
    std::string typeName;

    switch (type) {
        case ShaderType::Vertex:
            glType = GL_VERTEX_SHADER;
            typeName = "VERTEX";
            break;
        case ShaderType::Fragment:
            glType = GL_FRAGMENT_SHADER;
            typeName = "FRAGMENT";
            break;
        case ShaderType::Geometry:
            glType = GL_GEOMETRY_SHADER;
            typeName = "GEOMETRY";
            break;
        case ShaderType::Compute:
            glType = GL_COMPUTE_SHADER;
            typeName = "COMPUTE";
            break;
        default:
            VR_ERROR("Unknown shader type");
            return 0;
    }

    GLuint shader = glCreateShader(glType);
    const char* sourceCStr = source.c_str();
    glShaderSource(shader, 1, &sourceCStr, nullptr);
    glCompileShader(shader);

    if (!CheckCompileError(shader, type)) {
        glDeleteShader(shader);
        return 0;
    }

    return shader;
}

bool Shader::LinkProgram() {
    m_programID = glCreateProgram();

    if (m_vertexShader) {
        glAttachShader(m_programID, m_vertexShader);
    }
    if (m_fragmentShader) {
        glAttachShader(m_programID, m_fragmentShader);
    }
    if (m_geometryShader) {
        glAttachShader(m_programID, m_geometryShader);
    }
    if (m_computeShader) {
        glAttachShader(m_programID, m_computeShader);
    }

    glLinkProgram(m_programID);

    if (!CheckLinkError(m_programID)) {
        glDeleteProgram(m_programID);
        m_programID = 0;
        return false;
    }

    // 删除着色器（已经链接到程序中了）
    if (m_vertexShader) {
        glDeleteShader(m_vertexShader);
        m_vertexShader = 0;
    }
    if (m_fragmentShader) {
        glDeleteShader(m_fragmentShader);
        m_fragmentShader = 0;
    }
    if (m_geometryShader) {
        glDeleteShader(m_geometryShader);
        m_geometryShader = 0;
    }
    if (m_computeShader) {
        glDeleteShader(m_computeShader);
        m_computeShader = 0;
    }

    // 清除 uniform 位置缓存
    m_uniformLocationCache.clear();

    return true;
}

bool Shader::CheckCompileError(GLuint shader, ShaderType type) {
    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);

    if (!success) {
        GLint logLength;
        glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &logLength);

        std::string log(logLength, ' ');
        glGetShaderInfoLog(shader, logLength, nullptr, &log[0]);

        std::string typeName;
        switch (type) {
            case ShaderType::Vertex: typeName = "VERTEX"; break;
            case ShaderType::Fragment: typeName = "FRAGMENT"; break;
            case ShaderType::Geometry: typeName = "GEOMETRY"; break;
            case ShaderType::Compute: typeName = "COMPUTE"; break;
        }

        VR_ERROR("Shader compilation failed (" + typeName + "):\n" + log);
        return false;
    }

    return true;
}

bool Shader::CheckLinkError(GLuint program) {
    GLint success;
    glGetProgramiv(program, GL_LINK_STATUS, &success);

    if (!success) {
        GLint logLength;
        glGetProgramiv(program, GL_INFO_LOG_LENGTH, &logLength);

        std::string log(logLength, ' ');
        glGetProgramInfoLog(program, logLength, nullptr, &log[0]);

        VR_ERROR("Shader program linking failed:\n" + log);
        return false;
    }

    return true;
}

void Shader::Use() const {
    if (m_programID) {
        glUseProgram(m_programID);
    }
}

void Shader::Unuse() const {
    glUseProgram(0);
}

GLint Shader::GetUniformLocation(const std::string& name) {
    // 检查缓存
    auto it = m_uniformLocationCache.find(name);
    if (it != m_uniformLocationCache.end()) {
        return it->second;
    }

    // 查询 OpenGL
    GLint location = glGetUniformLocation(m_programID, name.c_str());
    if (location == -1) {
        VR_WARNING("Uniform '" + name + "' not found");
    }

    // 缓存结果
    m_uniformLocationCache[name] = location;
    return location;
}

void Shader::SetBool(const std::string& name, bool value) {
    glUniform1i(GetUniformLocation(name), static_cast<int>(value));
}

void Shader::SetInt(const std::string& name, int value) {
    glUniform1i(GetUniformLocation(name), value);
}

void Shader::SetFloat(const std::string& name, float value) {
    glUniform1f(GetUniformLocation(name), value);
}

void Shader::SetVec2(const std::string& name, const Vec2& value) {
    glUniform2fv(GetUniformLocation(name), 1, glm::value_ptr(value));
}

void Shader::SetVec3(const std::string& name, const Vec3& value) {
    glUniform3fv(GetUniformLocation(name), 1, glm::value_ptr(value));
}

void Shader::SetVec4(const std::string& name, const Vec4& value) {
    glUniform4fv(GetUniformLocation(name), 1, glm::value_ptr(value));
}

void Shader::SetMat3(const std::string& name, const Mat3& value) {
    glUniformMatrix3fv(GetUniformLocation(name), 1, GL_FALSE, glm::value_ptr(value));
}

void Shader::SetMat4(const std::string& name, const Mat4& value) {
    glUniformMatrix4fv(GetUniformLocation(name), 1, GL_FALSE, glm::value_ptr(value));
}

void Shader::SetVec3Array(const std::string& name, const Vec3* values, int count) {
    for (int i = 0; i < count; i++) {
        std::string elementName = name + "[" + std::to_string(i) + "]";
        SetVec3(elementName, values[i]);
    }
}

void Shader::SetMat4Array(const std::string& name, const Mat4* values, int count) {
    for (int i = 0; i < count; i++) {
        std::string elementName = name + "[" + std::to_string(i) + "]";
        SetMat4(elementName, values[i]);
    }
}

void Shader::Destroy() {
    if (m_programID) {
        glDeleteProgram(m_programID);
        m_programID = 0;
    }
    m_isCompiled = false;
    m_uniformLocationCache.clear();
}

// ShaderManager 实现
ShaderManager& ShaderManager::GetInstance() {
    static ShaderManager instance;
    return instance;
}

SharedPtr<Shader> ShaderManager::LoadShader(const std::string& name,
                                             const std::string& vertexPath,
                                             const std::string& fragmentPath) {
    // 检查是否已存在
    auto it = m_shaders.find(name);
    if (it != m_shaders.end()) {
        return it->second;
    }

    // 创建新着色器
    auto shader = std::make_shared<Shader>();
    if (!shader->LoadFromFile(vertexPath, fragmentPath)) {
        VR_ERROR("Failed to load shader: " + name);
        return nullptr;
    }

    m_shaders[name] = shader;
    return shader;
}

SharedPtr<Shader> ShaderManager::GetShader(const std::string& name) {
    auto it = m_shaders.find(name);
    if (it != m_shaders.end()) {
        return it->second;
    }
    return nullptr;
}

SharedPtr<Shader> ShaderManager::CreateBuiltinShader(const std::string& name) {
    // 检查是否已存在
    auto it = m_shaders.find(name);
    if (it != m_shaders.end()) {
        return it->second;
    }

    auto shader = std::make_shared<Shader>();

    if (name == "basic") {
        if (!shader->LoadFromSource(BuiltinShaders::BASIC_VERTEX, BuiltinShaders::BASIC_FRAGMENT)) {
            return nullptr;
        }
    } else if (name == "wireframe") {
        if (!shader->LoadFromSource(BuiltinShaders::WIREFRAME_VERTEX, BuiltinShaders::WIREFRAME_FRAGMENT)) {
            return nullptr;
        }
    } else if (name == "distortion") {
        if (!shader->LoadFromSource(BuiltinShaders::DISTORTION_VERTEX, BuiltinShaders::DISTORTION_FRAGMENT)) {
            return nullptr;
        }
    } else {
        VR_ERROR("Unknown builtin shader: " + name);
        return nullptr;
    }

    m_shaders[name] = shader;
    return shader;
}

void ShaderManager::Clear() {
    m_shaders.clear();
}

}  // namespace vr