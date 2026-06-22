#include "core/Application.h"
#include <iostream>
#include <sstream>
#include <iomanip>

namespace vr {

Application::Application() = default;

Application::~Application() {
    Shutdown();
}

bool Application::Initialize(const AppConfig& config) {
    if (m_state != AppState::Uninitialized) {
        return true;
    }

    m_config = config;

    // 初始化引擎
    if (!InitializeEngine()) {
        VR_ERROR("Failed to initialize engine");
        return false;
    }

    // 初始化渲染器
    if (!InitializeRenderer()) {
        VR_ERROR("Failed to initialize renderer");
        return false;
    }

    // 初始化 VR 系统
    if (!InitializeVR()) {
        VR_ERROR("Failed to initialize VR system");
        return false;
    }

    // 初始化输入系统
    if (!InitializeInput()) {
        VR_ERROR("Failed to initialize input system");
        return false;
    }

    // 初始化场景
    if (!InitializeScene()) {
        VR_ERROR("Failed to initialize scene");
        return false;
    }

    // 调用子类初始化
    if (!OnInitialize()) {
        VR_ERROR("Application-specific initialization failed");
        return false;
    }

    m_state = AppState::Running;
    VR_INFO("Application initialized successfully");

    return true;
}

void Application::Shutdown() {
    if (m_state == AppState::Uninitialized) {
        return;
    }

    // 调用子类关闭
    OnShutdown();

    // 关闭子系统
    if (m_inputManager) {
        m_inputManager->Shutdown();
        m_inputManager.reset();
    }

    if (m_vrSystem) {
        m_vrSystem->Shutdown();
        m_vrSystem.reset();
    }

    if (m_renderer) {
        m_renderer->Shutdown();
        m_renderer.reset();
    }

    if (m_engine) {
        m_engine->Shutdown();
        m_engine.reset();
    }

    m_state = AppState::Uninitialized;
    VR_INFO("Application shutdown");
}

void Application::Run() {
    if (m_state != AppState::Running) {
        return;
    }

    VR_INFO("Starting main loop");

    while (!m_engine->ShouldClose() && m_state == AppState::Running) {
        // 处理事件
        ProcessEvents();

        // 获取 deltaTime
        float deltaTime = m_engine->GetFrameStats().deltaTime;

        // 更新
        Update(deltaTime);

        // 渲染
        Render();

        // 交换缓冲区
        m_engine->SwapBuffers();
    }

    VR_INFO("Main loop ended");
}

void Application::Quit() {
    m_state = AppState::Quitting;
}

const FrameStats& Application::GetFrameStats() const {
    return m_engine->GetFrameStats();
}

bool Application::OnInitialize() {
    return true;
}

void Application::OnShutdown() {
}

void Application::OnUpdate(float deltaTime) {
}

void Application::OnRender() {
}

void Application::OnVRRender() {
}

void Application::OnGUI() {
}

void Application::CreateScene() {
    // 创建默认场景
    m_mainScene = SceneManager::GetInstance().CreateScene("Main");
    m_mainScene->CreateDefaultScene();
}

void Application::UpdateScene(float deltaTime) {
    if (m_mainScene) {
        m_mainScene->Update(deltaTime);
    }
}

void Application::RenderScene() {
    if (!m_mainScene) return;

    // 获取相机
    auto camera = m_mainScene->GetActiveCamera();
    if (!camera) return;

    // 设置渲染器的视图和投影矩阵
    m_renderer->SetViewMatrix(camera->GetViewMatrix());
    m_renderer->SetProjectionMatrix(camera->GetProjectionMatrix());
    m_renderer->SetViewPosition(camera->GetTransform().GetPosition());

    // 设置光照
    m_renderer->SetDirectionalLight(m_mainScene->GetMainDirectionalLight());
    m_renderer->ClearPointLights();
    for (const auto& light : m_mainScene->GetPointLights()) {
        m_renderer->AddPointLight(light);
    }

    // 渲染场景
    m_mainScene->Render(*m_renderer);
}

void Application::ProcessInput(float deltaTime) {
    // 更新输入管理器
    m_inputManager->Update(deltaTime);

    // 更新桌面模式输入
    if (m_vrSystem->IsDesktopMode()) {
        m_vrSystem->UpdateDesktopInput(m_engine->GetWindow(), deltaTime);
    }
}

void Application::HandleInteraction(const InteractionEvent& event) {
    // 子类可以重写此函数
}

void Application::ProcessEvents() {
    m_engine->PollEvents();

    // 处理 VR 事件
    VREvent vrEvent;
    while (m_vrSystem->PollEvents(vrEvent)) {
        switch (vrEvent.type) {
            case VREventType::SessionStateChanged:
                // 处理会话状态变化
                break;
            case VREventType::ControllerConnected:
                VR_INFO("Controller connected");
                break;
            case VREventType::ControllerDisconnected:
                VR_INFO("Controller disconnected");
                break;
            default:
                break;
        }
    }
}

void Application::Update(float deltaTime) {
    // 更新输入
    ProcessInput(deltaTime);

    // 更新场景
    UpdateScene(deltaTime);

    // 调用子类更新
    OnUpdate(deltaTime);

    // 更新 FPS 显示
    m_fpsUpdateTimer += deltaTime;
    if (m_fpsUpdateTimer >= 0.5f) {
        m_currentFPS = m_engine->GetFrameStats().fps;
        m_fpsUpdateTimer = 0.0f;
    }

    // 记录帧时间历史
    m_frameTimeHistory[m_frameTimeIndex] = m_engine->GetFrameStats().frameTime;
    m_frameTimeIndex = (m_frameTimeIndex + 1) % 128;
}

void Application::Render() {
    m_renderer->BeginFrame();

    // 清除屏幕
    m_renderer->Clear(Vec4(0.2f, 0.3f, 0.3f, 1.0f));

    // 设置视口
    int width, height;
    m_engine->GetWindowSize(width, height);
    m_renderer->SetViewport(0, 0, width, height);

    // 渲染场景
    RenderScene();

    // 渲染网格
    if (m_showGrid) {
        m_renderer->RenderGrid(20.0f, 1.0f, Vec4(0.5f, 0.5f, 0.5f, 0.5f));
    }

    // 调用子类渲染
    OnRender();

    // VR 渲染
    if (!m_vrSystem->IsDesktopMode()) {
        OnVRRender();
    }

    // 渲染调试信息
    RenderDebugInfo();

    // 调用 GUI 渲染
    OnGUI();

    m_renderer->EndFrame();
}

void Application::RenderDebugInfo() {
    if (!m_config.enableDebugTools || !m_showDebugInfo) {
        return;
    }

    // 这里可以添加 ImGui 或其他 GUI 渲染
    // 简化实现：在控制台输出调试信息
    static float debugTimer = 0.0f;
    debugTimer += m_engine->GetFrameStats().deltaTime;

    if (debugTimer >= 1.0f) {
        debugTimer = 0.0f;

        const auto& stats = m_engine->GetFrameStats();
        const auto& renderStats = m_renderer->GetStats();

        std::stringstream ss;
        ss << std::fixed << std::setprecision(1);
        ss << "FPS: " << stats.fps
           << " | Frame Time: " << stats.frameTime << "ms"
           << " | Draw Calls: " << renderStats.drawCalls
           << " | Vertices: " << renderStats.vertices;

        VR_DEBUG(ss.str());
    }
}

bool Application::InitializeEngine() {
    m_engine = std::make_unique<Engine>();

    EngineConfig engineConfig;
    engineConfig.window = m_config.window;
    engineConfig.enableDebug = m_config.enableDebugTools;
    engineConfig.enableVR = !m_config.vr.enableDesktopMode;
    engineConfig.desktopMode = m_config.vr.enableDesktopMode;

    if (!m_engine->Initialize(engineConfig)) {
        return false;
    }

    // 设置窗口回调
    m_engine->SetFramebufferSizeCallback([this](int width, int height) {
        OnFramebufferSize(width, height);
    });

    m_engine->SetKeyCallback([this](int key, int scancode, int action, int mods) {
        OnKey(key, scancode, action, mods);
    });

    return true;
}

bool Application::InitializeRenderer() {
    m_renderer = std::make_unique<Renderer>();

    if (!m_renderer->Initialize(m_config.renderer)) {
        return false;
    }

    return true;
}

bool Application::InitializeVR() {
    m_vrSystem = std::make_unique<VRSystem>();

    if (!m_vrSystem->Initialize(m_config.vr)) {
        VR_WARNING("VR system initialization failed, using desktop mode");
        m_config.vr.enableDesktopMode = true;
    }

    return true;
}

bool Application::InitializeInput() {
    m_inputManager = std::make_unique<InputManager>();

    if (!m_inputManager->Initialize(m_vrSystem.get(), m_config.input)) {
        VR_WARNING("Input manager initialization failed");
    }

    // 注册交互回调
    m_inputManager->RegisterInteractionCallback(InteractionType::Grab,
        [this](const InteractionEvent& event) {
            HandleInteraction(event);
        });

    m_inputManager->RegisterInteractionCallback(InteractionType::Release,
        [this](const InteractionEvent& event) {
            HandleInteraction(event);
        });

    return true;
}

bool Application::InitializeScene() {
    CreateScene();
    return true;
}

void Application::OnFramebufferSize(int width, int height) {
    if (width == 0 || height == 0) return;

    glViewport(0, 0, width, height);

    // 更新相机宽高比
    if (m_mainScene) {
        auto camera = m_mainScene->GetActiveCamera();
        if (camera) {
            camera->SetAspect(static_cast<float>(width) / static_cast<float>(height));
        }
    }
}

void Application::OnKey(int key, int scancode, int action, int mods) {
    // ESC 退出
    if (key == GLFW_KEY_ESCAPE && action == GLFW_PRESS) {
        Quit();
    }

    // F1 切换调试信息
    if (key == GLFW_KEY_F1 && action == GLFW_PRESS) {
        m_showDebugInfo = !m_showDebugInfo;
    }

    // F2 切换线框模式
    if (key == GLFW_KEY_F2 && action == GLFW_PRESS) {
        m_showWireframe = !m_showWireframe;
        m_renderer->SetWireframeMode(m_showWireframe);
    }

    // F3 切换包围盒显示
    if (key == GLFW_KEY_F3 && action == GLFW_PRESS) {
        m_showBoundingBoxes = !m_showBoundingBoxes;
    }

    // F4 切换网格显示
    if (key == GLFW_KEY_F4 && action == GLFW_PRESS) {
        m_showGrid = !m_showGrid;
    }
}

// SimpleVRApp 实现
SimpleVRApp::SimpleVRApp() = default;

SimpleVRApp::~SimpleVRApp() = default;

bool SimpleVRApp::OnInitialize() {
    VR_INFO("SimpleVRApp initialized");
    return true;
}

void SimpleVRApp::OnShutdown() {
    VR_INFO("SimpleVRApp shutdown");
}

void SimpleVRApp::OnUpdate(float deltaTime) {
    m_animationTime += deltaTime;

    // 旋转立方体
    if (m_cube) {
        m_cube->GetTransform().Rotate(Vec3(0, 1, 0), deltaTime * 45.0f * DEG_TO_RAD);
    }

    // 上下浮动球体
    if (m_sphere) {
        float y = 1.0f + sin(m_animationTime * 2.0f) * 0.3f;
        m_sphere->GetTransform().SetPosition(Vec3(2.0f, y, 0.0f));
    }
}

void SimpleVRApp::OnRender() {
    // 渲染交互物体
    for (auto& obj : m_interactiveObjects) {
        if (obj->IsVisible()) {
            obj->Render(*GetRenderer());
        }
    }
}

void SimpleVRApp::OnVRRender() {
    // VR 渲染（简化实现）
    auto* vrSystem = GetVRSystem();
    auto* renderer = GetRenderer();

    if (!vrSystem || !renderer) return;

    // 获取 VR 视图
    VRView leftView = vrSystem->GetView(Eye::Left);
    VRView rightView = vrSystem->GetView(Eye::Right);

    // 渲染左眼
    renderer->BeginVREye(Eye::Left);
    renderer->SetViewMatrix(leftView.viewMatrix);
    renderer->SetProjectionMatrix(leftView.projectionMatrix);
    RenderScene();
    renderer->EndVREye(Eye::Left);

    // 渲染右眼
    renderer->BeginVREye(Eye::Right);
    renderer->SetViewMatrix(rightView.viewMatrix);
    renderer->SetProjectionMatrix(rightView.projectionMatrix);
    RenderScene();
    renderer->EndVREye(Eye::Right);

    // 提交 VR 帧
    renderer->SubmitVRFrame();
}

void SimpleVRApp::CreateScene() {
    // 创建场景
    m_mainScene = SceneManager::GetInstance().CreateScene("SimpleVRScene");

    // 创建相机
    auto camera = std::make_shared<Camera>("MainCamera");
    camera->SetPerspective(45.0f, 16.0f / 9.0f, 0.1f, 1000.0f);
    camera->GetTransform().SetPosition(Vec3(0, 2, 5));
    camera->LookAt(Vec3(0, 0, 0));
    m_mainScene->SetActiveCamera(camera);

    // 创建方向光
    auto dirLight = std::make_shared<Light>("DirectionalLight");
    dirLight->SetLightType(LightType::Directional);
    dirLight->GetTransform().SetRotationEuler(Vec3(-45.0f, -45.0f, 0.0f));
    dirLight->SetDiffuse(Vec3(0.8f));
    dirLight->SetAmbient(Vec3(0.2f));
    m_mainScene->AddLight(dirLight);

    // 创建地面
    m_ground = std::make_shared<SceneObject>("Ground");
    m_ground->SetRenderObject(Renderer::CreatePlane(20.0f, 20.0f));
    Material groundMat;
    groundMat.diffuse = Vec3(0.5f, 0.5f, 0.5f);
    groundMat.ambient = Vec3(0.1f);
    m_ground->GetRenderObject().material = &groundMat;
    m_mainScene->AddObject(m_ground);

    // 创建立方体
    m_cube = std::make_shared<SceneObject>("Cube");
    m_cube->SetRenderObject(Renderer::CreateCube(1.0f));
    Material cubeMat;
    cubeMat.diffuse = Vec3(0.8f, 0.2f, 0.2f);
    cubeMat.ambient = Vec3(0.1f, 0.05f, 0.05f);
    m_cube->GetRenderObject().material = &cubeMat;
    m_cube->GetTransform().SetPosition(Vec3(-2.0f, 0.5f, 0.0f));
    m_mainScene->AddObject(m_cube);

    // 创建球体
    m_sphere = std::make_shared<SceneObject>("Sphere");
    m_sphere->SetRenderObject(Renderer::CreateSphere(0.5f));
    Material sphereMat;
    sphereMat.diffuse = Vec3(0.2f, 0.8f, 0.2f);
    sphereMat.ambient = Vec3(0.05f, 0.1f, 0.05f);
    m_sphere->GetRenderObject().material = &sphereMat;
    m_sphere->GetTransform().SetPosition(Vec3(2.0f, 1.0f, 0.0f));
    m_mainScene->AddObject(m_sphere);

    // 创建可交互物体
    for (int i = 0; i < 5; i++) {
        auto obj = std::make_shared<SceneObject>("Interactive_" + std::to_string(i));
        obj->SetRenderObject(Renderer::CreateCube(0.3f));

        Material mat;
        mat.diffuse = Vec3(
            static_cast<float>(rand()) / RAND_MAX,
            static_cast<float>(rand()) / RAND_MAX,
            static_cast<float>(rand()) / RAND_MAX
        );
        obj->GetRenderObject().material = &mat;

        float x = -2.0f + i * 1.0f;
        obj->GetTransform().SetPosition(Vec3(x, 0.15f, -2.0f));
        m_interactiveObjects.push_back(obj);
        m_mainScene->AddObject(obj);
    }

    VR_INFO("SimpleVRScene created");
}

void SimpleVRApp::ProcessInput(float deltaTime) {
    // 调用基类处理
    Application::ProcessInput(deltaTime);

    auto* input = GetInputManager();
    if (!input) return;

    // 检测抓取
    for (int i = 0; i < 2; i++) {
        if (input->IsButtonJustPressed(i, 0)) {  // 触发器按钮
            // 射线检测
            HitResult hit = input->RaycastController(i);
            if (hit.hit) {
                // 找到可交互物体
                for (auto& obj : m_interactiveObjects) {
                    if (obj->GetID() == hit.objectID) {
                        m_isGrabbing = true;
                        VR_INFO("Grabbed object: " + obj->GetName());
                        break;
                    }
                }
            }
        }

        if (input->IsButtonJustReleased(i, 0)) {
            if (m_isGrabbing) {
                m_isGrabbing = false;
                VR_INFO("Released object");
            }
        }
    }
}

void SimpleVRApp::HandleInteraction(const InteractionEvent& event) {
    switch (event.type) {
        case InteractionType::Grab:
            VR_INFO("Grab interaction at position: " +
                    std::to_string(event.position.x) + ", " +
                    std::to_string(event.position.y) + ", " +
                    std::to_string(event.position.z));
            break;

        case InteractionType::Release:
            VR_INFO("Release interaction");
            break;

        default:
            break;
    }
}

}  // namespace vr