/**
 * 11_using_enum.cpp - C++20 using enum 声明
 *
 * using enum 将枚举成员引入当前作用域，减少代码冗余。
 *
 * 核心要点：
 * 1. using enum 将所有枚举成员引入作用域
 * 2. 在 switch 语句中特别有用
 * 3. 可用于函数体、类作用域、块作用域
 */

#include <iostream>
#include <string>
#include <array>
#include <stdexcept>

// ============================================================
// 1. 基本枚举定义
// ============================================================

enum class Color { Red, Green, Blue, Yellow, White, Black };
enum class Direction { North, South, East, West };
enum class LogLevel { Debug, Info, Warning, Error, Fatal };

// ============================================================
// 2. using enum 在 switch 中使用
// ============================================================

std::string color_name(Color c) {
    switch (c) {
        // C++17: 需要写 Color::Red, Color::Green, ...
        // C++20: using enum 让代码更简洁
        using enum Color;
        case Red:    return "红色";
        case Green:  return "绿色";
        case Blue:   return "蓝色";
        case Yellow: return "黄色";
        case White:  return "白色";
        case Black:  return "黑色";
        default:     return "未知";
    }
}

// ============================================================
// 3. using enum 在函数体中使用
// ============================================================

std::string describe_direction(Direction d) {
    using enum Direction;

    if (d == North) return "向北";
    if (d == South) return "向南";
    if (d == East)  return "向东";
    if (d == West)  return "向西";
    return "未知方向";
}

// ============================================================
// 4. using enum 在类中使用
// ============================================================

class Logger {
public:
    void log(LogLevel level, const std::string& message) {
        using enum LogLevel;
        switch (level) {
            case Debug:   std::cout << "[DEBUG] "; break;
            case Info:    std::cout << "[INFO] "; break;
            case Warning: std::cout << "[WARN] "; break;
            case Error:   std::cout << "[ERROR] "; break;
            case Fatal:   std::cout << "[FATAL] "; break;
        }
        std::cout << message << "\n";
    }
};

// ============================================================
// 5. using enum 用于比较
// ============================================================

bool is_primary(Color c) {
    using enum Color;
    return c == Red || c == Green || c == Blue;
}

bool is_error_level(LogLevel level) {
    using enum LogLevel;
    return level == Error || level == Fatal;
}

// ============================================================
// 6. 传统写法对比
// ============================================================

// C++17 风格 - 冗长
std::string color_name_old(Color c) {
    switch (c) {
        case Color::Red:    return "红色";
        case Color::Green:  return "绿色";
        case Color::Blue:   return "蓝色";
        case Color::Yellow: return "黄色";
        case Color::White:  return "白色";
        case Color::Black:  return "黑色";
        default:            return "未知";
    }
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 using enum 示例 ===\n\n";

    // 1. switch 中使用
    std::cout << "【1. switch 中使用 using enum】\n";
    std::cout << "Color::Red -> " << color_name(Color::Red) << "\n";
    std::cout << "Color::Blue -> " << color_name(Color::Blue) << "\n\n";

    // 2. 函数中使用
    std::cout << "【2. 函数体中使用】\n";
    std::cout << "Direction::North -> " << describe_direction(Direction::North) << "\n";
    std::cout << "Direction::West -> " << describe_direction(Direction::West) << "\n\n";

    // 3. 日志类
    std::cout << "【3. 类方法中使用】\n";
    Logger logger;
    logger.log(LogLevel::Info, "应用启动");
    logger.log(LogLevel::Error, "连接失败");
    std::cout << "\n";

    // 4. 比较操作
    std::cout << "【4. 用于比较】\n";
    std::cout << "Red 是原色: " << std::boolalpha << is_primary(Color::Red) << "\n";
    std::cout << "Yellow 是原色: " << is_primary(Color::Yellow) << "\n";
    std::cout << "Error 级别: " << is_error_level(LogLevel::Error) << "\n";
    std::cout << "Info 级别: " << is_error_level(LogLevel::Info) << "\n\n";

    // 5. 与数组配合
    std::cout << "【5. 与数组配合】\n";
    using enum Color;
    std::array<Color, 3> primary_colors = {Red, Green, Blue};
    std::cout << "原色: ";
    for (auto c : primary_colors) {
        std::cout << color_name(c) << " ";
    }
    std::cout << "\n\n";

    // 6. 优势总结
    std::cout << "【6. using enum 优势】\n";
    std::cout << "  - 减少代码冗余（不用重复写 Color::）\n";
    std::cout << "  - switch 语句更清晰\n";
    std::cout << "  - 与 C++17 的 using 声明类似，但作用于整个枚举\n";
    std::cout << "  - 不影响枚举的强类型特性\n";

    std::cout << "\n=== using enum 示例完成 ===\n";
    return 0;
}
