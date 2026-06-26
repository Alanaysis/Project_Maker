/**
 * @file example_basic.c
 * @brief 示例 1: 任务创建和调度
 *
 * 本示例演示 RTOS 的基本功能：
 * 1. 创建多个任务
 * 2. 观察任务调度顺序
 * 3. 理解优先级调度的工作原理
 *
 * 学习要点：
 * - 高优先级任务会抢占低优先级任务
 * - 相同优先级的任务轮流执行（轮转调度）
 * - 任务通过 rtos_delay() 让出 CPU
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "../include/rtos.h"

/* ==================== 任务函数 ==================== */

/**
 * 任务 A：高优先级任务
 *
 * 由于优先级最高，它会在大多数时间运行。
 * 每次运行后延时 5 ticks，给其他任务机会。
 */
void task_a_entry(void *arg)
{
    (void)arg;
    uint32_t count = 0;

    printf("\n[任务 A] 启动 (优先级: 10)\n");

    while (1) {
        count++;
        printf("[任务 A] 运行计数: %lu (系统 tick: %lu)\n",
               (unsigned long)count,
               (unsigned long)rtos_get_tick_count());

        /* 延时 5 个 tick，让出 CPU */
        rtos_delay(5);
    }
}

/**
 * 任务 B：中优先级任务
 *
 * 优先级低于 A，高于 C。
 * 当 A 延时时，B 有机会运行。
 */
void task_b_entry(void *arg)
{
    (void)arg;
    uint32_t count = 0;

    printf("\n[任务 B] 启动 (优先级: 20)\n");

    while (1) {
        count++;
        printf("[任务 B] 运行计数: %lu (系统 tick: %lu)\n",
               (unsigned long)count,
               (unsigned long)rtos_get_tick_count());

        /* 延时 10 个 tick */
        rtos_delay(10);
    }
}

/**
 * 任务 C：低优先级任务
 *
 * 优先级最低，只有在 A 和 B 都延时时才运行。
 */
void task_c_entry(void *arg)
{
    (void)arg;
    uint32_t count = 0;

    printf("\n[任务 C] 启动 (优先级: 30)\n");

    while (1) {
        count++;
        printf("[任务 C] 运行计数: %lu (系统 tick: %lu)\n",
               (unsigned long)count,
               (unsigned long)rtos_get_tick_count());

        /* 延时 15 个 tick */
        rtos_delay(15);
    }
}

/* ==================== 主函数 ==================== */

int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  RTOS 内核学习示例 1: 任务创建与调度\n");
    printf("========================================\n\n");

    /* 内核初始化 */
    rtos_init();

    /* 创建任务 */
    rtos_task_create("TaskA", task_a_entry, NULL, 512, 10);  /* 高优先级 */
    rtos_task_create("TaskB", task_b_entry, NULL, 512, 20);  /* 中优先级 */
    rtos_task_create("TaskC", task_c_entry, NULL, 512, 30);  /* 低优先级 */

    /* 打印系统状态 */
    rtos_print_status();

    /* 启动调度器 */
    printf("=== 启动调度器 ===\n\n");
    rtos_start();

    /* 调度器永远不会返回 */
    return 0;
}
