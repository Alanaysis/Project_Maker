#include "rendering/Renderer.h"
#include <iostream>
#include <cmath>

namespace vr {

// Vertex 实现
void Vertex::SetupAttributes() {
    // 位置
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                          (void*)offsetof(Vertex, position));

    // 法线
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                          (void*)offsetof(Vertex, normal));

    // 纹理坐标
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                          (void*)offsetof(Vertex, texCoord));
}

// Framebuffer 实现
bool Framebuffer::Create(int w, int h, bool hdr) {
    width = w;
    height = h;

    glGenFramebuffers(1, &fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);

    // 创建颜色纹理
    glGenTextures(1, &colorTexture);
    glBindTexture(GL_TEXTURE_2D, colorTexture);
    if (hdr) {
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, width, height, 0, GL_RGBA, GL_FLOAT, nullptr);
    } else {
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    }
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, colorTexture, 0);

    // 创建深度纹理
    glGenTextures(1, &depthTexture);
    glBindTexture(GL_TEXTURE_2D, depthTexture);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, width, height, 0, GL_DEPTH_COMPONENT, GL_FLOAT, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depthTexture, 0);

    // 检查完整性
    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
        VR_ERROR("Framebuffer is not complete");
        Destroy();
        return false;
    }

    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    return true;
}

void Framebuffer::Destroy() {
    if (fbo) {
        glDeleteFramebuffers(1, &fbo);
        fbo = 0;
    }
    if (colorTexture) {
        glDeleteTextures(1, &colorTexture);
        colorTexture = 0;
    }
    if (depthTexture) {
        glDeleteTextures(1, &depthTexture);
        depthTexture = 0;
    }
}

void Framebuffer::Bind() {
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    glViewport(0, 0, width, height);
}

void Framebuffer::Unbind() {
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

void Framebuffer::Resize(int w, int h) {
    if (w == width && h == height) return;
    Destroy();
    Create(w, h);
}

// VRRenderTargets 实现
bool VRRenderTargets::Create(uint32_t w, uint32_t h) {
    width = w;
    height = h;
    return leftEye.Create(w, h, true) && rightEye.Create(w, h, true);
}

void VRRenderTargets::Destroy() {
    leftEye.Destroy();
    rightEye.Destroy();
}

void VRRenderTargets::Resize(uint32_t w, uint32_t h) {
    width = w;
    height = h;
    leftEye.Resize(w, h);
    rightEye.Resize(w, h);
}

// Renderer 实现
Renderer::Renderer() = default;

Renderer::~Renderer() {
    Shutdown();
}

bool Renderer::Initialize(const RendererConfig& config) {
    if (m_isInitialized) return true;

    m_config = config;

    // 初始化着色器
    if (!InitializeShaders()) {
        VR_ERROR("Failed to initialize shaders");
        return false;
    }

    // 初始化调试缓冲区
    if (!InitializeBuffers()) {
        VR_ERROR("Failed to initialize debug buffers");
        return false;
    }

    // 创建 VR 渲染目标
    m_vrTargets.Create(1920, 1080);

    m_isInitialized = true;
    VR_INFO("Renderer initialized successfully");
    return true;
}

void Renderer::Shutdown() {
    if (!m_isInitialized) return;

    m_mainShader.reset();
    m_wireframeShader.reset();
    m_distortionShader.reset();

    m_vrTargets.Destroy();

    if (m_debugVAO) glDeleteVertexArrays(1, &m_debugVAO);
    if (m_debugVBO) glDeleteBuffers(1, &m_debugVBO);
    if (m_instanceVBO) glDeleteBuffers(1, &m_instanceVBO);

    m_isInitialized = false;
    VR_INFO("Renderer shutdown");
}

bool Renderer::InitializeShaders() {
    // 创建主着色器
    m_mainShader = std::make_shared<Shader>();
    if (!m_mainShader->LoadFromSource(BuiltinShaders::BASIC_VERTEX, BuiltinShaders::BASIC_FRAGMENT)) {
        VR_ERROR("Failed to load main shader");
        return false;
    }

    // 创建线框着色器
    m_wireframeShader = std::make_shared<Shader>();
    if (!m_wireframeShader->LoadFromSource(BuiltinShaders::WIREFRAME_VERTEX, BuiltinShaders::WIREFRAME_FRAGMENT)) {
        VR_ERROR("Failed to load wireframe shader");
        return false;
    }

    // 创建畸变着色器
    m_distortionShader = std::make_shared<Shader>();
    if (!m_distortionShader->LoadFromSource(BuiltinShaders::DISTORTION_VERTEX, BuiltinShaders::DISTORTION_FRAGMENT)) {
        VR_ERROR("Failed to load distortion shader");
        return false;
    }

    return true;
}

bool Renderer::InitializeBuffers() {
    // 创建调试用的 VAO/VBO
    glGenVertexArrays(1, &m_debugVAO);
    glGenBuffers(1, &m_debugVBO);

    glBindVertexArray(m_debugVAO);
    glBindBuffer(GL_ARRAY_BUFFER, m_debugVBO);

    // 位置属性
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vec3), (void*)0);

    glBindVertexArray(0);

    return true;
}

