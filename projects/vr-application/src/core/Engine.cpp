#include "core/Engine.h"
#include <iostream>
#include <sstream>
#include <iomanip>

namespace vr {

// Timer 实现
Timer::Timer() {
    m_startTime = Clock::now();
    m_lastTime = m_startTime;
    m_currentTime = m_startTime;
    m_fpsUpdateTime = m_startTime;
}

void Timer::Update() {
    m_lastTime = m_currentTime;
    m_currentTime = Clock::now();

    // 计算 deltaTime
    m_deltaTime = std::chrono::duration<float>(m_currentTime - m_lastTime).count();

    // 限制 deltaTime 防止卡顿时跳跃
    if (m_deltaTime > 0.1f) {
        m_deltaTime = 0.1f;
    }

    // 计算总时间
    m_totalTime = std::chrono::duration<float>(m_currentTime - m_startTime).count();

    // 更新帧数
    m_frameCount++;

    // 计算 FPS
    m_fpsAccumulator += m_deltaTime;
    m_fpsFrameCount++;

    float fpsUpdateInterval = 0.5f;  // 每 0.5 秒更新一次 FPS
    if (m_fpsAccumulator >= fpsUpdateInterval) {
        m_fps = static_cast<float>(m_fpsFrameCount) / m_fpsAccumulator;
        m_fpsAccumulator = 0.0f;
        m_fpsFrameCount = 0;
    }
}

void Timer::SetTargetFPS(float fps) {
    m_targetFPS = fps;
}

// Engine 实现
Engine::Engine() = default;

Engine::~Engine() {
    Shutdown();
}

bool Engine::Initialize(const EngineConfig& config) {
    if (m_isInitialized) {
        return true;
    }

    m_config = config;

    // 初始化日志系统
    Logger::GetInstance().Initialize();

    // 初始化 GLFW
    if (!InitializeGLFW()) {
        VR_ERROR("Failed to initialize GLFW");
        return false;
    }

    // 初始化 OpenGL
    if (!InitializeOpenGL()) {
        VR_ERROR("Failed to initialize OpenGL");
        return false;
    }

    // 初始化调试
    if (config.enableDebug) {
        if (!InitializeDebug()) {
            VR_WARNING("Failed to initialize debug tools");
        }
    }

    m_isInitialized = true;
    VR_INFO("Engine initialized successfully");

    return true;
}

void Engine::Shutdown() {
    if (!m_isInitialized) {
        return;
    }

    // 销毁窗口
    if (m_window) {
        glfwDestroyWindow(m_window);
        m_window = nullptr;
    }

    // 终止 GLFW
    glfwTerminate();

    m_isInitialized = false;
    VR_INFO("Engine shutdown");
}

bool Engine::InitializeGLFW() {
    // 设置错误回调
    glfwSetErrorCallback(GLFWErrorCallback);

    // 初始化 GLFW
    if (!glfwInit()) {
        VR_ERROR("Failed to initialize GLFW");
        return false;
    }

    // 配置 GLFW
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 5);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
    glfwWindowHint(GLFW_SAMPLES, m_config.window.msaaSamples);
    glfwWindowHint(GLFW_RESIZABLE, GLFW_TRUE);

    if (m_config.enableDebug) {
        glfwWindowHint(GLFW_OPENGL_DEBUG_CONTEXT, GL_TRUE);
    }

    // 创建窗口
    GLFWmonitor* monitor = m_config.window.fullscreen ? glfwGetPrimaryMonitor() : nullptr;
    m_window = glfwCreateWindow(
        m_config.window.width,
        m_config.window.height,
        m_config.window.title.c_str(),
        monitor,
        nullptr
    );

    if (!m_window) {
        VR_ERROR("Failed to create GLFW window");
        glfwTerminate();
        return false;
    }

    // 设置上下文
    glfwMakeContextCurrent(m_window);

    // 设置 VSync
    glfwSwapInterval(m_config.window.vsync ? 1 : 0);

