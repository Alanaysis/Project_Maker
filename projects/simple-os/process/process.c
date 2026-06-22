/**
 * 进程管理 (process.c)
 * 功能: 创建、销毁和管理进程
 */

#include "../include/process.h"
#include "../include/memory.h"
#include "../include/screen.h"

// 进程表
static process_t *process_table[MAX_PROCESSES];
static process_t *current_process = NULL;
static uint32_t next_pid = 1;

// 就绪队列
static process_queue_t ready_queue;

// 初始化进程管理
void process_init() {
    memset(process_table, 0, sizeof(process_table));
    current_process = NULL;

    // 初始化就绪队列
    ready_queue.head = NULL;
    ready_queue.tail = NULL;
    ready_queue.size = 0;

    screen_puts("[PROCESS] Process manager initialized.\n");
}

// 创建新进程
process_t *process_create(void (*entry_point)()) {
    return process_create_with_name(entry_point, "unnamed");
}

// 创建带名称的新进程
process_t *process_create_with_name(void (*entry_point)(), const char *name) {
    // 分配进程控制块
    process_t *process = (process_t *)kmalloc(sizeof(process_t));
    if (!process) {
        screen_puts("[PROCESS] ERROR: Failed to allocate process!\n");
        return NULL;
    }
    memset(process, 0, sizeof(process_t));

    // 初始化进程
    process->pid = next_pid++;
    process->state = PROCESS_READY;
    process->priority = 1;
    process->time_slice = 10;  // 10 个时钟滴答
    process->ticks = 0;
    process->exit_status = 0;
    process->parent = current_process;

    // 设置进程名
    if (name) {
        int i = 0;
        while (name[i] && i < 63) {
            process->name[i] = name[i];
            i++;
        }
        process->name[i] = '\0';
    } else {
        process->name[0] = '\0';
    }

    // 分配内核栈
    process->kernel_stack = (uint32_t)kmalloc(KERNEL_STACK_SIZE);
    if (!process->kernel_stack) {
        screen_puts("[PROCESS] ERROR: Failed to allocate kernel stack!\n");
        kfree(process);
        return NULL;
    }

    // 设置初始上下文
    // 栈从高地址向低地址增长
    process->esp = process->kernel_stack + KERNEL_STACK_SIZE - sizeof(uint32_t) * 10;
    process->ebp = process->esp;

    // 设置初始寄存器
    process->eip = (uint32_t)entry_point;
    process->eflags = 0x202;  // IF 位设置，启用中断

    // 设置段寄存器 (内核段)
    process->cs = 0x08;   // 代码段
    process->ds = 0x10;   // 数据段
    process->es = 0x10;
    process->fs = 0x10;
    process->gs = 0x10;
    process->ss = 0x10;   // 栈段

    // 设置栈指针
    // 模拟中断帧: SS, ESP, EFLAGS, CS, EIP
    uint32_t *stack = (uint32_t *)(process->kernel_stack + KERNEL_STACK_SIZE);
    *(--stack) = process->ss;      // SS
    *(--stack) = process->esp;     // ESP
    *(--stack) = process->eflags;  // EFLAGS
    *(--stack) = process->cs;      // CS
    *(--stack) = process->eip;     // EIP

    // 保存通用寄存器 (初始为 0)
    *(--stack) = 0;  // EAX
    *(--stack) = 0;  // ECX
    *(--stack) = 0;  // EDX
    *(--stack) = 0;  // EBX
    *(--stack) = 0;  // ESP (占位)
    *(--stack) = 0;  // EBP
    *(--stack) = 0;  // ESI
    *(--stack) = 0;  // EDI
    *(--stack) = process->ds;  // DS

    process->esp = (uint32_t)stack;

    // 创建页目录
    process->page_directory = (uint32_t)paging_create_directory();

    // 添加到进程表
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if (!process_table[i]) {
            process_table[i] = process;
            break;
        }
    }

    // 添加到就绪队列
    scheduler_add_process(process);

    screen_puts("[PROCESS] Created process '");
    screen_puts(process->name);
    screen_puts("' (PID: ");
    screen_put_int(process->pid);
    screen_puts(")\n");

    return process;
}