void Renderer::BeginFrame() {
    // 重置统计
    ResetStats();
}

void Renderer::EndFrame() {
    // 可以在这里进行后处理
}

void Renderer::SetViewMatrix(const Mat4& view) {
    m_viewMatrix = view;
}

void Renderer::SetProjectionMatrix(const Mat4& projection) {
    m_projectionMatrix = projection;
}

void Renderer::SetViewPosition(const Vec3& position) {
    m_viewPosition = position;
}

void Renderer::RenderObject(const RenderObject& object) {
    if (!object.isVisible) return;

    // 使用主着色器
    m_mainShader->Use();

    // 设置变换矩阵
    m_mainShader->SetMat4("model", object.modelMatrix);
    m_mainShader->SetMat4("view", m_viewMatrix);
    m_mainShader->SetMat4("projection", m_projectionMatrix);

    // 设置相机位置
    m_mainShader->SetVec3("viewPos", m_viewPosition);

    // 设置材质
    if (object.material) {
        SetMaterialUniforms(*object.material);
    }

    // 设置光照
    SetLightUniforms();

    // 绑定 VAO 并绘制
    glBindVertexArray(object.vao);

    if (object.isWireframe) {
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
    }

    if (object.indexCount > 0) {
        glDrawElements(GL_TRIANGLES, object.indexCount, GL_UNSIGNED_INT, 0);
        m_stats.triangles += object.indexCount / 3;
    } else {
        glDrawArrays(GL_TRIANGLES, 0, object.vertexCount);
        m_stats.triangles += object.vertexCount / 3;
    }

    if (object.isWireframe) {
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    }

    glBindVertexArray(0);

    m_stats.drawCalls++;
    m_stats.vertices += object.vertexCount;
}

void Renderer::RenderObjects(const std::vector<RenderObject>& objects) {
    for (const auto& object : objects) {
        RenderObject(object);
    }
}

