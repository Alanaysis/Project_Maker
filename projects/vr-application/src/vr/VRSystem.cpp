#include "vr/VRSystem.h"
#include <iostream>
#include <cmath>

namespace vr {

// VRPose 实现
Mat4 VRPose::ToMatrix() const {
    Mat4 translation = glm::translate(Mat4(1.0f), position);
    Mat4 rotation = glm::toMat4(orientation);
    return translation * rotation;
}

VRPose VRPose::Lerp(const VRPose& a, const VRPose& b, float t) {
    VRPose result;
    result.position = glm::mix(a.position, b.position, t);
    result.orientation = glm::slerp(a.orientation, b.orientation, t);
    result.linearVelocity = glm::mix(a.linearVelocity, b.linearVelocity, t);
    result.angularVelocity = glm::mix(a.angularVelocity, b.angularVelocity, t);
    return result;
}

// VRSystem 实现
VRSystem::VRSystem() {
    m_handPaths[0] = 0;
    m_handPaths[1] = 1;
}

VRSystem::~VRSystem() {
    Shutdown();
}

bool VRSystem::Initialize(const VRConfig& config) {
    if (m_state != VRState::Uninitialized) {
        return true;
    }

    m_config = config;

#ifdef USE_OPENXR
    // 初始化 OpenXR
    if (!config.enableDesktopMode) {
        if (!InitializeOpenXR()) {
            VR_WARNING("OpenXR initialization failed, falling back to desktop mode");
            m_config.enableDesktopMode = true;
        }
    }
#endif

    if (m_config.enableDesktopMode) {
        // 桌面模式初始化
        m_deviceType = VRDeviceType::Desktop;
        m_desktopMode = true;
        m_renderWidth = 1920;
        m_renderHeight = 1080;

        VR_INFO("VR System initialized in desktop mode");
    }

    m_state = VRState::Initialized;
    return true;
}

void VRSystem::Shutdown() {
    if (m_state == VRState::Uninitialized) {
        return;
    }

#ifdef USE_OPENXR
    if (!m_desktopMode) {
        ShutdownOpenXR();
    }
#endif

    m_state = VRState::Uninitialized;
    VR_INFO("VR System shutdown");
}

bool VRSystem::BeginSession() {
    if (m_state != VRState::Initialized && m_state != VRState::Ready) {
        return false;
    }

    m_state = VRState::Running;
    return true;
}

void VRSystem::EndSession() {
    m_state = VRState::Stopped;
}

bool VRSystem::IsSessionActive() const {
    return m_state == VRState::Running;
}

bool VRSystem::WaitFrame() {
    if (!IsSessionActive()) return false;

#ifdef USE_OPENXR
    if (!m_desktopMode) {
        // OpenXR 帧等待
        XrFrameState frameState = {XR_TYPE_FRAME_STATE};
        // xrWaitFrame would be called here
    }
#endif

    return true;
}

bool VRSystem::BeginFrame() {
    if (!IsSessionActive()) return false;

    m_frameStarted = true;

#ifdef USE_OPENXR
    if (!m_desktopMode) {
        // OpenXR 帧开始
        // xrBeginFrame would be called here
        UpdatePoses();
    }
#endif

    return true;
}

bool VRSystem::EndFrame() {
    if (!m_frameStarted) return false;

    m_frameStarted = false;

#ifdef USE_OPENXR
    if (!m_desktopMode) {
        // OpenXR 帧结束
        // xrEndFrame would be called here
    }
#endif

    return true;
}

VRView VRSystem::GetView(Eye eye) const {
    VRView view;

    if (m_desktopMode) {
        // 桌面模式：使用简单的透视投影
        float aspect = static_cast<float>(m_renderWidth) / static_cast<float>(m_renderHeight);
        view.projectionMatrix = glm::perspective(glm::radians(45.0f), aspect, m_config.nearClip, m_config.farClip);

        // 计算视图矩阵
        Mat4 headMatrix = m_headPose.ToMatrix();
        view.viewMatrix = glm::inverse(headMatrix);

        // 为双眼添加轻微偏移（模拟 IPD）
        float ipdOffset = (eye == Eye::Left) ? -m_config.ipd / 2.0f : m_config.ipd / 2.0f;
        view.viewMatrix = glm::translate(view.viewMatrix, Vec3(ipdOffset, 0, 0));

        view.pose = m_headPose;
        view.fovLeft = 45.0f;
        view.fovRight = 45.0f;
        view.fovUp = 45.0f;
        view.fovDown = 45.0f;
    }
#ifdef USE_OPENXR
    else {
        // OpenXR 模式
        int eyeIndex = static_cast<int>(eye);
        if (eyeIndex < 2) {
            // 从 OpenXR 获取视图
            XrView& xrView = m_views[eyeIndex];

            // 构建投影矩阵
            view.projectionMatrix = ...;  // 从 XrView 计算

            // 构建视图矩阵
            view.viewMatrix = ...;  // 从 XrView 计算

            view.pose.position = Vec3(xrView.pose.position.x, xrView.pose.position.y, xrView.pose.position.z);
            view.pose.orientation = Quat(xrView.pose.orientation.w, xrView.pose.orientation.x,
                                         xrView.pose.orientation.y, xrView.pose.orientation.z);
        }
    }
#endif

    return view;
}

VRPose VRSystem::GetHeadPose() const {
    return m_headPose;
}

ControllerState VRSystem::GetControllerState(int controller) const {
    if (controller >= 0 && controller < 2) {
        return m_controllerStates[controller];
    }
    return ControllerState();
}

VRPose VRSystem::GetControllerPose(int controller) const {
    if (controller >= 0 && controller < 2) {
        return m_controllerPoses[controller];
    }
    return VRPose();
}

bool VRSystem::PollEvents(VREvent& event) {
    if (m_eventQueue.empty()) {
        return false;
    }

    event = m_eventQueue.front();
    m_eventQueue.erase(m_eventQueue.begin());
    return true;
}

std::vector<VREvent> VRSystem::PollAllEvents() {
    std::vector<VREvent> events = m_eventQueue;
    m_eventQueue.clear();
    return events;
}

bool VRSystem::SetReferenceSpace(const Vec3& position) {
    m_referenceSpacePosition = position;

#ifdef USE_OPENXR
    if (!m_desktopMode) {
        // 更新 OpenXR 参考空间
        // xrCreateReferenceSpace would be called here
    }
#endif

    return true;
}

Vec3 VRSystem::GetReferenceSpacePosition() const {
    return m_referenceSpacePosition;
}

bool VRSystem::IsTrackingActive() const {
    return m_state == VRState::Running;
}

void VRSystem::SetConfig(const VRConfig& config) {
    m_config = config;
}

std::string VRSystem::GetDeviceName() const {
    switch (m_deviceType) {
        case VRDeviceType::Desktop: return "Desktop (Simulated)";
        case VRDeviceType::Oculus: return "Oculus";
        case VRDeviceType::SteamVR: return "SteamVR";
        case VRDeviceType::WMR: return "Windows Mixed Reality";
        default: return "Unknown";
    }
}

void VRSystem::GetRenderTargetSize(uint32_t& width, uint32_t& height) const {
    width = m_renderWidth;
    height = m_renderHeight;
}

void VRSystem::UpdateDesktopInput(GLFWwindow* window, float deltaTime) {
    if (!window) return;

    // 鼠标控制视角
    static double lastX = 0, lastY = 0;
    static bool firstMouse = true;

    double xpos, ypos;
    glfwGetCursorPos(window, &xpos, &ypos);

    if (firstMouse) {
        lastX = xpos;
        lastY = ypos;
        firstMouse = false;
    }

    float xoffset = static_cast<float>(xpos - lastX) * 0.1f;
    float yoffset = static_cast<float>(lastY - ypos) * 0.1f;
    lastX = xpos;
    lastY = ypos;

    // 更新视角
    m_desktopYaw += xoffset;
    m_desktopPitch += yoffset;

    // 限制俯仰角
    m_desktopPitch = glm::clamp(m_desktopPitch, -89.0f, 89.0f);

    // 计算朝向
    Vec3 front;
    front.x = cos(glm::radians(m_desktopYaw)) * cos(glm::radians(m_desktopPitch));
    front.y = sin(glm::radians(m_desktopPitch));
    front.z = sin(glm::radians(m_desktopYaw)) * cos(glm::radians(m_desktopPitch));
    front = glm::normalize(front);

    // 键盘移动
    float moveSpeed = 5.0f * deltaTime;
    Vec3 right = glm::normalize(glm::cross(front, Vec3(0, 1, 0)));

    if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS) {
        m_desktopPosition += front * moveSpeed;
    }
    if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS) {
        m_desktopPosition -= front * moveSpeed;
    }
    if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS) {
        m_desktopPosition -= right * moveSpeed;
    }
    if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS) {
        m_desktopPosition += right * moveSpeed;
    }
    if (glfwGetKey(window, GLFW_KEY_SPACE) == GLFW_PRESS) {
        m_desktopPosition.y += moveSpeed;
    }
    if (glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS) {
        m_desktopPosition.y -= moveSpeed;
    }

    // 更新头部姿态
    m_headPose.position = m_desktopPosition;
    m_headPose.orientation = glm::quatLookAt(front, Vec3(0, 1, 0));

    // 模拟手柄
    for (int i = 0; i < 2; i++) {
        Vec3 handOffset = (i == 0) ? Vec3(-0.3f, -0.3f, -0.5f) : Vec3(0.3f, -0.3f, -0.5f);
        Mat4 headMatrix = m_headPose.ToMatrix();
        Vec3 handPos = Vec3(headMatrix * Vec4(handOffset, 1.0f));

        m_controllerPoses[i].position = handPos;
        m_controllerPoses[i].orientation = m_headPose.orientation;

        m_controllerStates[i].pose = m_controllerPoses[i];
        m_controllerStates[i].isConnected = true;

        // 鼠标左键模拟触发器
        if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS) {
            m_controllerStates[i].triggerPressed = true;
            m_controllerStates[i].triggerValue = 1.0f;
        } else {
            m_controllerStates[i].triggerPressed = false;
            m_controllerStates[i].triggerValue = 0.0f;
        }

        // 鼠标右键模拟抓取
        if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_RIGHT) == GLFW_PRESS) {
            m_controllerStates[i].gripPressed = true;
            m_controllerStates[i].gripValue = 1.0f;
        } else {
            m_controllerStates[i].gripPressed = false;
            m_controllerStates[i].gripValue = 0.0f;
        }
    }
}

