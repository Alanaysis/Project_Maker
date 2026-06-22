#pragma once

#include "Common.h"
#include "rendering/Shader.h"
#include <vector>

namespace vr {

// 顶点结构
struct Vertex {
    Vec3 position;
    Vec3 normal;
    Vec2 texCoord;

    // 顶点属性布局
    static void SetupAttributes();
};

// 渲染对象
struct RenderObject {
    GLuint vao = 0;
    GLuint vbo = 0;
    GLuint ebo = 0;
    uint32_t indexCount = 0;
    uint32_t vertexCount = 0;

    Material* material = nullptr;
    Mat4 modelMatrix = Mat4(1.0f);

    bool isVisible = true;
    bool isWireframe = false;
};

// 材质
struct Material {
    Vec3 ambient = Vec3(0.1f);
    Vec3 diffuse = Vec3(0.8f);
    Vec3 specular = Vec3(1.0f);
    float shininess = 32.0f;

    GLuint diffuseTexture = 0;
    GLuint specularTexture = 0;
    GLuint normalTexture = 0;

    bool useTexture = false;
};

// 光源
struct DirectionalLight {
    Vec3 direction = Vec3(-0.2f, -1.0f, -0.3f);
    Vec3 ambient = Vec3(0.2f);
    Vec3 diffuse = Vec3(0.5f);
    Vec3 specular = Vec3(1.0f);
};

struct PointLight {
    Vec3 position = Vec3(0.0f);
    Vec3 ambient = Vec3(0.1f);
    Vec3 diffuse = Vec3(0.8f);
    Vec3 specular = Vec3(1.0f);

    float constant = 1.0f;
    float linear = 0.09f;
    float quadratic = 0.032f;
};

// 渲染统计
struct RenderStats {
    int drawCalls = 0;
    int vertices = 0;
    int triangles = 0;
    int textureBinds = 0;
    int shaderSwitches = 0;
};

// 帧缓冲
struct Framebuffer {
    GLuint fbo = 0;
    GLuint colorTexture = 0;
    GLuint depthTexture = 0;
    GLuint depthRenderbuffer = 0;

    int width = 0;
    int height = 0;

    bool Create(int width, int height, bool hdr = false);
    void Destroy();
    void Bind();
    void Unbind();
    void Resize(int width, int height);
};

// VR 渲染目标
struct VRRenderTargets {
    Framebuffer leftEye;
    Framebuffer rightEye;
    uint32_t width = 0;
    uint32_t height = 0;

    bool Create(uint32_t width, uint32_t height);
    void Destroy();
    void Resize(uint32_t width, uint32_t height);
};

// 渲染器配置
struct RendererConfig {
    int maxPointLights = 4;
    bool enableShadows = false;
    bool enablePostProcessing = false;
    bool enableMSAA = true;
    int msaaSamples = 4;
    bool enableHDR = false;
    float gamma = 2.2f;
};

// 渲染器类
class Renderer {
public:
    Renderer();
    ~Renderer();

    // 禁用拷贝
    Renderer(const Renderer&) = delete;
    Renderer& operator=(const Renderer&) = delete;

    // 初始化和关闭
    bool Initialize(const RendererConfig& config = RendererConfig());
    void Shutdown();

    // 帧操作
    void BeginFrame();
    void EndFrame();

    // 渲染设置
    void SetViewMatrix(const Mat4& view);
    void SetProjectionMatrix(const Mat4& projection);
    void SetViewPosition(const Vec3& position);

    // 渲染对象
    void RenderObject(const RenderObject& object);
    void RenderObjects(const std::vector<RenderObject>& objects);

    // 批量渲染
    void RenderInstanced(const RenderObject& object, const std::vector<Mat4>& modelMatrices);

    // 调试渲染
    void RenderWireframe(const RenderObject& object, const Vec4& color = Colors::Green);
    void RenderBoundingBox(const Vec3& min, const Vec3& max, const Vec4& color = Colors::Green);
    void RenderLine(const Vec3& start, const Vec3& end, const Vec4& color = Colors::White);
    void RenderGrid(float size, float step, const Vec4& color = Colors::Gray);

    // 光照设置
    void SetDirectionalLight(const DirectionalLight& light);
    void AddPointLight(const PointLight& light);
    void ClearPointLights();

    // 渲染状态
    void SetWireframeMode(bool enabled);
    void SetDepthTest(bool enabled);
    void SetBlending(bool enabled);
    void SetCullFace(bool enabled);
    void SetCullFaceMode(GLenum mode);

    // 清除
    void Clear(const Vec4& color = Colors::DarkGray);
    void ClearDepth();

    // 视口
    void SetViewport(int x, int y, int width, int height);

    // VR 渲染
    void BeginVREye(Eye eye);
    void EndVREye(Eye eye);
    void SubmitVRFrame();

    // 获取着色器
    SharedPtr<Shader> GetMainShader() const { return m_mainShader; }
    SharedPtr<Shader> GetWireframeShader() const { return m_wireframeShader; }

    // 获取统计信息
    const RenderStats& GetStats() const { return m_stats; }
    void ResetStats();

    // 获取配置
    const RendererConfig& GetConfig() const { return m_config; }

    // 创建渲染对象
    static RenderObject CreateCube(float size = 1.0f);
    static RenderObject CreateSphere(float radius = 0.5f, int segments = 32);
    static RenderObject CreatePlane(float width = 1.0f, float height = 1.0f);
    static RenderObject CreateCylinder(float radius = 0.5f, float height = 1.0f, int segments = 32);

    // 从数据创建
    static RenderObject CreateFromVertices(const std::vector<Vertex>& vertices,
                                           const std::vector<uint32_t>& indices);

private:
    // 初始化着色器
    bool InitializeShaders();

    // 初始化缓冲区
    bool InitializeBuffers();

    // 设置材质
    void SetMaterialUniforms(const Material& material);

    // 设置光照
    void SetLightUniforms();

    // 成员变量
    RendererConfig m_config;

    // 着色器
    SharedPtr<Shader> m_mainShader;
    SharedPtr<Shader> m_wireframeShader;
    SharedPtr<Shader> m_distortionShader;

    // VR 渲染目标
    VRRenderTargets m_vrTargets;

    // 当前渲染状态
    Mat4 m_viewMatrix = Mat4(1.0f);
    Mat4 m_projectionMatrix = Mat4(1.0f);
    Vec3 m_viewPosition = Vec3(0.0f);

    // 光源
    DirectionalLight m_directionalLight;
    std::vector<PointLight> m_pointLights;

    // 调试渲染缓冲区
    GLuint m_debugVAO = 0;
    GLuint m_debugVBO = 0;

    // 统计信息
    RenderStats m_stats;

    // 状态
    bool m_isInitialized = false;
    bool m_wireframeMode = false;
};

}  // namespace vr