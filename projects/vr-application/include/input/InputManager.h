#pragma once

#include "Common.h"
#include "vr/VRSystem.h"
#include <functional>
#include <unordered_map>

namespace vr {

// 输入事件类型
enum class InputEventType {
    ButtonPressed,
    ButtonReleased,
    TriggerPulled,
    TriggerReleased,
    ThumbstickMoved,
    GestureDetected
};

// 输入事件
struct InputEvent {
    InputEventType type;
    int controller;  // 0 = 左手, 1 = 右手
    int button;
    float value;
    Vec2 axisValue;
};

// 交互类型
enum class InteractionType {
    Grab,
    Release,
    Point,
    Touch,
    Teleport,
    Menu
};

// 交互事件
struct InteractionEvent {
    InteractionType type;
    int controller;
    Vec3 position;
    Vec3 direction;
    float value;
};

// 射线
struct Ray {
    Vec3 origin;
    Vec3 direction;

    Vec3 GetPoint(float t) const { return origin + direction * t; }
};

// 碰撞结果
struct HitResult {
    bool hit = false;
    Vec3 point = Vec3(0.0f);
    Vec3 normal = Vec3(0.0f);
    float distance = 0.0f;
    int objectID = -1;
};

// 可交互物体
class Interactable {
public:
    Interactable();
    virtual ~Interactable();

    // 交互回调
    using Callback = std::function<void(const InteractionEvent&)>;

    // 设置回调
    void SetOnGrab(Callback callback) { m_onGrab = callback; }
    void SetOnRelease(Callback callback) { m_onRelease = callback; }
    void SetOnHover(Callback callback) { m_onHover = callback; }
    void SetOnUnhover(Callback callback) { m_onUnhover = callback; }
    void SetOnTrigger(Callback callback) { m_onTrigger = callback; }

    // 触发交互
    void OnGrab(const InteractionEvent& event);
    void OnRelease(const InteractionEvent& event);
    void OnHover(const InteractionEvent& event);
    void OnUnhover(const InteractionEvent& event);
    void OnTrigger(const InteractionEvent& event);

    // 状态
    bool IsGrabbed() const { return m_isGrabbed; }
    bool IsHovered() const { return m_isHovered; }
    int GetGrabbedBy() const { return m_grabbedBy; }

    // 碰撞体
    virtual bool CheckCollision(const Ray& ray, HitResult& hit) const = 0;
    virtual bool CheckCollision(const Vec3& point, float radius) const = 0;

    // 变换
    void SetPosition(const Vec3& position) { m_position = position; }
    void SetRotation(const Quat& rotation) { m_rotation = rotation; }
    void SetScale(const Vec3& scale) { m_scale = scale; }

    Vec3 GetPosition() const { return m_position; }
    Quat GetRotation() const { return m_rotation; }
    Vec3 GetScale() const { return m_scale; }
    Mat4 GetTransformMatrix() const;

    // ID
    int GetID() const { return m_id; }
    void SetID(int id) { m_id = id; }

protected:
    int m_id = -1;
    Vec3 m_position = Vec3(0.0f);
    Quat m_rotation = Quat(1.0f, 0.0f, 0.0f, 0.0f);
    Vec3 m_scale = Vec3(1.0f);

    bool m_isGrabbed = false;
    bool m_isHovered = false;
    int m_grabbedBy = -1;

    Callback m_onGrab;
    Callback m_onRelease;
    Callback m_onHover;
    Callback m_onUnhover;
    Callback m_onTrigger;
};

// 球形碰撞体
class SphereInteractable : public Interactable {
public:
    SphereInteractable(float radius = 0.5f);

    bool CheckCollision(const Ray& ray, HitResult& hit) const override;
    bool CheckCollision(const Vec3& point, float radius) const override;

    void SetRadius(float radius) { m_radius = radius; }
    float GetRadius() const { return m_radius; }

private:
    float m_radius;
};

// 盒形碰撞体
class BoxInteractable : public Interactable {
public:
    BoxInteractable(const Vec3& size = Vec3(1.0f));

    bool CheckCollision(const Ray& ray, HitResult& hit) const override;
    bool CheckCollision(const Vec3& point, float radius) const override;

