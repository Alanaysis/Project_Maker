#ifndef PROCESS_H
#define PROCESS_H

#include "types.h"
#include "memory.h"

// 最大进程数
#define MAX_PROCESSES    64
#define KERNEL_STACK_SIZE 4096

// 进程状态
typedef enum {
    PROCESS_READY,
    PROCESS_RUNNING,
    PROCESS_BLOCKED,
    PROCESS_ZOMBIE
} process_state_t;

// 进程控制块
typedef struct process {
    uint32_t pid;
    process_state_t state;
    uint32_t esp;
    uint32_t ebp;
    uint32_t eip;
    uint32_t eflags;
    uint32_t eax, ebx, ecx, edx;
    uint32_t esi, edi;
    uint32_t cs, ds, es, fs, gs, ss;
    uint32_t page_directory;
    uint32_t kernel_stack;
    uint32_t user_stack;
    uint32_t priority;
    uint32_t time_slice;
    uint32_t ticks;
    int exit_status;
    struct process *parent;
    struct process *next;
    char name[64];
} process_t;

// 进程队列
typedef struct {
    process_t *head;
    process_t *tail;
    uint32_t size;
} process_queue_t;

// 进程管理函数
void process_init();
process_t *process_create(void (*entry_point)());
process_t *process_create_with_name(void (*entry_point)(), const char *name);
void process_destroy(process_t *process);
process_t *process_fork();
void process_exit(int status);
void process_wait(pid_t pid);
process_t *process_get_by_pid(pid_t pid);
process_t *process_get_current();

// 调度器函数
void scheduler_init();
void scheduler_add_process(process_t *process);
void scheduler_remove_process(process_t *process);
void schedule();
void yield();
void sleep();
void wake(process_t *process);
void scheduler_start();

// 上下文切换
void context_switch(process_t *prev, process_t *next);
void switch_to_user_mode();

#endif /* PROCESS_H */
