/**
 * @file example_semaphore.c
 * @brief 示例 2: 信号量同步
 *
 * 本示例演示如何使用信号量进行任务同步：
 * 1. 二值信号量：事件通知
 * 2. 计数信号量：资源计数
 * 3. 信号量在 producer-consumer 模式中的应用
 *
 * 学习要点：
 * - 信号量的 P/V 操作
 * - 事件同步（一个任务等待另一个任务的事件）
 * - 资源计数（有多少个可用资源）
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "../include/rtos.h"

/* ==================== 全局变量 ==================== */

static rtos_semaphore_t *event_sem;     /* 事件信号量（二值） */
static rtos_semaphore_t *resource_sem;  /* 资源信号量（计数） */

#define MAX_RESOURCES 3  /* 可用资源数量 */

/* ==================== Producer 任务 ==================== */

/**
 * Producer 任务：产生事件并通知 Consumer
 *
 * Producer 定期产生事件，通过信号量通知 Consumer。
 * 这是典型的事件驱动模式。
 */
void producer_entry(void *arg)
{
    (void)arg;
    uint32_t event_count = 0;

    printf("\n[Producer] 启动\n");

    while (1) {
        event_count++;

        /* 模拟产生事件 */
        printf("[Producer] 产生事件 #%lu\n", (unsigned long)event_count);

        /* 释放信号量，通知 Consumer 有事件待处理 */
        rtos_semaphore_give(event_sem);

        /* 延时后产生下一个事件 */
        rtos_delay(20);
    }
}

/* ==================== Consumer 任务 ==================== */

/**
 * Consumer 任务：等待事件并处理
 *
 * Consumer 等待信号量，当 Producer 发出事件时被唤醒。
 * 这是典型的等待-处理模式。
 */
void consumer_entry(void *arg)
{
    (void)arg;

    printf("\n[Consumer] 启动，等待事件...\n");

    while (1) {
        /* 等待事件信号量（无限等待） */
        rtos_semaphore_take(event_sem, 0);

        /* 处理事件 */
        printf("[Consumer] 收到事件，开始处理...\n");

        /* 模拟处理时间 */
        rtos_delay(10);

        printf("[Consumer] 事件处理完成\n");
    }
}

/* ==================== Resource User 任务 ==================== */

/**
 * 资源使用者任务
 *
 * 多个任务竞争有限资源（通过计数信号量管理）。
 * 演示资源计数和互斥访问。
 */
void resource_user_entry(void *arg)
{
    uint32_t task_id = (uintptr_t)arg;
    uint32_t use_count = 0;

    printf("\n[资源用户 %lu] 启动\n", (unsigned long)task_id);

    while (1) {
        /* 获取资源（等待计数信号量） */
        rtos_semaphore_take(resource_sem, 0);

        use_count++;
        printf("[资源用户 %lu] 获取资源! 使用计数: %lu\n",
               (unsigned long)task_id, (unsigned long)use_count);

        /* 模拟使用资源 */
        rtos_delay(15);

        printf("[资源用户 %lu] 释放资源\n", (unsigned long)task_id);

        /* 释放资源 */
        rtos_semaphore_give(resource_sem);

        /* 延时 */
        rtos_delay(10);
    }
}

/* ==================== 主函数 ==================== */

int main(int argc, char *argv[])
{
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  RTOS 内核学习示例 2: 信号量同步\n");
    printf("========================================\n\n");

    /* 内核初始化 */
    rtos_init();

    /* 创建二值信号量（用于事件通知） */
    event_sem = rtos_semaphore_create("EventSem", SEMAPHORE_TYPE_BINARY, 0, 1);

    /* 创建计数信号量（用于资源计数） */
    resource_sem = rtos_semaphore_create("ResourceSem", SEMAPHORE_TYPE_COUNTING,
                                          MAX_RESOURCES, MAX_RESOURCES);

    /* 创建 Producer 任务 */
    rtos_task_create("Producer", producer_entry, NULL, 512, 10);

    /* 创建 Consumer 任务 */
    rtos_task_create("Consumer", consumer_entry, NULL, 512, 20);

    /* 创建资源使用者任务 */
    rtos_task_create("User1", resource_user_entry, (void *)1, 512, 30);
    rtos_task_create("User2", resource_user_entry, (void *)2, 512, 30);
    rtos_task_create("User3", resource_user_entry, (void *)3, 512, 30);

    /* 打印系统状态 */
    rtos_print_status();

    /* 启动调度器 */
    printf("=== 启动调度器 ===\n\n");
    rtos_start();

    return 0;
}