    // 设置回调
    glfwSetWindowUserPointer(m_window, this);
    glfwSetFramebufferSizeCallback(m_window, GLFWFramebufferSizeCallback);
    glfwSetKeyCallback(m_window, GLFWKeyCallback);
    glfwSetMouseButtonCallback(m_window, GLFWMouseButtonCallback);
    glfwSetCursorPosCallback(m_window, GLFWCursorPosCallback);
    glfwSetScrollCallback(m_window, GLFWScrollCallback);

    VR_INFO("GLFW initialized successfully");
    return true;
}

bool Engine::InitializeOpenGL() {
    // 初始化 GLEW
    glewExperimental = GL_TRUE;
    GLenum err = glewInit();
    if (err != GLEW_OK) {
        VR_ERROR("Failed to initialize GLEW: " + std::string(reinterpret_cast<const char*>(glewGetErrorString(err))));
        return false;
    }

    // 打印 OpenGL 信息
    VR_INFO("OpenGL Version: " + GetGLVersion());
    VR_INFO("OpenGL Renderer: " + GetGLRenderer());
    VR_INFO("OpenGL Vendor: " + GetGLVendor());

    // 检查 OpenGL 版本
    if (!GLEW_VERSION_4_5) {
        VR_ERROR("OpenGL 4.5 is required");
        return false;
    }

    // 设置 OpenGL 状态
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_MULTISAMPLE);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
    glFrontFace(GL_CCW);

    // 设置清除颜色
    glClearColor(0.2f, 0.3f, 0.3f, 1.0f);

    // 设置视口
    int width, height;
    glfwGetFramebufferSize(m_window, &width, &height);
    glViewport(0, 0, width, height);

    VR_INFO("OpenGL initialized successfully");
    return true;
}

bool Engine::InitializeDebug() {
    // 启用 OpenGL 调试输出
    glEnable(GL_DEBUG_OUTPUT);
    glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);

    // 设置调试回调
    glDebugMessageCallback([](GLenum source, GLenum type, GLuint id, GLenum severity,
                             GLsizei length, const GLchar* message, const void* userParam) {
        // 忽略一些不重要的消息
        if (id == 131169 || id == 131185 || id == 131218 || id == 131204) {
            return;
        }

        std::string msg = "GL Debug [";
        switch (severity) {
            case GL_DEBUG_SEVERITY_HIGH: msg += "HIGH"; break;
            case GL_DEBUG_SEVERITY_MEDIUM: msg += "MEDIUM"; break;
            case GL_DEBUG_SEVERITY_LOW: msg += "LOW"; break;
            case GL_DEBUG_SEVERITY_NOTIFICATION: msg += "NOTIFICATION"; break;
            default: msg += "UNKNOWN"; break;
        }
        msg += "]: " + std::string(message);

        if (severity == GL_DEBUG_SEVERITY_HIGH) {
            VR_ERROR(msg);
        } else if (severity == GL_DEBUG_SEVERITY_MEDIUM) {
            VR_WARNING(msg);
        }
    }, nullptr);

    VR_INFO("OpenGL debug output enabled");
    return true;
}

void Engine::PollEvents() {
    glfwPollEvents();
}

void Engine::SwapBuffers() {
    glfwSwapBuffers(m_window);
    m_timer.Update();
    UpdateStats();
}

bool Engine::ShouldClose() const {
    return glfwWindowShouldClose(m_window);
}

void Engine::UpdateStats() {
    m_frameStats.fps = m_timer.GetFPS();
    m_frameStats.frameTime = m_timer.GetDeltaTime() * 1000.0f;  // 转换为毫秒
    m_frameStats.deltaTime = m_timer.GetDeltaTime();
    m_frameStats.frameCount = m_timer.GetFrameCount();
}

void Engine::SetFramebufferSizeCallback(std::function<void(int, int)> callback) {
    m_framebufferSizeCallback = callback;
}

void Engine::SetKeyCallback(std::function<void(int, int, int, int)> callback) {
    m_keyCallback = callback;
}