#ifdef USE_OPENXR
bool VRSystem::InitializeOpenXR() {
    // 创建 OpenXR 实例
    XrApplicationInfo appInfo = {};
    strcpy(appInfo.applicationName, "VR Application");
    appInfo.applicationVersion = 1;
    strcpy(appInfo.engineName, "VREngine");
    appInfo.engineVersion = 1;
    appInfo.apiVersion = XR_CURRENT_API_VERSION;

    XrInstanceCreateInfo instanceCreateInfo = {XR_TYPE_INSTANCE_CREATE_INFO};
    instanceCreateInfo.applicationInfo = appInfo;

    // 启用的扩展
    const char* enabledExtensions[] = {
        XR_KHR_OPENGL_ENABLE_EXTENSION_NAME,
    };
    instanceCreateInfo.enabledExtensionCount = 1;
    instanceCreateInfo.enabledExtensionNames = enabledExtensions;

    XrResult result = xrCreateInstance(&instanceCreateInfo, &m_instance);
    if (result != XR_SUCCESS) {
        VR_ERROR("Failed to create OpenXR instance");
        return false;
    }

    // 获取系统
    XrSystemGetInfo systemGetInfo = {XR_TYPE_SYSTEM_GET_INFO};
    systemGetInfo.formFactor = XR_FORM_FACTOR_HEAD_MOUNTED_DISPLAY;

    result = xrGetSystem(m_instance, &systemGetInfo, &m_system);
    if (result != XR_SUCCESS) {
        VR_ERROR("Failed to get OpenXR system");
        return false;
    }

    // 获取系统属性
    XrSystemProperties systemProperties = {XR_TYPE_SYSTEM_PROPERTIES};
    result = xrGetSystemProperties(m_instance, m_system, &systemProperties);
    if (result == XR_SUCCESS) {
        VR_INFO("VR Device: " + std::string(systemProperties.systemName));
    }

    // 设置渲染分辨率
    uint32_t viewCount;
    XrViewConfigurationView viewConfig = {XR_TYPE_VIEW_CONFIGURATION_VIEW};
    result = xrEnumerateViewConfigurationViews(m_instance, m_system,
                                                XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO,
                                                1, &viewCount, &viewConfig);
    if (result == XR_SUCCESS && viewCount > 0) {
        m_renderWidth = viewConfig.recommendedImageRectWidth;
        m_renderHeight = viewConfig.recommendedImageRectHeight;
    }

    // 创建会话
    if (!CreateSession()) {
        return false;
    }

    // 创建动作
    if (!CreateActions()) {
        return false;
    }

    m_deviceType = VRDeviceType::Other;
    return true;
}

