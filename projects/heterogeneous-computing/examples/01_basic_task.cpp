/**
 * @file 01_basic_task.cpp
 * @brief 基本任务示例
 *
 * 本示例展示如何创建和执行基本的计算任务。
 *
 * 学习目标:
 * - 理解任务的创建和配置
 * - 掌握任务的执行流程
 * - 了解任务状态管理
 */

#include <heterogeneous/task.h>
#include <heterogeneous/device.h>
#include <iostream>
#include <vector>
#include <cmath>

using namespace heterogeneous;

int main() {
    std::cout << "=== 基本任务示例 ===" << std::endl;
    std::cout << std::endl;

    // 1. 初始化设备管理器
    std::cout << "1. 初始化设备管理器..." << std::endl;
    auto& device_manager = DeviceManager::instance();
    if (!device_manager.initialize()) {
        std::cerr << "错误: 无法初始化设备管理器" << std::endl;
        return 1;
    }

    // 显示可用设备
    auto devices = device_manager.detect_devices();
    std::cout << "   检测到 " << devices.size() << " 个设备:" << std::endl;
    for (const auto& info : devices) {
        std::cout << "   - " << info.name
                  << " (" << device_type_name(info.type) << ")"
                  << ", 计算单元: " << info.compute_units
                  << std::endl;
    }
    std::cout << std::endl;

    // 2. 获取任务管理器
    std::cout << "2. 获取任务管理器..." << std::endl;
    auto& task_manager = TaskManager::instance();
    std::cout << "   任务管理器已就绪" << std::endl;
    std::cout << std::endl;

    // 3. 创建简单任务 - 向量缩放
    std::cout << "3. 创建向量缩放任务..." << std::endl;

    const size_t N = 10;
    std::vector<float> input(N), output(N, 0.0f);
    float scale = 2.0f;

    // 初始化输入数据
    for (size_t i = 0; i < N; i++) {
        input[i] = static_cast<float>(i);
    }

    // 创建任务
    auto task = task_manager.create_task("vector_scale",
        [&input, &output, scale, N](const void*, void*, size_t, const DeviceInfo*) {
            for (size_t i = 0; i < N; i++) {
                output[i] = input[i] * scale;
            }
        });

    // 配置任务
    task->set_input(input.data(), N * sizeof(float))
          .set_output(output.data(), N * sizeof(float))
          .prefer_device(DeviceType::CPU)
          .set_priority(TaskPriority::Normal);

    // 设置回调
    task->on_complete([](const Task& t) {
        std::cout << "   任务完成: " << t.name()
                  << " (耗时: " << t.execution_time().count() << " 微秒)"
                  << std::endl;
    });

    task->on_error([](const Task& t, const std::exception& e) {
        std::cerr << "   任务失败: " << t.name()
                  << " (错误: " << e.what() << ")"
                  << std::endl;
    });

    std::cout << "   任务已创建: " << task->id() << std::endl;
    std::cout << std::endl;

    // 4. 执行任务
    std::cout << "4. 执行任务..." << std::endl;

    // 显示输入数据
    std::cout << "   输入: [";
    for (size_t i = 0; i < N; i++) {
        if (i > 0) std::cout << ", ";
        std::cout << input[i];
    }
    std::cout << "]" << std::endl;

    // 执行任务
    task->execute();

    // 显示输出数据
    std::cout << "   输出: [";
    for (size_t i = 0; i < N; i++) {
        if (i > 0) std::cout << ", ";
        std::cout << output[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 5. 验证结果
    std::cout << "5. 验证结果..." << std::endl;
    bool correct = true;
    for (size_t i = 0; i < N; i++) {
        float expected = input[i] * scale;
        if (std::abs(output[i] - expected) > 1e-5f) {
            correct = false;
            std::cerr << "   错误: output[" << i << "] = " << output[i]
                      << ", 期望: " << expected << std::endl;
        }
    }

    if (correct) {
        std::cout << "   结果正确!" << std::endl;
    }
    std::cout << std::endl;

    // 6. 显示任务信息
    std::cout << "6. 任务信息:" << std::endl;
    std::cout << "   任务 ID: " << task->id() << std::endl;
    std::cout << "   任务名称: " << task->name() << std::endl;
    std::cout << "   任务状态: " << task_status_name(task->status()) << std::endl;
    std::cout << "   执行时间: " << task->execution_time().count() << " 微秒" << std::endl;
    std::cout << "   使用设备: " << task->device_used() << std::endl;
    std::cout << std::endl;

    // 7. 清理
    std::cout << "7. 清理资源..." << std::endl;
    device_manager.shutdown();
    std::cout << "   完成!" << std::endl;

    return 0;
}
