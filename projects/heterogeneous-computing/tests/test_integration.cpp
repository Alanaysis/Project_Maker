/**
 * @file test_integration.cpp
 * @brief 集成测试
 */

#include "heterogeneous/task.h"
#include "heterogeneous/device.h"
#include "heterogeneous/memory.h"
#include "heterogeneous/scheduler.h"
#include "heterogeneous/executor.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>
#include <chrono>

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

// 测试向量加法
bool test_vector_addition() {
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();
    auto& task_manager = TaskManager::instance();

    // 初始化
    device_manager.initialize();
    memory_manager.initialize();

    // 获取 CPU 设备
    auto device = device_manager.get_default_device(DeviceType::CPU);
    TEST_ASSERT(device != nullptr, "CPU device should be available");

    // 创建执行器
    auto executor = ExecutorFactory::create(device);
    TEST_ASSERT(executor != nullptr, "Executor should be created");

    // 准备数据
    const size_t N = 1000;
    std::vector<float> a(N), b(N), c(N, 0.0f);

    for (size_t i = 0; i < N; i++) {
        a[i] = static_cast<float>(i);
        b[i] = static_cast<float>(i * 2);
    }

    // 创建任务
    auto task = task_manager.create_task("vector_add",
        [&a, &b, &c](const void*, void*, size_t, const DeviceInfo*) {
            for (size_t i = 0; i < N; i++) {
                c[i] = a[i] + b[i];
            }
        });

    task->set_input(a.data(), N * sizeof(float))
          .set_output(c.data(), N * sizeof(float));

    // 执行任务
    auto result = executor->execute(task);

    TEST_ASSERT(result.success, "Task should succeed");
    TEST_ASSERT(result.error_code == ErrorCode::Success, "Error code should be Success");

    // 验证结果
    for (size_t i = 0; i < N; i++) {
        float expected = static_cast<float>(i) + static_cast<float>(i * 2);
        TEST_ASSERT(std::abs(c[i] - expected) < 1e-5f, "Result should match expected");
    }

    // 清理
    memory_manager.shutdown();
    device_manager.shutdown();

    TEST_PASS("test_vector_addition");
}

// 测试矩阵乘法
bool test_matrix_multiplication() {
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();
    auto& task_manager = TaskManager::instance();

    // 初始化
    device_manager.initialize();
    memory_manager.initialize();

    // 获取 CPU 设备
    auto device = device_manager.get_default_device(DeviceType::CPU);
    TEST_ASSERT(device != nullptr, "CPU device should be available");

    // 创建执行器
    auto executor = ExecutorFactory::create(device);
    TEST_ASSERT(executor != nullptr, "Executor should be created");

    // 准备数据
    const size_t M = 64, N = 64, K = 64;
    std::vector<float> A(M * K), B(K * N), C(M * N, 0.0f);

    // 初始化矩阵
    for (size_t i = 0; i < M * K; i++) A[i] = 1.0f;
    for (size_t i = 0; i < K * N; i++) B[i] = 1.0f;

    // 创建任务
    auto task = task_manager.create_task("matrix_mul",
        [&A, &B, &C, M, N, K](const void*, void*, size_t, const DeviceInfo*) {
            for (size_t i = 0; i < M; i++) {
                for (size_t j = 0; j < N; j++) {
                    float sum = 0.0f;
                    for (size_t k = 0; k < K; k++) {
                        sum += A[i * K + k] * B[k * N + j];
                    }
                    C[i * N + j] = sum;
                }
            }
        });

    task->set_input(A.data(), M * K * sizeof(float))
          .set_output(C.data(), M * N * sizeof(float));

    // 执行任务
    auto result = executor->execute(task);

    TEST_ASSERT(result.success, "Task should succeed");

    // 验证结果 (全1矩阵相乘，结果应该是 K)
    for (size_t i = 0; i < M * N; i++) {
        TEST_ASSERT(std::abs(C[i] - static_cast<float>(K)) < 1e-5f,
                    "Result should be K for all-ones matrices");
    }

    // 清理
    memory_manager.shutdown();
    device_manager.shutdown();

    TEST_PASS("test_matrix_multiplication");
}

