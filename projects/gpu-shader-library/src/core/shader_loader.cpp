/**
 * 着色器加载器实现
 */

#include "shader_loader.h"
#include <filesystem>

namespace gpu_shader {

// 静态缓存
std::unordered_map<std::string, std::shared_ptr<ShaderProgram>> ShaderLoader::s_cache;

// ===================== ShaderProgram 实现 =====================

bool ShaderProgram::loadFromFile(const std::string& vertexPath, const std::string& fragmentPath) {
    std::string vertexSource = ShaderLoader::loadFile(vertexPath);
    std::string fragmentSource = ShaderLoader::loadFile(fragmentPath);

    if (vertexSource.empty() || fragmentSource.empty()) {
        std::cerr << "Failed to load shader files: "
                  << vertexPath << ", " << fragmentPath << std::endl;
        return false;
    }

    return loadFromSource(vertexSource, fragmentSource);
}

bool ShaderProgram::loadFromSource(const std::string& vertexSource, const std::string& fragmentSource) {
    // 编译着色器
    GLuint vertexShader = compileShader(ShaderType::Vertex, vertexSource);
    GLuint fragmentShader = compileShader(ShaderType::Fragment, fragmentSource);

    if (vertexShader == 0 || fragmentShader == 0) {
        return false;
    }

    // 创建程序
    m_programID = glCreateProgram();
    glAttachShader(m_programID, vertexShader);
    glAttachShader(m_programID, fragmentShader);

    // 链接
    bool success = link();

    // 清理
    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);

    return success;
}

bool ShaderProgram::loadComputeShader(const std::string& computePath) {
    std::string computeSource = ShaderLoader::loadFile(computePath);
    if (computeSource.empty()) {
        std::cerr << "Failed to load compute shader: " << computePath << std::endl;
        return false;
    }

    GLuint computeShader = compileShader(ShaderType::Compute, computeSource);
    if (computeShader == 0) {
        return false;
    }

    m_programID = glCreateProgram();
    glAttachShader(m_programID, computeShader);

    bool success = link();

    glDeleteShader(computeShader);

    return success;
}

bool ShaderProgram::link() {
    glLinkProgram(m_programID);
    return checkLinkErrors(m_programID);
}

void ShaderProgram::setBool(const std::string& name, bool value) {
    glUniform1i(getUniformLocation(name), static_cast<int>(value));
}

void ShaderProgram::setInt(const std::string& name, int value) {
    glUniform1i(getUniformLocation(name), value);
}

void ShaderProgram::setFloat(const std::string& name, float value) {
    glUniform1f(getUniformLocation(name), value);
}

void ShaderProgram::setVec2(const std::string& name, const glm::vec2& value) {
    glUniform2fv(getUniformLocation(name), 1, glm::value_ptr(value));
}

void ShaderProgram::setVec3(const std::string& name, const glm::vec3& value) {
    glUniform3fv(getUniformLocation(name), 1, glm::value_ptr(value));
}

void ShaderProgram::setVec4(const std::string& name, const glm::vec4& value) {
    glUniform4fv(getUniformLocation(name), 1, glm::value_ptr(value));
}

void ShaderProgram::setMat2(const std::string& name, const glm::mat2& value) {
    glUniformMatrix2fv(getUniformLocation(name), 1, GL_FALSE, glm::value_ptr(value));
}

void ShaderProgram::setMat3(const std::string& name, const glm::mat3& value) {
    glUniformMatrix3fv(getUniformLocation(name), 1, GL_FALSE, glm::value_ptr(value));
}

void ShaderProgram::setMat4(const std::string& name, const glm::mat4& value) {
    glUniformMatrix4fv(getUniformLocation(name), 1, GL_FALSE, glm::value_ptr(value));
}

void ShaderProgram::bindUniformBlock(const std::string& name, GLuint bindingPoint) {
    GLuint blockIndex = glGetUniformBlockIndex(m_programID, name.c_str());
    if (blockIndex != GL_INVALID_INDEX) {
        glUniformBlockBinding(m_programID, blockIndex, bindingPoint);
    }
}

