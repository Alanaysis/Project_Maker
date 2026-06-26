/**
 * @file rtos_kernel.c
 * @brief RTOS 内核核心实现
 *
 * 本文件实现了 RTOS 内核的核心功能：
 * 1. 内核初始化
 * 2. 任务调度（优先级抢占 + 同级轮转）
 * 3. 上下文切换（栈管理、寄存器模拟）
 * 4. 时钟 tick 处理
 *
 * 核心调度算法：
 *
 * 优先级抢占式调度：
 *   系统总是选择优先级最高的就绪任务运行。
 *   当高优先级任务从阻塞变为就绪时，立即抢占当前低优先级任务。
 *
 * 同级轮转调度 (Round-Robin for same priority):
 *   相同优先级的就绪任务按 FIFO 顺序轮流执行。
 *   每个任务执行一个时间片后，让出 CPU 给同优先级的下一个任务。
 *
 * 上下文切换原理：
 *   在真实 CPU 上，上下文切换需要保存/恢复：
 *   - PC (程序计数器)
 *   - SP (栈指针)
 *   - 通用寄存器
 *   - 状态寄存器
 *
 *   在我们的模拟中，我们简化了这个过程：
 *   - 只需要管理栈指针
 *   - 通过栈恢复模拟寄存器状态
 *   - 使用 setjmp/longjmp 实现栈切换
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include "rtos.h"

/* ==================== 内核全局状态 ==================== */

/**
 * 全局内核实例
 *
 * 在真实 RTOS 中，这个结构体通常由编译器/链接器放在特定内存段中。
 * 这里我们使用简单的全局变量。
 */
static rtos_kernel_t g_kernel = {
    .running = false,
    .in_isr = false,
    .interrupt_nest = 0,
    .current_task = NULL,
    .total_tasks = 0,
    .total_context_switches = 0,
    .idle_task_ticks = 0,
    .free_memory = 1024 * 1024  /* 模拟 1MB 可用内存 */
};

/**
 * 用于上下文切换的 jmp_buf 数组
 *
 * 每个任务有一个 jmp_buf，用于：
 * - 保存当前执行点（当任务被抢占时）
 * - 恢复执行点（当任务再次被调度时）
 *
 * 在真实 RTOS 中，这部分由汇编实现。
 * 这里我们使用 POSIX setjmp/longjmp 模拟。
 */
static jmp_buf g_context_buf[MAX_TASKS];

/**
 * 内存池（模拟 RTOS 内存管理）
 *
 * 真实 RTOS 通常使用内存池来管理任务栈和 TCB，避免频繁 malloc/free。
 * 这里我们使用简单的方式，但保留了内存池的接口。
 */
#define MEMORY_POOL_SIZE (1024 * 64)  /* 64KB 内存池 */
static uint8_t g_memory_pool[MEMORY_POOL_SIZE];
static uint32_t g_memory_pool_used = 0;

/* ==================== 空闲任务 ==================== */

/**
 * 空闲任务函数
 *
 * 空闲任务是 RTOS 中必须存在的特殊任务：
 * - 它是系统中优先级最低的任务
 * - 当没有其他任务可运行时，它执行
 * - 它不应该永久阻塞
 * - 可用于：
 *   - CPU 空闲时间统计
 *   - 低功耗模式进入
 *   - 内存回收
 *
 * 在我们的实现中，空闲任务只是计数并打印状态。
 */
static void idle_task_entry(void *arg)
{
    (void)arg;

    printf("[IDLE] 空闲任务已启动\n");
    printf("[IDLE] 当没有其他任务运行时，此任务在执行\n");

    /* 空闲任务的主循环 - 它永远不会退出 */
    while (g_kernel.running) {
        g_kernel.idle_task_ticks++;

        /* 在有更高优先级任务时，让出 CPU */
        rtos_task_yield();

        /* 每隔一段时间打印系统状态 */
        if (g_kernel.tick_count % 100 == 0) {
            printf("[IDLE] 系统运行 %lu ticks, %lu 个任务\n",
                   (unsigned long)g_kernel.tick_count,
                   (unsigned long)g_kernel.total_tasks);
        }
    }

    printf("[IDLE] 空闲任务退出\n");
}