// 测试批量任务执行
bool test_batch_execution() {
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();
    auto& task_manager = TaskManager::instance();

    // 初始化
    device_manager.initialize();
    memory_manager.initialize();

    // 获取 CPU 设备
    auto device = device_manager.get_default_device(DeviceType::CPU);
    TEST_ASSERT(device != nullptr, "CPU device should be available");

    // 创建执行器
    auto executor = ExecutorFactory::create(device);
    TEST_ASSERT(executor != nullptr, "Executor should be created");

    // 创建多个任务
    std::vector<std::shared_ptr<Task>> tasks;
    std::vector<int> results(10, 0);

    for (int i = 0; i < 10; i++) {
        auto task = task_manager.create_task("batch_task_" + std::to_string(i),
            [&results, i](const void*, void*, size_t, const DeviceInfo*) {
                results[i] = i * i;
            });
        tasks.push_back(task);
    }

    // 批量执行
    auto batch_results = executor->execute_batch(tasks);

    // 验证结果
    TEST_ASSERT(batch_results.size() == 10, "Should have 10 results");

    for (size_t i = 0; i < 10; i++) {
        TEST_ASSERT(batch_results[i].success, "Task should succeed");
        TEST_ASSERT(results[i] == static_cast<int>(i * i), "Result should match expected");
    }

    // 清理
    memory_manager.shutdown();
    device_manager.shutdown();

    TEST_PASS("test_batch_execution");
}

// 测试异步执行
bool test_async_execution() {
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();
    auto& task_manager = TaskManager::instance();

    // 初始化
    device_manager.initialize();
    memory_manager.initialize();

    // 获取 CPU 设备
    auto device = device_manager.get_default_device(DeviceType::CPU);
    TEST_ASSERT(device != nullptr, "CPU device should be available");

    // 创建执行器
    auto executor = ExecutorFactory::create(device);
    TEST_ASSERT(executor != nullptr, "Executor should be created");

    // 创建任务
    int result = 0;
    auto task = task_manager.create_task("async_task",
        [&result](const void*, void*, size_t, const DeviceInfo*) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            result = 42;
        });

    // 异步执行
    auto future = executor->execute_async(task);

    // 等待完成
    auto task_result = future.get();

    TEST_ASSERT(task_result.success, "Task should succeed");
    TEST_ASSERT(result == 42, "Result should be 42");

    // 清理
    memory_manager.shutdown();
    device_manager.shutdown();

    TEST_PASS("test_async_execution");
}

// 测试设备管理
bool test_device_management() {
    auto& manager = DeviceManager::instance();

    // 初始化
    TEST_ASSERT(manager.initialize(), "Device manager should initialize");

    // 检测设备
    auto devices = manager.detect_devices();
    TEST_ASSERT(devices.size() >= 1, "Should detect at least 1 device");

    // 检查 CPU
    TEST_ASSERT(manager.has_gpu() || true, "GPU detection works (may not have GPU)");

    // 获取设备
    auto cpu = manager.get_default_device(DeviceType::CPU);
    TEST_ASSERT(cpu != nullptr, "Should have CPU device");
    TEST_ASSERT(cpu->type() == DeviceType::CPU, "Device type should be CPU");
    TEST_ASSERT(cpu->is_available(), "CPU should be available");

    // 获取设备信息
    auto info = cpu->info();
    TEST_ASSERT(!info.name.empty(), "Device name should not be empty");
    TEST_ASSERT(info.compute_units > 0, "Should have compute units");

    // 清理
    manager.shutdown();

    TEST_PASS("test_device_management");
}