void VRSystem::ShutdownOpenXR() {
    DestroyActions();
    DestroySession();

    if (m_instance) {
        xrDestroyInstance(m_instance);
        m_instance = XR_NULL_HANDLE;
    }
}

bool VRSystem::CreateSession() {
    // 创建会话需要图形绑定
    // 这里简化实现

    XrSessionCreateInfo sessionCreateInfo = {XR_TYPE_SESSION_CREATE_INFO};
    sessionCreateInfo.systemId = m_system;

    XrResult result = xrCreateSession(m_instance, &sessionCreateInfo, &m_session);
    if (result != XR_SUCCESS) {
        VR_ERROR("Failed to create OpenXR session");
        return false;
    }

    // 创建参考空间
    XrReferenceSpaceCreateInfo spaceCreateInfo = {XR_TYPE_REFERENCE_SPACE_CREATE_INFO};
    spaceCreateInfo.referenceSpaceType = XR_REFERENCE_SPACE_TYPE_LOCAL;
    spaceCreateInfo.poseInReferenceSpace.orientation.w = 1.0f;

    result = xrCreateReferenceSpace(m_session, &spaceCreateInfo, &m_appSpace);
    if (result != XR_SUCCESS) {
        VR_ERROR("Failed to create reference space");
        return false;
    }

    return true;
}