void Engine::SetMouseButtonCallback(std::function<void(int, int, int)> callback) {
    m_mouseButtonCallback = callback;
}

void Engine::SetCursorPosCallback(std::function<void(double, double)> callback) {
    m_cursorPosCallback = callback;
}

void Engine::SetScrollCallback(std::function<void(double, double)> callback) {
    m_scrollCallback = callback;
}

void Engine::SetWindowTitle(const std::string& title) {
    glfwSetWindowTitle(m_window, title.c_str());
}

void Engine::GetWindowSize(int& width, int& height) const {
    glfwGetWindowSize(m_window, &width, &height);
}

void Engine::SetWindowSize(int width, int height) {
    glfwSetWindowSize(m_window, width, height);
}

bool Engine::IsWindowFocused() const {
    return glfwGetWindowAttrib(m_window, GLFW_FOCUSED) != 0;
}

bool Engine::IsWindowMinimized() const {
    return glfwGetWindowAttrib(m_window, GLFW_ICONIFIED) != 0;
}

bool Engine::IsKeyPressed(int key) const {
    return glfwGetKey(m_window, key) == GLFW_PRESS;
}

bool Engine::IsMouseButtonPressed(int button) const {
    return glfwGetMouseButton(m_window, button) == GLFW_PRESS;
}

void Engine::GetCursorPos(double& x, double& y) const {
    glfwGetCursorPos(m_window, &x, &y);
}

std::string Engine::GetGLVersion() const {
    const char* version = reinterpret_cast<const char*>(glGetString(GL_VERSION));
    return version ? version : "Unknown";
}

std::string Engine::GetGLRenderer() const {
    const char* renderer = reinterpret_cast<const char*>(glGetString(GL_RENDERER));
    return renderer ? renderer : "Unknown";
}

std::string Engine::GetGLVendor() const {
    const char* vendor = reinterpret_cast<const char*>(glGetString(GL_VENDOR));
    return vendor ? vendor : "Unknown";
}

// GLFW 回调函数
void Engine::GLFWErrorCallback(int error, const char* description) {
    VR_ERROR("GLFW Error [" + std::to_string(error) + "]: " + std::string(description));
}

void Engine::GLFWFramebufferSizeCallback(GLFWwindow* window, int width, int height) {
    Engine* engine = static_cast<Engine*>(glfwGetWindowUserPointer(window));
    if (engine && engine->m_framebufferSizeCallback) {
        engine->m_framebufferSizeCallback(width, height);
    }
}

void Engine::GLFWKeyCallback(GLFWwindow* window, int key, int scancode, int action, int mods) {
    Engine* engine = static_cast<Engine*>(glfwGetWindowUserPointer(window));
    if (engine && engine->m_keyCallback) {
        engine->m_keyCallback(key, scancode, action, mods);
    }
}

void Engine::GLFWMouseButtonCallback(GLFWwindow* window, int button, int action, int mods) {
    Engine* engine = static_cast<Engine*>(glfwGetWindowUserPointer(window));
    if (engine && engine->m_mouseButtonCallback) {
        engine->m_mouseButtonCallback(button, action, mods);
    }
}

void Engine::GLFWCursorPosCallback(GLFWwindow* window, double xpos, double ypos) {
    Engine* engine = static_cast<Engine*>(glfwGetWindowUserPointer(window));
    if (engine && engine->m_cursorPosCallback) {
        engine->m_cursorPosCallback(xpos, ypos);
    }
}

void Engine::GLFWScrollCallback(GLFWwindow* window, double xoffset, double yoffset) {
    Engine* engine = static_cast<Engine*>(glfwGetWindowUserPointer(window));
    if (engine && engine->m_scrollCallback) {
        engine->m_scrollCallback(xoffset, yoffset);
    }
}

// Logger 实现
Logger& Logger::GetInstance() {
    static Logger instance;
    return instance;
}

Logger::~Logger() {
    if (m_logFile.is_open()) {
        m_logFile.close();
    }
}