/* ==================== 内核初始化 ==================== */

void rtos_init(void)
{
    printf("=== RTOS 内核初始化 ===\n");

    /* 重置内核状态 */
    memset(&g_kernel, 0, sizeof(g_kernel));
    g_kernel.running = false;
    g_kernel.in_isr = false;
    g_kernel.interrupt_nest = 0;
    g_kernel.tick_count = 0;
    g_kernel.total_tasks = 0;
    g_kernel.total_context_switches = 0;
    g_kernel.idle_task_ticks = 0;
    g_kernel.free_memory = MEMORY_POOL_SIZE;

    /* 重置就绪链表 */
    for (int i = 0; i < MAX_TASKS; i++) {
        g_kernel.ready_list[i].state = TASK_STATE_READY;
        g_kernel.ready_list[i].next = NULL;
        g_kernel.ready_list[i].prev = NULL;
    }

    /* 初始化内存池 */
    memset(g_memory_pool, 0, MEMORY_POOL_SIZE);
    g_memory_pool_used = 0;

    /* 创建空闲任务 */
    /*
     * 空闲任务的创建过程：
     * 1. 分配 TCB
     * 2. 分配栈空间
     * 3. 初始化栈（设置初始栈状态，模拟任务被调度时的寄存器值）
     * 4. 将任务加入就绪链表
     */
    g_kernel.idle_task_tcb = (rtos_tcb_t *)rtos_malloc(sizeof(rtos_tcb_t));
    memset(g_kernel.idle_task_tcb, 0, sizeof(rtos_tcb_t));

    /* 初始化 TCB */
    g_kernel.idle_task_tcb->name[0] = '\0';
    strncpy(g_kernel.idle_task_tcb->name, "Idle", MAX_TASK_NAME_LEN - 1);
    g_kernel.idle_task_tcb->state = TASK_STATE_READY;
    g_kernel.idle_task_tcb->priority = RTOS_PRIORITY_IDLE;
    g_kernel.idle_task_tcb->time_slice_max = 1;
    g_kernel.idle_task_tcb->entry_func = idle_task_entry;
    g_kernel.idle_task_tcb->entry_arg = NULL;
    g_kernel.idle_task_tcb->blocked = false;

    /* 分配栈空间 */
    g_kernel.idle_task_tcb->stack = (uint32_t *)rtos_malloc(
        RTOS_IDLE_STACK_SIZE * sizeof(uint32_t));
    g_kernel.idle_task_tcb->stack_end = g_kernel.idle_task_tcb->stack;
    g_kernel.idle_task_tcb->stack_top = g_kernel.idle_task_tcb->stack +
                                          RTOS_IDLE_STACK_SIZE;

    /* 初始化栈（模拟 x86_64 栈状态）
     *
     * 栈向下增长（从高地址向低地址）
     * 当任务被首次调度时，需要模拟从函数调用返回的状态：
     * - 栈顶应该指向一个"返回地址"（我们的 idle_task_entry 函数入口）
     * - 这样 longjmp 返回时，任务会从 entry_func 开始执行
     */
    /* 预留空间用于模拟返回地址 */
    g_kernel.idle_task_tcb->stack_top -= 1;
    *g_kernel.idle_task_tcb->stack_top = (uint32_t)(uintptr_t)idle_task_entry;

    g_kernel.total_tasks = 1;

    printf("内核初始化完成，空闲任务已创建\n");
    printf("就绪链表大小: %d\n", MAX_TASKS);
    printf("内存池大小: %d 字节\n", MEMORY_POOL_SIZE);
}

/**
 * 启动 RTOS 调度器
 *
 * 启动过程：
 * 1. 检查是否有至少一个用户任务（除了空闲任务）
 * 2. 设置内核运行标志
 * 3. 选择最高优先级任务作为当前任务
 * 4. 切换到当前任务执行
 *
 * 注意：在真实 RTOS 中，启动过程更复杂，需要：
 * - 设置异常向量表
 * - 配置 SysTick 定时器
 * - 初始化 MPU (Memory Protection Unit)
 * - 设置 MSP (Main Stack Pointer)
 */
