#include "input/InputManager.h"
#include <algorithm>
#include <cmath>

namespace vr {

// Interactable 实现
Interactable::Interactable() : m_id(-1) {}

Interactable::~Interactable() = default;

void Interactable::OnGrab(const InteractionEvent& event) {
    m_isGrabbed = true;
    m_grabbedBy = event.controller;
    if (m_onGrab) m_onGrab(event);
}

void Interactable::OnRelease(const InteractionEvent& event) {
    m_isGrabbed = false;
    m_grabbedBy = -1;
    if (m_onRelease) m_onRelease(event);
}

void Interactable::OnHover(const InteractionEvent& event) {
    m_isHovered = true;
    if (m_onHover) m_onHover(event);
}

void Interactable::OnUnhover(const InteractionEvent& event) {
    m_isHovered = false;
    if (m_onUnhover) m_onUnhover(event);
}

void Interactable::OnTrigger(const InteractionEvent& event) {
    if (m_onTrigger) m_onTrigger(event);
}

Mat4 Interactable::GetTransformMatrix() const {
    Mat4 translation = glm::translate(Mat4(1.0f), m_position);
    Mat4 rotation = glm::toMat4(m_rotation);
    Mat4 scale = glm::scale(Mat4(1.0f), m_scale);
    return translation * rotation * scale;
}

// SphereInteractable 实现
SphereInteractable::SphereInteractable(float radius) : m_radius(radius) {}

bool SphereInteractable::CheckCollision(const Ray& ray, HitResult& hit) const {
    Vec3 oc = ray.origin - m_position;
    float a = glm::dot(ray.direction, ray.direction);
    float b = 2.0f * glm::dot(oc, ray.direction);
    float c = glm::dot(oc, oc) - m_radius * m_radius;
    float discriminant = b * b - 4 * a * c;

    if (discriminant < 0) return false;

    float sqrtDisc = sqrt(discriminant);
    float t1 = (-b - sqrtDisc) / (2 * a);
    float t2 = (-b + sqrtDisc) / (2 * a);

    float t = (t1 > 0) ? t1 : t2;
    if (t < 0) return false;

    hit.hit = true;
    hit.point = ray.GetPoint(t);
    hit.normal = glm::normalize(hit.point - m_position);
    hit.distance = t;
    hit.objectID = m_id;

    return true;
}

bool SphereInteractable::CheckCollision(const Vec3& point, float radius) const {
    float distance = glm::length(point - m_position);
    return distance < (m_radius + radius);
}

// BoxInteractable 实现
BoxInteractable::BoxInteractable(const Vec3& size) : m_size(size) {}

bool BoxInteractable::CheckCollision(const Ray& ray, HitResult& hit) const {
    Vec3 min = m_position - m_size * 0.5f;
    Vec3 max = m_position + m_size * 0.5f;

    float tmin = 0.0f;
    float tmax = std::numeric_limits<float>::max();

    for (int i = 0; i < 3; i++) {
        float invD = 1.0f / (ray.direction[i] + 0.0001f);
        float t0 = (min[i] - ray.origin[i]) * invD;
        float t1 = (max[i] - ray.origin[i]) * invD;

        if (invD < 0.0f) std::swap(t0, t1);

        tmin = std::max(tmin, t0);
        tmax = std::min(tmax, t1);

        if (tmax < tmin) return false;
    }

    if (tmin < 0) {
        tmin = tmax;
        if (tmin < 0) return false;
    }

    hit.hit = true;
    hit.point = ray.GetPoint(tmin);
    hit.distance = tmin;
    hit.objectID = m_id;

    // 计算法线
    Vec3 localPoint = hit.point - m_position;
    Vec3 absPoint = glm::abs(localPoint);
    Vec3 halfSize = m_size * 0.5f;

    if (absPoint.x > absPoint.y && absPoint.x > absPoint.z) {
        hit.normal = Vec3(localPoint.x > 0 ? 1 : -1, 0, 0);
    } else if (absPoint.y > absPoint.z) {
        hit.normal = Vec3(0, localPoint.y > 0 ? 1 : -1, 0);
    } else {
        hit.normal = Vec3(0, 0, localPoint.z > 0 ? 1 : -1);
    }

    return true;
}

bool BoxInteractable::CheckCollision(const Vec3& point, float radius) const {
    Vec3 min = m_position - m_size * 0.5f - Vec3(radius);
    Vec3 max = m_position + m_size * 0.5f + Vec3(radius);

    return point.x >= min.x && point.x <= max.x &&
           point.y >= min.y && point.y <= max.y &&
           point.z >= min.z && point.z <= max.z;
}

// InputManager 实现
InputManager::InputManager() = default;

InputManager::~InputManager() {
    Shutdown();
}

bool InputManager::Initialize(VRSystem* vrSystem, const InputManagerConfig& config) {
    if (m_isInitialized) return true;

    m_vrSystem = vrSystem;
    m_config = config;

    m_isInitialized = true;
    VR_INFO("Input Manager initialized");
    return true;
}

void InputManager::Shutdown() {
    if (!m_isInitialized) return;

    m_interactables.clear();
    m_inputCallbacks.clear();
    m_interactionCallbacks.clear();

    m_isInitialized = false;
    VR_INFO("Input Manager shutdown");
}

void InputManager::Update(float deltaTime) {
    if (!m_isInitialized || !m_vrSystem) return;

    // 保存上一帧状态
    m_previousStates[0] = m_currentStates[0];
    m_previousStates[1] = m_currentStates[1];

    // 获取当前帧状态
    m_currentStates[0] = m_vrSystem->GetControllerState(0);
    m_currentStates[1] = m_vrSystem->GetControllerState(1);

    // 处理每个控制器
    for (int i = 0; i < 2; i++) {
        if (!m_currentStates[i].isConnected) continue;

        ProcessControllerInput(i, m_currentStates[i], deltaTime);
        DetectInteractions(i, m_currentStates[i]);
    }
}

ControllerState InputManager::GetControllerState(int controller) const {
    if (controller >= 0 && controller < 2) {
        return m_currentStates[controller];
    }
    return ControllerState();
}

VRPose InputManager::GetControllerPose(int controller) const {
    if (controller >= 0 && controller < 2) {
        return m_currentStates[controller].pose;
    }
    return VRPose();
}

Ray InputManager::GetPointerRay(int controller) const {
    Ray ray;
    if (controller >= 0 && controller < 2) {
        ray.origin = m_currentStates[controller].pose.position;
        Vec3 forward = glm::rotate(m_currentStates[controller].pose.orientation, Vec3(0, 0, -1));
        ray.direction = glm::normalize(forward);
    }
    return ray;
}

bool InputManager::IsButtonPressed(int controller, int button) const {
    if (controller < 0 || controller >= 2) return false;

    switch (button) {
        case 0: return m_currentStates[controller].triggerPressed;
        case 1: return m_currentStates[controller].gripPressed;
        case 2: return m_currentStates[controller].buttonAPressed;
        case 3: return m_currentStates[controller].buttonBPressed;
        default: return false;
    }
}

bool InputManager::IsButtonJustPressed(int controller, int button) const {
    return IsButtonPressed(controller, button) &&
           !m_previousStates[controller][button];
}

bool InputManager::IsButtonJustReleased(int controller, int button) const {
    return !IsButtonPressed(controller, button) &&
           m_previousStates[controller][button];
}

float InputManager::GetTriggerValue(int controller) const {
    if (controller >= 0 && controller < 2) {
        return m_currentStates[controller].triggerValue;
    }
    return 0.0f;
}

float InputManager::GetGripValue(int controller) const {
    if (controller >= 0 && controller < 2) {
        return m_currentStates[controller].gripValue;
    }
    return 0.0f;
}

Vec2 InputManager::GetThumbstick(int controller) const {
    if (controller >= 0 && controller < 2) {
        return m_currentStates[controller].thumbstickValue;
    }
    return Vec2(0.0f);
}

void InputManager::TriggerHaptic(int controller, float amplitude, float duration) {
    if (!m_vrSystem || controller < 0 || controller >= 2) return;

    // 触发振动反馈
    m_currentStates[controller].hapticAmplitude = amplitude;
    m_currentStates[controller].hapticDuration = duration;
}

void InputManager::RegisterInteractable(SharedPtr<Interactable> interactable) {
    if (!interactable) return;

    interactable->SetID(m_nextInteractableID++);
    m_interactables[interactable->GetID()] = interactable;
}

void InputManager::UnregisterInteractable(int id) {
    m_interactables.erase(id);
}

SharedPtr<Interactable> InputManager::GetInteractable(int id) {
    auto it = m_interactables.find(id);
    if (it != m_interactables.end()) {
        return it->second;
    }
    return nullptr;
}

HitResult InputManager::Raycast(const Ray& ray, float maxDistance) const {
    HitResult closestHit;
    closestHit.distance = maxDistance;

    for (const auto& [id, interactable] : m_interactables) {
        HitResult hit;
        if (interactable->CheckCollision(ray, hit)) {
            if (hit.distance < closestHit.distance) {
                closestHit = hit;
            }
        }
    }

    return closestHit;
}

HitResult InputManager::RaycastController(int controller) const {
    Ray ray = GetPointerRay(controller);
    return Raycast(ray, m_config.pointerLength);
}

std::vector<SharedPtr<Interactable>> InputManager::GetNearbyInteractables(const Vec3& position, float radius) const {
    std::vector<SharedPtr<Interactable>> result;

    for (const auto& [id, interactable] : m_interactables) {
        if (interactable->CheckCollision(position, radius)) {
            result.push_back(interactable);
        }
    }

    return result;
}

void InputManager::RegisterCallback(InputEventType type, InputCallback callback) {
    m_inputCallbacks[type].push_back(callback);
}

void InputManager::RegisterInteractionCallback(InteractionType type, InteractionCallback callback) {
    m_interactionCallbacks[type].push_back(callback);
}

void InputManager::ProcessControllerInput(int controller, const ControllerState& state, float deltaTime) {
    // 处理按钮事件
    for (int button = 0; button < 4; button++) {
        bool current = IsButtonPressed(controller, button);
        bool previous = (controller == 0) ?
            IsButtonPressed(0, button) :
            IsButtonPressed(1, button);  // 简化实现

        if (current && !previous) {
            InputEvent event;
            event.type = InputEventType::ButtonPressed;
            event.controller = controller;
            event.button = button;
            TriggerEvent(event);
        } else if (!current && previous) {
            InputEvent event;
            event.type = InputEventType::ButtonReleased;
            event.controller = controller;
            event.button = button;
            TriggerEvent(event);
        }
    }
}

void InputManager::DetectInteractions(int controller, const ControllerState& state) {
    // 射线检测
    Ray ray = GetPointerRay(controller);
    HitResult hit = Raycast(ray, m_config.pointerLength);

    // 处理指向
    ProcessPointing(controller, state);

    // 处理抓取
    ProcessGrab(controller, state);

    m_lastHits[controller] = hit;
}

void InputManager::ProcessGrab(int controller, const ControllerState& state) {
    bool gripPressed = state.gripPressed;
    bool gripWasPressed = m_previousStates[controller].gripPressed;

    if (gripPressed && !gripWasPressed) {
        // 开始抓取
        Ray ray = GetPointerRay(controller);
        HitResult hit = Raycast(ray, m_config.grabRadius * 10.0f);

        if (hit.hit) {
            auto interactable = GetInteractable(hit.objectID);
            if (interactable && !interactable->IsGrabbed()) {
                InteractionEvent event;
                event.type = InteractionType::Grab;
                event.controller = controller;
                event.position = hit.point;
                event.direction = ray.direction;

                interactable->OnGrab(event);
                m_grabbedObjects[controller] = interactable;
                TriggerInteraction(event);
            }
        }
    } else if (!gripPressed && gripWasPressed) {
        // 释放抓取
        if (m_grabbedObjects[controller]) {
            InteractionEvent event;
            event.type = InteractionType::Release;
            event.controller = controller;
            event.position = m_grabbedObjects[controller]->GetPosition();

            m_grabbedObjects[controller]->OnRelease(event);
            m_grabbedObjects[controller].reset();
            TriggerInteraction(event);
        }
    }

    // 更新被抓取物体的位置
    if (m_grabbedObjects[controller]) {
        m_grabbedObjects[controller]->SetPosition(state.pose.position);
        m_grabbedObjects[controller]->SetRotation(state.pose.orientation);
    }
}

void InputManager::ProcessPointing(int controller, const ControllerState& state) {
    Ray ray = GetPointerRay(controller);
    HitResult hit = Raycast(ray, m_config.pointerLength);

    auto& hoveredObject = m_hoveredObjects[controller];

    if (hit.hit) {
        auto interactable = GetInteractable(hit.objectID);

        if (interactable) {
            if (!hoveredObject || hoveredObject->GetID() != hit.objectID) {
                // 取消悬停旧物体
                if (hoveredObject) {
                    InteractionEvent unhoverEvent;
                    unhoverEvent.type = InteractionType::Release;  // 使用 Release 代替
                    unhoverEvent.controller = controller;
                    hoveredObject->OnUnhover(unhoverEvent);
                }

                // 悬停新物体
                InteractionEvent hoverEvent;
                hoverEvent.type = InteractionType::Point;
                hoverEvent.controller = controller;
                hoverEvent.position = hit.point;

                interactable->OnHover(hoverEvent);
                hoveredObject = interactable;
            }
        }
    } else {
        if (hoveredObject) {
            InteractionEvent unhoverEvent;
            unhoverEvent.type = InteractionType::Release;
            unhoverEvent.controller = controller;

            hoveredObject->OnUnhover(unhoverEvent);
            hoveredObject.reset();
        }
    }
}

void InputManager::TriggerEvent(const InputEvent& event) {
    auto it = m_inputCallbacks.find(event.type);
    if (it != m_inputCallbacks.end()) {
        for (const auto& callback : it->second) {
            callback(event);
        }
    }
}

void InputManager::TriggerInteraction(const InteractionEvent& event) {
    auto it = m_interactionCallbacks.find(event.type);
    if (it != m_interactionCallbacks.end()) {
        for (const auto& callback : it->second) {
            callback(event);
        }
    }
}

// PointerVisualizer 实现
PointerVisualizer::PointerVisualizer() = default;

PointerVisualizer::~PointerVisualizer() {
    Shutdown();
}

bool PointerVisualizer::Initialize() {
    // 创建线条缓冲区
    glGenVertexArrays(1, &m_lineVAO);
    glGenBuffers(1, &m_lineVBO);

    glBindVertexArray(m_lineVAO);
    glBindBuffer(GL_ARRAY_BUFFER, m_lineVBO);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vec3), (void*)0);

    glBindVertexArray(0);

    // 创建点缓冲区
    glGenVertexArrays(1, &m_dotVAO);
    glGenBuffers(1, &m_dotVBO);

    glBindVertexArray(m_dotVAO);
    glBindBuffer(GL_ARRAY_BUFFER, m_dotVBO);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vec3), (void*)0);

    glBindVertexArray(0);

    // 加载着色器
    m_shader = ShaderManager::GetInstance().CreateBuiltinShader("wireframe");

    return true;
}

