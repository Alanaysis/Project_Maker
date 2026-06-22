#include "scene/Scene.h"
#include <algorithm>
#include <fstream>
#include <sstream>

namespace vr {

// Transform 实现
Transform::Transform() = default;
Transform::~Transform() = default;

void Transform::SetPosition(const Vec3& position) {
    m_position = position;
    SetDirty();
}

void Transform::Translate(const Vec3& offset) {
    m_position += offset;
    SetDirty();
}

void Transform::SetRotation(const Quat& rotation) {
    m_rotation = rotation;
    SetDirty();
}

void Transform::SetRotationEuler(const Vec3& euler) {
    m_rotation = Quat(glm::radians(euler));
    SetDirty();
}

Vec3 Transform::GetEulerAngles() const {
    return glm::degrees(glm::eulerAngles(m_rotation));
}

void Transform::Rotate(const Quat& rotation) {
    m_rotation = rotation * m_rotation;
    SetDirty();
}

void Transform::Rotate(const Vec3& axis, float angle) {
    m_rotation = glm::rotate(m_rotation, angle, axis);
    SetDirty();
}

void Transform::SetScale(const Vec3& scale) {
    m_scale = scale;
    SetDirty();
}

void Transform::SetScale(float scale) {
    m_scale = Vec3(scale);
    SetDirty();
}

Mat4 Transform::GetLocalMatrix() const {
    if (m_isDirty) {
        UpdateWorldMatrix();
    }
    return m_localMatrix;
}

Mat4 Transform::GetWorldMatrix() const {
    if (m_isDirty) {
        UpdateWorldMatrix();
    }
    return m_worldMatrix;
}

Vec3 Transform::GetForward() const {
    return glm::rotate(m_rotation, Vec3(0, 0, -1));
}

Vec3 Transform::GetRight() const {
    return glm::rotate(m_rotation, Vec3(1, 0, 0));
}

Vec3 Transform::GetUp() const {
    return glm::rotate(m_rotation, Vec3(0, 1, 0));
}

void Transform::SetParent(Transform* parent) {
    if (m_parent) {
        m_parent->RemoveChild(this);
    }

    m_parent = parent;

    if (m_parent) {
        m_parent->AddChild(this);
    }

    SetDirty();
}

void Transform::AddChild(Transform* child) {
    if (child && std::find(m_children.begin(), m_children.end(), child) == m_children.end()) {
        m_children.push_back(child);
        child->m_parent = this;
        child->SetDirty();
    }
}

void Transform::RemoveChild(Transform* child) {
    auto it = std::find(m_children.begin(), m_children.end(), child);
    if (it != m_children.end()) {
        m_children.erase(it);
        child->m_parent = nullptr;
        child->SetDirty();
    }
}

void Transform::SetDirty() {
    m_isDirty = true;
    for (auto* child : m_children) {
        child->SetDirty();
    }
}

void Transform::UpdateWorldMatrix() const {
    m_localMatrix = glm::translate(Mat4(1.0f), m_position);
    m_localMatrix *= glm::toMat4(m_rotation);
    m_localMatrix = glm::scale(m_localMatrix, m_scale);

    if (m_parent) {
        m_worldMatrix = m_parent->GetWorldMatrix() * m_localMatrix;
    } else {
        m_worldMatrix = m_localMatrix;
    }

    m_isDirty = false;
}

// SceneObject 实现
int SceneObject::s_nextID = 0;

SceneObject::SceneObject(const std::string& name)
    : m_id(s_nextID++), m_name(name) {}

SceneObject::~SceneObject() = default;

void SceneObject::SetRenderObject(const RenderObject& renderObject) {
    m_renderObject = renderObject;
}

void SceneObject::SetBoundingBox(const Vec3& min, const Vec3& max) {
    m_boundingBoxMin = min;
    m_boundingBoxMax = max;
}

void SceneObject::GetBoundingBox(Vec3& min, Vec3& max) const {
    Mat4 worldMatrix = m_transform.GetWorldMatrix();
    min = Vec3(worldMatrix * Vec4(m_boundingBoxMin, 1.0f));
    max = Vec3(worldMatrix * Vec4(m_boundingBoxMax, 1.0f));
}

bool SceneObject::IsInFrustum(const Mat4& viewProjection) const {
    // 简化的视锥体检测
    Vec3 worldPos = m_transform.GetPosition();
    Vec4 clipPos = viewProjection * Vec4(worldPos, 1.0f);

    // 检查是否在标准化设备坐标范围内
    if (clipPos.w <= 0) return false;

    Vec3 ndcPos = Vec3(clipPos) / clipPos.w;
    return ndcPos.x >= -1 && ndcPos.x <= 1 &&
           ndcPos.y >= -1 && ndcPos.y <= 1 &&
           ndcPos.z >= -1 && ndcPos.z <= 1;
}

void SceneObject::Update(float deltaTime) {
    // 默认实现：无操作
}

void SceneObject::Render(Renderer& renderer) {
    if (!m_isVisible) return;

    // 设置模型矩阵
    m_renderObject.modelMatrix = m_transform.GetWorldMatrix();

    // 渲染
    renderer.RenderObject(m_renderObject);

    // 渲染包围盒（调试用）
    // renderer.RenderBoundingBox(m_boundingBoxMin, m_boundingBoxMax);
}

SharedPtr<SceneObject> SceneObject::Clone() const {
    auto clone = std::make_shared<SceneObject>(m_name + "_clone");
    clone->m_transform = m_transform;
    clone->m_renderObject = m_renderObject;
    clone->m_isVisible = m_isVisible;
    clone->m_boundingBoxMin = m_boundingBoxMin;
    clone->m_boundingBoxMax = m_boundingBoxMax;
    return clone;
}

// Camera 实现
Camera::Camera(const std::string& name) : SceneObject(name) {
    m_type = ObjectType::Camera;
}

Camera::~Camera() = default;

Mat4 Camera::GetViewMatrix() const {
    if (m_viewDirty) {
        Vec3 position = m_transform.GetPosition();
        Vec3 forward = m_transform.GetForward();
        Vec3 up = m_transform.GetUp();

        m_viewMatrix = glm::lookAt(position, position + forward, up);
        m_viewDirty = false;
    }
    return m_viewMatrix;
}

Mat4 Camera::GetProjectionMatrix() const {
    if (m_projectionDirty) {
        switch (m_cameraType) {
            case CameraType::Perspective:
                m_projectionMatrix = glm::perspective(glm::radians(m_fov), m_aspect, m_near, m_far);
                break;
            case CameraType::Orthographic:
                m_projectionMatrix = glm::ortho(m_orthoLeft, m_orthoRight, m_orthoBottom, m_orthoTop, m_near, m_far);
                break;
            case CameraType::VR:
                // VR 投影矩阵从 OpenXR 获取
                break;
        }
        m_projectionDirty = false;
    }
    return m_projectionMatrix;
}

void Camera::SetPerspective(float fov, float aspect, float near, float far) {
    m_fov = fov;
    m_aspect = aspect;
    m_near = near;
    m_far = far;
    m_cameraType = CameraType::Perspective;
    m_projectionDirty = true;
}

void Camera::SetOrthographic(float left, float right, float bottom, float top, float near, float far) {
    m_orthoLeft = left;
    m_orthoRight = right;
    m_orthoBottom = bottom;
    m_orthoTop = top;
    m_near = near;
    m_far = far;
    m_cameraType = CameraType::Orthographic;
    m_projectionDirty = true;
}

void Camera::SetVRView(const VRView& view) {
    m_vrView = view;
    m_cameraType = CameraType::VR;
    m_viewMatrix = view.viewMatrix;
    m_projectionMatrix = view.projectionMatrix;
    m_viewDirty = false;
    m_projectionDirty = false;
}

void Camera::LookAt(const Vec3& target) {
    Vec3 position = m_transform.GetPosition();
    Vec3 direction = glm::normalize(target - position);

    // 计算旋转
    float yaw = glm::degrees(atan2(direction.z, direction.x));
    float pitch = glm::degrees(asin(direction.y));

    m_transform.SetRotationEuler(Vec3(pitch, yaw, 0));
    m_viewDirty = true;
}

void Camera::ProcessKeyboard(int direction, float deltaTime) {
    float velocity = 5.0f * deltaTime;

    Vec3 position = m_transform.GetPosition();
    Vec3 forward = m_transform.GetForward();
    Vec3 right = m_transform.GetRight();

    switch (direction) {
        case 0: position += forward * velocity; break;   // 前进
        case 1: position -= forward * velocity; break;   // 后退
        case 2: position -= right * velocity; break;     // 左移
        case 3: position += right * velocity; break;     // 右移
        case 4: position.y += velocity; break;           // 上升
        case 5: position.y -= velocity; break;           // 下降
    }

    m_transform.SetPosition(position);
    m_viewDirty = true;
}

void Camera::ProcessMouseMovement(float xoffset, float yoffset) {
    xoffset *= m_sensitivity;
    yoffset *= m_sensitivity;

    m_yaw += xoffset;
    m_pitch += yoffset;

    m_pitch = glm::clamp(m_pitch, -89.0f, 89.0f);

    Vec3 front;
    front.x = cos(glm::radians(m_yaw)) * cos(glm::radians(m_pitch));
    front.y = sin(glm::radians(m_pitch));
    front.z = sin(glm::radians(m_yaw)) * cos(glm::radians(m_pitch));

    m_transform.SetRotation(glm::quatLookAt(glm::normalize(front), Vec3(0, 1, 0)));
    m_viewDirty = true;
}

void Camera::ProcessMouseScroll(float yoffset) {
    m_fov -= yoffset;
    m_fov = glm::clamp(m_fov, 1.0f, 120.0f);
    m_projectionDirty = true;
}

void Camera::Update(float deltaTime) {
    SceneObject::Update(deltaTime);
    m_viewDirty = true;
}

// Light 实现
Light::Light(const std::string& name) : SceneObject(name) {
    m_type = ObjectType::Light;
}

Light::~Light() = default;

DirectionalLight Light::ToDirectionalLight() const {
    DirectionalLight light;
    light.direction = m_transform.GetForward();
    light.ambient = m_ambient;
    light.diffuse = m_diffuse;
    light.specular = m_specular;
    return light;
}

PointLight Light::ToPointLight() const {
    PointLight light;
    light.position = m_transform.GetPosition();
    light.ambient = m_ambient;
    light.diffuse = m_diffuse;
    light.specular = m_specular;
    light.constant = m_constant;
    light.linear = m_linear;
    light.quadratic = m_quadratic;
    return light;
}

// Scene 实现
Scene::Scene(const std::string& name) : m_name(name) {}

Scene::~Scene() {
    Clear();
}

void Scene::AddObject(SharedPtr<SceneObject> object) {
    if (!object) return;

    m_objectIndexMap[object->GetID()] = m_objects.size();
    m_objects.push_back(object);
}

void Scene::RemoveObject(int id) {
    auto it = m_objectIndexMap.find(id);
    if (it != m_objectIndexMap.end()) {
        size_t index = it->second;
        m_objects.erase(m_objects.begin() + index);
        m_objectIndexMap.erase(it);

        // 更新索引映射
        for (auto& [key, value] : m_objectIndexMap) {
            if (value > index) {
                value--;
            }
        }
    }
}

void Scene::RemoveObject(const std::string& name) {
    auto it = std::find_if(m_objects.begin(), m_objects.end(),
        [&name](const SharedPtr<SceneObject>& obj) {
            return obj->GetName() == name;
        });

    if (it != m_objects.end()) {
        int id = (*it)->GetID();
        m_objectIndexMap.erase(id);
        m_objects.erase(it);
    }
}

SharedPtr<SceneObject> Scene::GetObject(int id) const {
    auto it = m_objectIndexMap.find(id);
    if (it != m_objectIndexMap.end()) {
        return m_objects[it->second];
    }
    return nullptr;
}

SharedPtr<SceneObject> Scene::GetObject(const std::string& name) const {
    auto it = std::find_if(m_objects.begin(), m_objects.end(),
        [&name](const SharedPtr<SceneObject>& obj) {
            return obj->GetName() == name;
        });

    if (it != m_objects.end()) {
        return *it;
    }
    return nullptr;
}

std::vector<SharedPtr<SceneObject>> Scene::GetObjectsByType(ObjectType type) const {
    std::vector<SharedPtr<SceneObject>> result;
    for (const auto& obj : m_objects) {
        if (obj->GetType() == type) {
            result.push_back(obj);
        }
    }
    return result;
}

void Scene::SetActiveCamera(SharedPtr<Camera> camera) {
    m_activeCamera = camera;
}

void Scene::AddLight(SharedPtr<Light> light) {
    if (light) {
        m_lights.push_back(light);
        AddObject(light);
    }
}

void Scene::RemoveLight(int id) {
    auto it = std::find_if(m_lights.begin(), m_lights.end(),
        [id](const SharedPtr<Light>& light) {
            return light->GetID() == id;
        });

    if (it != m_lights.end()) {
        m_lights.erase(it);
    }
}

DirectionalLight Scene::GetMainDirectionalLight() const {
    for (const auto& light : m_lights) {
        if (light->GetLightType() == LightType::Directional) {
            return light->ToDirectionalLight();
        }
    }
    return DirectionalLight();
}

std::vector<PointLight> Scene::GetPointLights() const {
    std::vector<PointLight> lights;
    for (const auto& light : m_lights) {
        if (light->GetLightType() == LightType::Point) {
            lights.push_back(light->ToPointLight());
        }
    }
    return lights;
}

void Scene::Update(float deltaTime) {
    for (auto& obj : m_objects) {
        obj->Update(deltaTime);
    }

    if (m_activeCamera) {
        m_activeCamera->Update(deltaTime);
    }
}

void Scene::Render(Renderer& renderer) {
    for (auto& obj : m_objects) {
        if (obj->GetType() != ObjectType::Camera && obj->GetType() != ObjectType::Light) {
            obj->Render(renderer);
        }
    }
}

void Scene::Clear() {
    m_objects.clear();
    m_lights.clear();
    m_objectIndexMap.clear();
    m_activeCamera.reset();
}

void Scene::CreateDefaultScene() {
    // 创建相机
    auto camera = std::make_shared<Camera>("MainCamera");
    camera->SetPerspective(45.0f, 16.0f / 9.0f, 0.1f, 1000.0f);
    camera->GetTransform().SetPosition(Vec3(0, 2, 5));
    camera->LookAt(Vec3(0, 0, 0));
    SetActiveCamera(camera);

    // 创建方向光
    auto dirLight = std::make_shared<Light>("DirectionalLight");
    dirLight->SetLightType(LightType::Directional);
    dirLight->GetTransform().SetRotationEuler(Vec3(-45.0f, -45.0f, 0.0f));
    dirLight->SetDiffuse(Vec3(0.8f));
    dirLight->SetAmbient(Vec3(0.2f));
    AddLight(dirLight);

    // 创建地面
    auto ground = std::make_shared<SceneObject>("Ground");
    ground->SetRenderObject(Renderer::CreatePlane(20.0f, 20.0f));
    AddObject(ground);

    // 创建一些物体
    auto cube = std::make_shared<SceneObject>("Cube");
    cube->SetRenderObject(Renderer::CreateCube(1.0f));
    cube->GetTransform().SetPosition(Vec3(-2.0f, 0.5f, 0.0f));
    AddObject(cube);

    auto sphere = std::make_shared<SceneObject>("Sphere");
    sphere->SetRenderObject(Renderer::CreateSphere(0.5f));
    sphere->GetTransform().SetPosition(Vec3(2.0f, 0.5f, 0.0f));
    AddObject(sphere);

    auto cylinder = std::make_shared<SceneObject>("Cylinder");
    cylinder->SetRenderObject(Renderer::CreateCylinder(0.3f, 1.0f));
    cylinder->GetTransform().SetPosition(Vec3(0.0f, 0.5f, -2.0f));
    AddObject(cylinder);
}

bool Scene::LoadFromFile(const std::string& path) {
    // 简化实现：加载场景文件
    std::ifstream file(path);
    if (!file.is_open()) {
        return false;
    }

    // 解析场景文件
    // 这里只是示例，实际应该实现完整的解析器

    return true;
}

bool Scene::SaveToFile(const std::string& path) const {
    // 简化实现：保存场景文件
    std::ofstream file(path);
    if (!file.is_open()) {
        return false;
    }

    // 写入场景数据
    // 这里只是示例，实际应该实现完整的序列化器

    return true;
}

// SceneManager 实现
SceneManager& SceneManager::GetInstance() {
    static SceneManager instance;
    return instance;
}

SharedPtr<Scene> SceneManager::CreateScene(const std::string& name) {
    auto scene = std::make_shared<Scene>(name);
    m_scenes[name] = scene;

    if (m_activeSceneName.empty()) {
        m_activeSceneName = name;
    }

    return scene;
}

void SceneManager::LoadScene(const std::string& name) {
    auto it = m_scenes.find(name);
    if (it != m_scenes.end()) {
        m_activeSceneName = name;
    }
}

void SceneManager::UnloadScene(const std::string& name) {
    auto it = m_scenes.find(name);
    if (it != m_scenes.end()) {
        if (m_activeSceneName == name) {
            m_activeSceneName.clear();
        }
        m_scenes.erase(it);
    }
}

SharedPtr<Scene> SceneManager::GetScene(const std::string& name) {
    auto it = m_scenes.find(name);
    if (it != m_scenes.end()) {
        return it->second;
    }
    return nullptr;
}

SharedPtr<Scene> SceneManager::GetActiveScene() {
    return GetScene(m_activeSceneName);
}

void SceneManager::SetActiveScene(const std::string& name) {
    if (m_scenes.find(name) != m_scenes.end()) {
        m_activeSceneName = name;
    }
}

void SceneManager::Update(float deltaTime) {
    auto scene = GetActiveScene();
    if (scene) {
        scene->Update(deltaTime);
    }
}

void SceneManager::Render(Renderer& renderer) {
    auto scene = GetActiveScene();
    if (scene) {
        scene->Render(renderer);
    }
}

void SceneManager::Clear() {
    m_scenes.clear();
    m_activeSceneName.clear();
}

}  // namespace vr