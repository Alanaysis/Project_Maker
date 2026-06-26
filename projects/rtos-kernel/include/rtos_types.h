/**
 * @file rtos_types.h
 * @brief RTOS 内核基础类型定义
 *
 * 本文件定义了 RTOS 内核使用的所有基础类型和常量。
 * 在真实 RTOS 中，这些类型通常由编译器或标准库提供。
 * 这里我们使用 C99 标准类型以确保可移植性。
 */

#ifndef RTOS_TYPES_H
#define RTOS_TYPES_H

/* ==================== 基础类型定义 ==================== */

/* 使用标准 C 类型确保可移植性 */
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* 内核状态码 */
typedef enum {
    RTOS_OK = 0,        /* 操作成功 */
    RTOS_ERR_TIMEOUT,   /* 操作超时 */
    RTOS_ERR_FULL,      /* 队列/缓冲区已满 */
    RTOS_ERR_EMPTY,     /* 队列/缓冲区已空 */
    RTOS_ERR_INVALID,   /* 无效参数 */
    RTOS_ERR_DENIED,    /* 权限拒绝 */
    RTOS_ERR_NO_MEM,    /* 内存不足 */
    RTOS_ERR_ISR        /* 在中断服务程序中不允许 */
} rtos_status_t;

/* ==================== 任务状态 ==================== */

/**
 * 任务状态枚举
 *
 * RTOS 中任务在其生命周期中会经历多种状态：
 * - READY: 任务已创建，等待调度器分配 CPU
 * - RUNNING: 任务正在 CPU 上执行
 * - BLOCKED: 任务等待某个事件（信号量、消息等）
 * - SUSPENDED: 任务被主动挂起（类似暂停）
 *
 * 理解任务状态转换是理解 RTOS 的核心：
 *  READY -> RUNNING : 调度器选择该任务
 *  RUNNING -> BLOCKED : 任务等待事件
 *  BLOCKED -> READY : 等待的事件发生
 *  RUNNING -> SUSPENDED : 被其他任务挂起
 *  SUSPENDED -> READY : 被恢复
 */
typedef enum {
    TASK_STATE_IDLE = 0,    /* 空闲任务（系统启动后一直运行） */
    TASK_STATE_READY,       /* 就绪：等待 CPU */
    TASK_STATE_RUNNING,     /* 运行：正在 CPU 上执行 */
    TASK_STATE_BLOCKED,     /* 阻塞：等待事件 */
    TASK_STATE_SUSPENDED    /* 挂起：被主动暂停 */
} task_state_t;

/* ==================== 任务控制块 (TCB) ==================== */

/**
 * 任务控制块 (Task Control Block)
 *
 * TCB 是 RTOS 中最重要的数据结构，它管理每个任务的所有信息。
 * 在真实 RTOS（如 FreeRTOS、RT-Thread）中，TCB 包含更多内容。
 *
 * 本实现的 TCB 包含：
 * - 任务名称：便于调试
 * - 任务状态：当前处于什么状态
 * - 任务优先级：数值越小优先级越高（或反之，取决于实现）
 * - 栈指针：指向任务私有栈的指针
 * - 栈大小：栈的容量（以字为单位）
 * - 时间片：轮转调度中的剩余时间片
 * - 等待的事件类型：如果处于阻塞状态，在等什么
 */
#define MAX_TASK_NAME_LEN 32
#define MAX_TASKS 32

typedef struct rtos_tcb {
    char name[MAX_TASK_NAME_LEN];     /* 任务名称 */
    task_state_t state;               /* 当前状态 */
    uint8_t priority;                 /* 优先级 (0=最高, 255=最低) */
    uint32_t *stack;                  /* 任务栈指针 */
    uint32_t *stack_top;              /* 栈顶指针（栈向下增长） */
    uint32_t *stack_end;              /* 栈底指针 */
    uint16_t time_slice;              /* 剩余时间片（用于轮转调度） */
    uint16_t time_slice_max;          /* 最大时间片 */
    void (*entry_func)(void *);       /* 任务入口函数 */
    void *entry_arg;                  /* 任务入口函数参数 */
    uint32_t tick_count;              /* 已运行 tick 数 */
    struct rtos_tcb *next;            /* 就绪链表下一个节点 */
    struct rtos_tcb *prev;            /* 就绪链表上一个节点 */

    /* 阻塞相关字段 */
    bool blocked;                     /* 是否处于阻塞状态 */
    uint32_t block_timeout;           /* 阻塞超时 tick */
    void *block_event;                /* 等待的事件对象 */
    uint8_t block_reason;             /* 阻塞原因 */
} rtos_tcb_t;

/* ==================== 任务优先级 ==================== */

#define RTOS_PRIORITY_IDLE    255     /* 最低优先级 */
#define RTOS_PRIORITY_MIN     254     /* 最低正常优先级 */
#define RTOS_PRIORITY_MAX     0       /* 最高优先级 */

/* ==================== 同步原语 ==================== */

/**
 * 信号量类型
 *
 * 信号量是 RTOS 中最基本的同步原语：
 * - 二值信号量：计数值只有 0 和 1，用于互斥或事件通知
 * - 计数信号量：计数值可以大于 1，用于资源计数
 *
 * 信号量的两个核心操作：
 * - take (P 操作)：等待信号量，计数减 1，若为 0 则阻塞
 * - give (V 操作)：释放信号量，计数加 1，唤醒等待者
 */
