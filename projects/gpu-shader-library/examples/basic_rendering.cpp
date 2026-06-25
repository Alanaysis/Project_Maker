/**
 * 基础渲染示例
 *
 * 功能：
 * - 窗口创建
 * - 基础光照
 * - 模型加载
 */

#include <iostream>
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include "shader_loader.h"
#include "mesh_generator.h"

using namespace gpu_shader;

// 窗口尺寸
const unsigned int WINDOW_WIDTH = 1280;
const unsigned int WINDOW_HEIGHT = 720;

// 相机参数
glm::vec3 cameraPos = glm::vec3(0.0f, 2.0f, 5.0f);
glm::vec3 cameraFront = glm::vec3(0.0f, 0.0f, -1.0f);
glm::vec3 cameraUp = glm::vec3(0.0f, 1.0f, 0.0f);

float deltaTime = 0.0f;
float lastFrame = 0.0f;

// 鼠标控制
bool firstMouse = true;
float yaw = -90.0f;
float pitch = 0.0f;
float lastX = WINDOW_WIDTH / 2.0f;
float lastY = WINDOW_HEIGHT / 2.0f;

// 回调函数
void framebuffer_size_callback(GLFWwindow* window, int width, int height) {
    glViewport(0, 0, width, height);
}

void mouse_callback(GLFWwindow* window, double xpos, double ypos) {
    if (firstMouse) {
        lastX = xpos;
        lastY = ypos;
        firstMouse = false;
    }

    float xoffset = xpos - lastX;
    float yoffset = lastY - ypos;
    lastX = xpos;
    lastY = ypos;

    float sensitivity = 0.1f;
    xoffset *= sensitivity;
    yoffset *= sensitivity;

    yaw += xoffset;
    pitch += yoffset;

    if (pitch > 89.0f) pitch = 89.0f;
    if (pitch < -89.0f) pitch = -89.0f;

    glm::vec3 front;
    front.x = cos(glm::radians(yaw)) * cos(glm::radians(pitch));
    front.y = sin(glm::radians(pitch));
    front.z = sin(glm::radians(yaw)) * cos(glm::radians(pitch));
    cameraFront = glm::normalize(front);
}

void processInput(GLFWwindow* window) {
    float cameraSpeed = 2.5f * deltaTime;
    if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS)
        cameraPos += cameraSpeed * cameraFront;
    if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS)
        cameraPos -= cameraSpeed * cameraFront;
    if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS)
        cameraPos -= glm::normalize(glm::cross(cameraFront, cameraUp)) * cameraSpeed;
    if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS)
        cameraPos += glm::normalize(glm::cross(cameraFront, cameraUp)) * cameraSpeed;
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
        glfwSetWindowShouldClose(window, true);
}

