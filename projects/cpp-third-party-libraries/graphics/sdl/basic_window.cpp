/**
 * @file basic_window.cpp
 * @brief SDL 多媒体库基础窗口示例
 * @details 展示 SDL 的基本用法
 *          SDL 是一个跨平台的多媒体库
 *          支持窗口管理、事件处理、渲染等
 */

#include <iostream>
#include <SDL2/SDL.h>

/**
 * @brief 基础窗口示例
 * @details 创建简单的窗口并处理事件
 */
void basic_window() {
    std::cout << "=== 基础窗口 ===" << std::endl;

    // 初始化 SDL
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        std::cerr << "SDL could not initialize! SDL_Error: " << SDL_GetError() << std::endl;
        return;
    }

    // 创建窗口
    SDL_Window* window = SDL_CreateWindow(
        "SDL Window",
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        800, 600,
        SDL_WINDOW_SHOWN
    );

    if (window == nullptr) {
        std::cerr << "Window could not be created! SDL_Error: " << SDL_GetError() << std::endl;
        SDL_Quit();
        return;
    }

    // 主循环
    bool quit = false;
    SDL_Event e;

    while (!quit) {
        // 处理事件
        while (SDL_PollEvent(&e) != 0) {
            if (e.type == SDL_QUIT) {
                quit = true;
            }

            if (e.type == SDL_KEYDOWN) {
                if (e.key.keysym.sym == SDLK_ESCAPE) {
                    quit = true;
                }
            }
        }

        // 获取窗口表面
        SDL_Surface* surface = SDL_GetWindowSurface(window);

        // 填充白色
        SDL_FillRect(surface, nullptr, SDL_MapRGB(surface->format, 255, 255, 255));

        // 更新窗口
        SDL_UpdateWindowSurface(window);
    }

    // 清理
    SDL_DestroyWindow(window);
    SDL_Quit();
}

/**
 * @brief 渲染器示例
 * @details 展示如何使用 SDL 渲染器
 */
void renderer_example() {
    std::cout << "=== 渲染器示例 ===" << std::endl;

    // 初始化 SDL
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        std::cerr << "SDL could not initialize! SDL_Error: " << SDL_GetError() << std::endl;
        return;
    }

    // 创建窗口
    SDL_Window* window = SDL_CreateWindow(
        "SDL Renderer",
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        800, 600,
        SDL_WINDOW_SHOWN
    );

    if (window == nullptr) {
        std::cerr << "Window could not be created! SDL_Error: " << SDL_GetError() << std::endl;
        SDL_Quit();
        return;
    }

    // 创建渲染器
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (renderer == nullptr) {
        std::cerr << "Renderer could not be created! SDL_Error: " << SDL_GetError() << std::endl;
        SDL_DestroyWindow(window);
        SDL_Quit();
        return;
    }

    // 主循环
    bool quit = false;
    SDL_Event e;

    while (!quit) {
        // 处理事件
        while (SDL_PollEvent(&e) != 0) {
            if (e.type == SDL_QUIT) {
                quit = true;
            }
        }

        // 清屏（黑色）
        SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
        SDL_RenderClear(renderer);

        // 绘制红色矩形
        SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
        SDL_Rect rect = {100, 100, 200, 150};
        SDL_RenderFillRect(renderer, &rect);

        // 绘制绿色矩形
        SDL_SetRenderDrawColor(renderer, 0, 255, 0, 255);
        SDL_Rect rect2 = {400, 100, 200, 150};
        SDL_RenderFillRect(renderer, &rect2);

        // 绘制蓝色矩形
        SDL_SetRenderDrawColor(renderer, 0, 0, 255, 255);
        SDL_Rect rect3 = {250, 300, 200, 150};
        SDL_RenderFillRect(renderer, &rect3);

        // 更新屏幕
        SDL_RenderPresent(renderer);
    }

    // 清理
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
}

/**
 * @brief SDL 概念说明
 * @details 介绍 SDL 的核心概念
 */
void sdl_concepts() {
    std::cout << "=== SDL 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "SDL（Simple DirectMedia Layer）是一个跨平台多媒体库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要功能：" << std::endl;
    std::cout << "  - 窗口管理" << std::endl;
    std::cout << "  - 事件处理" << std::endl;
    std::cout << "  - 2D 渲染" << std::endl;
    std::cout << "  - 音频播放" << std::endl;
    std::cout << "  - 输入设备" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 跨平台支持" << std::endl;
    std::cout << "  - 底层控制" << std::endl;
    std::cout << "  - 高性能" << std::endl;
    std::cout << "  - 广泛使用" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== SDL 多媒体库示例 ===" << std::endl;
    std::cout << std::endl;

    sdl_concepts();

    // 注意：以下示例需要图形环境
    // basic_window();
    // renderer_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 SDL 示例需要图形环境" << std::endl;
    std::cout << "请取消注释 main() 中的函数调用来运行示例" << std::endl;

    return 0;
}