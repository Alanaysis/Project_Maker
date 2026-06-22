/**
 * @file test_task.cpp
 * @brief 任务管理器测试
 */

#include "heterogeneous/task.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>

using namespace heterogeneous;

// 测试辅助函数
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            std::cerr << "FAIL: " << message << " (" << __FILE__ << ":" << __LINE__ << ")" << std::endl; \
            return false; \
        } \
    } while(0)

#define TEST_PASS(test_name) \
    std::cout << "PASS: " << test_name << std::endl; \
    return true;

// 测试任务创建
bool test_task_creation() {
    auto& manager = TaskManager::instance();

    // 创建简单任务
    auto task = manager.create_task("test_task", [](const void* in, void* out, size_t size, const DeviceInfo*) {
        // 简单的复制任务
        if (in && out && size > 0) {
            std::memcpy(out, in, size);
        }
    });

    TEST_ASSERT(task != nullptr, "Task should be created");
    TEST_ASSERT(task->name() == "test_task", "Task name should match");
    TEST_ASSERT(task->status() == TaskStatus::Created, "Initial status should be Created");
    TEST_ASSERT(!task->id().empty(), "Task ID should not be empty");

    TEST_PASS("test_task_creation");
}

// 测试任务配置
bool test_task_configuration() {
    auto& manager = TaskManager::instance();

    int input = 42;
    int output = 0;

    auto task = manager.create_task("config_task", [](const void* in, void* out, size_t size, const DeviceInfo*) {
        if (in && out && size >= sizeof(int)) {
            *static_cast<int*>(out) = *static_cast<const int*>(in);
        }
    });

    // 配置任务
    task->set_input(&input, sizeof(int))
          .set_output(&output, sizeof(int))
          .prefer_device(DeviceType::CPU)
          .set_priority(TaskPriority::High);

    TEST_ASSERT(task->input_data() == &input, "Input data should match");
    TEST_ASSERT(task->output_data() == &output, "Output data should match");
    TEST_ASSERT(task->data_size() == sizeof(int), "Data size should match");
    TEST_ASSERT(task->preferred_device() == DeviceType::CPU, "Preferred device should match");
    TEST_ASSERT(task->priority() == TaskPriority::High, "Priority should match");

    TEST_PASS("test_task_configuration");
}

// 测试任务执行
bool test_task_execution() {
    auto& manager = TaskManager::instance();

    std::vector<float> input = {1.0f, 2.0f, 3.0f, 4.0f};
    std::vector<float> output(4, 0.0f);

    auto task = manager.create_task("exec_task", [](const void* in, void* out, size_t size, const DeviceInfo*) {
        const float* input = static_cast<const float*>(in);
        float* output = static_cast<float*>(out);
        size_t count = size / sizeof(float);

        for (size_t i = 0; i < count; i++) {
            output[i] = input[i] * 2.0f;
        }
    });

    task->set_input(input.data(), input.size() * sizeof(float))
          .set_output(output.data(), output.size() * sizeof(float));

    // 执行任务
    task->execute();

    TEST_ASSERT(task->status() == TaskStatus::Completed, "Task should complete successfully");
    TEST_ASSERT(output[0] == 2.0f, "Output[0] should be 2.0");
    TEST_ASSERT(output[1] == 4.0f, "Output[1] should be 4.0");
    TEST_ASSERT(output[2] == 6.0f, "Output[2] should be 6.0");
    TEST_ASSERT(output[3] == 8.0f, "Output[3] should be 8.0");

    TEST_PASS("test_task_execution");
}

// 测试任务依赖
bool test_task_dependencies() {
    auto& manager = TaskManager::instance();

    auto task1 = manager.create_task("dep_task_1", [](const void*, void*, size_t, const DeviceInfo*) {});
    auto task2 = manager.create_task("dep_task_2", [](const void*, void*, size_t, const DeviceInfo*) {});

    // 添加依赖
    task2->add_dependency(task1->id());

    TEST_ASSERT(task2->dependencies().size() == 1, "Task2 should have 1 dependency");
    TEST_ASSERT(task2->dependencies()[0] == task1->id(), "Dependency should match task1 ID");

    TEST_PASS("test_task_dependencies");
}