void rtos_start(void)
{
    printf("\n=== 启动 RTOS 调度器 ===\n");

    /* 检查是否有用户任务 */
    bool has_user_task = false;
    for (int i = 0; i < MAX_TASKS; i++) {
        if (g_kernel.ready_list[i].state == TASK_STATE_READY &&
            &g_kernel.ready_list[i] != g_kernel.idle_task_tcb) {
            has_user_task = true;
            break;
        }
    }

    if (!has_user_task) {
        printf("错误: 没有用户任务可运行！\n");
        printf("在调用 rtos_start() 之前，请至少创建一个用户任务。\n");
        return;
    }

    /* 设置内核状态 */
    g_kernel.running = true;
    g_kernel.tick_count = 0;

    /* 选择最高优先级任务 */
    rtos_tcb_t *next_task = rtos_schedule_next();
    if (!next_task) {
        printf("错误: 没有可运行的任务！\n");
        return;
    }

    /* 设置当前任务 */
    if (g_kernel.current_task != next_task) {
        g_kernel.current_task = next_task;
        g_kernel.current_task->state = TASK_STATE_RUNNING;
        g_kernel.total_context_switches++;
        printf("初始任务: %s (优先级 %d)\n",
               g_kernel.current_task->name,
               g_kernel.current_task->priority);
    }

    /* 切换到当前任务执行 */
    /*
     * 使用 longjmp 模拟第一次任务切换。
     * longjmp 会恢复之前由 setjmp 保存的栈状态。
     * 对于第一个任务，我们让它从 entry_func 开始执行。
     */
    longjmp(g_context_buf[0], 1);
}

/**
 * 让内核进入空闲循环
 *
 * 当没有用户任务可运行时（或被停止），系统会进入此循环。
 * 空闲任务在这里执行。
 */
void rtos_idle_loop(void)
{
    printf("RTOS 已停止，进入空闲循环\n");

    while (1) {
        /* 在真实系统中，这里会进入低功耗模式 */
        rtos_delay(100);
    }
}

/* ==================== 内存管理 ==================== */

void *rtos_malloc(uint32_t size)
{
    /* 对齐到 4 字节 */
    size = (size + 3) & ~3;

    if (g_memory_pool_used + size > MEMORY_POOL_SIZE) {
        printf("内存分配失败: 需要 %lu 字节, 剩余 %lu 字节\n",
               (unsigned long)size,
               (unsigned long)(MEMORY_POOL_SIZE - g_memory_pool_used));
        return NULL;
    }

    void *ptr = g_memory_pool + g_memory_pool_used;
    g_memory_pool_used += size;
    g_kernel.free_memory -= size;

    return ptr;
}

void rtos_free(void *ptr)
{
    /* 简单的内存释放 - 在我们的线性池实现中，只更新计数器 */
    if (ptr >= g_memory_pool && ptr < g_memory_pool + MEMORY_POOL_SIZE) {
        uint32_t offset = (uint8_t *)ptr - g_memory_pool;
        if (offset <= g_memory_pool_used) {
            g_memory_pool_used -= offset;
            g_kernel.free_memory += offset;
        }
    }
}

/* ==================== 任务管理 ==================== */

