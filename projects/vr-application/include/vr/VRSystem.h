#pragma once

#include "Common.h"
#include <vector>
#include <optional>

namespace vr {

// VR 姿态
struct VRPose {
    Vec3 position = Vec3(0.0f);
    Quat orientation = Quat(1.0f, 0.0f, 0.0f, 0.0f);
    Vec3 linearVelocity = Vec3(0.0f);
    Vec3 angularVelocity = Vec3(0.0f);

    // 转换为矩阵
    Mat4 ToMatrix() const;

    // 插值
    static VRPose Lerp(const VRPose& a, const VRPose& b, float t);
};

// VR 视图
struct VRView {
    Mat4 projectionMatrix = Mat4(1.0f);
    Mat4 viewMatrix = Mat4(1.0f);
    VRPose pose;

    // 视场角
    float fovLeft = 0.0f;
    float fovRight = 0.0f;
    float fovUp = 0.0f;
    float fovDown = 0.0f;
};

// VR 控制器状态
struct ControllerState {
    VRPose pose;
    bool isConnected = false;

    // 按钮状态
    bool triggerPressed = false;
    float triggerValue = 0.0f;
    bool gripPressed = false;
    float gripValue = 0.0f;
    bool buttonAPressed = false;
    bool buttonBPressed = false;
    bool thumbstickPressed = false;
    Vec2 thumbstickValue = Vec2(0.0f);

    // 振动
    float hapticAmplitude = 0.0f;
    float hapticDuration = 0.0f;
};

// VR 事件
enum class VREventType {
    SessionStateChanged,
    ReferenceSpaceChanged,
    ControllerConnected,
    ControllerDisconnected,
    InteractionProfileChanged
};

struct VREvent {
    VREventType type;
    // 事件数据...
};

// VR 配置
struct VRConfig {
    bool enableDesktopMode = false;  // 桌面模拟模式
    float renderScale = 1.0f;
    float ipd = 0.064f;  // 瞳距
    float nearClip = 0.1f;
    float farClip = 1000.0f;

    // 追踪设置
    bool enablePositionTracking = true;
    bool enableRotationTracking = true;
    bool enableHandTracking = false;

    // 渲染设置
    bool enableDistortion = true;
    bool enableFoveatedRendering = false;
    bool enableATW = true;  // 异步时间扭曲
};

// VR 系统状态
enum class VRState {
    Uninitialized,
    Initialized,
    Ready,
    Running,
    Paused,
    Stopped,
    Error
};

// VR 系统类
class VRSystem {
public:
    VRSystem();
    ~VRSystem();

    // 禁用拷贝
    VRSystem(const VRSystem&) = delete;
    VRSystem& operator=(const VRSystem&) = delete;

    // 初始化和关闭
    bool Initialize(const VRConfig& config = VRConfig());
    void Shutdown();

    // 会话管理
    bool BeginSession();
    void EndSession();
    bool IsSessionActive() const;

    // 帧循环
    bool WaitFrame();
    bool BeginFrame();
    bool EndFrame();

    // 获取视图
    VRView GetView(Eye eye) const;
    VRPose GetHeadPose() const;

    // 控制器
    ControllerState GetControllerState(int controller) const;
    VRPose GetControllerPose(int controller) const;

    // 事件处理
    bool PollEvents(VREvent& event);
    std::vector<VREvent> PollAllEvents();

    // 参考空间
    bool SetReferenceSpace(const Vec3& position = Vec3(0.0f));
    Vec3 GetReferenceSpacePosition() const;

    // 状态查询
    VRState GetState() const { return m_state; }
    bool IsDesktopMode() const { return m_config.enableDesktopMode; }
    bool IsTrackingActive() const;

    // 配置
    const VRConfig& GetConfig() const { return m_config; }
    void SetConfig(const VRConfig& config);

    // 设备信息
    std::string GetDeviceName() const;
    VRDeviceType GetDeviceType() const { return m_deviceType; }