    void SetSize(const Vec3& size) { m_size = size; }
    Vec3 GetSize() const { return m_size; }

private:
    Vec3 m_size;
};

// 输入管理器配置
struct InputManagerConfig {
    bool enableHandTracking = false;
    float grabRadius = 0.1f;  // 抓取检测半径
    float pointerLength = 10.0f;  // 射线长度
    bool enableHaptics = true;
};

// 输入管理器类
class InputManager {
public:
    InputManager();
    ~InputManager();

    // 禁用拷贝
    InputManager(const InputManager&) = delete;
    InputManager& operator=(const InputManager&) = delete;

    // 初始化和关闭
    bool Initialize(VRSystem* vrSystem, const InputManagerConfig& config = InputManagerConfig());
    void Shutdown();

    // 更新输入状态
    void Update(float deltaTime);

    // 获取控制器状态
    ControllerState GetControllerState(int controller) const;

    // 获取控制器姿态
    VRPose GetControllerPose(int controller) const;

    // 获取射线
    Ray GetPointerRay(int controller) const;

    // 按钮状态
    bool IsButtonPressed(int controller, int button) const;
    bool IsButtonJustPressed(int controller, int button) const;
    bool IsButtonJustReleased(int controller, int button) const;
    float GetTriggerValue(int controller) const;
    float GetGripValue(int controller) const;
    Vec2 GetThumbstick(int controller) const;

    // 振动反馈
    void TriggerHaptic(int controller, float amplitude, float duration);

    // 交互物体管理
    void RegisterInteractable(SharedPtr<Interactable> interactable);
    void UnregisterInteractable(int id);
    SharedPtr<Interactable> GetInteractable(int id);

    // 射线检测
    HitResult Raycast(const Ray& ray, float maxDistance = 10.0f) const;
    HitResult RaycastController(int controller) const;

    // 拾取检测
    std::vector<SharedPtr<Interactable>> GetNearbyInteractables(const Vec3& position, float radius) const;

    // 事件回调
    using InputCallback = std::function<void(const InputEvent&)>;
    void RegisterCallback(InputEventType type, InputCallback callback);

    using InteractionCallback = std::function<void(const InteractionEvent&)>;
    void RegisterInteractionCallback(InteractionType type, InteractionCallback callback);

    // 获取配置
    const InputManagerConfig& GetConfig() const { return m_config; }

private:
    // 处理控制器输入
    void ProcessControllerInput(int controller, const ControllerState& state, float deltaTime);

    // 检测交互
    void DetectInteractions(int controller, const ControllerState& state);

    // 处理抓取
    void ProcessGrab(int controller, const ControllerState& state);

    // 处理指向
    void ProcessPointing(int controller, const ControllerState& state);

    // 触发事件
    void TriggerEvent(const InputEvent& event);
    void TriggerInteraction(const InteractionEvent& event);

    // 成员变量
    VRSystem* m_vrSystem = nullptr;
    InputManagerConfig m_config;

    // 控制器状态
    ControllerState m_currentStates[2];
    ControllerState m_previousStates[2];

    // 交互物体
    std::unordered_map<int, SharedPtr<Interactable>> m_interactables;
    int m_nextInteractableID = 0;

    // 当前交互状态
    SharedPtr<Interactable> m_grabbedObjects[2];
    SharedPtr<Interactable> m_hoveredObjects[2];
    HitResult m_lastHits[2];

    // 事件回调
    std::unordered_map<InputEventType, std::vector<InputCallback>> m_inputCallbacks;
    std::unordered_map<InteractionType, std::vector<InteractionCallback>> m_interactionCallbacks;

    // 状态
    bool m_isInitialized = false;
};

// 射线可视化
class PointerVisualizer {
public:
    PointerVisualizer();
    ~PointerVisualizer();

    bool Initialize();
    void Shutdown();

    void Render(const Ray& ray, float length, const HitResult& hit, const Vec4& color = Colors::Cyan);
    void RenderController(int controller, const Ray& ray, const HitResult& hit);

private:
    GLuint m_lineVAO = 0;
    GLuint m_lineVBO = 0;
    GLuint m_dotVAO = 0;
    GLuint m_dotVBO = 0;

    SharedPtr<Shader> m_shader;
};

}  // namespace vr