typedef enum {
    SEMAPHORE_TYPE_BINARY = 0,  /* 二值信号量 */
    SEMAPHORE_TYPE_COUNTING     /* 计数信号量 */
} semaphore_type_t;

typedef struct rtos_semaphore {
    char name[MAX_TASK_NAME_LEN];       /* 信号量名称 */
    semaphore_type_t type;              /* 信号量类型 */
    uint8_t count;                      /* 当前计数值 */
    uint8_t max_count;                  /* 最大计数值（计数信号量用） */
    rtos_tcb_t *wait_list;              /* 等待此信号量的任务链表 */
    uint32_t wait_count;                /* 等待任务数量 */
} rtos_semaphore_t;

/**
 * 互斥锁类型
 *
 * 互斥锁 (Mutex) 是一种特殊的二值信号量，具有优先级继承机制。
 *
 * 优先级继承解决的问题（优先级反转）：
 * 1. 低优先级任务 L 持有互斥锁
 * 2. 高优先级任务 H 尝试获取锁，被阻塞
 * 3. 中优先级任务 M 抢占 L 执行
 * 4. 结果：H 必须等 M 执行完才能获取锁， effectively H 被 M 间接阻塞
 *
 * 优先级继承解决方案：
 * - 当 H 尝试获取被 L 持有的锁时，L 的优先级提升到 H 的优先级
 * - L 继续以高优先级执行，尽快释放锁
 * - H 获得锁后，L 恢复原始优先级
 */
typedef struct rtos_mutex {
    char name[MAX_TASK_NAME_LEN];       /* 互斥锁名称 */
    rtos_tcb_t *owner;                  /* 当前持有者 */
    uint8_t original_priority;          /* 持有者的原始优先级 */
    uint8_t count;                      /* 递归计数 */
    rtos_tcb_t *wait_list;              /* 等待此互斥锁的任务链表 */
    uint32_t wait_count;                /* 等待任务数量 */
} rtos_mutex_t;

/**
 * 消息队列类型
 *
 * 消息队列用于任务间通信 (IPC - Inter-Process Communication)。
 * 在 RTOS 中，这是任务间传递数据的主要方式。
 *
 * 消息队列的核心操作：
 * - send: 向队列发送消息，队列满时阻塞
 * - receive: 从队列接收消息，队列空时阻塞
 *
 * 消息队列的优势：
 * - 解耦发送者和接收者
 * - 支持多对多通信
 * - 避免竞态条件
 */
#define MAX_QUEUE_DEPTH 16
#define MAX_MSG_SIZE 64

typedef struct rtos_message {
    uint32_t sender_id;               /* 发送者任务 ID */
    uint32_t msg_id;                  /* 消息 ID（用于区分消息类型） */
    uint8_t data[MAX_MSG_SIZE];       /* 消息数据 */
    uint16_t data_len;                /* 数据长度 */
    struct rtos_message *next;        /* 队列下一个节点 */
} rtos_message_t;

typedef struct rtos_queue {
    char name[MAX_TASK_NAME_LEN];       /* 队列名称 */
    rtos_message_t *head;               /* 队列头（取消息端） */
    rtos_message_t *tail;               /* 队列尾（发消息端） */
    uint16_t depth;                     /* 队列深度 */
    uint16_t msg_count;                 /* 当前消息数 */
    rtos_tcb_t *wait_send;              /* 等待发送的任务 */
    rtos_tcb_t *wait_receive;           /* 等待接收的任务 */
    uint32_t wait_send_count;           /* 等待发送的任务数 */
    uint32_t wait_receive_count;        /* 等待接收的任务数 */
} rtos_queue_t;

/* ==================== 系统配置 ==================== */

#define RTOS_TICK_RATE_HZ     1000    /* 时钟频率：1ms/tick */
#define RTOS_DEFAULT_STACK    512     /* 默认栈大小（字） */
#define RTOS_MAX_PRIORITIES   32      /* 最大优先级数 */
#define RTOS_IDLE_STACK_SIZE  256     /* 空闲任务栈大小 */

/* ==================== 内核句柄 ==================== */

/**
 * RTOS 内核控制块
 *
 * 这是整个 RTOS 的核心数据结构，管理所有系统级信息。
 * 类似真实 RTOS 中的 "kernel" 或 "system" 结构体。
 */
typedef struct {
    bool running;                       /* 内核是否正在运行 */
    bool in_isr;                        /* 是否在中断中 */
    uint8_t interrupt_nest;             /* 中断嵌套深度 */
    rtos_tcb_t *idle_task;              /* 空闲任务 TCB */
    rtos_tcb_t *current_task;           /* 当前运行任务 */
    rtos_tcb_t *idle_task_tcb;          /* 空闲任务控制块 */
    rtos_tcb_t ready_list[MAX_TASKS];   /* 就绪任务链表数组（按优先级） */
    uint32_t tick_count;                /* 系统运行 tick 总数 */
    uint32_t total_tasks;               /* 已创建的任务总数 */
    uint32_t total_context_switches;    /* 上下文切换次数统计 */
    uint32_t idle_task_ticks;           /* 空闲任务运行 tick 数 */
    uint32_t free_memory;               /* 可用内存估计 */
} rtos_kernel_t;

/* ==================== 前向声明 ==================== */

typedef struct rtos_semaphore rtos_semaphore_t;
typedef struct rtos_mutex rtos_mutex_t;
typedef struct rtos_queue rtos_queue_t;

#endif /* RTOS_TYPES_H */