void Renderer::RenderInstanced(const RenderObject& object, const std::vector<Mat4>& modelMatrices) {
    if (!object.isVisible || modelMatrices.empty()) return;

    m_mainShader->Use();
    m_mainShader->SetMat4("view", m_viewMatrix);
    m_mainShader->SetMat4("projection", m_projectionMatrix);
    m_mainShader->SetVec3("viewPos", m_viewPosition);

    if (object.material) {
        SetMaterialUniforms(*object.material);
    }

    SetLightUniforms();

    // 绑定 VAO
    glBindVertexArray(object.vao);

    // 创建实例化缓冲区（缓存 VBO，只在大小变化时重新分配）
    size_t bufferSize = modelMatrices.size() * sizeof(Mat4);
    if (m_instanceVBO == 0) {
        glGenBuffers(1, &m_instanceVBO);
        glBindBuffer(GL_ARRAY_BUFFER, m_instanceVBO);
        glBufferData(GL_ARRAY_BUFFER, bufferSize, modelMatrices.data(), GL_STATIC_DRAW);
        m_instanceVBOCapacity = bufferSize;
    } else {
        glBindBuffer(GL_ARRAY_BUFFER, m_instanceVBO);
        if (bufferSize > m_instanceVBOCapacity) {
            glBufferData(GL_ARRAY_BUFFER, bufferSize, modelMatrices.data(), GL_STATIC_DRAW);
            m_instanceVBOCapacity = bufferSize;
        } else {
            glBufferSubData(GL_ARRAY_BUFFER, 0, bufferSize, modelMatrices.data());
        }
    }

    // 设置实例化矩阵属性
    for (int i = 0; i < 4; i++) {
        glEnableVertexAttribArray(3 + i);
        glVertexAttribPointer(3 + i, 4, GL_FLOAT, GL_FALSE, sizeof(Mat4),
                              (void*)(sizeof(Vec4) * i));
        glVertexAttribDivisor(3 + i, 1);
    }

    // 绘制
    if (object.indexCount > 0) {
        glDrawElementsInstanced(GL_TRIANGLES, object.indexCount, GL_UNSIGNED_INT, 0,
                                static_cast<GLsizei>(modelMatrices.size()));
    } else {
        glDrawArraysInstanced(GL_TRIANGLES, 0, object.vertexCount,
                              static_cast<GLsizei>(modelMatrices.size()));
    }

    // 清理
    for (int i = 0; i < 4; i++) {
        glDisableVertexAttribArray(3 + i);
    }

    glBindVertexArray(0);

    m_stats.drawCalls++;
    m_stats.vertices += object.vertexCount * static_cast<int>(modelMatrices.size());
}

void Renderer::RenderWireframe(const RenderObject& object, const Vec4& color) {
    m_wireframeShader->Use();
    m_wireframeShader->SetMat4("model", object.modelMatrix);
    m_wireframeShader->SetMat4("view", m_viewMatrix);
    m_wireframeShader->SetMat4("projection", m_projectionMatrix);
    m_wireframeShader->SetVec4("lineColor", color);

    glBindVertexArray(object.vao);
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);

    if (object.indexCount > 0) {
        glDrawElements(GL_TRIANGLES, object.indexCount, GL_UNSIGNED_INT, 0);
    } else {
        glDrawArrays(GL_TRIANGLES, 0, object.vertexCount);
    }

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    glBindVertexArray(0);
}

void Renderer::RenderBoundingBox(const Vec3& min, const Vec3& max, const Vec4& color) {
    // 定义包围盒的 8 个顶点
    Vec3 vertices[] = {
        Vec3(min.x, min.y, min.z),
        Vec3(max.x, min.y, min.z),
        Vec3(max.x, max.y, min.z),
        Vec3(min.x, max.y, min.z),
        Vec3(min.x, min.y, max.z),
        Vec3(max.x, min.y, max.z),
        Vec3(max.x, max.y, max.z),
        Vec3(min.x, max.y, max.z)
    };

    // 定义 12 条边
    uint32_t indices[] = {
        0, 1, 1, 2, 2, 3, 3, 0,  // 前面
        4, 5, 5, 6, 6, 7, 7, 4,  // 后面
        0, 4, 1, 5, 2, 6, 3, 7   // 连接
    };

    m_wireframeShader->Use();
    m_wireframeShader->SetMat4("model", Mat4(1.0f));
    m_wireframeShader->SetMat4("view", m_viewMatrix);
    m_wireframeShader->SetMat4("projection", m_projectionMatrix);
    m_wireframeShader->SetVec4("lineColor", color);

    glBindVertexArray(m_debugVAO);
    glBindBuffer(GL_ARRAY_BUFFER, m_debugVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_DYNAMIC_DRAW);

    glLineWidth(2.0f);
    glDrawElements(GL_LINES, 24, GL_UNSIGNED_INT, indices);
    glLineWidth(1.0f);

    glBindVertexArray(0);
}