int main() {
    // 初始化 GLFW
    glfwInit();
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 5);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    // 创建窗口
    GLFWwindow* window = glfwCreateWindow(WINDOW_WIDTH, WINDOW_HEIGHT,
                                           "GPU Shader Library - Basic Rendering",
                                           nullptr, nullptr);
    if (!window) {
        std::cerr << "Failed to create GLFW window" << std::endl;
        glfwTerminate();
        return -1;
    }
    glfwMakeContextCurrent(window);

    // 初始化 GLAD
    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cerr << "Failed to initialize GLAD" << std::endl;
        return -1;
    }

    // 设置回调
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback);
    glfwSetCursorPosCallback(window, mouse_callback);
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);

    // OpenGL 设置
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_CULL_FACE);

    // 加载着色器
    auto shader = ShaderLoader::loadShader(
        "shaders/glsl/basic/vertex_transform.glsl",
        "shaders/glsl/lighting/blinn_phong.glsl"
    );

    if (!shader) {
        std::cerr << "Failed to load shaders" << std::endl;
        return -1;
    }

    // 生成网格
    auto sphereMesh = MeshGenerator::generateSphere(1.0f, 32, 32);
    auto planeMesh = MeshGenerator::generatePlane(10.0f, 10.0f, 10);

    // 创建 VAO/VBO/EBO
    auto createVAO = [](const MeshData& mesh) -> GLuint {
        GLuint VAO, VBO, EBO;
        glGenVertexArrays(1, &VAO);
        glGenBuffers(1, &VBO);
        glGenBuffers(1, &EBO);

        glBindVertexArray(VAO);

        glBindBuffer(GL_ARRAY_BUFFER, VBO);
        glBufferData(GL_ARRAY_BUFFER, mesh.vertices.size() * sizeof(Vertex),
                     mesh.vertices.data(), GL_STATIC_DRAW);

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, mesh.indices.size() * sizeof(uint32_t),
                     mesh.indices.data(), GL_STATIC_DRAW);

        // 位置
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                              (void*)offsetof(Vertex, position));
        glEnableVertexAttribArray(0);

        // 法线
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                              (void*)offsetof(Vertex, normal));
        glEnableVertexAttribArray(1);

        // 纹理坐标
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                              (void*)offsetof(Vertex, texCoord));
        glEnableVertexAttribArray(2);

        glBindVertexArray(0);

        return VAO;
    };

    GLuint sphereVAO = createVAO(sphereMesh);
    GLuint planeVAO = createVAO(planeMesh);

    // 渲染循环
    while (!glfwWindowShouldClose(window)) {
        float currentFrame = glfwGetTime();
        deltaTime = currentFrame - lastFrame;
        lastFrame = currentFrame;

        processInput(window);

        // 清屏
        glClearColor(0.1f, 0.1f, 0.15f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        // 使用着色器
        shader->use();

        // 设置变换矩阵
        glm::mat4 view = glm::lookAt(cameraPos, cameraPos + cameraFront, cameraUp);
        glm::mat4 projection = glm::perspective(
            glm::radians(45.0f),
            static_cast<float>(WINDOW_WIDTH) / WINDOW_HEIGHT,
            0.1f, 100.0f
        );

        shader->setMat4("uView", view);
        shader->setMat4("uProjection", projection);
        shader->setVec3("uCameraPos", cameraPos);

        // 设置光源
        shader->setVec3("uLights[0].position", glm::vec3(5.0f, 5.0f, 5.0f));
        shader->setVec3("uLights[0].color", glm::vec3(1.0f));
        shader->setFloat("uLights[0].intensity", 1.0f);
        shader->setInt("uNumLights", 1);

        // 设置材质
        shader->setVec3("uDiffuseColor", glm::vec3(0.8f, 0.2f, 0.2f));
        shader->setVec3("uSpecularColor", glm::vec3(1.0f));
        shader->setFloat("uShininess", 32.0f);
        shader->setBool("uUseTextures", false);
        shader->setBool("uUseNormalMap", false);
        shader->setVec3("uAmbientColor", glm::vec3(0.1f));
        shader->setFloat("uAmbientStrength", 0.1f);

        // 绘制球体
        glm::mat4 model = glm::mat4(1.0f);
        model = glm::translate(model, glm::vec3(0.0f, 1.0f, 0.0f));
        shader->setMat4("uModel", model);
        shader->setMat3("uNormalMatrix", glm::mat3(glm::transpose(glm::inverse(model))));

        glBindVertexArray(sphereVAO);
        glDrawElements(GL_TRIANGLES, sphereMesh.indices.size(), GL_UNSIGNED_INT, 0);

        // 绘制平面
        model = glm::mat4(1.0f);
        shader->setMat4("uModel", model);
        shader->setMat3("uNormalMatrix", glm::mat3(1.0f));
        shader->setVec3("uDiffuseColor", glm::vec3(0.3f, 0.5f, 0.3f));

        glBindVertexArray(planeVAO);
        glDrawElements(GL_TRIANGLES, planeMesh.indices.size(), GL_UNSIGNED_INT, 0);

        // 交换缓冲区
        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    // 清理
    glDeleteVertexArrays(1, &sphereVAO);
    glDeleteVertexArrays(1, &planeVAO);

    glfwTerminate();
    return 0;
}