void ShaderProgram::dispatch(GLuint numGroupsX, GLuint numGroupsY, GLuint numGroupsZ) {
    glDispatchCompute(numGroupsX, numGroupsY, numGroupsZ);
    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT);
}

GLuint ShaderProgram::compileShader(ShaderType type, const std::string& source) {
    GLenum glType;
    switch (type) {
        case ShaderType::Vertex:         glType = GL_VERTEX_SHADER; break;
        case ShaderType::Fragment:       glType = GL_FRAGMENT_SHADER; break;
        case ShaderType::Geometry:       glType = GL_GEOMETRY_SHADER; break;
        case ShaderType::Compute:        glType = GL_COMPUTE_SHADER; break;
        case ShaderType::TessControl:    glType = GL_TESS_CONTROL_SHADER; break;
        case ShaderType::TessEvaluation: glType = GL_TESS_EVALUATION_SHADER; break;
        default:
            std::cerr << "Unknown shader type" << std::endl;
            return 0;
    }

    GLuint shader = glCreateShader(glType);
    const char* src = source.c_str();
    glShaderSource(shader, 1, &src, nullptr);
    glCompileShader(shader);

    if (!checkCompileErrors(shader, "SHADER")) {
        glDeleteShader(shader);
        return 0;
    }

    return shader;
}

bool ShaderProgram::checkCompileErrors(GLuint shader, const std::string& type) {
    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        GLint logLength;
        glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &logLength);
        std::vector<char> infoLog(logLength);
        glGetShaderInfoLog(shader, logLength, nullptr, infoLog.data());
        std::cerr << "Shader compilation error (" << type << "):\n"
                  << infoLog.data() << std::endl;
        return false;
    }
    return true;
}

bool ShaderProgram::checkLinkErrors(GLuint program) {
    GLint success;
    glGetProgramiv(program, GL_LINK_STATUS, &success);
    if (!success) {
        GLint logLength;
        glGetProgramiv(program, GL_INFO_LOG_LENGTH, &logLength);
        std::vector<char> infoLog(logLength);
        glGetProgramInfoLog(program, logLength, nullptr, infoLog.data());
        std::cerr << "Program linking error:\n" << infoLog.data() << std::endl;
        return false;
    }
    return true;
}

GLint ShaderProgram::getUniformLocation(const std::string& name) {
    auto it = m_uniforms.find(name);
    if (it != m_uniforms.end()) {
        return it->second;
    }

    GLint location = glGetUniformLocation(m_programID, name.c_str());
    m_uniforms[name] = location;
    return location;
}

void ShaderProgram::destroy() {
    if (m_programID != 0) {
        glDeleteProgram(m_programID);
        m_programID = 0;
    }
}

// ===================== ShaderLoader 实现 =====================

std::string ShaderLoader::loadFile(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << path << std::endl;
        return "";
    }

    std::stringstream ss;
    ss << file.rdbuf();
    return ss.str();
}

std::shared_ptr<ShaderProgram> ShaderLoader::loadShader(
    const std::string& vertexPath,
    const std::string& fragmentPath)
{
    std::string key = vertexPath + ":" + fragmentPath;

    auto it = s_cache.find(key);
    if (it != s_cache.end()) {
        return it->second;
    }

    auto shader = std::make_shared<ShaderProgram>();
    if (shader->loadFromFile(vertexPath, fragmentPath)) {
        s_cache[key] = shader;
        return shader;
    }

    return nullptr;
}

std::shared_ptr<ShaderProgram> ShaderLoader::loadComputeShader(const std::string& computePath) {
    auto it = s_cache.find(computePath);
    if (it != s_cache.end()) {
        return it->second;
    }

    auto shader = std::make_shared<ShaderProgram>();
    if (shader->loadComputeShader(computePath)) {
        s_cache[computePath] = shader;
        return shader;
    }

    return nullptr;
}

void ShaderLoader::clearCache() {
    s_cache.clear();
}

} // namespace gpu_shader
