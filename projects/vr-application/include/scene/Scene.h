#pragma once

#include "Common.h"
#include "rendering/Renderer.h"
#include <vector>
#include <memory>
#include <string>

namespace vr {

// 变换组件
class Transform {
public:
    Transform();
    ~Transform();

    // 位置
    void SetPosition(const Vec3& position);
    Vec3 GetPosition() const { return m_position; }
    void Translate(const Vec3& offset);

    // 旋转
    void SetRotation(const Quat& rotation);
    void SetRotationEuler(const Vec3& euler);
    Quat GetRotation() const { return m_rotation; }
    Vec3 GetEulerAngles() const;
    void Rotate(const Quat& rotation);
    void Rotate(const Vec3& axis, float angle);

    // 缩放
    void SetScale(const Vec3& scale);
    void SetScale(float scale);
    Vec3 GetScale() const { return m_scale; }

    // 变换矩阵
    Mat4 GetLocalMatrix() const;
    Mat4 GetWorldMatrix() const;

    // 方向向量
    Vec3 GetForward() const;
    Vec3 GetRight() const;
    Vec3 GetUp() const;

    // 父子关系
    void SetParent(Transform* parent);
    Transform* GetParent() const { return m_parent; }
    void AddChild(Transform* child);
    void RemoveChild(Transform* child);
    const std::vector<Transform*>& GetChildren() const { return m_children; }

    // 标记脏
    void SetDirty();
    bool IsDirty() const { return m_isDirty; }

private:
    void UpdateWorldMatrix() const;

    Vec3 m_position = Vec3(0.0f);
    Quat m_rotation = Quat(1.0f, 0.0f, 0.0f, 0.0f);
    Vec3 m_scale = Vec3(1.0f);

    mutable Mat4 m_localMatrix = Mat4(1.0f);
    mutable Mat4 m_worldMatrix = Mat4(1.0f);
    mutable bool m_isDirty = true;

    Transform* m_parent = nullptr;
    std::vector<Transform*> m_children;
};

// 场景对象类型
enum class ObjectType {
    Static,
    Dynamic,
    Interactive,
    Camera,
    Light
};

// 场景对象
class SceneObject {
public:
    SceneObject(const std::string& name = "Object");
    virtual ~SceneObject();

    // 基本属性
    const std::string& GetName() const { return m_name; }
    void SetName(const std::string& name) { m_name = name; }

    int GetID() const { return m_id; }
    ObjectType GetType() const { return m_type; }

    // 变换
    Transform& GetTransform() { return m_transform; }
    const Transform& GetTransform() const { return m_transform; }

    // 渲染
    void SetRenderObject(const RenderObject& renderObject);
    const RenderObject& GetRenderObject() const { return m_renderObject; }
    bool IsVisible() const { return m_isVisible; }
    void SetVisible(bool visible) { m_isVisible = visible; }

    // 包围盒
    void SetBoundingBox(const Vec3& min, const Vec3& max);
    void GetBoundingBox(Vec3& min, Vec3& max) const;
    bool IsInFrustum(const Mat4& viewProjection) const;

    // 更新
    virtual void Update(float deltaTime);

    // 渲染
    virtual void Render(Renderer& renderer);

    // 克隆
    virtual SharedPtr<SceneObject> Clone() const;

protected:
    int m_id;
    std::string m_name;
    ObjectType m_type = ObjectType::Static;
    Transform m_transform;
    RenderObject m_renderObject;
    bool m_isVisible = true;

    Vec3 m_boundingBoxMin = Vec3(-0.5f);
    Vec3 m_boundingBoxMax = Vec3(0.5f);

    static int s_nextID;
};

// 相机类型
enum class CameraType {
    Perspective,
    Orthographic,
    VR
};

// 相机
class Camera : public SceneObject {
public:
    Camera(const std::string& name = "Camera");
    virtual ~Camera();

    // 相机类型
    CameraType GetCameraType() const { return m_cameraType; }
    void SetCameraType(CameraType type) { m_cameraType = type; }

    // 视图矩阵
    Mat4 GetViewMatrix() const;

    // 投影矩阵
    Mat4 GetProjectionMatrix() const;
    void SetPerspective(float fov, float aspect, float near, float far);
    void SetOrthographic(float left, float right, float bottom, float top, float near, float far);

    // VR 视图
    void SetVRView(const VRView& view);
    VRView GetVRView() const { return m_vrView; }

    // 控制
    void LookAt(const Vec3& target);
    void ProcessKeyboard(int direction, float deltaTime);
    void ProcessMouseMovement(float xoffset, float yoffset);
    void ProcessMouseScroll(float yoffset);

    // 参数
    float GetFOV() const { return m_fov; }
    void SetFOV(float fov) { m_fov = fov; m_projectionDirty = true; }
    float GetAspect() const { return m_aspect; }
    void SetAspect(float aspect) { m_aspect = aspect; m_projectionDirty = true; }
    float GetNear() const { return m_near; }
    float GetFar() const { return m_far; }

    // 更新
    void Update(float deltaTime) override;

private:
    CameraType m_cameraType = CameraType::Perspective;

    float m_fov = 45.0f;
    float m_aspect = 16.0f / 9.0f;
    float m_near = 0.1f;
    float m_far = 1000.0f;