rtos_tcb_t *rtos_task_create(const char *name,
                              void (*entry_func)(void *),
                              void *arg,
                              uint32_t stack_size,
                              uint8_t priority)
{
    if (!entry_func) {
        printf("错误: 任务入口函数为空\n");
        return NULL;
    }

    if (g_kernel.total_tasks >= MAX_TASKS) {
        printf("错误: 任务数量达到上限 (%d)\n", MAX_TASKS);
        return NULL;
    }

    /* 分配 TCB */
    rtos_tcb_t *task = (rtos_tcb_t *)rtos_malloc(sizeof(rtos_tcb_t));
    if (!task) {
        return NULL;
    }
    memset(task, 0, sizeof(rtos_tcb_t));

    /* 初始化 TCB */
    strncpy(task->name, name, MAX_TASK_NAME_LEN - 1);
    task->name[MAX_TASK_NAME_LEN - 1] = '\0';
    task->state = TASK_STATE_READY;
    task->priority = priority;
    task->time_slice_max = 10;  /* 默认时间片 */
    task->time_slice = task->time_slice_max;
    task->entry_func = entry_func;
    task->entry_arg = arg;
    task->blocked = false;
    task->block_timeout = 0;
    task->block_event = NULL;
    task->tick_count = 0;
    task->next = NULL;
    task->prev = NULL;

    /* 分配栈空间 */
    if (stack_size == 0) {
        stack_size = RTOS_DEFAULT_STACK;
    }
    task->stack = (uint32_t *)rtos_malloc(stack_size * sizeof(uint32_t));
    if (!task->stack) {
        rtos_free(task);
        return NULL;
    }
    task->stack_end = task->stack;
    task->stack_top = task->stack + stack_size;

    /*
     * 初始化任务栈
     *
     * 栈初始化是上下文切换的关键！
     * 当任务首次被调度时，需要从"仿佛刚从函数调用返回"的状态开始执行。
     *
     * x86_64 调用约定：
     * - 栈向下增长
     * - 函数返回时，RSP 指向返回地址
     * - longjmp 恢复栈时，会弹出返回地址到 RIP
     *
     * 我们的简化模型：
     * - 栈顶放置 entry_func 的地址
     * - 当 longjmp 返回时，RIP 被设置为 entry_func
     * - 任务从 entry_func(arg) 开始执行
     */
    task->stack_top -= 1;
    *task->stack_top = (uint32_t)(uintptr_t)entry_func;

    /* 将任务加入就绪链表 */
    /*
     * 就绪链表按优先级排序。
     * 新任务插入到同优先级的链表尾部（FIFO 轮转）。
     */
    bool list_empty = (g_kernel.ready_list[priority].state != TASK_STATE_READY);

    if (list_empty) {
        g_kernel.ready_list[priority].state = TASK_STATE_READY;
        g_kernel.ready_list[priority] = *task;
        task->next = NULL;
        task->prev = NULL;
    } else {
        /* 找到链表尾部 */
        rtos_tcb_t *curr = &g_kernel.ready_list[priority];
        while (curr->next) {
            curr = curr->next;
        }
        curr->next = task;
        task->prev = curr;
        task->next = NULL;
    }

    g_kernel.total_tasks++;

    printf("任务创建: %s (优先级 %d, 栈 %lu 字)\n",
           task->name, priority, (unsigned long)stack_size);

    /* 如果当前没有运行任务，此任务将成为当前任务 */
    if (g_kernel.current_task == NULL) {
        g_kernel.current_task = task;
        task->state = TASK_STATE_RUNNING;
    }

    return task;
}

void rtos_task_delete(rtos_tcb_t *task)
{
    if (!task || task == g_kernel.idle_task_tcb) {
        printf("错误: 不能删除空闲任务\n");
        return;
    }

    /* 如果任务是当前任务，先标记为非运行 */
    if (task == g_kernel.current_task) {
        g_kernel.current_task = NULL;
    }

    /* 从就绪链表移除 */
    if (task->priority < MAX_TASKS) {
        if (task->prev) {
            task->prev->next = task->next;
        } else {
            /* task 是链表头 */
            if (task->next) {
                g_kernel.ready_list[task->priority] = *task->next;
            } else {
                g_kernel.ready_list[task->priority].state = 0;
            }
        }
        if (task->next) {
            task->next->prev = task->prev;
        }
    }

    /* 释放资源 */
    if (task->stack) {
        rtos_free(task->stack);
    }
    rtos_free(task);

    g_kernel.total_tasks--;

    printf("任务删除: %s\n", task ? task->name : "未知");

    /* 触发重新调度 */
    if (g_kernel.running) {
        rtos_schedule();
    }
}

void rtos_task_suspend(rtos_tcb_t *task)
{
    if (!task) return;

    task->state = TASK_STATE_SUSPENDED;
    printf("任务挂起: %s\n", task->name);

    if (task == g_kernel.current_task) {
        g_kernel.current_task = NULL;
        rtos_schedule();
    }
}

