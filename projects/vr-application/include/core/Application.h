#pragma once

#include "Common.h"
#include "core/Engine.h"
#include "rendering/Renderer.h"
#include "vr/VRSystem.h"
#include "input/InputManager.h"
#include "scene/Scene.h"

namespace vr {

// 应用程序配置
struct AppConfig {
    // 窗口配置
    WindowConfig window = {
        1280, 720,
        "VR Application",
        false, true, 4
    };

    // VR 配置
    VRConfig vr;

    // 渲染配置
    RendererConfig renderer;

    // 输入配置
    InputManagerConfig input;

    // 应用设置
    bool enableDebugTools = true;
    bool enablePerformanceOverlay = true;
    bool enableVRPreview = true;
};

// 应用程序状态
enum class AppState {
    Uninitialized,
    Running,
    Paused,
    Quitting
};

// 应用程序类
class Application {
public:
    Application();
    virtual ~Application();

    // 禁用拷贝
    Application(const Application&) = delete;
    Application& operator=(const Application&) = delete;

    // 初始化和关闭
    bool Initialize(const AppConfig& config = AppConfig());
    void Shutdown();

    // 主循环
    void Run();
    void Quit();

    // 状态
    AppState GetState() const { return m_state; }
    bool IsRunning() const { return m_state == AppState::Running; }

    // 获取子系统
    Engine* GetEngine() { return m_engine.get(); }
    Renderer* GetRenderer() { return m_renderer.get(); }
    VRSystem* GetVRSystem() { return m_vrSystem.get(); }
    InputManager* GetInputManager() { return m_inputManager.get(); }
    SceneManager* GetSceneManager() { return &SceneManager::GetInstance(); }

    // 获取配置
    const AppConfig& GetConfig() const { return m_config; }

    // 获取统计信息
    const FrameStats& GetFrameStats() const;

protected:
    // 虚函数（子类可重写）
    virtual bool OnInitialize();
    virtual void OnShutdown();
    virtual void OnUpdate(float deltaTime);
    virtual void OnRender();
    virtual void OnVRRender();
    virtual void OnGUI();

    // 场景管理
    virtual void CreateScene();
    virtual void UpdateScene(float deltaTime);
    virtual void RenderScene();

    // 交互处理
    virtual void ProcessInput(float deltaTime);
    virtual void HandleInteraction(const InteractionEvent& event);

private:
    // 主循环步骤
    void ProcessEvents();
    void Update(float deltaTime);
    void Render();
    void RenderDebugInfo();

    // 初始化子系统
    bool InitializeEngine();
    bool InitializeRenderer();
    bool InitializeVR();
    bool InitializeInput();
    bool InitializeScene();

    // 窗口回调
    void OnFramebufferSize(int width, int height);
    void OnKey(int key, int scancode, int action, int mods);

    // 成员变量
    AppConfig m_config;
    AppState m_state = AppState::Uninitialized;

    // 子系统
    UniquePtr<Engine> m_engine;
    UniquePtr<Renderer> m_renderer;
    UniquePtr<VRSystem> m_vrSystem;
    UniquePtr<InputManager> m_inputManager;

    // 场景
    SharedPtr<Scene> m_mainScene;

    // 调试
    bool m_showDebugInfo = false;
    bool m_showWireframe = false;
    bool m_showBoundingBoxes = false;
    bool m_showGrid = true;

    // 性能监控
    float m_fpsUpdateTimer = 0.0f;
    float m_currentFPS = 0.0f;
    float m_frameTimeHistory[128] = {};
    int m_frameTimeIndex = 0;
};

// 简单的 VR 应用示例
class SimpleVRApp : public Application {
public:
    SimpleVRApp();
    ~SimpleVRApp() override;

protected:
    // 重写虚函数
    bool OnInitialize() override;
    void OnShutdown() override;
    void OnUpdate(float deltaTime) override;
    void OnRender() override;
    void OnVRRender() override;
    void CreateScene() override;
    void ProcessInput(float deltaTime) override;
    void HandleInteraction(const InteractionEvent& event) override;

private:
    // 场景对象
    SharedPtr<SceneObject> m_ground;
    SharedPtr<SceneObject> m_cube;
    SharedPtr<SceneObject> m_sphere;
    std::vector<SharedPtr<SceneObject>> m_interactiveObjects;

    // 交互状态
    SharedPtr<Interactable> m_grabbedObject;
    bool m_isGrabbing = false;

    // 动画
    float m_animationTime = 0.0f;
};

}  // namespace vr