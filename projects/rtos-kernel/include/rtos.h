/**
 * @file rtos.h
 * @brief RTOS 内核公共 API
 *
 * 本文件定义了 RTOS 内核的所有公共 API 接口。
 * 这是用户与 RTOS 交互的主要入口点。
 *
 * API 分类：
 * 1. 内核管理：初始化、启动、运行
 * 2. 任务管理：创建、删除、挂起、恢复
 * 3. 调度器：手动触发调度
 * 4. 同步原语：信号量、互斥锁
 * 5. 消息队列：发送、接收
 * 6. 时间管理：延时、获取 tick
 * 7. 内存管理：分配、释放
 */

#ifndef RTOS_H
#define RTOS_H

#include "rtos_types.h"

/* ==================== 内核管理 ==================== */

/**
 * 初始化 RTOS 内核
 *
 * 在调用任何其他 RTOS API 之前必须先调用此函数。
 * 它负责：
 * - 初始化内核控制块
 * - 创建空闲任务
 * - 初始化就绪链表
 * - 设置初始运行任务
 */
void rtos_init(void);

/**
 * 启动 RTOS 调度器
 *
 * 调用此函数后，RTOS 开始调度任务执行。
 * 在启动前必须至少创建一个用户任务。
 * 启动后，调度器会根据优先级选择最高优先级的就绪任务运行。
 */
void rtos_start(void);

/**
 * 让当前任务进入空闲循环
 *
 * 通常在 rtos_start() 中被调用。
 * 当没有更高优先级的任务可运行时，空闲任务会执行此函数。
 * 空闲任务是系统中唯一永远不会阻塞的任务。
 */
void rtos_idle_loop(void);

/* ==================== 任务管理 ==================== */

/**
 * 创建任务
 *
 * @param name       任务名称（用于调试）
 * @param entry_func 任务入口函数
 * @param arg        传递给入口函数的参数
 * @param stack_size 栈大小（以字为单位）
 * @param priority   任务优先级（0=最高，255=最低）
 * @return 任务控制块指针，创建失败返回 NULL
 *
 * 任务创建过程：
 * 1. 分配 TCB 结构
 * 2. 分配任务栈空间
 * 3. 初始化栈（模拟任务启动时的寄存器状态）
 * 4. 将任务加入就绪链表
 * 5. 如果当前没有任务在运行，设置此任务为当前任务
 */
rtos_tcb_t *rtos_task_create(const char *name,
                              void (*entry_func)(void *),
                              void *arg,
                              uint32_t stack_size,
                              uint8_t priority);

/**
 * 删除任务
 *
 * @param task 要删除的任务控制块指针
 *
 * 删除任务会：
 * 1. 从就绪链表中移除
 * 2. 释放任务栈内存
 * 3. 释放 TCB 内存
 * 4. 如果删除的是当前任务，触发重新调度
 */
void rtos_task_delete(rtos_tcb_t *task);

/**
 * 挂起任务
 *
 * @param task 要挂起的任务
 *
 * 挂起的任务不会被调度器选择，直到被恢复。
 * 挂起不同于阻塞：阻塞是任务主动等待事件，挂起是被动的。
 */
void rtos_task_suspend(rtos_tcb_t *task);

/**
 * 恢复任务
 *
 * @param task 要恢复的任务
 */
void rtos_task_resume(rtos_tcb_t *task);

/**
 * 将当前任务移至就绪链表尾部（让出 CPU）
 *
 * 用于实现协作式多任务。
 * 调用此任务后，调度器会选择下一个就绪任务运行。
 */
void rtos_task_yield(void);

/**
 * 获取当前运行任务的 TCB
 *
 * @return 当前运行任务的 TCB 指针
 */
rtos_tcb_t *rtos_task_current(void);

/* ==================== 调度器 ==================== */

/**
 * 触发调度器决策
 *
 * 调度器会根据优先级选择最高优先级的就绪任务运行。
 * 如果选择的任务不是当前任务，则执行上下文切换。
 *
 * 调度算法：
 * - 优先级抢占式调度：总是运行最高优先级的就绪任务
 * - 同级轮转调度：相同优先级的任务按 FIFO 轮流执行
 */
void rtos_schedule(void);

/**
 * 获取下一个要运行的任务
 *
 * 不执行上下文切换，只返回调度决策结果。
 * 用于分析和调试。
 *
 * @return 下一个应该运行的任务 TCB
 */
rtos_tcb_t *rtos_schedule_next(void);

/* ==================== 同步原语 - 信号量 ==================== */

/**
 * 创建信号量
 *
 * @param name   信号量名称
 * @param type   信号量类型（二值或计数）
 * @param initial_count 初始计数值
 * @param max_count 最大计数值（仅计数信号量用）
 * @return 信号量指针
 */
rtos_semaphore_t *rtos_semaphore_create(const char *name,
                                         semaphore_type_t type,
                                         uint8_t initial_count,
                                         uint8_t max_count);