void Renderer::RenderLine(const Vec3& start, const Vec3& end, const Vec4& color) {
    Vec3 vertices[] = {start, end};

    m_wireframeShader->Use();
    m_wireframeShader->SetMat4("model", Mat4(1.0f));
    m_wireframeShader->SetMat4("view", m_viewMatrix);
    m_wireframeShader->SetMat4("projection", m_projectionMatrix);
    m_wireframeShader->SetVec4("lineColor", color);

    glBindVertexArray(m_debugVAO);
    glBindBuffer(GL_ARRAY_BUFFER, m_debugVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_DYNAMIC_DRAW);

    glLineWidth(2.0f);
    glDrawArrays(GL_LINES, 0, 2);
    glLineWidth(1.0f);

    glBindVertexArray(0);
}

void Renderer::RenderGrid(float size, float step, const Vec4& color) {
    float halfSize = size / 2.0f;

    for (float i = -halfSize; i <= halfSize; i += step) {
        // X 方向的线
        RenderLine(Vec3(i, 0, -halfSize), Vec3(i, 0, halfSize), color);
        // Z 方向的线
        RenderLine(Vec3(-halfSize, 0, i), Vec3(halfSize, 0, i), color);
    }
}

void Renderer::SetDirectionalLight(const DirectionalLight& light) {
    m_directionalLight = light;
}

void Renderer::AddPointLight(const PointLight& light) {
    if (m_pointLights.size() < static_cast<size_t>(m_config.maxPointLights)) {
        m_pointLights.push_back(light);
    }
}

void Renderer::ClearPointLights() {
    m_pointLights.clear();
}

void Renderer::SetMaterialUniforms(const Material& material) {
    m_mainShader->SetVec3("material.ambient", material.ambient);
    m_mainShader->SetVec3("material.diffuse", material.diffuse);
    m_mainShader->SetVec3("material.specular", material.specular);
    m_mainShader->SetFloat("material.shininess", material.shininess);
    m_mainShader->SetBool("material.useTexture", material.useTexture);

    if (material.useTexture && material.diffuseTexture) {
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, material.diffuseTexture);
        m_mainShader->SetInt("material.diffuseTexture", 0);
    }
}

void Renderer::SetLightUniforms() {
    // 方向光
    m_mainShader->SetVec3("dirLight.direction", m_directionalLight.direction);
    m_mainShader->SetVec3("dirLight.ambient", m_directionalLight.ambient);
    m_mainShader->SetVec3("dirLight.diffuse", m_directionalLight.diffuse);
    m_mainShader->SetVec3("dirLight.specular", m_directionalLight.specular);

    // 点光源
    int numLights = std::min(static_cast<int>(m_pointLights.size()), m_config.maxPointLights);
    m_mainShader->SetInt("numPointLights", numLights);

    for (int i = 0; i < numLights; i++) {
        std::string prefix = "pointLights[" + std::to_string(i) + "]";
        m_mainShader->SetVec3(prefix + ".position", m_pointLights[i].position);
        m_mainShader->SetVec3(prefix + ".ambient", m_pointLights[i].ambient);
        m_mainShader->SetVec3(prefix + ".diffuse", m_pointLights[i].diffuse);
        m_mainShader->SetVec3(prefix + ".specular", m_pointLights[i].specular);
        m_mainShader->SetFloat(prefix + ".constant", m_pointLights[i].constant);
        m_mainShader->SetFloat(prefix + ".linear", m_pointLights[i].linear);
        m_mainShader->SetFloat(prefix + ".quadratic", m_pointLights[i].quadratic);
    }
}

void Renderer::SetWireframeMode(bool enabled) {
    m_wireframeMode = enabled;
    if (enabled) {
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
    } else {
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    }
}

void Renderer::SetDepthTest(bool enabled) {
    if (enabled) {
        glEnable(GL_DEPTH_TEST);
    } else {
        glDisable(GL_DEPTH_TEST);
    }
}

void Renderer::SetBlending(bool enabled) {
    if (enabled) {
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    } else {
        glDisable(GL_BLEND);
    }
}

void Renderer::SetCullFace(bool enabled) {
    if (enabled) {
        glEnable(GL_CULL_FACE);
    } else {
        glDisable(GL_CULL_FACE);
    }
}

void Renderer::SetCullFaceMode(GLenum mode) {
    glCullFace(mode);
}