void PointerVisualizer::Shutdown() {
    if (m_lineVAO) glDeleteVertexArrays(1, &m_lineVAO);
    if (m_lineVBO) glDeleteBuffers(1, &m_lineVBO);
    if (m_dotVAO) glDeleteVertexArrays(1, &m_dotVAO);
    if (m_dotVBO) glDeleteBuffers(1, &m_dotVBO);

    m_shader.reset();
}

void PointerVisualizer::Render(const Ray& ray, float length, const HitResult& hit, const Vec4& color) {
    if (!m_shader) return;

    m_shader->Use();
    m_shader->SetMat4("model", Mat4(1.0f));
    // 注意：需要设置 view 和 projection 矩阵

    Vec3 endPoint = hit.hit ? hit.point : ray.origin + ray.direction * length;

    // 绘制射线
    Vec3 lineVertices[] = {ray.origin, endPoint};

    glBindVertexArray(m_lineVAO);
    glBindBuffer(GL_ARRAY_BUFFER, m_lineVBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(lineVertices), lineVertices, GL_DYNAMIC_DRAW);

    m_shader->SetVec4("lineColor", color);
    glLineWidth(2.0f);
    glDrawArrays(GL_LINES, 0, 2);
    glLineWidth(1.0f);

    glBindVertexArray(0);

    // 绘制命中点
    if (hit.hit) {
        Vec3 dotVertices[] = {hit.point};

        glBindVertexArray(m_dotVAO);
        glBindBuffer(GL_ARRAY_BUFFER, m_dotVBO);
        glBufferData(GL_ARRAY_BUFFER, sizeof(dotVertices), dotVertices, GL_DYNAMIC_DRAW);

        m_shader->SetVec4("lineColor", Vec4(1.0f, 0.0f, 0.0f, 1.0f));
        glPointSize(8.0f);
        glDrawArrays(GL_POINTS, 0, 1);
        glPointSize(1.0f);

        glBindVertexArray(0);
    }
}

void PointerVisualizer::RenderController(int controller, const Ray& ray, const HitResult& hit) {
    Vec4 color = (controller == 0) ? Vec4(0.0f, 1.0f, 0.0f, 1.0f) : Vec4(0.0f, 0.0f, 1.0f, 1.0f);
    Render(ray, 10.0f, hit, color);
}

}  // namespace vr