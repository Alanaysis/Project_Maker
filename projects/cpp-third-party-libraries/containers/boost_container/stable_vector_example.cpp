/**
 * @file stable_vector_example.cpp
 * @brief Boost.Container stable_vector 示例
 * @details 展示 boost::container::stable_vector 的使用方法
 *          stable_vector 提供稳定的迭代器和引用
 *          即使插入/删除元素，已有元素的指针和引用仍然有效
 */

#include <iostream>
#include <string>
#include <boost/container/stable_vector.hpp>

/**
 * @brief 基础用法示例
 * @details 展示 stable_vector 的基本操作
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 stable_vector
    boost::container::stable_vector<int> vec = {1, 2, 3, 4, 5};

    // 遍历
    std::cout << "Elements: ";
    for (const auto& elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    // 添加元素
    vec.push_back(6);
    vec.insert(vec.begin() + 2, 10);

    std::cout << "After insert: ";
    for (const auto& elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 迭代器稳定性示例
 * @details 展示 stable_vector 的迭代器稳定性
 */
void iterator_stability() {
    std::cout << "=== 迭代器稳定性 ===" << std::endl;

    boost::container::stable_vector<int> vec = {1, 2, 3, 4, 5};

    // 获取迭代器
    auto it = vec.begin() + 2;  // 指向元素 3
    std::cout << "Before insert: *it = " << *it << std::endl;

    // 在前面插入元素
    vec.insert(vec.begin(), 0);

    // 迭代器仍然有效
    std::cout << "After insert: *it = " << *it << " (still valid)" << std::endl;

    // 获取指针
    int* ptr = &vec[2];
    std::cout << "Before erase: *ptr = " << *ptr << std::endl;

    // 删除其他元素
    vec.erase(vec.begin());

    // 指针仍然有效
    std::cout << "After erase: *ptr = " << *ptr << " (still valid)" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 与 std::vector 对比
 * @details 展示 stable_vector 与 std::vector 的差异
 */
void comparison_with_vector() {
    std::cout << "=== 与 std::vector 对比 ===" << std::endl;

    std::cout << "stable_vector 特点:" << std::endl;
    std::cout << "  - 迭代器和引用在插入/删除后仍然有效" << std::endl;
    std::cout << "  - 不会因为扩容而移动元素" << std::endl;
    std::cout << "  - 每个元素单独分配内存" << std::endl;

    std::cout << std::endl;

    std::cout << "使用场景:" << std::endl;
    std::cout << "  - 需要稳定引用的场景" << std::endl;
    std::cout << "  - 元素较大，移动成本高" << std::endl;
    std::cout << "  - 频繁插入/删除的场景" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 stable_vector 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：任务队列，任务之间有依赖关系
    struct Task {
        int id;
        std::string name;
        bool completed;

        Task(int id, const std::string& name)
            : id(id), name(name), completed(false) {}
    };

    boost::container::stable_vector<Task> tasks;
    tasks.emplace_back(1, "Task A");
    tasks.emplace_back(2, "Task B");
    tasks.emplace_back(3, "Task C");

    // 保存任务引用
    Task* task_b = &tasks[1];

    // 添加新任务
    tasks.emplace_back(4, "Task D");

    // 原有引用仍然有效
    std::cout << "Task B: " << task_b->name
              << " (id=" << task_b->id << ")" << std::endl;

    // 完成任务
    task_b->completed = true;
    std::cout << "Task B completed: "
              << (task_b->completed ? "Yes" : "No") << std::endl;

    // 遍历所有任务
    std::cout << "\nAll tasks:" << std::endl;
    for (const auto& task : tasks) {
        std::cout << "  " << task.id << ": " << task.name
                  << " [" << (task.completed ? "Done" : "Pending") << "]"
                  << std::endl;
    }

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Container stable_vector 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_usage();
    iterator_stability();
    comparison_with_vector();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}