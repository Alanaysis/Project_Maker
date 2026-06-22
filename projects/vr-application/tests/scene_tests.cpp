#include <iostream>
#include <cassert>
#include <cmath>
#include "scene/Scene.h"
#include "rendering/Renderer.h"

// 测试宏
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            std::cerr << "FAILED: " << message << " (" << __FILE__ << ":" << __LINE__ << ")" << std::endl; \
            return false; \
        } \
    } while(0)

#define TEST_ASSERT_APPROX(a, b, epsilon) \
    TEST_ASSERT(std::abs((a) - (b)) < (epsilon), \
                "Expected " << (a) << " ≈ " << (b) << " (epsilon=" << (epsilon) << ")")

#define RUN_TEST(test_func) \
    do { \
        std::cout << "Running " << #test_func << "... "; \
        if (test_func()) { \
            std::cout << "PASSED" << std::endl; \
            passed++; \
        } else { \
            std::cout << "FAILED" << std::endl; \
            failed++; \
        } \
        total++; \
    } while(0)

using namespace vr;

// Transform 测试
bool TestTransform() {
    Transform transform;

    // 测试初始状态
    TEST_ASSERT(transform.GetPosition() == Vec3(0.0f), "Initial position should be zero");
    TEST_ASSERT(transform.GetScale() == Vec3(1.0f), "Initial scale should be one");

    // 测试设置位置
    transform.SetPosition(Vec3(1.0f, 2.0f, 3.0f));
    TEST_ASSERT_APPROX(transform.GetPosition().x, 1.0f, 0.001f);
    TEST_ASSERT_APPROX(transform.GetPosition().y, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(transform.GetPosition().z, 3.0f, 0.001f);

    // 测试平移
    transform.Translate(Vec3(1.0f, 0.0f, 0.0f));
    TEST_ASSERT_APPROX(transform.GetPosition().x, 2.0f, 0.001f);

    // 测试缩放
    transform.SetScale(Vec3(2.0f, 3.0f, 4.0f));
    TEST_ASSERT_APPROX(transform.GetScale().x, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(transform.GetScale().y, 3.0f, 0.001f);
    TEST_ASSERT_APPROX(transform.GetScale().z, 4.0f, 0.001f);

    // 测试旋转
    transform.SetRotationEuler(Vec3(0.0f, 90.0f, 0.0f));
    Vec3 forward = transform.GetForward();
    TEST_ASSERT_APPROX(forward.x, 0.0f, 0.01f);
    TEST_ASSERT_APPROX(forward.z, -1.0f, 0.01f);

    // 测试变换矩阵
    Mat4 matrix = transform.GetWorldMatrix();
    Vec4 transformed = matrix * Vec4(0.0f, 0.0f, 0.0f, 1.0f);
    TEST_ASSERT_APPROX(transformed.x, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(transformed.y, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(transformed.z, 3.0f, 0.001f);

    return true;
}

// SceneObject 测试
bool TestSceneObject() {
    auto object = std::make_shared<SceneObject>("TestObject");

    // 测试初始状态
    TEST_ASSERT(object->GetName() == "TestObject", "Name should be TestObject");
    TEST_ASSERT(object->IsVisible() == true, "Should be visible by default");

    // 测试变换
    object->GetTransform().SetPosition(Vec3(1.0f, 2.0f, 3.0f));
    TEST_ASSERT_APPROX(object->GetTransform().GetPosition().x, 1.0f, 0.001f);

    // 测试包围盒
    object->SetBoundingBox(Vec3(-1.0f), Vec3(1.0f));
    Vec3 min, max;
    object->GetBoundingBox(min, max);
    TEST_ASSERT_APPROX(min.x, -1.0f, 0.001f);
    TEST_ASSERT_APPROX(max.x, 1.0f, 0.001f);

    // 测试可见性
    object->SetVisible(false);
    TEST_ASSERT(object->IsVisible() == false, "Should not be visible");

    return true;
}

// Camera 测试
bool TestCamera() {
    auto camera = std::make_shared<Camera>("TestCamera");

    // 测试透视投影
    camera->SetPerspective(45.0f, 16.0f / 9.0f, 0.1f, 100.0f);
    TEST_ASSERT_APPROX(camera->GetFOV(), 45.0f, 0.001f);
    TEST_ASSERT_APPROX(camera->GetAspect(), 16.0f / 9.0f, 0.001f);

    // 测试视图矩阵
    camera->GetTransform().SetPosition(Vec3(0.0f, 0.0f, 5.0f));
    camera->LookAt(Vec3(0.0f, 0.0f, 0.0f));

    Mat4 view = camera->GetViewMatrix();
    Vec4 viewOrigin = view * Vec4(0.0f, 0.0f, 0.0f, 1.0f);
    TEST_ASSERT_APPROX(viewOrigin.z, -5.0f, 0.1f);

    // 测试投影矩阵
    Mat4 projection = camera->GetProjectionMatrix();
    TEST_ASSERT(projection[0][0] != 0.0f, "Projection matrix should not be zero");

    return true;
}

// Light 测试
bool TestLight() {
    auto light = std::make_shared<Light>("TestLight");

    // 测试方向光
    light->SetLightType(LightType::Directional);
    light->GetTransform().SetRotationEuler(Vec3(-45.0f, 0.0f, 0.0f));
    light->SetDiffuse(Vec3(0.8f));
    light->SetAmbient(Vec3(0.2f));

    DirectionalLight dirLight = light->ToDirectionalLight();
    TEST_ASSERT_APPROX(dirLight.diffuse.x, 0.8f, 0.001f);
    TEST_ASSERT_APPROX(dirLight.ambient.x, 0.2f, 0.001f);

    // 测试点光源
    auto pointLight = std::make_shared<Light>("PointLight");
    pointLight->SetLightType(LightType::Point);
    pointLight->GetTransform().SetPosition(Vec3(1.0f, 2.0f, 3.0f));
    pointLight->SetDiffuse(Vec3(1.0f, 0.0f, 0.0f));

    PointLight pl = pointLight->ToPointLight();
    TEST_ASSERT_APPROX(pl.position.x, 1.0f, 0.001f);
    TEST_ASSERT_APPROX(pl.position.y, 2.0f, 0.001f);
    TEST_ASSERT_APPROX(pl.diffuse.x, 1.0f, 0.001f);

    return true;
}

// Scene 测试
bool TestScene() {
    auto scene = std::make_shared<Scene>("TestScene");

    // 测试创建场景
    TEST_ASSERT(scene->GetName() == "TestScene", "Scene name should be TestScene");

    // 添加对象
    auto object1 = std::make_shared<SceneObject>("Object1");
    auto object2 = std::make_shared<SceneObject>("Object2");
    scene->AddObject(object1);
    scene->AddObject(object2);

    TEST_ASSERT(scene->GetObjectCount() == 2, "Should have 2 objects");

    // 获取对象
    auto retrieved = scene->GetObject("Object1");
    TEST_ASSERT(retrieved != nullptr, "Should find Object1");
    TEST_ASSERT(retrieved->GetName() == "Object1", "Retrieved object name should match");

    // 删除对象
    scene->RemoveObject("Object1");
    TEST_ASSERT(scene->GetObjectCount() == 1, "Should have 1 object after deletion");

    // 添加光源
    auto light = std::make_shared<Light>("TestLight");
    light->SetLightType(LightType::Directional);
    scene->AddLight(light);
    TEST_ASSERT(scene->GetLightCount() == 1, "Should have 1 light");

    // 设置相机
    auto camera = std::make_shared<Camera>("MainCamera");
    scene->SetActiveCamera(camera);
    TEST_ASSERT(scene->GetActiveCamera() != nullptr, "Should have active camera");

    return true;
}

// SceneManager 测试
bool TestSceneManager() {
    auto& manager = SceneManager::GetInstance();

    // 创建场景
    auto scene1 = manager.CreateScene("Scene1");
    auto scene2 = manager.CreateScene("Scene2");

    TEST_ASSERT(scene1 != nullptr, "Scene1 should be created");
    TEST_ASSERT(scene2 != nullptr, "Scene2 should be created");

    // 设置活动场景
    manager.SetActiveScene("Scene1");
    TEST_ASSERT(manager.GetActiveScene() == scene1, "Active scene should be Scene1");

    // 切换场景
    manager.SetActiveScene("Scene2");
    TEST_ASSERT(manager.GetActiveScene() == scene2, "Active scene should be Scene2");

    // 获取场景
    auto retrieved = manager.GetScene("Scene1");
    TEST_ASSERT(retrieved == scene1, "Should find Scene1");

    // 删除场景
    manager.UnloadScene("Scene1");
    TEST_ASSERT(manager.GetScene("Scene1") == nullptr, "Scene1 should be deleted");

    // 清理
    manager.Clear();

    return true;
}

// Transform 父子关系测试
bool TestTransformHierarchy() {
    Transform parent;
    Transform child;

    // 设置父子关系
    child.SetParent(&parent);

    // 设置父变换
    parent.SetPosition(Vec3(1.0f, 0.0f, 0.0f));
    parent.SetRotationEuler(Vec3(0.0f, 45.0f, 0.0f));

    // 设置子变换（相对于父）
    child.SetPosition(Vec3(1.0f, 0.0f, 0.0f));

    // 子的世界位置应该是父变换后的结果
    Vec3 worldPos = child.GetPosition();
    Mat4 worldMatrix = child.GetWorldMatrix();
    Vec4 transformed = worldMatrix * Vec4(0.0f, 0.0f, 0.0f, 1.0f);

    // 预期：父位置 + 旋转后的子位置
    float expectedX = 1.0f + std::cos(glm::radians(45.0f));
    float expectedZ = -std::sin(glm::radians(45.0f));

    TEST_ASSERT_APPROX(transformed.x, expectedX, 0.01f);
    TEST_ASSERT_APPROX(transformed.z, expectedZ, 0.01f);

    return true;
}

// 方向向量测试
bool TestDirectionVectors() {
    Transform transform;

    // 默认朝向（-Z）
    Vec3 forward = transform.GetForward();
    TEST_ASSERT_APPROX(forward.z, -1.0f, 0.001f);

    // 旋转 90 度
    transform.SetRotationEuler(Vec3(0.0f, 90.0f, 0.0f));
    forward = transform.GetForward();
    TEST_ASSERT_APPROX(forward.x, 0.0f, 0.01f);
    TEST_ASSERT_APPROX(forward.z, -1.0f, 0.01f);

    // 右向量
    Vec3 right = transform.GetRight();
    TEST_ASSERT_APPROX(right.x, 1.0f, 0.01f);
    TEST_ASSERT_APPROX(right.z, 0.0f, 0.01f);

    // 上向量
    Vec3 up = transform.GetUp();
    TEST_ASSERT_APPROX(up.y, 1.0f, 0.001f);

    return true;
}

int main() {
    std::cout << "=== VR Application Scene Tests ===" << std::endl;
    std::cout << std::endl;

    int passed = 0;
    int failed = 0;
    int total = 0;

    RUN_TEST(TestTransform);
    RUN_TEST(TestSceneObject);
    RUN_TEST(TestCamera);
    RUN_TEST(TestLight);
    RUN_TEST(TestScene);
    RUN_TEST(TestSceneManager);
    RUN_TEST(TestTransformHierarchy);
    RUN_TEST(TestDirectionVectors);

    std::cout << std::endl;
    std::cout << "=== Results ===" << std::endl;
    std::cout << "Passed: " << passed << "/" << total << std::endl;

    if (failed > 0) {
        std::cout << "Failed: " << failed << "/" << total << std::endl;
        return 1;
    }

    std::cout << "All tests passed!" << std::endl;
    return 0;
}