/**
 * @file basic_window.cpp
 * @brief SFML 多媒体库基础窗口示例
 * @details 展示 SFML 的基本用法
 *          SFML 是一个简单易用的多媒体库
 *          支持窗口管理、图形绘制、音频播放等
 */

#include <iostream>
#include <SFML/Graphics.hpp>

/**
 * @brief 基础窗口示例
 * @details 创建简单的窗口并处理事件
 */
void basic_window() {
    std::cout << "=== 基础窗口 ===" << std::endl;

    // 创建窗口
    sf::RenderWindow window(sf::VideoMode(800, 600), "SFML Window");
    window.setFramerateLimit(60);

    // 主循环
    while (window.isOpen()) {
        // 处理事件
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) {
                window.close();
            }

            if (event.type == sf::Event::KeyPressed) {
                if (event.key.code == sf::Keyboard::Escape) {
                    window.close();
                }
            }
        }

        // 清屏
        window.clear(sf::Color::Black);

        // 绘制内容
        // ...

        // 显示
        window.display();
    }
}

/**
 * @brief 图形绘制示例
 * @details 展示如何绘制基本图形
 */
void drawing_shapes() {
    std::cout << "=== 图形绘制 ===" << std::endl;

    sf::RenderWindow window(sf::VideoMode(800, 600), "SFML Drawing");
    window.setFramerateLimit(60);

    // 创建圆形
    sf::CircleShape circle(50);
    circle.setFillColor(sf::Color::Red);
    circle.setPosition(100, 100);

    // 创建矩形
    sf::RectangleShape rectangle(sf::Vector2f(120, 80));
    rectangle.setFillColor(sf::Color::Green);
    rectangle.setPosition(300, 100);

    // 创建三角形
    sf::ConvexShape triangle;
    triangle.setPointCount(3);
    triangle.setPoint(0, sf::Vector2f(0, 0));
    triangle.setPoint(1, sf::Vector2f(50, 100));
    triangle.setPoint(2, sf::Vector2f(100, 0));
    triangle.setFillColor(sf::Color::Blue);
    triangle.setPosition(500, 100);

    // 主循环
    while (window.isOpen()) {
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) {
                window.close();
            }
        }

        window.clear(sf::Color::Black);

        // 绘制图形
        window.draw(circle);
        window.draw(rectangle);
        window.draw(triangle);

        window.display();
    }
}

/**
 * @brief 文本显示示例
 * @details 展示如何显示文本
 */
void text_display() {
    std::cout << "=== 文本显示 ===" << std::endl;

    sf::RenderWindow window(sf::VideoMode(800, 600), "SFML Text");
    window.setFramerateLimit(60);

    // 加载字体
    sf::Font font;
    if (!font.loadFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")) {
        std::cerr << "Failed to load font" << std::endl;
        return;
    }

    // 创建文本
    sf::Text text;
    text.setFont(font);
    text.setString("Hello, SFML!");
    text.setCharacterSize(48);
    text.setFillColor(sf::Color::White);
    text.setPosition(200, 250);

    // 主循环
    while (window.isOpen()) {
        sf::Event event;
        while (window.pollEvent(event)) {
            if (event.type == sf::Event::Closed) {
                window.close();
            }
        }

        window.clear(sf::Color::Black);
        window.draw(text);
        window.display();
    }
}

/**
 * @brief SFML 概念说明
 * @details 介绍 SFML 的核心概念
 */
void sfml_concepts() {
    std::cout << "=== SFML 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "SFML 是一个简单易用的多媒体库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要模块：" << std::endl;
    std::cout << "  - System: 基础系统功能" << std::endl;
    std::cout << "  - Window: 窗口和事件管理" << std::endl;
    std::cout << "  - Graphics: 2D 图形渲染" << std::endl;
    std::cout << "  - Audio: 音频播放" << std::endl;
    std::cout << "  - Network: 网络通信" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 简单易用的 API" << std::endl;
    std::cout << "  - 跨平台支持" << std::endl;
    std::cout << "  - 硬件加速渲染" << std::endl;
    std::cout << "  - 适合 2D 游戏开发" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== SFML 多媒体库示例 ===" << std::endl;
    std::cout << std::endl;

    sfml_concepts();

    // 注意：以下示例需要图形环境
    // basic_window();
    // drawing_shapes();
    // text_display();

    std::cout << "=== 示例结束 ===" << std::endl;
    std::cout << std::endl;
    std::cout << "注意：完整的 SFML 示例需要图形环境" << std::endl;
    std::cout << "请取消注释 main() 中的函数调用来运行示例" << std::endl;

    return 0;
}