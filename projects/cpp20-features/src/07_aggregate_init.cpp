/**
 * 07_aggregate_init.cpp - C++20 聚合初始化改进
 *
 * C++20 对聚合初始化进行了多项改进。
 *
 * 核心要点：
 * 1. 允许有用户声明的构造函数的类进行聚合初始化
 * 2. 聚合初始化支持括号初始化
 * 3. 更宽松的聚合类型定义
 */

#include <iostream>
#include <string>
#include <array>
#include <cstdint>

// ============================================================
// 1. C++20 放宽了聚合类型的限制
// ============================================================

// C++17 中，有用户声明的构造函数的类不是聚合类型
// C++20 中，只要没有用户提供/继承的构造函数即可

struct Point {
    int x;
    int y;
};

// C++20: 可以使用聚合初始化
// Point p{1, 2};  // OK in C++20, 错误 in C++17

// ============================================================
// 2. 使用括号初始化聚合类型
// ============================================================

struct Color {
    int r, g, b;
};

// C++20 支持使用括号进行聚合初始化
// Color c(255, 128, 0);  // C++20 OK

// ============================================================
// 3. 嵌套聚合初始化
// ============================================================

struct Line {
    Point start;
    Point end;
};

// 嵌套的聚合初始化
// Line line({0, 0}, {10, 20});  // C++20 OK

// ============================================================
// 4. 聚合初始化与数组
// ============================================================

struct Pixel {
    uint8_t r, g, b, a;
};

// ============================================================
// 5. 设计器指定初始化器 (Designated Initializers)
// ============================================================

// C++20 支持指定初始化器（来自 C99）
struct Config {
    int width;
    int height;
    bool fullscreen;
    std::string title;
};

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 聚合初始化改进示例 ===\n\n";

    // 1. 基本聚合初始化
    std::cout << "【1. 基本聚合初始化】\n";
    Color red{255, 0, 0};
    Color green = {0, 255, 0};
    std::cout << "red = (" << red.r << ", " << red.g << ", " << red.b << ")\n";
    std::cout << "green = (" << green.r << ", " << green.g << ", " << green.b << ")\n\n";

    // 2. 括号初始化
    std::cout << "【2. 括号初始化（C++20 新增）】\n";
    Color blue(0, 0, 255);
    std::cout << "blue = (" << blue.r << ", " << blue.g << ", " << blue.b << ")\n\n";

    // 3. 指定初始化器
    std::cout << "【3. 指定初始化器】\n";
    Config cfg{
        .width = 1920,
        .height = 1080,
        .fullscreen = true,
        .title = "C++20 Window"
    };
    std::cout << "Config: " << cfg.width << "x" << cfg.height
              << (cfg.fullscreen ? " fullscreen" : "")
              << " \"" << cfg.title << "\"\n";

    // 可以省略有默认值的字段（但顺序必须一致）
    Config cfg2{
        .width = 800,
        .height = 600,
        .fullscreen = false,
        .title = "Small Window"
    };
    std::cout << "Config2: " << cfg2.width << "x" << cfg2.height << "\n\n";

    // 4. 嵌套聚合初始化
    std::cout << "【4. 嵌套聚合初始化】\n";
    Line line{{0, 0}, {100, 200}};
    std::cout << "Line: (" << line.start.x << "," << line.start.y << ") -> ("
              << line.end.x << "," << line.end.y << ")\n\n";

    // 5. 聚合初始化数组
    std::cout << "【5. 聚合初始化数组】\n";
    Pixel pixels[] = {
        {255, 0, 0, 255},     // 红色
        {0, 255, 0, 255},     // 绿色
        {0, 0, 255, 255},     // 蓝色
    };
    for (size_t i = 0; i < 3; ++i) {
        std::cout << "Pixel " << i << ": rgba("
                  << (int)pixels[i].r << ", " << (int)pixels[i].g << ", "
                  << (int)pixels[i].b << ", " << (int)pixels[i].a << ")\n";
    }

    // 6. 使用默认成员初始化器
    std::cout << "\n【6. 默认成员初始化器】\n";
    struct Settings {
        int volume = 50;
        bool muted = false;
        std::string lang = "en";
    };
    Settings s1{};                    // 全部使用默认值
    Settings s2{.volume = 80};        // 体积=80, 其他默认
    Settings s3{.volume = 100, .muted = true, .lang = "zh"};
    std::cout << "s1: volume=" << s1.volume << " muted=" << s1.muted << " lang=" << s1.lang << "\n";
    std::cout << "s2: volume=" << s2.volume << " muted=" << s2.muted << " lang=" << s2.lang << "\n";
    std::cout << "s3: volume=" << s3.volume << " muted=" << s3.muted << " lang=" << s3.lang << "\n";

    std::cout << "\n=== 聚合初始化示例完成 ===\n";
    return 0;
}
