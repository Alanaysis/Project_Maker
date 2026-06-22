#include "core/Application.h"
#include <iostream>
#include <memory>

// 交互演示示例
class InteractionDemoApp : public vr::Application {
public:
    InteractionDemoApp() = default;
    ~InteractionDemoApp() override = default;

protected:
    bool OnInitialize() override {
        std::cout << "Interaction Demo initialized" << std::endl;
        std::cout << std::endl;
        std::cout << "This demo demonstrates basic VR interactions:" << std::endl;
        std::cout << "  - Object selection with ray casting" << std::endl;
        std::cout << "  - Grab and release objects" << std::endl;
        std::cout << "  - Visual feedback for interactions" << std::endl;
        std::cout << std::endl;
        std::cout << "Controls:" << std::endl;
        std::cout << "  WASD - Move camera" << std::endl;
        std::cout << "  Mouse - Look around" << std::endl;
        std::cout << "  Left Click - Select/Grab object" << std::endl;
        std::cout << "  Right Click - Release object" << std::endl;
        std::cout << "  ESC - Quit" << std::endl;
        std::cout << std::endl;

        return true;
    }

    void CreateScene() override {
        // 创建场景
        m_mainScene = vr::SceneManager::GetInstance().CreateScene("InteractionDemo");

        // 创建相机
        auto camera = std::make_shared<vr::Camera>("MainCamera");
        camera->SetPerspective(45.0f, 16.0f / 9.0f, 0.1f, 1000.0f);
        camera->GetTransform().SetPosition(vr::Vec3(0, 2, 5));
        camera->LookAt(vr::Vec3(0, 0, 0));
        m_mainScene->SetActiveCamera(camera);

        // 创建方向光
        auto dirLight = std::make_shared<vr::Light>("DirectionalLight");
        dirLight->SetLightType(vr::LightType::Directional);
        dirLight->GetTransform().SetRotationEuler(vr::Vec3(-45.0f, -45.0f, 0.0f));
        dirLight->SetDiffuse(vr::Vec3(0.8f));
        dirLight->SetAmbient(vr::Vec3(0.2f));
        m_mainScene->AddLight(dirLight);

        // 创建地面
        auto ground = std::make_shared<vr::SceneObject>("Ground");
        ground->SetRenderObject(vr::Renderer::CreatePlane(20.0f, 20.0f));
        m_mainScene->AddObject(ground);

        // 创建可交互物体
        CreateInteractableObjects();

        // 注册输入回调
        auto* input = GetInputManager();
        if (input) {
            input->RegisterInteractionCallback(vr::InteractionType::Grab,
                [this](const vr::InteractionEvent& event) {
                    OnGrab(event);
                });

            input->RegisterInteractionCallback(vr::InteractionType::Release,
                [this](const vr::InteractionEvent& event) {
                    OnRelease(event);
                });
        }

        std::cout << "Scene created with " << m_interactiveObjects.size()
                  << " interactive objects" << std::endl;
    }

    void CreateInteractableObjects() {
        // 创建不同形状的可交互物体
        std::vector<std::pair<std::string, vr::Vec3>> objectData = {
            {"Cube", vr::Vec3(-2, 0.5, 0)},
            {"Sphere", vr::Vec3(0, 0.5, 0)},
            {"Cylinder", vr::Vec3(2, 0.5, 0)},
            {"SmallCube1", vr::Vec3(-1, 0.25, -2)},
            {"SmallCube2", vr::Vec3(1, 0.25, -2)},
        };

        for (const auto& [name, position] : objectData) {
            auto obj = std::make_shared<vr::SceneObject>(name);
            obj->GetTransform().SetPosition(position);

            if (name == "Cube" || name.find("SmallCube") != std::string::npos) {
                float size = (name.find("Small") != std::string::npos) ? 0.5f : 1.0f;
                obj->SetRenderObject(vr::Renderer::CreateCube(size));
            } else if (name == "Sphere") {
                obj->SetRenderObject(vr::Renderer::CreateSphere(0.5f));
            } else if (name == "Cylinder") {
                obj->SetRenderObject(vr::Renderer::CreateCylinder(0.3f, 1.0f));
            }

            m_mainScene->AddObject(obj);
            m_interactiveObjects.push_back(obj);

            // 创建可交互碰撞体
            auto interactable = std::make_shared<vr::SphereInteractable>(0.5f);
            interactable->SetPosition(position);
            interactable->SetID(obj->GetID());

            // 设置回调
            interactable->SetOnGrab([this, name](const vr::InteractionEvent& e) {
                std::cout << "Grabbed: " << name << std::endl;
            });

            interactable->SetOnRelease([this, name](const vr::InteractionEvent& e) {
                std::cout << "Released: " << name << std::endl;
            });

            GetInputManager()->RegisterInteractable(interactable);
            m_interactables.push_back(interactable);
        }
    }

