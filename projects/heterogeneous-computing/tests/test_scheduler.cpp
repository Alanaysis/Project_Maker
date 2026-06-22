/**
 * @file test_scheduler.cpp
 * @brief 调度器测试
 */

#include "heterogeneous/scheduler.h"
#include "heterogeneous/task.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <thread>
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

// 测试轮询调度器
bool test_round_robin_scheduler() {
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::RoundRobin;
    auto scheduler = SchedulerFactory::create(config.strategy, config);

    TEST_ASSERT(scheduler != nullptr, "Scheduler should be created");

    // 初始化调度器
    TEST_ASSERT(scheduler->initialize(), "Scheduler should initialize");

    // 创建任务
    auto& manager = TaskManager::instance();
    auto task = manager.create_task("rr_task", [](const void*, void*, size_t, const DeviceInfo*) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    });

    // 提交任务
    TEST_ASSERT(scheduler->submit_task(task), "Task should be submitted");

    // 等待完成
    bool completed = scheduler->wait_for_task(task->id(), std::chrono::milliseconds(1000));
    TEST_ASSERT(completed, "Task should complete within timeout");

    // 检查统计
    auto stats = scheduler->get_stats();
    TEST_ASSERT(stats.total_tasks_scheduled >= 1, "Should have scheduled at least 1 task");

    scheduler->shutdown();
    TEST_PASS("test_round_robin_scheduler");
}

// 测试负载均衡调度器
bool test_load_balancing_scheduler() {
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::LoadBalancing;
    auto scheduler = SchedulerFactory::create(config.strategy, config);

    TEST_ASSERT(scheduler != nullptr, "Scheduler should be created");
    TEST_ASSERT(scheduler->initialize(), "Scheduler should initialize");

    // 创建多个任务
    auto& manager = TaskManager::instance();
    std::vector<std::shared_ptr<Task>> tasks;

    for (int i = 0; i < 5; i++) {
        auto task = manager.create_task("lb_task_" + std::to_string(i),
            [](const void*, void*, size_t, const DeviceInfo*) {
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            });
        tasks.push_back(task);
    }

    // 提交所有任务
    for (auto& task : tasks) {
        TEST_ASSERT(scheduler->submit_task(task), "Task should be submitted");
    }

    // 等待所有任务完成
    scheduler->wait_for_all();

    // 检查统计
    auto stats = scheduler->get_stats();
    TEST_ASSERT(stats.total_tasks_scheduled >= 5, "Should have scheduled at least 5 tasks");

    scheduler->shutdown();
    TEST_PASS("test_load_balancing_scheduler");
}

// 测试优先级调度器
bool test_priority_scheduler() {
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::Priority;
    auto scheduler = SchedulerFactory::create(config.strategy, config);

    TEST_ASSERT(scheduler != nullptr, "Scheduler should be created");
    TEST_ASSERT(scheduler->initialize(), "Scheduler should initialize");

    auto& manager = TaskManager::instance();

    // 创建不同优先级的任务
    auto low_task = manager.create_task("low_task",
        [](const void*, void*, size_t, const DeviceInfo*) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        });
    low_task->set_priority(TaskPriority::Low);

    auto high_task = manager.create_task("high_task",
        [](const void*, void*, size_t, const DeviceInfo*) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        });
    high_task->set_priority(TaskPriority::High);

    // 提交任务 (低优先级先提交)
    scheduler->submit_task(low_task);
    scheduler->submit_task(high_task);

    // 等待完成
    scheduler->wait_for_all();

    scheduler->shutdown();
    TEST_PASS("test_priority_scheduler");
}

// 测试自适应调度器
bool test_adaptive_scheduler() {
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::Adaptive;
    auto scheduler = std::make_unique<AdaptiveScheduler>(config);

    TEST_ASSERT(scheduler != nullptr, "Scheduler should be created");
    TEST_ASSERT(scheduler->initialize(), "Scheduler should initialize");

    // 记录性能数据
    scheduler->record_performance("task_a", "cpu_0", std::chrono::microseconds{1000});
    scheduler->record_performance("task_a", "cpu_0", std::chrono::microseconds{1200});
    scheduler->record_performance("task_a", "cpu_0", std::chrono::microseconds{800});

    auto& manager = TaskManager::instance();
    auto task = manager.create_task("task_a",
        [](const void*, void*, size_t, const DeviceInfo*) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        });

    // 提交任务
    scheduler->submit_task(task);

    // 等待完成
    bool completed = scheduler->wait_for_task(task->id(), std::chrono::milliseconds(1000));
    TEST_ASSERT(completed, "Task should complete within timeout");

    scheduler->shutdown();
    TEST_PASS("test_adaptive_scheduler");
}