// 销毁进程
void process_destroy(process_t *process) {
    if (!process) return;

    // 从进程表中移除
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if (process_table[i] == process) {
            process_table[i] = NULL;
            break;
        }
    }

    // 从调度队列中移除
    scheduler_remove_process(process);

    // 释放资源
    if (process->kernel_stack) {
        kfree((void *)process->kernel_stack);
    }
    if (process->page_directory) {
        paging_destroy_directory((page_directory_t *)process->page_directory);
    }

    kfree(process);
}

// 进程退出
void process_exit(int status) {
    if (!current_process) return;

    current_process->state = PROCESS_ZOMBIE;
    current_process->exit_status = status;

    screen_puts("[PROCESS] Process '");
    screen_puts(current_process->name);
    screen_puts("' (PID: ");
    screen_put_int(current_process->pid);
    screen_puts(") exited with status ");
    screen_put_int(status);
    screen_puts("\n");

    // 唤醒父进程
    if (current_process->parent && current_process->parent->state == PROCESS_BLOCKED) {
        wake(current_process->parent);
    }

    // 调度到其他进程
    schedule();
}

// 获取当前进程
process_t *process_get_current() {
    return current_process;
}

// 根据 PID 获取进程
process_t *process_get_by_pid(pid_t pid) {
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if (process_table[i] && process_table[i]->pid == pid) {
            return process_table[i];
        }
    }
    return NULL;
}

// 调度器初始化
void scheduler_init() {
    // 初始化已在 process_init 中完成
}

// 添加进程到就绪队列
void scheduler_add_process(process_t *process) {
    if (!process) return;

    process->next = NULL;

    if (!ready_queue.head) {
        ready_queue.head = process;
        ready_queue.tail = process;
    } else {
        ready_queue.tail->next = process;
        ready_queue.tail = process;
    }
    ready_queue.size++;
}

// 从就绪队列移除进程
void scheduler_remove_process(process_t *process) {
    if (!process || !ready_queue.head) return;

    if (ready_queue.head == process) {
        ready_queue.head = process->next;
        if (!ready_queue.head) {
            ready_queue.tail = NULL;
        }
    } else {
        process_t *prev = ready_queue.head;
        while (prev->next && prev->next != process) {
            prev = prev->next;
        }
        if (prev->next) {
            prev->next = process->next;
            if (!prev->next) {
                ready_queue.tail = prev;
            }
        }
    }
    ready_queue.size--;
}

// 调度函数
void schedule() {
    if (!ready_queue.head) {
        // 没有可运行的进程
        return;
    }

    // 选择下一个进程 (简单轮转)
    process_t *next = ready_queue.head;

    // 从队列头部取出
    ready_queue.head = next->next;
    if (!ready_queue.head) {
        ready_queue.tail = NULL;
    }
    next->next = NULL;

    // 如果当前进程还在运行，放回队列
    if (current_process && current_process->state == PROCESS_RUNNING) {
        current_process->state = PROCESS_READY;
        scheduler_add_process(current_process);
    }

    // 切换到新进程
    process_t *prev = current_process;
    current_process = next;
    current_process->state = PROCESS_RUNNING;

    // 执行上下文切换
    if (prev) {
        context_switch(prev, current_process);
    }
}

// 让出 CPU
void yield() {
    schedule();
}

// 进程休眠
void sleep() {
    if (!current_process) return;

    current_process->state = PROCESS_BLOCKED;
    schedule();
}

// 唤醒进程
void wake(process_t *process) {
    if (!process) return;

    if (process->state == PROCESS_BLOCKED) {
        process->state = PROCESS_READY;
        scheduler_add_process(process);
    }
}

// 启动调度器
void scheduler_start() {
    screen_puts("[SCHEDULER] Starting scheduler...\n");

    // 启用中断
    asm volatile("sti");

    // 触发第一次调度
    schedule();

    // 不应该到达这里
    while (1) {
        asm volatile("hlt");
    }
}

// 定时器中断处理 (由 kernel/timer.c 调用)
void scheduler_tick() {
    if (!current_process) return;

    current_process->ticks++;

    // 检查时间片是否用完
    if (current_process->ticks >= current_process->time_slice) {
        current_process->ticks = 0;
        yield();
    }
}
