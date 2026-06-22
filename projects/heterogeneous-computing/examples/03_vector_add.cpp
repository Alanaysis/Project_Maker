/**
 * @file 03_vector_add.cpp
 * @brief 向量加法示例
 *
 * 本示例展示如何实现向量加法，并演示 CPU/GPU 协同工作。
 *
 * 学习目标:
 * - 理解数据并行计算
 * - 掌握任务调度策略
 * - 了解负载均衡
 */

#include <heterogeneous/task.h>
#include <heterogeneous/device.h>
#include <heterogeneous/scheduler.h>
#include <utils/timer.h>
#include <iostream>
#include <vector>
#include <random>
#include <cmath>
#include <thread>
#include <chrono>

using namespace heterogeneous;
using namespace heterogeneous::utils;

// 向量加法内核
void vector_add(const float* a, const float* b, float* c, size_t n) {
    for (size_t i = 0; i < n; i++) {
        c[i] = a[i] + b[i];
    }
}

// 向量乘法内核
void vector_multiply(const float* a, const float* b, float* c, size_t n) {
    for (size_t i = 0; i < n; i++) {
        c[i] = a[i] * b[i];
    }
}

// 向量缩放内核
void vector_scale(const float* a, float* c, size_t n, float scale) {
    for (size_t i = 0; i < n; i++) {
        c[i] = a[i] * scale;
    }
}

int main() {
    std::cout << "=== 向量加法示例 ===" << std::endl;
    std::cout << std::endl;

    // 1. 初始化
    std::cout << "1. 初始化..." << std::endl;
    auto& device_manager = DeviceManager::instance();
    auto& task_manager = TaskManager::instance();

    if (!device_manager.initialize()) {
        std::cerr << "错误: 无法初始化设备管理器" << std::endl;
        return 1;
    }

    // 创建调度器
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::LoadBalancing;
    auto scheduler = SchedulerFactory::create(config.strategy, config);
    scheduler->initialize();

    std::cout << "   调度策略: 负载均衡" << std::endl;
    std::cout << std::endl;

    // 2. 准备数据
    std::cout << "2. 准备数据..." << std::endl;

    const size_t N = 1000000;  // 100万元素
    std::vector<float> a(N), b(N), c(N, 0.0f), d(N, 0.0f), e(N, 0.0f);

    // 初始化随机数据
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dist(-100.0f, 100.0f);

    for (size_t i = 0; i < N; i++) {
        a[i] = dist(gen);
        b[i] = dist(gen);
    }

    std::cout << "   向量大小: " << N << " 元素" << std::endl;
    std::cout << "   数据大小: " << (N * sizeof(float) * 2) / (1024 * 1024) << " MB" << std::endl;
    std::cout << std::endl;

    // 3. 创建多个任务
    std::cout << "3. 创建任务..." << std::endl;

    // 任务1: 向量加法
    auto add_task = task_manager.create_task("vector_add",
        [&a, &b, &c, N](const void*, void*, size_t, const DeviceInfo*) {
            vector_add(a.data(), b.data(), c.data(), N);
        });
    add_task->set_input(a.data(), N * sizeof(float))
             .set_output(c.data(), N * sizeof(float))
             .set_priority(TaskPriority::High);

    // 任务2: 向量乘法
    auto mul_task = task_manager.create_task("vector_multiply",
        [&a, &b, &d, N](const void*, void*, size_t, const DeviceInfo*) {
            vector_multiply(a.data(), b.data(), d.data(), N);
        });
    mul_task->set_input(a.data(), N * sizeof(float))
             .set_output(d.data(), N * sizeof(float))
             .set_priority(TaskPriority::Normal);

    // 任务3: 向量缩放
    auto scale_task = task_manager.create_task("vector_scale",
        [&a, &e, N](const void*, void*, size_t, const DeviceInfo*) {
            vector_scale(a.data(), e.data(), N, 2.0f);
        });
    scale_task->set_input(a.data(), N * sizeof(float))
               .set_output(e.data(), N * sizeof(float))
               .set_priority(TaskPriority::Low);

    std::cout << "   创建了 3 个任务:" << std::endl;
    std::cout << "   - 向量加法 (高优先级)" << std::endl;
    std::cout << "   - 向量乘法 (普通优先级)" << std::endl;
    std::cout << "   - 向量缩放 (低优先级)" << std::endl;
    std::cout << std::endl;

    // 4. 提交任务到调度器
    std::cout << "4. 提交任务到调度器..." << std::endl;

    Timer total_timer("Total", true);

    scheduler->submit_task(add_task);
    scheduler->submit_task(mul_task);
    scheduler->submit_task(scale_task);

    // 等待所有任务完成
    scheduler->wait_for_all();

    total_timer.stop();

    std::cout << "   所有任务已完成" << std::endl;
    std::cout << "   总执行时间: " << total_timer.elapsed_ms() << " ms" << std::endl;
    std::cout << std::endl;

    // 5. 验证结果
    std::cout << "5. 验证结果..." << std::endl;

    bool all_correct = true;

    // 验证加法
    for (size_t i = 0; i < N; i++) {
        float expected = a[i] + b[i];
        if (std::abs(c[i] - expected) > 1e-5f) {
            all_correct = false;
            std::cerr << "   加法错误: c[" << i << "] = " << c[i]
                      << ", 期望: " << expected << std::endl;
            break;
        }
    }

    // 验证乘法
    for (size_t i = 0; i < N; i++) {
        float expected = a[i] * b[i];
        if (std::abs(d[i] - expected) > 1e-5f) {
            all_correct = false;
            std::cerr << "   乘法错误: d[" << i << "] = " << d[i]
                      << ", 期望: " << expected << std::endl;
            break;
        }
    }

    // 验证缩放
    for (size_t i = 0; i < N; i++) {
        float expected = a[i] * 2.0f;
        if (std::abs(e[i] - expected) > 1e-5f) {
            all_correct = false;
            std::cerr << "   缩放错误: e[" << i << "] = " << e[i]
                      << ", 期望: " << expected << std::endl;
            break;
        }
    }

    if (all_correct) {
        std::cout << "   所有结果正确!" << std::endl;
    }
    std::cout << std::endl;

    // 6. 性能统计
    std::cout << "6. 性能统计:" << std::endl;

    auto stats = scheduler->get_stats();
    std::cout << "   总调度任务: " << stats.total_tasks_scheduled << std::endl;
    std::cout << "   CPU 任务: " << stats.tasks_on_cpu << std::endl;
    std::cout << "   GPU 任务: " << stats.tasks_on_gpu << std::endl;

    // 计算吞吐量
    double total_elements = N * 3;  // 3个任务
    double throughput = total_elements / (total_timer.elapsed_sec() * 1e6);
    std::cout << "   吞吐量: " << throughput << " MElements/s" << std::endl;
    std::cout << std::endl;

    // 7. 清理
    std::cout << "7. 清理资源..." << std::endl;
    scheduler->shutdown();
    device_manager.shutdown();
    std::cout << "   完成!" << std::endl;

    return 0;
}
