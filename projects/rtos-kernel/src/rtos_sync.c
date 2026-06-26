/**
 * @file rtos_sync.c
 * @brief RTOS 同步原语实现
 *
 * 本文件实现 RTOS 的核心同步机制：
 * 1. 信号量（二值和计数）
 * 2. 互斥锁（带优先级继承）
 *
 * 为什么要同步原语？
 *
 * 在多任务环境中，多个任务可能同时访问共享资源（变量、外设、数据结构等）。
 * 如果不加同步，会导致：
 * - 竞态条件 (Race Condition)
 * - 数据不一致
 * - 系统崩溃
 *
 * 同步原语提供了任务间协调的机制：
 * - 信号量：用于事件同步和资源计数
 * - 互斥锁：用于保护共享资源（互斥访问）
 * - 消息队列：用于任务间通信
 *
 * 信号量 vs 互斥锁的区别：
 * - 信号量：可以用于事件同步，不要求释放者与获取者是配对的任务
 * - 互斥锁：专门用于互斥访问，要求获取和释放由同一个任务完成
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "rtos.h"

/* ==================== 信号量实现 ==================== */

rtos_semaphore_t *rtos_semaphore_create(const char *name,
                                         semaphore_type_t type,
                                         uint8_t initial_count,
                                         uint8_t max_count)
{
    rtos_semaphore_t *sem = (rtos_semaphore_t *)rtos_malloc(sizeof(rtos_semaphore_t));
    if (!sem) {
        return NULL;
    }

    strncpy(sem->name, name, MAX_TASK_NAME_LEN - 1);
    sem->name[MAX_TASK_NAME_LEN - 1] = '\0';
    sem->type = type;
    sem->count = initial_count;
    sem->max_count = max_count;
    sem->wait_list = NULL;
    sem->wait_count = 0;

    printf("[信号量] 创建: %s (类型: %s, 初始值: %d)\n",
           sem->name,
           type == SEMAPHORE_TYPE_BINARY ? "二值" : "计数",
           initial_count);

    return sem;
}

rtos_status_t rtos_semaphore_take(rtos_semaphore_t *sem, uint32_t timeout)
{
    if (!sem || !g_kernel.current_task) {
        return RTOS_ERR_INVALID;
    }

    /*
     * P 操作（wait 操作）：
     *
     * 信号量的核心操作之一。
     * 伪代码：
     *   while (count == 0) {
     *       将当前任务加入等待链表
     *       阻塞当前任务
     *   }
     *   count--
     *
     * 在真实 RTOS 中，这个操作是原子的（不可中断的）。
     * 在我们的模拟中，我们假设单线程环境，所以不需要锁保护。
     */

    if (sem->count > 0) {
        /* 信号量可用，直接获取 */
        sem->count--;
        printf("[信号量] %s 获取信号量: %s (剩余: %d)\n",
               g_kernel.current_task->name, sem->name, sem->count);
        return RTOS_OK;
    }

    /* 信号量不可用，阻塞当前任务 */
    if (timeout == 0) {
        /* 无限等待 */
        printf("[信号量] %s 等待信号量: %s (无限等待)\n",
               g_kernel.current_task->name, sem->name);
    } else {
        printf("[信号量] %s 等待信号量: %s (超时: %lu ticks)\n",
               g_kernel.current_task->name, sem->name, (unsigned long)timeout);
    }

    /* 将当前任务加入等待链表 */
    g_kernel.current_task->blocked = true;
    g_kernel.current_task->block_event = sem;
    g_kernel.current_task->block_reason = 0;

    if (timeout > 0) {
        g_kernel.current_task->block_timeout = timeout;
    }

    g_kernel.current_task->state = TASK_STATE_BLOCKED;
    sem->wait_count++;

    /* 将任务插入等待链表头部 */
    g_kernel.current_task->next = sem->wait_list;
    g_kernel.current_task->prev = NULL;
    if (sem->wait_list) {
        sem->wait_list->prev = g_kernel.current_task;
    }
    sem->wait_list = g_kernel.current_task;

    /* 触发调度 */
    rtos_schedule();

    /* 任务被唤醒后继续执行 */
    sem->wait_count--;
    printf("[信号量] %s 获取信号量: %s (剩余: %d)\n",
           g_kernel.current_task->name, sem->name, sem->count);

    return RTOS_OK;
}

