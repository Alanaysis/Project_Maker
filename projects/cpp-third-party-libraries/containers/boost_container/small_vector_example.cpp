/**
 * @file small_vector_example.cpp
 * @brief Boost.Container small_vector 示例
 * @details 展示 boost::container::small_vector 的使用方法
 *          small_vector 对小对象进行优化，使用栈内存
 *          当元素数量超过预分配大小时，自动切换到堆内存
 */

#include <iostream>
#include <string>
#include <boost/container/small_vector.hpp>

/**
 * @brief 基础用法示例
 * @details 展示 small_vector 的基本操作
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 small_vector，预分配 10 个元素的空间
    boost::container::small_vector<int, 10> vec;

    // 添加元素
    for (int i = 0; i < 5; ++i) {
        vec.push_back(i);
    }

    std::cout << "Size: " << vec.size() << std::endl;
    std::cout << "Capacity: " << vec.capacity() << std::endl;
    std::cout << "Elements: ";
    for (const auto& elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 内存优化示例
 * @details 展示 small_vector 的内存优化特性
 */
void memory_optimization() {
    std::cout << "=== 内存优化 ===" << std::endl;

    // 小对象场景：使用栈内存
    boost::container::small_vector<int, 5> small_vec;
    std::cout << "Small vector (size=3):" << std::endl;
    std::cout << "  Size: " << small_vec.size() << std::endl;

    // 添加少量元素
    for (int i = 0; i < 3; ++i) {
        small_vec.push_back(i);
    }

    // 大对象场景：自动切换到堆内存
    boost::container::small_vector<int, 5> large_vec;
    std::cout << "Large vector (size=10):" << std::endl;

    for (int i = 0; i < 10; ++i) {
        large_vec.push_back(i);
    }
    std::cout << "  Size: " << large_vec.size() << std::endl;
    std::cout << "  Capacity: " << large_vec.capacity() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 性能对比示例
 * @details 展示 small_vector 与 std::vector 的性能差异
 */
void performance_comparison() {
    std::cout << "=== 性能对比 ===" << std::endl;

    std::cout << "small_vector 优势:" << std::endl;
    std::cout << "  - 小对象无堆分配" << std::endl;
    std::cout << "  - 缓存友好" << std::endl;
    std::cout << "  - 减少内存碎片" << std::endl;

    std::cout << std::endl;

    std::cout << "适用场景:" << std::endl;
    std::cout << "  - 元素数量通常较少" << std::endl;
    std::cout << "  - 频繁创建和销毁" << std::endl;
    std::cout << "  - 对性能敏感" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 small_vector 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：存储少量颜色值
    struct Color {
        uint8_t r, g, b, a;

        Color(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255)
            : r(r), g(g), b(b), a(a) {}

        friend std::ostream& operator<<(std::ostream& os, const Color& c) {
            os << "(" << (int)c.r << "," << (int)c.g << "," << (int)c.b << "," << (int)c.a << ")";
            return os;
        }
    };

    // 使用 small_vector 存储调色板
    boost::container::small_vector<Color, 8> palette;

    // 添加颜色
    palette.emplace_back(255, 0, 0);    // 红色
    palette.emplace_back(0, 255, 0);    // 绿色
    palette.emplace_back(0, 0, 255);    // 蓝色
    palette.emplace_back(255, 255, 0);  // 黄色

    std::cout << "Palette colors:" << std::endl;
    for (size_t i = 0; i < palette.size(); ++i) {
        std::cout << "  Color " << i << ": " << palette[i] << std::endl;
    }

    // 场景：存储路径点
    struct Point {
        float x, y;

        Point(float x, float y) : x(x), y(y) {}

        friend std::ostream& operator<<(std::ostream& os, const Point& p) {
            os << "(" << p.x << "," << p.y << ")";
            return os;
        }
    };

    boost::container::small_vector<Point, 6> path;
    path.emplace_back(0.0f, 0.0f);
    path.emplace_back(1.0f, 0.0f);
    path.emplace_back(1.0f, 1.0f);
    path.emplace_back(0.0f, 1.0f);

    std::cout << "\nPath points:" << std::endl;
    for (const auto& point : path) {
        std::cout << "  " << point << std::endl;
    }

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Container small_vector 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_usage();
    memory_optimization();
    performance_comparison();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}