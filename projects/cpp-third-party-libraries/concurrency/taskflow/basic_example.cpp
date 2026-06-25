/**
 * @file basic_example.cpp
 * @brief Taskflow 任务并行框架基础示例
 * @details 展示 Taskflow 的基本用法
 *          Taskflow 是一个任务并行框架
 *          支持 DAG 调度、条件任务、动态任务
 */

#include <iostream>
#include <taskflow/taskflow.hpp>

/**
 * @brief 基础任务图示例
 * @details 展示如何创建和执行任务图
 */
void basic_taskflow() {
    std::cout << "=== 基础任务图 ===" << std::endl;

    tf::Taskflow taskflow;

    // 创建任务
    auto [A, B, C, D] = taskflow.emplace(
        []() { std::cout << "Task A" << std::endl; },
        []() { std::cout << "Task B" << std::endl; },
        []() { std::cout << "Task C" << std::endl; },
        []() { std::cout << "Task D" << std::endl; }
    );

    // 设置依赖关系：A -> B -> D, A -> C -> D
    A.precede(B, C);
    B.precede(D);
    C.precede(D);

    // 执行任务图
    tf::Executor executor;
    executor.run(taskflow).wait();

    std::cout << std::endl;
}

/**
 * @brief 带数据的任务示例
 * @details 展示任务之间如何传递数据
 */
void data_passing() {
    std::cout << "=== 数据传递 ===" << std::endl;

    tf::Taskflow taskflow;

    int result = 0;

    auto [A, B, C] = taskflow.emplace(
        [&result]() {
            result = 42;
            std::cout << "Task A: set result = " << result << std::endl;
        },
        [&result]() {
            result *= 2;
            std::cout << "Task B: result = " << result << std::endl;
        },
        [&result]() {
            std::cout << "Task C: final result = " << result << std::endl;
        }
    );

    A.precede(B);
    B.precede(C);

    tf::Executor executor;
    executor.run(taskflow).wait();

    std::cout << std::endl;
}

/**
 * @brief 条件任务示例
 * @details 展示如何使用条件任务
 */
void conditional_task() {
    std::cout << "=== 条件任务 ===" << std::endl;

    tf::Taskflow taskflow;

    int value = 42;

    auto [init, condition, branch_a, branch_b, end] = taskflow.emplace(
        [&value]() {
            value = 42;
            std::cout << "Init: value = " << value << std::endl;
        },
        [&value]() -> int {
            return value > 40 ? 0 : 1;
        },
        [&value]() {
            std::cout << "Branch A: value > 40" << std::endl;
        },
        [&value]() {
            std::cout << "Branch B: value <= 40" << std::endl;
        },
        []() {
            std::cout << "End" << std::endl;
        }
    );

    init.precede(condition);
    condition.precede(branch_a, branch_b);
    branch_a.precede(end);
    branch_b.precede(end);

    tf::Executor executor;
    executor.run(taskflow).wait();

    std::cout << std::endl;
}

/**
 * @brief 并行任务示例
 * @details 展示如何创建并行执行的任务
 */
void parallel_tasks() {
    std::cout << "=== 并行任务 ===" << std::endl;

    tf::Taskflow taskflow;

    auto [start, parallel1, parallel2, parallel3, end] = taskflow.emplace(
        []() { std::cout << "Start" << std::endl; },
        []() { std::cout << "Parallel 1" << std::endl; },
        []() { std::cout << "Parallel 2" << std::endl; },
        []() { std::cout << "Parallel 3" << std::endl; },
        []() { std::cout << "End" << std::endl; }
    );

    // 三个并行任务
    start.precede(parallel1, parallel2, parallel3);
    parallel1.precede(end);
    parallel2.precede(end);
    parallel3.precede(end);

    tf::Executor executor;
    executor.run(taskflow).wait();

    std::cout << std::endl;
}

/**
 * @brief Taskflow 概念说明
 * @details 介绍 Taskflow 的核心概念
 */
void taskflow_concepts() {
    std::cout << "=== Taskflow 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "核心概念：" << std::endl;
    std::cout << "  - Taskflow: 任务图定义" << std::endl;
    std::cout << "  - Task: 单个任务" << std::endl;
    std::cout << "  - Executor: 任务执行器" << std::endl;
    std::cout << "  - Dependency: 任务依赖" << std::endl;
    std::cout << std::endl;

    std::cout << "任务类型：" << std::endl;
    std::cout << "  - Regular task: 普通任务" << std::endl;
    std::cout << "  - Condition task: 条件任务" << std::endl;
    std::cout << "  - Module task: 模块任务" << std::endl;
    std::cout << "  - Dynamic task: 动态任务" << std::endl;
    std::cout << std::endl;

    std::cout << "优势：" << std::endl;
    std::cout << "  - 高效的任务调度" << std::endl;
    std::cout << "  - 支持复杂依赖关系" << std::endl;
    std::cout << "  - 自动并行化" << std::endl;
    std::cout << "  - 易于使用" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Taskflow 任务并行框架示例 ===" << std::endl;
    std::cout << std::endl;

    taskflow_concepts();
    basic_taskflow();
    data_passing();
    conditional_task();
    parallel_tasks();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}