rtos_status_t rtos_semaphore_give(rtos_semaphore_t *sem)
{
    if (!sem) {
        return RTOS_ERR_INVALID;
    }

    /*
     * V 操作（signal 操作）：
     *
     * 信号量的另一个核心操作。
     * 伪代码：
     *   if (有任务在等待) {
     *       唤醒一个等待任务
     *   } else {
     *       count++
     *   }
     *
     * 注意：在某些 RTOS 实现中，即使有等待者，也会先增加计数。
     * 我们这里采用经典信号量定义：有等待者时不增加计数。
     */

    if (sem->wait_count > 0) {
        /* 有等待任务，唤醒优先级最高的（链表头部） */
        rtos_tcb_t *task = sem->wait_list;
        if (task) {
            /* 从等待链表中移除 */
            sem->wait_list = task->next;
            if (task->next) {
                task->next->prev = NULL;
            }
            task->next = NULL;
            task->prev = NULL;

            /* 将任务移回就绪状态 */
            task->blocked = false;
            task->block_event = NULL;
            task->state = TASK_STATE_READY;
            sem->wait_count--;

            printf("[信号量] %s 释放信号量: %s, 唤醒 %s\n",
                   g_kernel.current_task ? g_kernel.current_task->name : "系统",
                   sem->name, task->name);
        }
    } else {
        /* 没有等待者，增加计数 */
        if (sem->count < sem->max_count) {
            sem->count++;
        }
        printf("[信号量] %s 释放信号量: %s (计数: %d)\n",
               g_kernel.current_task ? g_kernel.current_task->name : "系统",
               sem->name, sem->count);
    }

    /* 触发调度（被唤醒的任务可能优先级更高） */
    rtos_schedule();

    return RTOS_OK;
}

/* ==================== 互斥锁实现 ==================== */

rtos_mutex_t *rtos_mutex_create(const char *name)
{
    rtos_mutex_t *mutex = (rtos_mutex_t *)rtos_malloc(sizeof(rtos_mutex_t));
    if (!mutex) {
        return NULL;
    }

    strncpy(mutex->name, name, MAX_TASK_NAME_LEN - 1);
    mutex->name[MAX_TASK_NAME_LEN - 1] = '\0';
    mutex->owner = NULL;
    mutex->original_priority = 0;
    mutex->count = 0;
    mutex->wait_list = NULL;
    mutex->wait_count = 0;

    printf("[互斥锁] 创建: %s\n", mutex->name);

    return mutex;
}