void Logger::Initialize(const std::string& logFile) {
    if (m_isInitialized) {
        return;
    }

    if (!logFile.empty()) {
        m_logFile.open(logFile, std::ios::out | std::ios::trunc);
        if (m_logFile.is_open()) {
            m_fileOutput = true;
        }
    }

    m_isInitialized = true;
}

void Logger::Log(LogLevel level, const char* file, int line, const std::string& message) {
    if (level < m_logLevel) {
        return;
    }

    std::string formatted = FormatMessage(level, file, line, message);

    if (m_consoleOutput) {
        if (level >= LogLevel::Error) {
            std::cerr << formatted << std::endl;
        } else {
            std::cout << formatted << std::endl;
        }
    }

    if (m_fileOutput && m_logFile.is_open()) {
        m_logFile << formatted << std::endl;
        m_logFile.flush();
    }
}

void Logger::Debug(const std::string& message) {
    Log(LogLevel::Debug, "", 0, message);
}

void Logger::Info(const std::string& message) {
    Log(LogLevel::Info, "", 0, message);
}

void Logger::Warning(const std::string& message) {
    Log(LogLevel::Warning, "", 0, message);
}

void Logger::Error(const std::string& message) {
    Log(LogLevel::Error, "", 0, message);
}

void Logger::Fatal(const std::string& message) {
    Log(LogLevel::Fatal, "", 0, message);
}

std::string Logger::FormatMessage(LogLevel level, const char* file, int line, const std::string& message) {
    // 获取当前时间
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;

    std::stringstream ss;
    ss << std::put_time(std::localtime(&time), "%H:%M:%S");
    ss << "." << std::setfill('0') << std::setw(3) << ms.count();

    std::string result = "[" + ss.str() + "] ";
    result += "[" + GetLogLevelString(level) + "] ";

    if (file && file[0]) {
        std::string filePath = file;
        size_t lastSlash = filePath.find_last_of("/\\");
        if (lastSlash != std::string::npos) {
            filePath = filePath.substr(lastSlash + 1);
        }
        result += filePath + ":" + std::to_string(line) + " ";
    }

    result += message;
    return result;
}

std::string Logger::GetLogLevelString(LogLevel level) {
    switch (level) {
        case LogLevel::Debug:   return "DEBUG";
        case LogLevel::Info:    return "INFO";
        case LogLevel::Warning: return "WARN";
        case LogLevel::Error:   return "ERROR";
        case LogLevel::Fatal:   return "FATAL";
        default:                return "UNKNOWN";
    }
}

// PathUtils 实现
std::string PathUtils::s_resourceDir = "resources";

std::string PathUtils::GetExecutableDir() {
    // 简化实现，返回当前目录
    return ".";
}

std::string PathUtils::GetResourceDir() {
    return s_resourceDir;
}

std::string PathUtils::GetShaderDir() {
    return Join(GetResourceDir(), "shaders");
}

std::string PathUtils::GetTextureDir() {
    return Join(GetResourceDir(), "textures");
}

std::string PathUtils::GetModelDir() {
    return Join(GetResourceDir(), "models");
}

std::string PathUtils::Join(const std::string& path1, const std::string& path2) {
    if (path1.empty()) return path2;
    if (path2.empty()) return path1;

    char lastChar = path1.back();
    if (lastChar == '/' || lastChar == '\\') {
        return path1 + path2;
    }
    return path1 + "/" + path2;
}

std::string PathUtils::GetExtension(const std::string& path) {
    size_t dotPos = path.find_last_of('.');
    if (dotPos != std::string::npos) {
        return path.substr(dotPos);
    }
    return "";
}

std::string PathUtils::GetFilename(const std::string& path) {
    size_t lastSlash = path.find_last_of("/\\");
    if (lastSlash != std::string::npos) {
        return path.substr(lastSlash + 1);
    }
    return path;
}

bool PathUtils::FileExists(const std::string& path) {
    std::ifstream file(path);
    return file.good();
}

}  // namespace vr