    // 正交投影参数
    float m_orthoLeft = -1.0f;
    float m_orthoRight = 1.0f;
    float m_orthoBottom = -1.0f;
    float m_orthoTop = 1.0f;

    // 鼠标控制
    float m_sensitivity = 0.1f;
    float m_yaw = -90.0f;
    float m_pitch = 0.0f;

    // VR 视图
    VRView m_vrView;

    // 缓存
    mutable Mat4 m_viewMatrix = Mat4(1.0f);
    mutable Mat4 m_projectionMatrix = Mat4(1.0f);
    mutable bool m_viewDirty = true;
    mutable bool m_projectionDirty = true;
};

// 光源类型
enum class LightType {
    Directional,
    Point,
    Spot
};

// 光源
class Light : public SceneObject {
public:
    Light(const std::string& name = "Light");
    virtual ~Light();

    // 光源类型
    LightType GetLightType() const { return m_lightType; }
    void SetLightType(LightType type) { m_lightType = type; }

    // 颜色
    void SetAmbient(const Vec3& ambient) { m_ambient = ambient; }
    void SetDiffuse(const Vec3& diffuse) { m_diffuse = diffuse; }
    void SetSpecular(const Vec3& specular) { m_specular = specular; }

    Vec3 GetAmbient() const { return m_ambient; }
    Vec3 GetDiffuse() const { return m_diffuse; }
    Vec3 GetSpecular() const { return m_specular; }

    // 点光源参数
    void SetConstant(float constant) { m_constant = constant; }
    void SetLinear(float linear) { m_linear = linear; }
    void SetQuadratic(float quadratic) { m_quadratic = quadratic; }

    float GetConstant() const { return m_constant; }
    float GetLinear() const { return m_linear; }
    float GetQuadratic() const { return m_quadratic; }

    // 聚光灯参数
    void SetCutoff(float cutoff) { m_cutoff = cutoff; }
    void SetOuterCutoff(float outerCutoff) { m_outerCutoff = outerCutoff; }

    float GetCutoff() const { return m_cutoff; }
    float GetOuterCutoff() const { return m_outerCutoff; }

    // 转换为渲染光源
    DirectionalLight ToDirectionalLight() const;
    PointLight ToPointLight() const;

private:
    LightType m_lightType = LightType::Directional;

    Vec3 m_ambient = Vec3(0.2f);
    Vec3 m_diffuse = Vec3(0.8f);
    Vec3 m_specular = Vec3(1.0f);

    // 点光源衰减
    float m_constant = 1.0f;
    float m_linear = 0.09f;
    float m_quadratic = 0.032f;

    // 聚光灯角度
    float m_cutoff = 12.5f;
    float m_outerCutoff = 17.5f;
};

// 场景
class Scene {
public:
    Scene(const std::string& name = "Default");
    ~Scene();

    // 场景管理
    const std::string& GetName() const { return m_name; }
    void SetName(const std::string& name) { m_name = name; }

    // 对象管理
    void AddObject(SharedPtr<SceneObject> object);
    void RemoveObject(int id);
    void RemoveObject(const std::string& name);
    SharedPtr<SceneObject> GetObject(int id) const;
    SharedPtr<SceneObject> GetObject(const std::string& name) const;

    // 获取所有对象
    const std::vector<SharedPtr<SceneObject>>& GetObjects() const { return m_objects; }
    std::vector<SharedPtr<SceneObject>> GetObjectsByType(ObjectType type) const;

    // 相机
    void SetActiveCamera(SharedPtr<Camera> camera);
    SharedPtr<Camera> GetActiveCamera() const { return m_activeCamera; }

    // 光源
    void AddLight(SharedPtr<Light> light);
    void RemoveLight(int id);
    const std::vector<SharedPtr<Light>>& GetLights() const { return m_lights; }
    DirectionalLight GetMainDirectionalLight() const;
    std::vector<PointLight> GetPointLights() const;

    // 更新
    void Update(float deltaTime);

    // 渲染
    void Render(Renderer& renderer);

    // 清空
    void Clear();

    // 创建默认场景
    void CreateDefaultScene();

    // 加载场景
    bool LoadFromFile(const std::string& path);
    bool SaveToFile(const std::string& path) const;

    // 统计
    int GetObjectCount() const { return static_cast<int>(m_objects.size()); }
    int GetLightCount() const { return static_cast<int>(m_lights.size()); }

private:
    std::string m_name;
    std::vector<SharedPtr<SceneObject>> m_objects;
    std::vector<SharedPtr<Light>> m_lights;
    SharedPtr<Camera> m_activeCamera;

    std::unordered_map<int, size_t> m_objectIndexMap;
};

// 场景管理器
class SceneManager {
public:
    static SceneManager& GetInstance();

    // 场景管理
    SharedPtr<Scene> CreateScene(const std::string& name);
    void LoadScene(const std::string& name);
    void UnloadScene(const std::string& name);

    // 获取场景
    SharedPtr<Scene> GetScene(const std::string& name);
    SharedPtr<Scene> GetActiveScene();
    void SetActiveScene(const std::string& name);

    // 更新和渲染
    void Update(float deltaTime);
    void Render(Renderer& renderer);

    // 清理
    void Clear();

private:
    SceneManager() = default;

    std::unordered_map<std::string, SharedPtr<Scene>> m_scenes;
    std::string m_activeSceneName;
};

}  // namespace vr