rtos_status_t rtos_mutex_take(rtos_mutex_t *mutex, uint32_t timeout)
{
    if (!mutex || !g_kernel.current_task) {
        return RTOS_ERR_INVALID;
    }

    /*
     * 获取互斥锁
     *
     * 如果互斥锁未被持有：
     *   当前任务成为持有者
     *
     * 如果已被持有：
     *   检查优先级继承条件
     *   如果持有者优先级低于当前任务，提升持有者优先级
     *   当前任务阻塞等待
     *
     * 优先级继承算法：
     *
     * 问题：优先级反转
     *
     *   高优先级任务 H ---等待锁---
     *                               |
     *   低优先级任务 L ---持有锁---
     *                               |
     *   中优先级任务 M ------------+--- 抢占 L ---
     *
     * 结果：H 被 M 间接阻塞，违反了优先级调度原则。
     *
     * 解决方案：优先级继承
     *   当 H 尝试获取被 L 持有的锁时：
     *   1. L 的优先级提升到 H 的优先级
     *   2. L 不再被 M 抢占
     *   3. L 尽快执行并释放锁
     *   4. H 获得锁，L 恢复原始优先级
     */

    if (mutex->owner == NULL) {
        /* 锁未被持有，直接获取 */
        mutex->owner = g_kernel.current_task;
        mutex->original_priority = g_kernel.current_task->priority;
        mutex->count = 1;

        printf("[互斥锁] %s 获取锁: %s\n",
               g_kernel.current_task->name, mutex->name);
        return RTOS_OK;
    }

    /* 锁已被持有 */
    if (mutex->owner == g_kernel.current_task) {
        /* 当前任务已经持有此锁（递归获取） */
        mutex->count++;
        printf("[互斥锁] %s 递归获取锁: %s (递归次数: %d)\n",
               g_kernel.current_task->name, mutex->name, mutex->count);
        return RTOS_OK;
    }

    /*
     * 优先级继承检查
     *
     * 如果当前任务的优先级高于锁持有者的优先级，
     * 需要提升锁持有者的优先级。
     */
    if (g_kernel.current_task->priority < mutex->owner->priority) {
        printf("[优先级继承] %s (优先级 %d) 持有锁，%s (优先级 %d) 等待\n",
               mutex->owner->name, mutex->owner->priority,
               g_kernel.current_task->name, g_kernel.current_task->priority);
        printf("[优先级继承] 将 %s 的优先级从 %d 提升到 %d\n",
               mutex->owner->name, mutex->owner->priority,
               g_kernel.current_task->priority);

        /* 保存原始优先级，以便释放时恢复 */
        mutex->original_priority = mutex->owner->priority;

        /* 提升持有者优先级 */
        mutex->owner->priority = g_kernel.current_task->priority;

        /* 重新将持有者插入就绪链表（优先级已改变） */
        /* 简化：暂时不重新插入，假设调度器会处理 */
    }

    /* 阻塞等待 */
    printf("[互斥锁] %s 等待锁: %s\n",
           g_kernel.current_task->name, mutex->name);

    g_kernel.current_task->blocked = true;
    g_kernel.current_task->block_event = mutex;
    g_kernel.current_task->block_reason = 1;  /* 等待互斥锁 */

    if (timeout > 0) {
        g_kernel.current_task->block_timeout = timeout;
    }

    g_kernel.current_task->state = TASK_STATE_BLOCKED;
    mutex->wait_count++;

    /* 插入等待链表 */
    g_kernel.current_task->next = mutex->wait_list;
    g_kernel.current_task->prev = NULL;
    if (mutex->wait_list) {
        mutex->wait_list->prev = g_kernel.current_task;
    }
    mutex->wait_list = g_kernel.current_task;

    /* 触发调度 */
    rtos_schedule();

    /* 被唤醒后继续 */
    mutex->wait_count--;
    printf("[互斥锁] %s 获取锁: %s\n",
           g_kernel.current_task->name, mutex->name);

    return RTOS_OK;
}

rtos_status_t rtos_mutex_give(rtos_mutex_t *mutex)
{
    if (!mutex || !g_kernel.current_task) {
        return RTOS_ERR_INVALID;
    }

    /* 检查当前任务是否是锁的持有者 */
    if (mutex->owner != g_kernel.current_task) {
        printf("[互斥锁] 错误: %s 不是 %s 的持有者\n",
               g_kernel.current_task->name, mutex->name);
        return RTOS_ERR_DENIED;
    }

    if (mutex->count > 1) {
        /* 递归释放 */
        mutex->count--;
        printf("[互斥锁] %s 递归释放锁: %s (剩余: %d)\n",
               g_kernel.current_task->name, mutex->name, mutex->count);
        return RTOS_OK;
    }

    /*
     * 释放互斥锁
     *
     * 1. 如果有等待者，唤醒优先级最高的
     * 2. 恢复持有者的原始优先级（优先级继承）
     * 3. 清除持有者
     */

    /* 唤醒等待者 */
    if (mutex->wait_count > 0) {
        rtos_tcb_t *task = mutex->wait_list;
        if (task) {
            mutex->wait_list = task->next;
            if (task->next) {
                task->next->prev = NULL;
            }
            task->next = NULL;
            task->prev = NULL;

            task->blocked = false;
            task->block_event = NULL;
            task->state = TASK_STATE_READY;
            mutex->wait_count--;

            /* 新持有者 */
            mutex->owner = task;
            mutex->count = 1;

            printf("[互斥锁] %s 释放锁: %s, 唤醒 %s\n",
                   g_kernel.current_task->name, mutex->name, task->name);
        }
    } else {
        /* 没有等待者 */
        mutex->owner = NULL;
        mutex->count = 0;
        printf("[互斥锁] %s 释放锁: %s\n",
               g_kernel.current_task->name, mutex->name);
    }

    /* 恢复原始优先级（优先级继承） */
    if (g_kernel.current_task->priority != mutex->original_priority) {
        printf("[优先级继承] 恢复 %s 的优先级从 %d 到 %d\n",
               g_kernel.current_task->name,
               g_kernel.current_task->priority,
               mutex->original_priority);
        g_kernel.current_task->priority = mutex->original_priority;
    }

    /* 触发调度 */
    rtos_schedule();

    return RTOS_OK;
}