void VRSystem::DestroySession() {
    if (m_appSpace) {
        xrDestroySpace(m_appSpace);
        m_appSpace = XR_NULL_HANDLE;
    }
    if (m_viewSpace) {
        xrDestroySpace(m_viewSpace);
        m_viewSpace = XR_NULL_HANDLE;
    }
    for (int i = 0; i < 2; i++) {
        if (m_handSpaces[i]) {
            xrDestroySpace(m_handSpaces[i]);
            m_handSpaces[i] = XR_NULL_HANDLE;
        }
    }
    if (m_session) {
        xrDestroySession(m_session);
        m_session = XR_NULL_HANDLE;
    }
}

bool VRSystem::CreateSwapchain() {
    // 简化实现
    return true;
}

void VRSystem::DestroySwapchain() {
    // 简化实现
}

bool VRSystem::CreateActions() {
    // 创建动作集
    XrActionSetCreateInfo actionSetCreateInfo = {XR_TYPE_ACTION_SET_CREATE_INFO};
    strcpy(actionSetCreateInfo.actionSetName, "default");
    strcpy(actionSetCreateInfo.localizedActionSetName, "Default Actions");

    XrResult result = xrCreateActionSet(m_instance, &actionSetCreateInfo, &m_actionSet);
    if (result != XR_SUCCESS) {
        VR_ERROR("Failed to create action set");
        return false;
    }

    // 创建触发器动作
    XrActionCreateInfo actionCreateInfo = {XR_TYPE_ACTION_CREATE_INFO};
    actionCreateInfo.actionType = XR_ACTION_TYPE_FLOAT_INPUT;
    strcpy(actionCreateInfo.actionName, "trigger");
    strcpy(actionCreateInfo.localizedActionName, "Trigger");
    xrCreateAction(m_actionSet, &actionCreateInfo, &m_triggerAction);

    // 创建抓取动作
    actionCreateInfo.actionType = XR_ACTION_TYPE_FLOAT_INPUT;
    strcpy(actionCreateInfo.actionName, "grip");
    strcpy(actionCreateInfo.localizedActionName, "Grip");
    xrCreateAction(m_actionSet, &actionCreateInfo, &m_gripAction);

    // 创建手柄姿态动作
    actionCreateInfo.actionType = XR_ACTION_TYPE_POSE_INPUT;
    strcpy(actionCreateInfo.actionName, "hand_pose");
    strcpy(actionCreateInfo.localizedActionName, "Hand Pose");
    xrCreateAction(m_actionSet, &actionCreateInfo, &m_handPoseAction);

    // 创建振动反馈动作
    actionCreateInfo.actionType = XR_ACTION_TYPE_VIBRATION_OUTPUT;
    strcpy(actionCreateInfo.actionName, "haptic");
    strcpy(actionCreateInfo.localizedActionName, "Haptic");
    xrCreateAction(m_actionSet, &actionCreateInfo, &m_hapticAction);

    // 绑定到交互配置文件
    // 这里需要根据具体的 VR 运行时进行绑定

    // 附加动作集到会话
    XrSessionActionSetsAttachInfo attachInfo = {XR_TYPE_SESSION_ACTION_SETS_ATTACH_INFO};
    attachInfo.countActionSets = 1;
    attachInfo.actionSets = &m_actionSet;
    xrAttachSessionActionSets(m_session, &attachInfo);

    return true;
}

