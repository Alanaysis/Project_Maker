#pragma once

/**
 * @file heterogeneous.h
 * @brief 异构计算框架主头文件
 *
 * 包含此头文件即可使用完整的异构计算框架功能。
 *
 * 使用示例:
 * ```cpp
 * #include <heterogeneous/heterogeneous.h>
 *
 * using namespace heterogeneous;
 *
 * int main() {
 *     // 初始化框架
 *     auto& device_manager = DeviceManager::instance();
 *     device_manager.initialize();
 *
 *     // 创建任务
 *     auto& task_manager = TaskManager::instance();
 *     auto task = task_manager.create_task("my_task", [](const void*, void*, size_t, const DeviceInfo*) {
 *         // 计算逻辑
 *     });
 *
 *     // 执行任务
 *     task->execute();
 *
 *     // 清理
 *     device_manager.shutdown();
 *     return 0;
 * }
 * ```
 */

// 核心定义
#include "core.h"

// 任务管理
#include "task.h"

// 设备管理
#include "device.h"

// 内存管理
#include "memory.h"

// 任务调度
#include "scheduler.h"

// 任务执行
#include "executor.h"

// 工具类
#include "../utils/timer.h"

/**
 * @namespace heterogeneous
 * @brief 异构计算框架命名空间
 */
namespace heterogeneous {

/**
 * @brief 框架初始化
 *
 * 初始化框架的所有组件，包括设备管理器、内存管理器等。
 *
 * @return true 如果初始化成功
 */
inline bool initialize() {
    auto& device_manager = DeviceManager::instance();
    auto& memory_manager = MemoryManager::instance();

    if (!device_manager.initialize()) {
        return false;
    }

    if (!memory_manager.initialize()) {
        return false;
    }

    return true;
}

/**
 * @brief 框架关闭
 *
 * 关闭框架的所有组件，释放资源。
 */
inline void shutdown() {
    MemoryManager::instance().shutdown();
    DeviceManager::instance().shutdown();
}

/**
 * @brief 获取框架版本
 */
inline std::string version() {
    return Version::to_string();
}

/**
 * @brief 获取框架状态
 */
inline FrameworkStatus status() {
    return FrameworkStatus::Ready;
}

} // namespace heterogeneous