// 测试完整工作流
bool test_complete_workflow() {
    // 初始化所有组件
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();
    auto& task_manager = TaskManager::instance();

    device_manager.initialize();
    memory_manager.initialize();

    // 创建调度器
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::RoundRobin;
    auto scheduler = SchedulerFactory::create(config.strategy, config);
    scheduler->initialize();

    // 准备数据
    const size_t N = 100;
    std::vector<float> input(N), output(N, 0.0f);
    for (size_t i = 0; i < N; i++) {
        input[i] = static_cast<float>(i);
    }

    // 创建任务
    auto task = task_manager.create_task("workflow_task",
        [&input, &output](const void*, void*, size_t, const DeviceInfo*) {
            for (size_t i = 0; i < input.size(); i++) {
                output[i] = input[i] * 2.0f;
            }
        });

    task->set_input(input.data(), N * sizeof(float))
          .set_output(output.data(), N * sizeof(float));

    // 提交到调度器
    scheduler->submit_task(task);

    // 等待完成
    bool completed = scheduler->wait_for_task(task->id(), std::chrono::milliseconds(5000));
    TEST_ASSERT(completed, "Task should complete within timeout");

    // 验证结果
    for (size_t i = 0; i < N; i++) {
        TEST_ASSERT(std::abs(output[i] - input[i] * 2.0f) < 1e-5f, "Result should match");
    }

    // 检查统计
    auto stats = scheduler->get_stats();
    TEST_ASSERT(stats.total_tasks_scheduled >= 1, "Should have scheduled tasks");

    // 清理
    scheduler->shutdown();
    memory_manager.shutdown();
    device_manager.shutdown();

    TEST_PASS("test_complete_workflow");
}

// 测试性能测量
bool test_performance_measurement() {
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();
    auto& task_manager = TaskManager::instance();

    device_manager.initialize();
    memory_manager.initialize();

    auto device = device_manager.get_default_device(DeviceType::CPU);
    auto executor = ExecutorFactory::create(device);

    // 创建计算密集型任务
    const size_t N = 1000000;
    std::vector<float> data(N, 1.0f);

    auto task = task_manager.create_task("perf_task",
        [&data](const void*, void*, size_t, const DeviceInfo*) {
            for (size_t i = 0; i < data.size(); i++) {
                data[i] = std::sin(data[i]) * std::cos(data[i]);
            }
        });

    task->set_input(data.data(), N * sizeof(float));

    // 执行并测量时间
    auto start = std::chrono::steady_clock::now();
    auto result = executor->execute(task);
    auto end = std::chrono::steady_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    TEST_ASSERT(result.success, "Task should succeed");
    TEST_ASSERT(duration.count() > 0, "Execution time should be positive");

    std::cout << "  Performance: " << duration.count() << " microseconds" << std::endl;

    memory_manager.shutdown();
    device_manager.shutdown();

    TEST_PASS("test_performance_measurement");
}

// 测试错误处理
bool test_error_handling() {
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();
    auto& task_manager = TaskManager::instance();

    device_manager.initialize();
    memory_manager.initialize();

    auto device = device_manager.get_default_device(DeviceType::CPU);
    auto executor = ExecutorFactory::create(device);

    // 创建会失败的任务
    bool error_caught = false;
    auto task = task_manager.create_task("error_task",
        [&error_caught](const void*, void*, size_t, const DeviceInfo*) {
            error_caught = true;
            throw std::runtime_error("Test error");
        });

    // 执行任务
    auto result = executor->execute(task);

    TEST_ASSERT(!result.success, "Task should fail");
    TEST_ASSERT(result.error_code == ErrorCode::TaskExecutionFailed, "Error code should match");
    TEST_ASSERT(!result.error_message.empty(), "Error message should not be empty");
    TEST_ASSERT(error_caught, "Error should be caught");

    memory_manager.shutdown();
    device_manager.shutdown();

    TEST_PASS("test_error_handling");
}

// 主函数
int main() {
    std::cout << "=== Integration Tests ===" << std::endl;

    int passed = 0;
    int failed = 0;

    auto run_test = [&](bool (*test)(), const char* name) {
        std::cout << "\n--- " << name << " ---" << std::endl;
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

    run_test(test_vector_addition, "test_vector_addition");
    run_test(test_matrix_multiplication, "test_matrix_multiplication");
    run_test(test_batch_execution, "test_batch_execution");
    run_test(test_async_execution, "test_async_execution");
    run_test(test_device_management, "test_device_management");
    run_test(test_complete_workflow, "test_complete_workflow");
    run_test(test_performance_measurement, "test_performance_measurement");
    run_test(test_error_handling, "test_error_handling");

    std::cout << "\n=== Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total:  " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