// 测试调度器配置
bool test_scheduler_config() {
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::RoundRobin;
    config.max_concurrent_tasks = 4;
    config.task_queue_size = 100;
    config.enable_task_reordering = true;
    config.enable_data_prefetch = true;
    config.cpu_load_threshold = 0.8;
    config.gpu_load_threshold = 0.9;
    config.task_timeout = std::chrono::milliseconds(5000);
    config.scheduling_interval = std::chrono::milliseconds(10);

    auto scheduler = SchedulerFactory::create(config.strategy, config);
    TEST_ASSERT(scheduler != nullptr, "Scheduler should be created");

    auto& scheduler_config = scheduler->config();
    TEST_ASSERT(scheduler_config.max_concurrent_tasks == 4, "Max concurrent tasks should match");
    TEST_ASSERT(scheduler_config.task_queue_size == 100, "Task queue size should match");
    TEST_ASSERT(scheduler_config.enable_task_reordering == true, "Task reordering should be enabled");

    TEST_PASS("test_scheduler_config");
}

// 测试调度器工厂
bool test_scheduler_factory() {
    // 测试各种调度策略
    SchedulerConfig config;

    auto rr = SchedulerFactory::create(SchedulingStrategy::RoundRobin, config);
    TEST_ASSERT(rr != nullptr, "RoundRobin scheduler should be created");

    auto lb = SchedulerFactory::create(SchedulingStrategy::LoadBalancing, config);
    TEST_ASSERT(lb != nullptr, "LoadBalancing scheduler should be created");

    auto pri = SchedulerFactory::create(SchedulingStrategy::Priority, config);
    TEST_ASSERT(pri != nullptr, "Priority scheduler should be created");

    auto ada = SchedulerFactory::create(SchedulingStrategy::Adaptive, config);
    TEST_ASSERT(ada != nullptr, "Adaptive scheduler should be created");

    TEST_PASS("test_scheduler_factory");
}

// 测试任务取消
bool test_task_cancellation() {
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::RoundRobin;
    auto scheduler = SchedulerFactory::create(config.strategy, config);

    TEST_ASSERT(scheduler->initialize(), "Scheduler should initialize");

    auto& manager = TaskManager::instance();

    // 创建一个长时间运行的任务
    auto task = manager.create_task("cancel_task",
        [](const void*, void*, size_t, const DeviceInfo*) {
            std::this_thread::sleep_for(std::chrono::seconds(10));
        });

    // 提交任务
    scheduler->submit_task(task);

    // 立即取消
    bool cancelled = scheduler->cancel_task(task->id());
    TEST_ASSERT(cancelled, "Task should be cancelled");

    scheduler->shutdown();
    TEST_PASS("test_task_cancellation");
}

// 测试调度统计
bool test_scheduling_stats() {
    SchedulerConfig config;
    config.strategy = SchedulingStrategy::RoundRobin;
    auto scheduler = SchedulerFactory::create(config.strategy, config);

    TEST_ASSERT(scheduler->initialize(), "Scheduler should initialize");

    auto& manager = TaskManager::instance();

    // 创建并提交多个任务
    for (int i = 0; i < 10; i++) {
        auto task = manager.create_task("stats_task_" + std::to_string(i),
            [](const void*, void*, size_t, const DeviceInfo*) {
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            });
        scheduler->submit_task(task);
    }

    // 等待所有任务完成
    scheduler->wait_for_all();

    // 检查统计
    auto stats = scheduler->get_stats();
    TEST_ASSERT(stats.total_tasks_scheduled >= 10, "Should have scheduled at least 10 tasks");

    scheduler->shutdown();
    TEST_PASS("test_scheduling_stats");
}

// 主函数
int main() {
    std::cout << "=== Scheduler Tests ===" << std::endl;

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

    run_test(test_round_robin_scheduler, "test_round_robin_scheduler");
    run_test(test_load_balancing_scheduler, "test_load_balancing_scheduler");
    run_test(test_priority_scheduler, "test_priority_scheduler");
    run_test(test_adaptive_scheduler, "test_adaptive_scheduler");
    run_test(test_scheduler_config, "test_scheduler_config");
    run_test(test_scheduler_factory, "test_scheduler_factory");
    run_test(test_task_cancellation, "test_task_cancellation");
    run_test(test_scheduling_stats, "test_scheduling_stats");

    std::cout << "\n=== Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total:  " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