    // 渲染目标大小
    void GetRenderTargetSize(uint32_t& width, uint32_t& height) const;

    // 桌面模式输入
    void UpdateDesktopInput(GLFWwindow* window, float deltaTime);

private:
#ifdef USE_OPENXR
    // OpenXR 初始化
    bool InitializeOpenXR();
    void ShutdownOpenXR();

    // OpenXR 会话
    bool CreateSession();
    void DestroySession();

    // OpenXR 交换链
    bool CreateSwapchain();
    void DestroySwapchain();

    // OpenXR 动作
    bool CreateActions();
    void DestroyActions();

    // 更新姿态
    void UpdatePoses();

    // OpenXR 对象
    XrInstance m_instance = XR_NULL_HANDLE;
    XrSystem m_system = XR_NULL_SYSTEM_ID;
    XrSession m_session = XR_NULL_HANDLE;
    XrSpace m_appSpace = XR_NULL_HANDLE;
    XrSpace m_viewSpace = XR_NULL_HANDLE;
    XrSpace m_handSpaces[2] = {XR_NULL_HANDLE, XR_NULL_HANDLE};

    // 交换链
    XrSwapchain m_swapchain = XR_NULL_HANDLE;
    std::vector<XrSwapchainImageOpenGLKHR> m_swapchainImages;

    // 视图
    XrView m_views[2];
    XrViewState m_viewState;

    // 动作
    XrActionSet m_actionSet = XR_NULL_HANDLE;
    XrAction m_triggerAction = XR_NULL_HANDLE;
    XrAction m_gripAction = XR_NULL_HANDLE;
    XrAction m_buttonAAction = XR_NULL_HANDLE;
    XrAction m_buttonBAction = XR_NULL_HANDLE;
    XrAction m_thumbstickAction = XR_NULL_HANDLE;
    XrAction m_hapticAction = XR_NULL_HANDLE;
    XrAction m_handPoseAction = XR_NULL_HANDLE;

    // 控制器路径
    XrPath m_handPaths[2];
#endif

    // 状态
    VRState m_state = VRState::Uninitialized;
    VRConfig m_config;
    VRDeviceType m_deviceType = VRDeviceType::Desktop;

    // 姿态数据
    VRPose m_headPose;
    VRPose m_controllerPoses[2];
    ControllerState m_controllerStates[2];

    // 参考空间
    Vec3 m_referenceSpacePosition = Vec3(0.0f);

    // 渲染目标
    uint32_t m_renderWidth = 1920;
    uint32_t m_renderHeight = 1080;

    // 桌面模式
    bool m_desktopMode = false;
    float m_desktopYaw = 0.0f;
    float m_desktopPitch = 0.0f;
    Vec3 m_desktopPosition = Vec3(0.0f, 1.6f, 0.0f);  // 默认眼睛高度

    // 帧状态
    bool m_frameStarted = false;

    // 事件队列
    std::vector<VREvent> m_eventQueue;
};

// VR 渲染器（处理 VR 特定的渲染逻辑）
class VRRenderer {
public:
    VRRenderer();
    ~VRRenderer();

    // 初始化
    bool Initialize(VRSystem* vrSystem);

    // 渲染
    void BeginEye(Eye eye);
    void EndEye(Eye eye);
    void SubmitFrame();

    // 获取视图矩阵
    Mat4 GetViewMatrix(Eye eye) const;

    // 获取投影矩阵
    Mat4 GetProjectionMatrix(Eye eye) const;

    // 畸变校正
    void ApplyDistortion();

private:
    VRSystem* m_vrSystem = nullptr;

    // 畸变参数
    float m_distortionK1 = 0.0f;
    float m_distortionK2 = 0.0f;

    // 渲染缓冲区
    GLuint m_framebuffers[2] = {0, 0};
    GLuint m_textures[2] = {0, 0};
    GLuint m_depthTextures[2] = {0, 0};
};

}  // namespace vr