void rtos_task_resume(rtos_tcb_t *task)
{
    if (!task) return;

    task->state = TASK_STATE_READY;
    task->blocked = false;

    printf("任务恢复: %s\n", task->name);

    /* 如果恢复的任务优先级高于当前任务，触发调度 */
    if (g_kernel.current_task &&
        task->priority < g_kernel.current_task->priority) {
        rtos_schedule();
    }
}

void rtos_task_yield(void)
{
    if (!g_kernel.current_task) return;

    /* 将当前任务移至同优先级链表的尾部 */
    rtos_tcb_t *task = g_kernel.current_task;

    if (task->prev) {
        task->prev->next = task->next;
    } else {
        /* task 是链表头 */
        if (task->next) {
            g_kernel.ready_list[task->priority] = *task->next;
        }
    }
    if (task->next) {
        task->next->prev = task->prev;
    }

    /* 移到尾部 */
    rtos_tcb_t *curr = &g_kernel.ready_list[task->priority];
    while (curr->next) {
        curr = curr->next;
    }
    curr->next = task;
    task->prev = curr;
    task->next = NULL;

    /* 重置时间片 */
    task->time_slice = task->time_slice_max;

    /* 触发调度 */
    rtos_schedule();
}

rtos_tcb_t *rtos_task_current(void)
{
    return g_kernel.current_task;
}

/* ==================== 调度器 ==================== */

rtos_tcb_t *rtos_schedule_next(void)
{
    /*
     * 调度算法实现：
     *
     * 1. 优先级抢占：遍历所有优先级，找到最高优先级的就绪任务
     * 2. 同级轮转：同优先级的任务按 FIFO 顺序执行
     * 3. 时间片耗尽：同优先级任务的剩余时间片减到 0 时切换到下一个
     *
     * 优先级数值越小，优先级越高（0 = 最高）
     */
    rtos_tcb_t *highest = NULL;

    for (int i = 0; i < MAX_TASKS; i++) {
        if (g_kernel.ready_list[i].state == TASK_STATE_READY) {
            highest = &g_kernel.ready_list[i];
            break;
        }
    }

    if (!highest) {
        printf("警告: 没有就绪任务！\n");
        return NULL;
    }

    /* 找到同优先级就绪链表中的第一个任务 */
    rtos_tcb_t *next = highest;
    if (next == g_kernel.current_task && next->time_slice > 0) {
        /* 如果当前任务还有时间片，继续执行 */
        return next;
    }

    /* 切换到同优先级的下一个任务（轮转） */
    if (next->next && next->next->state == TASK_STATE_READY) {
        next = next->next;
    }

    /* 重置时间片 */
    if (next == g_kernel.current_task) {
        next->time_slice = next->time_slice_max;
    }

    return next;
}

void rtos_schedule(void)
{
    if (!g_kernel.running) return;

    rtos_tcb_t *next = rtos_schedule_next();
    if (!next || next == g_kernel.current_task) {
        return;
    }

    /*
     * 上下文切换
     *
     * 上下文切换是操作系统的核心功能。
     * 它保存当前任务的执行状态，并恢复下一个任务的执行状态。
     *
     * 在真实系统中，上下文切换需要：
     * 1. 保存当前任务的寄存器到其栈/TCB
     * 2. 更新内核栈指针
     * 3. 切换页表（如果支持 MMU）
     * 4. 恢复下一个任务的寄存器
     * 5. 返回到下一个任务的执行点
     *
     * 在我们的模拟中，我们使用 setjmp/longjmp：
     * - setjmp 保存当前栈状态
     * - longjmp 恢复到之前保存的栈状态
     *
     * 注意：setjmp/longjmp 不是真正的上下文切换，
     * 它只是在同一个线程内切换栈。
     * 但对于学习 RTOS 原理来说，这已经足够了。
     */

    /* 保存当前任务的上下文 */
    if (g_kernel.current_task) {
        setjmp(g_context_buf[g_kernel.total_tasks]);
        g_kernel.current_task->state = TASK_STATE_READY;
    }

    /* 切换到新任务 */
    g_kernel.current_task = next;
    next->state = TASK_STATE_RUNNING;
    g_kernel.total_context_switches++;

    printf("[调度] 上下文切换: %s -> %s (切换次数: %lu)\n",
           g_kernel.current_task ? g_kernel.current_task->name : "NULL",
           next->name,
           (unsigned long)g_kernel.total_context_switches);

    /* 恢复新任务的上下文 */
    longjmp(g_context_buf[g_kernel.total_tasks], 1);
}

