#pragma once

#include "Common.h"

namespace vr {

// 窗口配置
struct WindowConfig {
    int width = 1280;
    int height = 720;
    std::string title = "VR Application";
    bool fullscreen = false;
    bool vsync = true;
    int msaaSamples = 4;
};

// 引擎配置
struct EngineConfig {
    WindowConfig window;
    bool enableDebug = false;
    bool enableVR = true;
    bool desktopMode = false;  // 桌面模拟模式
    float renderScale = 1.0f;
};

// 帧率统计
struct FrameStats {
    float fps = 0.0f;
    float frameTime = 0.0f;  // 毫秒
    float deltaTime = 0.0f;  // 秒
    uint64_t frameCount = 0;

    // 性能计数器
    float cpuTime = 0.0f;
    float gpuTime = 0.0f;
    int drawCalls = 0;
    int vertices = 0;
};

// 时间管理器
class Timer {
public:
    Timer();

    // 更新计时器
    void Update();

    // 获取时间
    float GetDeltaTime() const { return m_deltaTime; }
    float GetTotalTime() const { return m_totalTime; }
    float GetFPS() const { return m_fps; }
    uint64_t GetFrameCount() const { return m_frameCount; }

    // 帧率限制
    void SetTargetFPS(float fps);
    float GetTargetFPS() const { return m_targetFPS; }

private:
    using Clock = std::chrono::high_resolution_clock;
    using TimePoint = std::chrono::time_point<Clock>;
    using Duration = std::chrono::duration<float>;

    TimePoint m_startTime;
    TimePoint m_lastTime;
    TimePoint m_currentTime;

    float m_deltaTime = 0.0f;
    float m_totalTime = 0.0f;
    float m_fps = 0.0f;
    float m_targetFPS = 90.0f;
    uint64_t m_frameCount = 0;

    // FPS 计算
    float m_fpsAccumulator = 0.0f;
    int m_fpsFrameCount = 0;
    TimePoint m_fpsUpdateTime;
};

// 引擎类
class Engine {
public:
    Engine();
    ~Engine();

    // 禁用拷贝
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    // 初始化和关闭
    bool Initialize(const EngineConfig& config = EngineConfig());
    void Shutdown();

    // 主循环
    void PollEvents();
    void SwapBuffers();
    bool ShouldClose() const;

    // 获取窗口
    GLFWwindow* GetWindow() const { return m_window; }

    // 获取配置
    const EngineConfig& GetConfig() const { return m_config; }
    const WindowConfig& GetWindowConfig() const { return m_config.window; }

    // 获取统计信息
    const FrameStats& GetFrameStats() const { return m_frameStats; }
    const Timer& GetTimer() const { return m_timer; }

    // 更新统计信息
    void UpdateStats();

    // 窗口回调
    void SetFramebufferSizeCallback(std::function<void(int, int)> callback);
    void SetKeyCallback(std::function<void(int, int, int, int)> callback);
    void SetMouseButtonCallback(std::function<void(int, int, int)> callback);
    void SetCursorPosCallback(std::function<void(double, double)> callback);
    void SetScrollCallback(std::function<void(double, double)> callback);

    // 窗口操作
    void SetWindowTitle(const std::string& title);
    void GetWindowSize(int& width, int& height) const;
    void SetWindowSize(int width, int height);
    bool IsWindowFocused() const;
    bool IsWindowMinimized() const;

    // 输入查询
    bool IsKeyPressed(int key) const;
    bool IsMouseButtonPressed(int button) const;
    void GetCursorPos(double& x, double& y) const;

    // OpenGL 信息
    std::string GetGLVersion() const;
    std::string GetGLRenderer() const;
    std::string GetGLVendor() const;

private:
    // 初始化 GLFW
    bool InitializeGLFW();

    // 初始化 OpenGL
    bool InitializeOpenGL();

    // 初始化调试
    bool InitializeDebug();

    // 回调函数
    static void GLFWErrorCallback(int error, const char* description);
    static void GLFWFramebufferSizeCallback(GLFWwindow* window, int width, int height);
    static void GLFWKeyCallback(GLFWwindow* window, int key, int scancode, int action, int mods);
    static void GLFWMouseButtonCallback(GLFWwindow* window, int button, int action, int mods);
    static void GLFWCursorPosCallback(GLFWwindow* window, double xpos, double ypos);
    static void GLFWScrollCallback(GLFWwindow* window, double xoffset, double yoffset);

    // 成员变量
    GLFWwindow* m_window = nullptr;
    EngineConfig m_config;
    Timer m_timer;
    FrameStats m_frameStats;

    // 回调函数
    std::function<void(int, int)> m_framebufferSizeCallback;
    std::function<void(int, int, int, int)> m_keyCallback;
    std::function<void(int, int, int)> m_mouseButtonCallback;
    std::function<void(double, double)> m_cursorPosCallback;
    std::function<void(double, double)> m_scrollCallback;

    bool m_isInitialized = false;
};

// 日志系统
class Logger {
public:
    static Logger& GetInstance();

    // 初始化
    void Initialize(const std::string& logFile = "");

    // 日志记录
    void Log(LogLevel level, const char* file, int line, const std::string& message);
    void Debug(const std::string& message);
    void Info(const std::string& message);
    void Warning(const std::string& message);
    void Error(const std::string& message);
    void Fatal(const std::string& message);

    // 设置日志级别
    void SetLogLevel(LogLevel level) { m_logLevel = level; }
    LogLevel GetLogLevel() const { return m_logLevel; }

    // 设置输出
    void SetConsoleOutput(bool enabled) { m_consoleOutput = enabled; }
    void SetFileOutput(bool enabled) { m_fileOutput = enabled; }

private:
    Logger() = default;
    ~Logger();

    std::string FormatMessage(LogLevel level, const char* file, int line, const std::string& message);
    std::string GetLogLevelString(LogLevel level);

    LogLevel m_logLevel = LogLevel::Debug;
    bool m_consoleOutput = true;
    bool m_fileOutput = false;
    std::ofstream m_logFile;
    bool m_isInitialized = false;
};

// 资源路径工具
class PathUtils {
public:
    // 获取可执行文件目录
    static std::string GetExecutableDir();

    // 获取资源目录
    static std::string GetResourceDir();

    // 获取着色器目录
    static std::string GetShaderDir();

    // 获取纹理目录
    static std::string GetTextureDir();

    // 获取模型目录
    static std::string GetModelDir();

    // 路径操作
    static std::string Join(const std::string& path1, const std::string& path2);
    static std::string GetExtension(const std::string& path);
    static std::string GetFilename(const std::string& path);
    static bool FileExists(const std::string& path);

private:
    static std::string s_resourceDir;
};

}  // namespace vr