void Renderer::Clear(const Vec4& color) {
    glClearColor(color.r, color.g, color.b, color.a);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

void Renderer::ClearDepth() {
    glClear(GL_DEPTH_BUFFER_BIT);
}

void Renderer::SetViewport(int x, int y, int width, int height) {
    glViewport(x, y, width, height);
}

void Renderer::BeginVREye(Eye eye) {
    Framebuffer& fb = (eye == Eye::Left) ? m_vrTargets.leftEye : m_vrTargets.rightEye;
    fb.Bind();
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

void Renderer::EndVREye(Eye eye) {
    Framebuffer& fb = (eye == Eye::Left) ? m_vrTargets.leftEye : m_vrTargets.rightEye;
    fb.Unbind();
}

void Renderer::SubmitVRFrame() {
    // 应用畸变校正
    ApplyDistortion();
}

void Renderer::ApplyDistortion() {
    if (!m_distortionShader) return;

    // 绑定默认帧缓冲
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    glViewport(0, 0, 1280, 720);
    glClear(GL_COLOR_BUFFER_BIT);

    m_distortionShader->Use();
    m_distortionShader->SetVec2("distortionCoefficients", Vec2(0.0f, 0.0f));  // 无畸变
    m_distortionShader->SetVec2("centerOffset", Vec2(0.0f));
    m_distortionShader->SetFloat("scale", 1.0f);

    // 渲染左眼
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, m_vrTargets.leftEye.colorTexture);
    m_distortionShader->SetInt("inputTexture", 0);

    // 绘制全屏四边形
    glBindVertexArray(m_debugVAO);
    glDrawArrays(GL_TRIANGLES, 0, 6);

    // 渲染右眼（简化实现，实际应该分屏显示）
}

void Renderer::ResetStats() {
    m_stats = RenderStats();
}

// 创建基本几何体
RenderObject Renderer::CreateCube(float size) {
    float half = size / 2.0f;

    std::vector<Vertex> vertices = {
        // 前面
        {{-half, -half,  half}, { 0,  0,  1}, {0, 0}},
        {{ half, -half,  half}, { 0,  0,  1}, {1, 0}},
        {{ half,  half,  half}, { 0,  0,  1}, {1, 1}},
        {{-half,  half,  half}, { 0,  0,  1}, {0, 1}},

        // 后面
        {{ half, -half, -half}, { 0,  0, -1}, {0, 0}},
        {{-half, -half, -half}, { 0,  0, -1}, {1, 0}},
        {{-half,  half, -half}, { 0,  0, -1}, {1, 1}},
        {{ half,  half, -half}, { 0,  0, -1}, {0, 1}},

        // 上面
        {{-half,  half,  half}, { 0,  1,  0}, {0, 0}},
        {{ half,  half,  half}, { 0,  1,  0}, {1, 0}},
        {{ half,  half, -half}, { 0,  1,  0}, {1, 1}},
        {{-half,  half, -half}, { 0,  1,  0}, {0, 1}},

        // 下面
        {{-half, -half, -half}, { 0, -1,  0}, {0, 0}},
        {{ half, -half, -half}, { 0, -1,  0}, {1, 0}},
        {{ half, -half,  half}, { 0, -1,  0}, {1, 1}},
        {{-half, -half,  half}, { 0, -1,  0}, {0, 1}},

        // 右面
        {{ half, -half,  half}, { 1,  0,  0}, {0, 0}},
        {{ half, -half, -half}, { 1,  0,  0}, {1, 0}},
        {{ half,  half, -half}, { 1,  0,  0}, {1, 1}},
        {{ half,  half,  half}, { 1,  0,  0}, {0, 1}},

        // 左面
        {{-half, -half, -half}, {-1,  0,  0}, {0, 0}},
        {{-half, -half,  half}, {-1,  0,  0}, {1, 0}},
        {{-half,  half,  half}, {-1,  0,  0}, {1, 1}},
        {{-half,  half, -half}, {-1,  0,  0}, {0, 1}}
    };

    std::vector<uint32_t> indices = {
        0,  1,  2,  2,  3,  0,   // 前面
        4,  5,  6,  6,  7,  4,   // 后面
        8,  9,  10, 10, 11, 8,   // 上面
        12, 13, 14, 14, 15, 12,  // 下面
        16, 17, 18, 18, 19, 16,  // 右面
        20, 21, 22, 22, 23, 20   // 左面
    };

    return CreateFromVertices(vertices, indices);
}

RenderObject Renderer::CreateSphere(float radius, int segments) {
    std::vector<Vertex> vertices;
    std::vector<uint32_t> indices;

    for (int i = 0; i <= segments; i++) {
        float phi = PI * i / segments;
        for (int j = 0; j <= segments; j++) {
            float theta = TWO_PI * j / segments;

            Vertex vertex;
            vertex.position.x = radius * sin(phi) * cos(theta);
            vertex.position.y = radius * cos(phi);
            vertex.position.z = radius * sin(phi) * sin(theta);
            vertex.normal = glm::normalize(vertex.position);
            vertex.texCoord.x = static_cast<float>(j) / segments;
            vertex.texCoord.y = static_cast<float>(i) / segments;

            vertices.push_back(vertex);
        }
    }

    for (int i = 0; i < segments; i++) {
        for (int j = 0; j < segments; j++) {
            uint32_t first = i * (segments + 1) + j;
            uint32_t second = first + segments + 1;

            indices.push_back(first);
            indices.push_back(second);
            indices.push_back(first + 1);

            indices.push_back(second);
            indices.push_back(second + 1);
            indices.push_back(first + 1);
        }
    }

    return CreateFromVertices(vertices, indices);
}

RenderObject Renderer::CreatePlane(float width, float height) {
    float halfW = width / 2.0f;
    float halfH = height / 2.0f;

    std::vector<Vertex> vertices = {
        {{-halfW, 0, -halfH}, {0, 1, 0}, {0, 0}},
        {{ halfW, 0, -halfH}, {0, 1, 0}, {1, 0}},
        {{ halfW, 0,  halfH}, {0, 1, 0}, {1, 1}},
        {{-halfW, 0,  halfH}, {0, 1, 0}, {0, 1}}
    };

    std::vector<uint32_t> indices = {
        0, 1, 2,
        2, 3, 0
    };

    return CreateFromVertices(vertices, indices);
}

RenderObject Renderer::CreateCylinder(float radius, float height, int segments) {
    std::vector<Vertex> vertices;
    std::vector<uint32_t> indices;

    float halfHeight = height / 2.0f;

    // 侧面
    for (int i = 0; i <= segments; i++) {
        float theta = TWO_PI * i / segments;
        float x = radius * cos(theta);
        float z = radius * sin(theta);
        float u = static_cast<float>(i) / segments;

        // 底部顶点
        vertices.push_back({{x, -halfHeight, z}, {cos(theta), 0, sin(theta)}, {u, 0}});
        // 顶部顶点
        vertices.push_back({{x, halfHeight, z}, {cos(theta), 0, sin(theta)}, {u, 1}});
    }

    // 侧面索引
    for (int i = 0; i < segments; i++) {
        uint32_t base = i * 2;
        indices.push_back(base);
        indices.push_back(base + 1);
        indices.push_back(base + 2);

        indices.push_back(base + 1);
        indices.push_back(base + 3);
        indices.push_back(base + 2);
    }

    return CreateFromVertices(vertices, indices);
}

RenderObject Renderer::CreateFromVertices(const std::vector<Vertex>& vertices,
                                          const std::vector<uint32_t>& indices) {
    RenderObject object;
    object.vertexCount = static_cast<uint32_t>(vertices.size());
    object.indexCount = static_cast<uint32_t>(indices.size());

    glGenVertexArrays(1, &object.vao);
    glGenBuffers(1, &object.vbo);
    glGenBuffers(1, &object.ebo);

    glBindVertexArray(object.vao);

    // 顶点缓冲区
    glBindBuffer(GL_ARRAY_BUFFER, object.vbo);
    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(Vertex), vertices.data(), GL_STATIC_DRAW);

    // 索引缓冲区
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, object.ebo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.size() * sizeof(uint32_t), indices.data(), GL_STATIC_DRAW);

    // 设置顶点属性
    Vertex::SetupAttributes();

    glBindVertexArray(0);

    return object;
}

}  // namespace vr