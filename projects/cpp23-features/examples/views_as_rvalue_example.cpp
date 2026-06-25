/**
 * @file views_as_rvalue_example.cpp
 * @brief C++23 std::views::as_rvalue 示例
 *
 * std::views::as_rvalue 是 C++23 引入的右值视图。
 * 它将范围中的元素视为右值，便于移动操作。
 *
 * 主要特点：
 * - 将范围元素视为右值
 * - 支持移动语义
 * - 适用于资源转移场景
 * - 提高性能
 *
 * 编译命令：
 * g++ -std=c++23 -o views_as_rvalue_example views_as_rvalue_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>
#include <memory>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<std::string> strings = {"Hello", "World", "C++23"};

    std::cout << "Original: ";
    for (const auto& s : strings) std::cout << s << " ";
    std::cout << std::endl;

    // 创建右值视图
    auto rvalue_view = strings | std::views::as_rvalue;

    // 移动元素
    std::vector<std::string> moved;
    for (auto&& s : rvalue_view) {
        moved.push_back(std::move(s));
    }

    std::cout << "Moved to: ";
    for (const auto& s : moved) std::cout << s << " ";
    std::cout << std::endl;

    std::cout << "Original after move: ";
    for (const auto& s : strings) std::cout << "[" << s << "] ";
    std::cout << std::endl;
}

// ========== 2. 实际应用：容器移动 ==========

void container_move() {
    std::cout << "\n=== 实际应用：容器移动 ===" << std::endl;

    std::vector<std::unique_ptr<int>> pointers;
    pointers.push_back(std::make_unique<int>(1));
    pointers.push_back(std::make_unique<int>(2));
    pointers.push_back(std::make_unique<int>(3));

    std::cout << "Original pointers: ";
    for (const auto& p : pointers) std::cout << *p << " ";
    std::cout << std::endl;

    // 使用右值视图移动 unique_ptr
    std::vector<std::unique_ptr<int>> moved;
    for (auto&& p : pointers | std::views::as_rvalue) {
        moved.push_back(std::move(p));
    }

    std::cout << "Moved pointers: ";
    for (const auto& p : moved) std::cout << *p << " ";
    std::cout << std::endl;
}

// ========== 3. 实际应用：数据转换 ==========

void data_transformation() {
    std::cout << "\n=== 实际应用：数据转换 ===" << std::endl;

    std::vector<std::string> names = {"Alice", "Bob", "Charlie"};

    // 转换为大写并移动
    auto uppercase = names
        | std::views::as_rvalue
        | std::views::transform([](std::string&& s) {
            std::transform(s.begin(), s.end(), s.begin(), ::toupper);
            return std::move(s);
        })
        | std::ranges::to<std::vector>();

    std::cout << "Uppercase: ";
    for (const auto& s : uppercase) std::cout << s << " ";
    std::cout << std::endl;
}

// ========== 4. 实际应用：资源转移 ==========

void resource_transfer() {
    std::cout << "\n=== 实际应用：资源转移 ===" << std::endl;

    // 模拟资源
    struct Resource {
        std::string name;
        int value;

        Resource(std::string n, int v) : name(std::move(n)), value(v) {}

        Resource(Resource&& other) noexcept
            : name(std::move(other.name)), value(other.value) {
            std::cout << "  Moving resource: " << name << std::endl;
        }
    };

    std::vector<Resource> resources;
    resources.emplace_back("Res1", 100);
    resources.emplace_back("Res2", 200);
    resources.emplace_back("Res3", 300);

    // 使用右值视图移动资源
    std::vector<Resource> transferred;
    for (auto&& r : resources | std::views::as_rvalue) {
        transferred.push_back(std::move(r));
    }

    std::cout << "Transferred resources:" << std::endl;
    for (const auto& r : transferred) {
        std::cout << "  " << r.name << ": " << r.value << std::endl;
    }
}

// ========== 5. 实际应用：缓存系统 ==========

void cache_system() {
    std::cout << "\n=== 实际应用：缓存系统 ===" << std::endl;

    // 模拟缓存数据
    std::vector<std::string> cache = {"data1", "data2", "data3", "data4", "data5"};

    std::cout << "Cache before move: ";
    for (const auto& s : cache) std::cout << s << " ";
    std::cout << std::endl;

    // 移动缓存数据到处理队列
    std::vector<std::string> queue;
    for (auto&& item : cache | std::views::as_rvalue) {
        queue.push_back(std::move(item));
    }

    std::cout << "Queue: ";
    for (const auto& s : queue) std::cout << s << " ";
    std::cout << std::endl;

    std::cout << "Cache after move: ";
    for (const auto& s : cache) std::cout << "[" << s << "] ";
    std::cout << std::endl;
}

// ========== 6. 实际应用：管道处理 ==========

void pipeline_processing() {
    std::cout << "\n=== 实际应用：管道处理 ===" << std::endl;

    std::vector<std::string> input = {"hello", "world", "cpp", "twenty-three"};

    // 管道处理：转换 + 移动
    auto result = input
        | std::views::as_rvalue
        | std::views::transform([](std::string&& s) {
            // 转换为大写
            std::transform(s.begin(), s.end(), s.begin(), ::toupper);
            return std::move(s);
        })
        | std::views::filter([](const std::string& s) {
            return s.length() > 3;
        })
        | std::ranges::to<std::vector>();

    std::cout << "Pipeline result: ";
    for (const auto& s : result) std::cout << s << " ";
    std::cout << std::endl;
}

// ========== 7. 实际应用：数据迁移 ==========

void data_migration() {
    std::cout << "\n=== 实际应用：数据迁移 ===" << std::endl;

    // 模拟旧数据
    struct OldData {
        int id;
        std::string name;
        double value;

        OldData(int i, std::string n, double v)
            : id(i), name(std::move(n)), value(v) {}
    };

    // 模拟新数据结构
    struct NewData {
        int id;
        std::string name;
        double value;
        std::string timestamp;

        NewData(int i, std::string n, double v, std::string t)
            : id(i), name(std::move(n)), value(v), timestamp(std::move(t)) {}
    };

    std::vector<OldData> old_data;
    old_data.emplace_back(1, "Alice", 100.0);
    old_data.emplace_back(2, "Bob", 200.0);
    old_data.emplace_back(3, "Charlie", 300.0);

    // 迁移数据
    std::vector<NewData> new_data;
    for (auto&& old : old_data | std::views::as_rvalue) {
        new_data.emplace_back(
            old.id,
            std::move(old.name),
            old.value,
            "2024-01-01"
        );
    }

    std::cout << "Migrated data:" << std::endl;
    for (const auto& d : new_data) {
        std::cout << "  " << d.id << ": " << d.name << " = " << d.value
                  << " (" << d.timestamp << ")" << std::endl;
    }
}

// ========== 8. 实际应用：批处理 ==========

void batch_processing() {
    std::cout << "\n=== 实际应用：批处理 ===" << std::endl;

    std::vector<std::string> batch = {"task1", "task2", "task3", "task4", "task5"};

    std::cout << "Processing batch:" << std::endl;
    for (auto&& task : batch | std::views::as_rvalue) {
        std::cout << "  Processing: " << task << std::endl;
        // 处理任务
        // process(std::move(task));
    }
}

// ========== 9. 实际应用：事件处理 ==========

void event_handling() {
    std::cout << "\n=== 实际应用：事件处理 ===" << std::endl;

    struct Event {
        std::string type;
        std::string data;

        Event(std::string t, std::string d) : type(std::move(t)), data(std::move(d)) {}
    };

    std::vector<Event> events;
    events.emplace_back("click", "button1");
    events.emplace_back("keypress", "Enter");
    events.emplace_back("scroll", "down");

    // 处理事件
    std::cout << "Processing events:" << std::endl;
    for (auto&& event : events | std::views::as_rvalue) {
        std::cout << "  Event: " << event.type << " - " << event.data << std::endl;
        // 处理事件
        // handle_event(std::move(event));
    }
}

// ========== 10. 实际应用：数据序列化 ==========

void data_serialization() {
    std::cout << "\n=== 实际应用：数据序列化 ===" << std::endl;

    struct Record {
        int id;
        std::string name;
        std::vector<int> data;

        Record(int i, std::string n, std::vector<int> d)
            : id(i), name(std::move(n)), data(std::move(d)) {}
    };

    std::vector<Record> records;
    records.emplace_back(1, "Alice", std::vector<int>{1, 2, 3});
    records.emplace_back(2, "Bob", std::vector<int>{4, 5, 6});

    // 序列化 (移动数据)
    std::cout << "Serializing records:" << std::endl;
    for (auto&& record : records | std::views::as_rvalue) {
        std::cout << "  Record " << record.id << ": " << record.name << std::endl;
        std::cout << "    Data: [";
        bool first = true;
        for (int d : record.data) {
            if (!first) std::cout << ", ";
            std::cout << d;
            first = false;
        }
        std::cout << "]" << std::endl;
        // serialize(std::move(record));
    }
}

int main() {
    std::cout << "C++23 std::views::as_rvalue 示例\n" << std::endl;

    basic_usage();
    container_move();
    data_transformation();
    resource_transfer();
    cache_system();
    pipeline_processing();
    data_migration();
    batch_processing();
    event_handling();
    data_serialization();

    return 0;
}
