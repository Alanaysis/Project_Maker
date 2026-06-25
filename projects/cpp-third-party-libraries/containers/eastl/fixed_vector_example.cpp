/**
 * @file fixed_vector_example.cpp
 * @brief EASTL fixed_vector 示例
 * @details 展示 EASTL 的 fixed_vector 使用方法
 *          EASTL 是 EA 游戏公司开发的容器库
 *          专为游戏开发优化
 */

#include <iostream>
#include <string>
#include <EASTL/vector.h>
#include <EASTL/fixed_vector.h>

/**
 * @brief 基础用法示例
 * @details 展示 fixed_vector 的基本操作
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 fixed_vector，预分配 10 个元素的空间
    eastl::fixed_vector<int, 10> vec;

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
 * @details 展示 fixed_vector 的内存优化特性
 */
void memory_optimization() {
    std::cout << "=== 内存优化 ===" << std::endl;

    // 小对象场景：使用栈内存
    eastl::fixed_vector<int, 5> small_vec;
    std::cout << "Small vector (size=3):" << std::endl;
    std::cout << "  Size: " << small_vec.size() << std::endl;

    // 添加少量元素
    for (int i = 0; i < 3; ++i) {
        small_vec.push_back(i);
    }

    // 大对象场景：自动切换到堆内存
    eastl::fixed_vector<int, 5> large_vec;
    std::cout << "Large vector (size=10):" << std::endl;

    for (int i = 0; i < 10; ++i) {
        large_vec.push_back(i);
    }
    std::cout << "  Size: " << large_vec.size() << std::endl;
    std::cout << "  Capacity: " << large_vec.capacity() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 性能特点示例
 * @details 展示 EASTL 的性能优势
 */
void performance_features() {
    std::cout << "=== 性能特点 ===" << std::endl;

    std::cout << "EASTL 优势：" << std::endl;
    std::cout << "  - 游戏开发优化" << std::endl;
    std::cout << "  - 内存分配器支持" << std::endl;
    std::cout << "  - 缓存友好" << std::endl;
    std::cout << "  - 可预测的性能" << std::endl;

    std::cout << std::endl;

    std::cout << "适用场景：" << std::endl;
    std::cout << "  - 游戏开发" << std::endl;
    std::cout << "  - 实时系统" << std::endl;
    std::cout << "  - 嵌入式系统" << std::endl;
    std::cout << "  - 性能敏感应用" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 EASTL 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：游戏对象管理
    struct GameObject {
        int id;
        std::string name;
        float x, y, z;

        GameObject(int id, const std::string& name, float x, float y, float z)
            : id(id), name(name), x(x), y(y), z(z) {}
    };

    eastl::fixed_vector<GameObject, 100> objects;
    objects.emplace_back(1, "Player", 0.0f, 0.0f, 0.0f);
    objects.emplace_back(2, "Enemy", 10.0f, 0.0f, 5.0f);
    objects.emplace_back(3, "Item", 5.0f, 0.0f, 3.0f);

    std::cout << "Game objects:" << std::endl;
    for (const auto& obj : objects) {
        std::cout << "  " << obj.name << " at (" << obj.x << ", " << obj.y << ", " << obj.z << ")" << std::endl;
    }

    std::cout << std::endl;
}

int main() {
    std::cout << "=== EASTL fixed_vector 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_usage();
    memory_optimization();
    performance_features();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}