    void OnUpdate(float deltaTime) override {
        m_time += deltaTime;

        // 更新可交互物体的位置
        for (auto& interactable : m_interactables) {
            if (interactable->IsGrabbed()) {
                // 找到对应的场景对象并更新位置
                for (auto& obj : m_interactiveObjects) {
                    if (obj->GetID() == interactable->GetID()) {
                        obj->GetTransform().SetPosition(interactable->GetPosition());
                        obj->GetTransform().SetRotation(interactable->GetRotation());
                        break;
                    }
                }
            }
        }

        // 动画效果
        for (size_t i = 0; i < m_interactiveObjects.size(); i++) {
            auto& obj = m_interactiveObjects[i];
            if (!m_interactables[i]->IsGrabbed()) {
                // 未被抓取的物体添加轻微浮动
                vr::Vec3 pos = obj->GetTransform().GetPosition();
                float offset = std::sin(m_time * 2.0f + i * 0.5f) * 0.1f;
                obj->GetTransform().SetPosition(vr::Vec3(pos.x, pos.y + offset * deltaTime, pos.z));
            }
        }
    }

    void OnRender() override {
        auto* renderer = GetRenderer();
        auto* input = GetInputManager();

        if (!renderer || !input) return;

        // 渲染射线（调试用）
        for (int i = 0; i < 2; i++) {
            vr::Ray ray = input->GetPointerRay(i);
            vr::HitResult hit = input->RaycastController(i);

            // 渲染射线
            vr::Vec3 endPoint = hit.hit ? hit.point : ray.origin + ray.direction * 10.0f;
            vr::Vec4 color = hit.hit ? vr::Colors::Green : vr::Colors::Cyan;
            renderer->RenderLine(ray.origin, endPoint, color);

            // 渲染命中点
            if (hit.hit) {
                // 渲染一个小立方体表示命中点
                vr::RenderObject hitMarker = vr::Renderer::CreateCube(0.05f);
                hitMarker.modelMatrix = glm::translate(vr::Mat4(1.0f), hit.point);
                renderer->RenderWireframe(hitMarker, vr::Colors::Red);
            }
        }

        // 高亮显示悬停的物体
        for (auto& interactable : m_interactables) {
            if (interactable->IsHovered()) {
                // 找到对应的场景对象
                for (auto& obj : m_interactiveObjects) {
                    if (obj->GetID() == interactable->GetID()) {
                        // 渲染包围盒
                        vr::Vec3 min, max;
                        obj->GetBoundingBox(min, max);
                        renderer->RenderBoundingBox(min, max, vr::Colors::Yellow);
                        break;
                    }
                }
            }
        }
    }

    void OnGrab(const vr::InteractionEvent& event) {
        std::cout << "Grab event at position: ("
                  << event.position.x << ", "
                  << event.position.y << ", "
                  << event.position.z << ")" << std::endl;

        m_isGrabbing = true;
        m_grabbedController = event.controller;
    }

    void OnRelease(const vr::InteractionEvent& event) {
        std::cout << "Release event" << std::endl;

        m_isGrabbing = false;
        m_grabbedController = -1;
    }

private:
    std::vector<std::shared_ptr<vr::SceneObject>> m_interactiveObjects;
    std::vector<std::shared_ptr<vr::SphereInteractable>> m_interactables;

    bool m_isGrabbing = false;
    int m_grabbedController = -1;
    float m_time = 0.0f;
};

int main() {
    try {
        InteractionDemoApp app;

        vr::AppConfig config;
        config.window.title = "VR Application - Interaction Demo";
        config.window.width = 1280;
        config.window.height = 720;
        config.vr.enableDesktopMode = true;
        config.enableDebugTools = true;

        if (!app.Initialize(config)) {
            std::cerr << "Failed to initialize application" << std::endl;
            return -1;
        }

        app.Run();
        app.Shutdown();

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return -1;
    }
}