void VRSystem::DestroyActions() {
    if (m_triggerAction) {
        xrDestroyAction(m_triggerAction);
        m_triggerAction = XR_NULL_HANDLE;
    }
    if (m_gripAction) {
        xrDestroyAction(m_gripAction);
        m_gripAction = XR_NULL_HANDLE;
    }
    if (m_buttonAAction) {
        xrDestroyAction(m_buttonAAction);
        m_buttonAAction = XR_NULL_HANDLE;
    }
    if (m_buttonBAction) {
        xrDestroyAction(m_buttonBAction);
        m_buttonBAction = XR_NULL_HANDLE;
    }
    if (m_thumbstickAction) {
        xrDestroyAction(m_thumbstickAction);
        m_thumbstickAction = XR_NULL_HANDLE;
    }
    if (m_hapticAction) {
        xrDestroyAction(m_hapticAction);
        m_hapticAction = XR_NULL_HANDLE;
    }
    if (m_handPoseAction) {
        xrDestroyAction(m_handPoseAction);
        m_handPoseAction = XR_NULL_HANDLE;
    }
    if (m_actionSet) {
        xrDestroyActionSet(m_actionSet);
        m_actionSet = XR_NULL_HANDLE;
    }
}

void VRSystem::UpdatePoses() {
    if (!m_session) return;

    // 更新手柄姿态
    for (int i = 0; i < 2; i++) {
        XrActionStateGetInfo getInfo = {XR_TYPE_ACTION_STATE_GET_INFO};
        getInfo.action = m_handPoseAction;
        getInfo.subactionPath = m_handPaths[i];

        XrActionStatePose poseState = {XR_TYPE_ACTION_STATE_POSE};
        xrGetActionStatePose(m_session, &getInfo, &poseState);

        if (poseState.isActive) {
            XrSpaceLocation spaceLocation = {XR_TYPE_SPACE_LOCATION};
            xrLocateSpace(m_handSpaces[i], m_appSpace, 0, &spaceLocation);

            if (spaceLocation.locationFlags & XR_SPACE_LOCATION_POSITION_VALID_BIT) {
                m_controllerPoses[i].position = Vec3(
                    spaceLocation.pose.position.x,
                    spaceLocation.pose.position.y,
                    spaceLocation.pose.position.z
                );
            }

            if (spaceLocation.locationFlags & XR_SPACE_LOCATION_ORIENTATION_VALID_BIT) {
                m_controllerPoses[i].orientation = Quat(
                    spaceLocation.pose.orientation.w,
                    spaceLocation.pose.orientation.x,
                    spaceLocation.pose.orientation.y,
                    spaceLocation.pose.orientation.z
                );
            }
        }

        // 更新控制器状态
        m_controllerStates[i].pose = m_controllerPoses[i];
        m_controllerStates[i].isConnected = true;

        // 获取触发器状态
        XrActionStateFloat triggerState = {XR_TYPE_ACTION_STATE_FLOAT};
        getInfo.action = m_triggerAction;
        xrGetActionStateFloat(m_session, &getInfo, &triggerState);
        if (triggerState.isActive) {
            m_controllerStates[i].triggerValue = triggerState.currentState;
            m_controllerStates[i].triggerPressed = triggerState.currentState > 0.5f;
        }

        // 获取抓取状态
        XrActionStateFloat gripState = {XR_TYPE_ACTION_STATE_FLOAT};
        getInfo.action = m_gripAction;
        xrGetActionStateFloat(m_session, &getInfo, &gripState);
        if (gripState.isActive) {
            m_controllerStates[i].gripValue = gripState.currentState;
            m_controllerStates[i].gripPressed = gripState.currentState > 0.5f;
        }
    }

    // 更新头部姿态
    XrSpaceLocation headLocation = {XR_TYPE_SPACE_LOCATION};
    xrLocateSpace(m_viewSpace, m_appSpace, 0, &headLocation);

    if (headLocation.locationFlags & XR_SPACE_LOCATION_POSITION_VALID_BIT) {
        m_headPose.position = Vec3(
            headLocation.pose.position.x,
            headLocation.pose.position.y,
            headLocation.pose.position.z
        );
    }

    if (headLocation.locationFlags & XR_SPACE_LOCATION_ORIENTATION_VALID_BIT) {
        m_headPose.orientation = Quat(
            headLocation.pose.orientation.w,
            headLocation.pose.orientation.x,
            headLocation.pose.orientation.y,
            headLocation.pose.orientation.z
        );
    }
}
#endif

// VRRenderer 实现
VRRenderer::VRRenderer() = default;

VRRenderer::~VRRenderer() = default;

bool VRRenderer::Initialize(VRSystem* vrSystem) {
    m_vrSystem = vrSystem;
    return true;
}

void VRRenderer::BeginEye(Eye eye) {
    if (!m_vrSystem) return;

    int eyeIndex = static_cast<int>(eye);
    glBindFramebuffer(GL_FRAMEBUFFER, m_framebuffers[eyeIndex]);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

void VRRenderer::EndEye(Eye eye) {
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

void VRRenderer::SubmitFrame() {
    // 提交帧到 VR 运行时
}

Mat4 VRRenderer::GetViewMatrix(Eye eye) const {
    if (!m_vrSystem) return Mat4(1.0f);

    VRView view = m_vrSystem->GetView(eye);
    return view.viewMatrix;
}

Mat4 VRRenderer::GetProjectionMatrix(Eye eye) const {
    if (!m_vrSystem) return Mat4(1.0f);

    VRView view = m_vrSystem->GetView(eye);
    return view.projectionMatrix;
}

void VRRenderer::ApplyDistortion() {
    // 应用畸变校正
    // 简化实现
}

}  // namespace vr