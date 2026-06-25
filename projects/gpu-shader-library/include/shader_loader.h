#pragma once
/**
 * 着色器加载器
 *
 * 功能：
 * - GLSL 着色器编译
 * - 着色器程序链接
 * - Uniform 变量管理
 * - 错误处理
 */

#include <string>
#include <unordered_map>
#include <vector>
#include <memory>
#include <fstream>
#include <sstream>
#include <iostream>
#include <glad/glad.h>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>

namespace gpu_shader {

// 着色器类型
enum class ShaderType {
    Vertex,
    Fragment,
    Geometry,
    Compute,
    TessControl,
    TessEvaluation
};

// 着色器源码
struct ShaderSource {
    ShaderType type;
    std::string source;
};

// 着色器程序
class ShaderProgram {
public:
    ShaderProgram() : m_programID(0) {}
    ~ShaderProgram() { destroy(); }

    // 禁止拷贝
    ShaderProgram(const ShaderProgram&) = delete;
    ShaderProgram& operator=(const ShaderProgram&) = delete;

    // 移动语义
    ShaderProgram(ShaderProgram&& other) noexcept
        : m_programID(other.m_programID),
          m_uniforms(std::move(other.m_uniforms)) {
        other.m_programID = 0;
    }

    ShaderProgram& operator=(ShaderProgram&& other) noexcept {
        if (this != &other) {
            destroy();
            m_programID = other.m_programID;
            m_uniforms = std::move(other.m_uniforms);
            other.m_programID = 0;
        }
        return *this;
    }

    // 从文件加载
    bool loadFromFile(const std::string& vertexPath, const std::string& fragmentPath);

    // 从源码加载
    bool loadFromSource(const std::string& vertexSource, const std::string& fragmentSource);

    // 加载计算着色器
    bool loadComputeShader(const std::string& computePath);

    // 链接程序
    bool link();

    // 使用程序
    void use() const { glUseProgram(m_programID); }

    // 获取程序 ID
    GLuint getID() const { return m_programID; }

    // Uniform 设置
    void setBool(const std::string& name, bool value);
    void setInt(const std::string& name, int value);
    void setFloat(const std::string& name, float value);
    void setVec2(const std::string& name, const glm::vec2& value);
    void setVec3(const std::string& name, const glm::vec3& value);
    void setVec4(const std::string& name, const glm::vec4& value);
    void setMat2(const std::string& name, const glm::mat2& value);
    void setMat3(const std::string& name, const glm::mat3& value);
    void setMat4(const std::string& name, const glm::mat4& value);

    // Uniform 块绑定
    void bindUniformBlock(const std::string& name, GLuint bindingPoint);

    // 计算着色器调度
    void dispatch(GLuint numGroupsX, GLuint numGroupsY, GLuint numGroupsZ);

private:
    // 编译着色器
    GLuint compileShader(ShaderType type, const std::string& source);

    // 检查错误
    bool checkCompileErrors(GLuint shader, const std::string& type);
    bool checkLinkErrors(GLuint program);

    // 获取 Uniform 位置
    GLint getUniformLocation(const std::string& name);

    // 销毁资源
    void destroy();

    GLuint m_programID;
    std::unordered_map<std::string, GLint> m_uniforms;
};

// 着色器加载器
class ShaderLoader {
public:
    // 加载着色器文件
    static std::string loadFile(const std::string& path);

    // 加载着色器程序
    static std::shared_ptr<ShaderProgram> loadShader(
        const std::string& vertexPath,
        const std::string& fragmentPath
    );

    // 加载计算着色器
    static std::shared_ptr<ShaderProgram> loadComputeShader(
        const std::string& computePath
    );

    // 清除缓存
    static void clearCache();

private:
    static std::unordered_map<std::string, std::shared_ptr<ShaderProgram>> s_cache;
};

} // namespace gpu_shader