/* ==================== 时钟 tick 处理 ==================== */

void rtos_tick(void)
{
    g_kernel.tick_count++;

    /* 减少所有就绪任务的剩余时间片 */
    for (int i = 0; i < MAX_TASKS; i++) {
        if (g_kernel.ready_list[i].state == TASK_STATE_READY) {
            rtos_tcb_t *task = &g_kernel.ready_list[i];
            while (task) {
                if (task->state == TASK_STATE_READY && task->time_slice > 0) {
                    task->time_slice--;
                }
                task = task->next;
            }
        }
    }

    /* 检查阻塞任务的超时 */
    for (int i = 0; i < MAX_TASKS; i++) {
        if (g_kernel.ready_list[i].state == TASK_STATE_READY) {
            rtos_tcb_t *task = &g_kernel.ready_list[i];
            while (task) {
                if (task->blocked && task->block_timeout > 0) {
                    task->block_timeout--;
                    if (task->block_timeout == 0) {
                        /* 超时，将任务移回就绪状态 */
                        task->blocked = false;
                        task->state = TASK_STATE_READY;
                        task->block_event = NULL;
                        printf("[Tick] 任务超时唤醒: %s\n", task->name);
                    }
                }
                task = task->next;
            }
        }
    }

    /* 触发调度 */
    rtos_schedule();
}

/* ==================== 调试和统计 ==================== */

void rtos_print_task_status(rtos_tcb_t *task)
{
    if (!task) return;

    const char *state_str;
    switch (task->state) {
        case TASK_STATE_IDLE:    state_str = "IDLE"; break;
        case TASK_STATE_READY:   state_str = "READY"; break;
        case TASK_STATE_RUNNING: state_str = "RUNNING"; break;
        case TASK_STATE_BLOCKED: state_str = "BLOCKED"; break;
        case TASK_STATE_SUSPENDED: state_str = "SUSPENDED"; break;
        default:                 state_str = "UNKNOWN"; break;
    }

    printf("  任务: %s\n", task->name);
    printf("    状态: %s\n", state_str);
    printf("    优先级: %d\n", task->priority);
    printf("    时间片: %d/%d\n", task->time_slice, task->time_slice_max);
    printf("    运行 tick: %lu\n", (unsigned long)task->tick_count);
}

void rtos_print_ready_list(void)
{
    printf("\n=== 就绪链表 ===\n");
    for (int i = 0; i < MAX_TASKS; i++) {
        if (g_kernel.ready_list[i].state == TASK_STATE_READY) {
            printf("优先级 %d: ", i);
            rtos_tcb_t *task = &g_kernel.ready_list[i];
            while (task) {
                printf("[%s(%d)] -> ", task->name, task->priority);
                task = task->next;
            }
            printf("NULL\n");
        }
    }
}

void rtos_print_status(void)
{
    printf("\n========== RTOS 系统状态 ==========\n");
    printf("系统运行时间: %lu ticks\n", (unsigned long)g_kernel.tick_count);
    printf("任务总数: %lu\n", (unsigned long)g_kernel.total_tasks);
    printf("上下文切换次数: %lu\n", (unsigned long)g_kernel.total_context_switches);
    printf("空闲任务运行: %lu ticks\n", (unsigned long)g_kernel.idle_task_ticks);
    printf("内存使用: %lu / %d 字节\n",
           (unsigned long)g_memory_pool_used, MEMORY_POOL_SIZE);

    rtos_print_ready_list();

    printf("\n=== 所有任务状态 ===\n");
    for (int i = 0; i < MAX_TASKS; i++) {
        if (g_kernel.ready_list[i].state == TASK_STATE_READY) {
            rtos_tcb_t *task = &g_kernel.ready_list[i];
            while (task) {
                rtos_print_task_status(task);
                task = task->next;
            }
        }
    }
    printf("====================================\n\n");
}
