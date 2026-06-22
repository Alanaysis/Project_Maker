#include "core/Application.h"
#include <iostream>
#include <exception>

int main(int argc, char* argv[]) {
    try {
        // 创建应用程序
        vr::SimpleVRApp app;

        // 配置
        vr::AppConfig config;
        config.window.title = "VR Application - Learning Project";
        config.window.width = 1280;
        config.window.height = 720;
        config.vr.enableDesktopMode = true;  // 默认使用桌面模式
        config.enableDebugTools = true;

        // 解析命令行参数
        for (int i = 1; i < argc; i++) {
            std::string arg = argv[i];
            if (arg == "--vr") {
                config.vr.enableDesktopMode = false;
            } else if (arg == "--desktop") {
                config.vr.enableDesktopMode = true;
            } else if (arg == "--width" && i + 1 < argc) {
                config.window.width = std::stoi(argv[++i]);
            } else if (arg == "--height" && i + 1 < argc) {
                config.window.height = std::stoi(argv[++i]);
            } else if (arg == "--fullscreen") {
                config.window.fullscreen = true;
            } else if (arg == "--no-vsync") {
                config.window.vsync = false;
            } else if (arg == "--help") {
                std::cout << "VR Application - Learning Project\n"
                          << "\nUsage: " << argv[0] << " [options]\n"
                          << "\nOptions:\n"
                          << "  --vr              Enable VR mode\n"
                          << "  --desktop         Enable desktop mode (default)\n"
                          << "  --width <value>   Set window width\n"
                          << "  --height <value>  Set window height\n"
                          << "  --fullscreen      Enable fullscreen\n"
                          << "  --no-vsync        Disable vsync\n"
                          << "  --help            Show this help\n"
                          << std::endl;
                return 0;
            }
        }

        // 初始化应用程序
        if (!app.Initialize(config)) {
            std::cerr << "Failed to initialize application" << std::endl;
            return -1;
        }

        // 运行主循环
        app.Run();

        // 关闭
        app.Shutdown();

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return -1;
    } catch (...) {
        std::cerr << "Unknown exception" << std::endl;
        return -1;
    }
}