/**
 * 获取信号量（take/P 操作）
 *
 * @param sem      信号量指针
 * @param timeout  超时 tick 数，0 表示无限等待
 * @return RTOS_OK 成功获取，RTOS_ERR_TIMEOUT 超时
 *
 * 如果信号量计数 > 0，计数减 1 并立即返回。
 * 如果计数 = 0，当前任务进入阻塞状态等待。
 */
rtos_status_t rtos_semaphore_take(rtos_semaphore_t *sem, uint32_t timeout);

/**
 * 释放信号量（give/V 操作）
 *
 * @param sem 信号量指针
 * @return RTOS_OK 成功释放
 *
 * 计数加 1，如果有等待任务，唤醒一个。
 */
rtos_status_t rtos_semaphore_give(rtos_semaphore_t *sem);

/* ==================== 同步原语 - 互斥锁 ==================== */

/**
 * 创建互斥锁
 *
 * @param name 互斥锁名称
 * @return 互斥锁指针
 */
rtos_mutex_t *rtos_mutex_create(const char *name);

/**
 * 获取互斥锁
 *
 * @param mutex    互斥锁指针
 * @param timeout  超时 tick 数
 * @return RTOS_OK 成功获取
 *
 * 如果互斥锁未被持有，当前任务成为持有者。
 * 如果已被持有，调用者阻塞直到锁可用。
 * 如果持有者优先级低于调用者，触发优先级继承。
 */
rtos_status_t rtos_mutex_take(rtos_mutex_t *mutex, uint32_t timeout);

/**
 * 释放互斥锁
 *
 * @param mutex 互斥锁指针
 * @return RTOS_OK 成功释放
 *
 * 释放时如果有等待者，唤醒最高优先级的等待者。
 * 如果当前持有者不是锁的拥有者，返回错误。
 */
rtos_status_t rtos_mutex_give(rtos_mutex_t *mutex);

/* ==================== 消息队列 ==================== */

/**
 * 创建消息队列
 *
 * @param name   队列名称
 * @param depth  队列深度（可容纳的消息数）
 * @param msg_size 消息大小（字节）
 * @return 队列指针
 */
rtos_queue_t *rtos_queue_create(const char *name, uint16_t depth);

/**
 * 向队列发送消息
 *
 * @param queue   队列指针
 * @param msg_id  消息 ID（用于区分消息类型）
 * @param data    消息数据
 * @param len     数据长度
 * @param timeout 超时 tick 数
 * @return RTOS_OK 发送成功
 *
 * 如果队列已满，发送者阻塞直到队列有空间。
 */
rtos_status_t rtos_queue_send(rtos_queue_t *queue,
                               uint32_t msg_id,
                               const void *data,
                               uint16_t len,
                               uint32_t timeout);

/**
 * 从队列接收消息
 *
 * @param queue   队列指针
 * @param msg_id  输出的消息 ID
 * @param data    输出的数据缓冲区
 * @param max_len 缓冲区最大长度
 * @param timeout 超时 tick 数
 * @return RTOS_OK 接收成功
 *
 * 如果队列为空，接收者阻塞直到有消息可用。
 */
rtos_status_t rtos_queue_receive(rtos_queue_t *queue,
                                  uint32_t *msg_id,
                                  void *data,
                                  uint16_t max_len,
                                  uint32_t timeout);

/* ==================== 时间管理 ==================== */

/**
 * 延时指定 tick 数
 *
 * @param ticks 延时的 tick 数
 *
 * 调用此函数的任务会进入阻塞状态，直到指定的 tick 数到达。
 * 这是任务同步的基本方式之一。
 */
void rtos_delay(uint32_t ticks);

/**
 * 获取系统 tick 计数
 *
 * @return 系统启动以来的总 tick 数
 */
uint32_t rtos_get_tick_count(void);

/**
 * 模拟时钟中断（tick 中断）
 *
 * 在真实系统中，这由硬件定时器中断触发。
 * 在我们的模拟中，由主循环调用。
 *
 * 每个 tick 会：
 * - 增加系统 tick 计数
 * - 减少所有就绪任务的剩余时间片
 * - 检查阻塞任务的超时
 * - 触发调度
 */
void rtos_tick(void);

/* ==================== 内存管理 ==================== */

/**
 * 分配内存
 *
 * @param size 需要的字节数
 * @return 分配的内存指针
 */
void *rtos_malloc(uint32_t size);

/**
 * 释放内存
 *
 * @param ptr 要释放的内存指针
 */
void rtos_free(void *ptr);

/* ==================== 调试和统计 ==================== */

/**
 * 打印系统状态信息
 *
 * 用于调试和监控：
 * - 所有任务的状态
 * - 就绪链表
 * - 系统统计信息
 */
void rtos_print_status(void);

/**
 * 打印就绪链表
 */
void rtos_print_ready_list(void);

/**
 * 打印任务状态
 */
void rtos_print_task_status(rtos_tcb_t *task);

#endif /* RTOS_H */