// 测试任务回调
bool test_task_callbacks() {
    auto& manager = TaskManager::instance();

    bool complete_called = false;
    bool error_called = false;

    auto task = manager.create_task("callback_task", [](const void*, void*, size_t, const DeviceInfo*) {
        // 正常完成
    });

    task->on_complete([&complete_called](const Task&) {
        complete_called = true;
    });

    task->on_error([&error_called](const Task&, const std::exception&) {
        error_called = true;
    });

    // 执行任务
    task->execute();

    TEST_ASSERT(complete_called, "Complete callback should be called");
    TEST_ASSERT(!error_called, "Error callback should not be called");

    TEST_PASS("test_task_callbacks");
}

// 测试任务错误处理
bool test_task_error_handling() {
    auto& manager = TaskManager::instance();

    bool error_called = false;
    std::string error_message;

    auto task = manager.create_task("error_task", [](const void*, void*, size_t, const DeviceInfo*) {
        throw std::runtime_error("Test error");
    });

    task->on_error([&error_called, &error_message](const Task&, const std::exception& e) {
        error_called = true;
        error_message = e.what();
    });

    // 执行任务
    try {
        task->execute();
    } catch (const std::exception&) {
        // 预期异常
    }

    TEST_ASSERT(task->status() == TaskStatus::Failed, "Task should fail");
    TEST_ASSERT(error_called, "Error callback should be called");
    TEST_ASSERT(error_message == "Test error", "Error message should match");

    TEST_PASS("test_task_error_handling");
}

// 测试任务管理器
bool test_task_manager() {
    auto& manager = TaskManager::instance();

    // 创建多个任务
    auto task1 = manager.create_task("mgr_task_1", [](const void*, void*, size_t, const DeviceInfo*) {});
    auto task2 = manager.create_task("mgr_task_2", [](const void*, void*, size_t, const DeviceInfo*) {});
    auto task3 = manager.create_task("mgr_task_3", [](const void*, void*, size_t, const DeviceInfo*) {});

    // 提交任务
    TEST_ASSERT(manager.submit_task(task1), "Task1 should be submitted");
    TEST_ASSERT(manager.submit_task(task2), "Task2 should be submitted");
    TEST_ASSERT(manager.submit_task(task3), "Task3 should be submitted");

    // 获取任务
    auto retrieved = manager.get_task(task1->id());
    TEST_ASSERT(retrieved == task1, "Retrieved task should match");

    // 获取任务列表
    auto tasks = manager.get_tasks(TaskStatus::Ready);
    TEST_ASSERT(tasks.size() >= 3, "Should have at least 3 ready tasks");

    TEST_PASS("test_task_manager");
}

// 测试任务状态转换
bool test_task_status_transitions() {
    auto& manager = TaskManager::instance();

    auto task = manager.create_task("status_task", [](const void*, void*, size_t, const DeviceInfo*) {});

    // 初始状态
    TEST_ASSERT(task->status() == TaskStatus::Created, "Initial status should be Created");

    // 转换到 Ready
    task->set_status(TaskStatus::Ready);
    TEST_ASSERT(task->status() == TaskStatus::Ready, "Status should be Ready");

    // 转换到 Running
    task->set_status(TaskStatus::Running);
    TEST_ASSERT(task->status() == TaskStatus::Running, "Status should be Running");

    // 转换到 Completed
    task->set_status(TaskStatus::Completed);
    TEST_ASSERT(task->status() == TaskStatus::Completed, "Status should be Completed");

    TEST_PASS("test_task_status_transitions");
}

// 主函数
int main() {
    std::cout << "=== Task Manager Tests ===" << std::endl;

    int passed = 0;
    int failed = 0;

    auto run_test = [&](bool (*test)(), const char* name) {
        try {
            if (test()) {
                passed++;
            } else {
                failed++;
            }
        } catch (const std::exception& e) {
            std::cerr << "EXCEPTION in " << name << ": " << e.what() << std::endl;
            failed++;
        }
    };

    run_test(test_task_creation, "test_task_creation");
    run_test(test_task_configuration, "test_task_configuration");
    run_test(test_task_execution, "test_task_execution");
    run_test(test_task_dependencies, "test_task_dependencies");
    run_test(test_task_callbacks, "test_task_callbacks");
    run_test(test_task_error_handling, "test_task_error_handling");
    run_test(test_task_manager, "test_task_manager");
    run_test(test_task_status_transitions, "test_task_status_transitions");

    std::cout << "\n=== Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total:  " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
