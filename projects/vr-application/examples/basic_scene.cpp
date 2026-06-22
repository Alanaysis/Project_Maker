#include "core/Application.h"
#include <iostream>
#include <memory>

// 基本场景示例
class BasicSceneApp : public vr::Application {
public:
    BasicSceneApp() = default;
    ~BasicSceneApp() override = default;

protected:
    bool OnInitialize() override {
        std::cout << "Basic Scene Example initialized" << std::endl;
        std::cout << std::endl;
        std::cout << "Controls:" << std::endl;
        std::cout << "  WASD - Move camera" << std::endl;
        std::cout << "  Space - Move up" << std::endl;
        std::cout << "  Shift - Move down" << std::endl;
        std::cout << "  Mouse - Look around" << std::endl;
        std::cout << "  F1 - Toggle debug info" << std::endl;
        std::cout << "  F2 - Toggle wireframe" << std::endl;
        std::cout << "  F3 - Toggle bounding boxes" << std::endl;
        std::cout << "  F4 - Toggle grid" << std::endl;
        std::cout << "  ESC - Quit" << std::endl;
        std::cout << std::endl;

        return true;
    }

    void CreateScene() override {
        // 创建场景
        m_mainScene = vr::SceneManager::GetInstance().CreateScene("BasicScene");

        // 创建相机
        auto camera = std::make_shared<vr::Camera>("MainCamera");
        camera->SetPerspective(45.0f, 16.0f / 9.0f, 0.1f, 1000.0f);
        camera->GetTransform().SetPosition(vr::Vec3(0, 3, 8));
        camera->LookAt(vr::Vec3(0, 0, 0));
        m_mainScene->SetActiveCamera(camera);

        // 创建方向光
        auto dirLight = std::make_shared<vr::Light>("DirectionalLight");
        dirLight->SetLightType(vr::LightType::Directional);
        dirLight->GetTransform().SetRotationEuler(vr::Vec3(-45.0f, -45.0f, 0.0f));
        dirLight->SetDiffuse(vr::Vec3(0.8f));
        dirLight->SetAmbient(vr::Vec3(0.2f));
        m_mainScene->AddLight(dirLight);

        // 创建点光源
        auto pointLight1 = std::make_shared<vr::Light>("PointLight1");
        pointLight1->SetLightType(vr::LightType::Point);
        pointLight1->GetTransform().SetPosition(vr::Vec3(-3, 2, 0));
        pointLight1->SetDiffuse(vr::Vec3(1.0f, 0.0f, 0.0f));
        pointLight1->SetAmbient(vr::Vec3(0.1f, 0.0f, 0.0f));
        m_mainScene->AddLight(pointLight1);

        auto pointLight2 = std::make_shared<vr::Light>("PointLight2");
        pointLight2->SetLightType(vr::LightType::Point);
        pointLight2->GetTransform().SetPosition(vr::Vec3(3, 2, 0));
        pointLight2->SetDiffuse(vr::Vec3(0.0f, 0.0f, 1.0f));
        pointLight2->SetAmbient(vr::Vec3(0.0f, 0.0f, 0.1f));
        m_mainScene->AddLight(pointLight2);

        // 创建地面
        m_ground = std::make_shared<vr::SceneObject>("Ground");
        m_ground->SetRenderObject(vr::Renderer::CreatePlane(20.0f, 20.0f));
        m_mainScene->AddObject(m_ground);

        // 创建中心立方体
        m_centerCube = std::make_shared<vr::SceneObject>("CenterCube");
        m_centerCube->SetRenderObject(vr::Renderer::CreateCube(1.5f));
        m_centerCube->GetTransform().SetPosition(vr::Vec3(0, 0.75f, 0));
        m_mainScene->AddObject(m_centerCube);

        // 创建球体
        m_sphere = std::make_shared<vr::SceneObject>("Sphere");
        m_sphere->SetRenderObject(vr::Renderer::CreateSphere(0.8f, 32));
        m_sphere->GetTransform().SetPosition(vr::Vec3(-3, 0.8f, 0));
        m_mainScene->AddObject(m_sphere);

        // 创建圆柱体
        m_cylinder = std::make_shared<vr::SceneObject>("Cylinder");
        m_cylinder->SetRenderObject(vr::Renderer::CreateCylinder(0.5f, 2.0f, 32));
        m_cylinder->GetTransform().SetPosition(vr::Vec3(3, 1.0f, 0));
        m_mainScene->AddObject(m_cylinder);

        // 创建物体阵列
        for (int i = 0; i < 5; i++) {
            for (int j = 0; j < 5; j++) {
                auto obj = std::make_shared<vr::SceneObject>(
                    "Array_" + std::to_string(i) + "_" + std::to_string(j));

                float x = -4.0f + i * 2.0f;
                float z = -4.0f + j * 2.0f;
                float height = 0.5f + static_cast<float>(rand()) / RAND_MAX * 1.5f;

                obj->SetRenderObject(vr::Renderer::CreateCube(0.4f));
                obj->GetTransform().SetPosition(vr::Vec3(x, height / 2, z));
                obj->GetTransform().SetScale(vr::Vec3(1.0f, height, 1.0f));

                m_mainScene->AddObject(obj);
                m_arrayObjects.push_back(obj);
            }
        }

        std::cout << "Scene created with " << m_mainScene->GetObjectCount() << " objects" << std::endl;
    }

    void OnUpdate(float deltaTime) override {
        m_time += deltaTime;

        // 旋转中心立方体
        if (m_centerCube) {
            m_centerCube->GetTransform().Rotate(vr::Vec3(0, 1, 0), deltaTime * 30.0f * vr::DEG_TO_RAD);
        }

        // 上下浮动球体
        if (m_sphere) {
            float y = 0.8f + std::sin(m_time * 2.0f) * 0.3f;
            m_sphere->GetTransform().SetPosition(vr::Vec3(-3, y, 0));
        }

        // 旋转圆柱体
        if (m_cylinder) {
            m_cylinder->GetTransform().Rotate(vr::Vec3(0, 1, 0), deltaTime * -20.0f * vr::DEG_TO_RAD);
        }

        // 波浪效果
        for (size_t i = 0; i < m_arrayObjects.size(); i++) {
            auto& obj = m_arrayObjects[i];
            vr::Vec3 pos = obj->GetTransform().GetPosition();
            float wave = std::sin(m_time * 3.0f + i * 0.5f) * 0.5f;
            obj->GetTransform().SetPosition(vr::Vec3(pos.x, 0.5f + wave, pos.z));
        }
    }

    void OnRender() override {
        // 渲染光照位置指示器
        auto* renderer = GetRenderer();
        if (renderer) {
            // 渲染点光源位置
            renderer->RenderLine(vr::Vec3(-3, 2, 0), vr::Vec3(-3, 0, 0), vr::Colors::Red);
            renderer->RenderLine(vr::Vec3(3, 2, 0), vr::Vec3(3, 0, 0), vr::Colors::Blue);
        }
    }

private:
    std::shared_ptr<vr::SceneObject> m_ground;
    std::shared_ptr<vr::SceneObject> m_centerCube;
    std::shared_ptr<vr::SceneObject> m_sphere;
    std::shared_ptr<vr::SceneObject> m_cylinder;
    std::vector<std::shared_ptr<vr::SceneObject>> m_arrayObjects;

    float m_time = 0.0f;
};

int main() {
    try {
        BasicSceneApp app;

        vr::AppConfig config;
        config.window.title = "VR Application - Basic Scene Example";
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