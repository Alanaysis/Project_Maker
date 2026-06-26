/**
 * @file rtos_queue.c
 * @brief RTOS 消息队列实现
 *
 * 本文件实现任务间通信的核心机制：消息队列。
 *
 * 为什么需要消息队列？
 *
 * 在 RTOS 中，任务之间需要交换数据。直接使用共享变量会有问题：
 * - 竞态条件：两个任务同时读写同一变量
 * - 同步困难：如何知道数据已准备好？
 * - 耦合度高：发送者和接收者必须精确同步
 *
 * 消息队列的解决方案：
 * - 解耦：发送者把消息放入队列就完成，不需要知道谁接收
 * - 同步：接收者可以等待消息（阻塞）
 * - 缓冲：多个消息可以排队等待处理
 *
 * 消息队列 vs 邮箱 vs 管道：
 * - 消息队列：固定大小的消息缓冲区
 * - 邮箱：通常指单消息缓冲（类似信号量 + 数据）
 * - 管道：流式数据，无固定消息边界
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "rtos.h"

/* ==================== 消息管理 ==================== */

/**
 * 分配消息缓冲区
 */
static rtos_message_t *queue_alloc_message(void)
{
    rtos_message_t *msg = (rtos_message_t *)rtos_malloc(sizeof(rtos_message_t));
    if (msg) {
        memset(msg, 0, sizeof(rtos_message_t));
        msg->next = NULL;
    }
    return msg;
}

/**
 * 释放消息缓冲区
 */
static void queue_free_message(rtos_message_t *msg)
{
    if (msg) {
        rtos_free(msg);
    }
}

/* ==================== 消息队列实现 ==================== */

rtos_queue_t *rtos_queue_create(const char *name, uint16_t depth)
{
    rtos_queue_t *queue = (rtos_queue_t *)rtos_malloc(sizeof(rtos_queue_t));
    if (!queue) {
        return NULL;
    }

    strncpy(queue->name, name, MAX_TASK_NAME_LEN - 1);
    queue->name[MAX_TASK_NAME_LEN - 1] = '\0';
    queue->depth = depth;
    queue->msg_count = 0;
    queue->head = NULL;
    queue->tail = NULL;
    queue->wait_send = NULL;
    queue->wait_receive = NULL;
    queue->wait_send_count = 0;
    queue->wait_receive_count = 0;

    printf("[消息队列] 创建: %s (深度: %d)\n", queue->name, depth);

    return queue;
}

rtos_status_t rtos_queue_send(rtos_queue_t *queue,
                               uint32_t msg_id,
                               const void *data,
                               uint16_t len,
                               uint32_t timeout)
{
    if (!queue || !g_kernel.current_task) {
        return RTOS_ERR_INVALID;
    }

    /*
     * 发送消息
     *
     * 如果队列未满：
     *   创建消息并加入队列尾部
     *
     * 如果队列已满：
     *   如果 timeout == 0，无限等待
     *   否则等待 timeout ticks
     *   超时则返回 RTOS_ERR_TIMEOUT
     *
     * 消息队列的 FIFO 特性：
     * - 消息按发送顺序排列
     * - 先发送的消息先被接收
     * - 这保证了消息传递的顺序性
     */

    /* 检查队列是否已满 */
    if (queue->msg_count >= queue->depth) {
        printf("[消息队列] %s: 队列已满 (%d/%d)，等待发送\n",
               queue->name, queue->msg_count, queue->depth);

        /* 阻塞等待队列空间 */
        g_kernel.current_task->blocked = true;
        g_kernel.current_task->block_event = queue;
        g_kernel.current_task->block_reason = 2;  /* 等待队列空间 */

        if (timeout > 0) {
            g_kernel.current_task->block_timeout = timeout;
        }

        g_kernel.current_task->state = TASK_STATE_BLOCKED;
        queue->wait_send_count++;

        /* 插入等待发送链表 */
        g_kernel.current_task->next = queue->wait_send;
        g_kernel.current_task->prev = NULL;
        if (queue->wait_send) {
            queue->wait_send->prev = g_kernel.current_task;
        }
        queue->wait_send = g_kernel.current_task;

        /* 触发调度 */
        rtos_schedule();

        /* 被唤醒后继续 */
        queue->wait_send_count--;
    }

    /* 创建消息 */
    rtos_message_t *msg = queue_alloc_message();
    if (!msg) {
        return RTOS_ERR_NO_MEM;
    }

    msg->sender_id = g_kernel.current_task->priority;
    msg->msg_id = msg_id;
    msg->data_len = (len > MAX_MSG_SIZE) ? MAX_MSG_SIZE : len;
    if (data) {
        memcpy(msg->data, data, msg->data_len);
    }

    /* 加入队列尾部 */
    msg->next = NULL;
    if (queue->tail) {
        queue->tail->next = msg;
    } else {
        queue->head = msg;
    }
    queue->tail = msg;
    queue->msg_count++;

    printf("[消息队列] %s: %s 发送消息 (ID: %lu, 队列: %d/%d)\n",
           queue->name, g_kernel.current_task->name,
           (unsigned long)msg_id, queue->msg_count, queue->depth);

    /* 如果有等待接收的任务，唤醒一个 */
    if (queue->wait_receive_count > 0 && queue->wait_receive) {
        rtos_tcb_t *receiver = queue->wait_receive;
        queue->wait_receive = receiver->next;
        if (queue->wait_receive) {
            queue->wait_receive->prev = NULL;
        }
        receiver->next = NULL;
        receiver->prev = NULL;

        receiver->blocked = false;
        receiver->block_event = NULL;
        receiver->state = TASK_STATE_READY;
        queue->wait_receive_count--;

        printf("[消息队列] %s: 唤醒接收者 %s\n",
               queue->name, receiver->name);
    }

    /* 触发调度 */
    rtos_schedule();

    return RTOS_OK;
}

rtos_status_t rtos_queue_receive(rtos_queue_t *queue,
                                  uint32_t *msg_id,
                                  void *data,
                                  uint16_t max_len,
                                  uint32_t timeout)
{
    if (!queue || !g_kernel.current_task) {
        return RTOS_ERR_INVALID;
    }

    /*
     * 接收消息
     *
     * 如果队列不为空：
     *   从队列头部取出消息
     *   复制数据到缓冲区
     *
     * 如果队列为空：
     *   阻塞等待消息
     *
     * 注意：消息队列的接收是"消耗性"的。
     * 一旦消息被接收，它就从队列中移除。
     */

    /* 检查队列是否为空 */
    if (queue->msg_count == 0) {
        printf("[消息队列] %s: 队列为空，等待接收\n", queue->name);

        /* 阻塞等待消息 */
        g_kernel.current_task->blocked = true;
        g_kernel.current_task->block_event = queue;
        g_kernel.current_task->block_reason = 3;  /* 等待消息 */

        if (timeout > 0) {
            g_kernel.current_task->block_timeout = timeout;
        }

        g_kernel.current_task->state = TASK_STATE_BLOCKED;
        queue->wait_receive_count++;

        /* 插入等待接收链表 */
        g_kernel.current_task->next = queue->wait_receive;
        g_kernel.current_task->prev = NULL;
        if (queue->wait_receive) {
            queue->wait_receive->prev = g_kernel.current_task;
        }
        queue->wait_receive = g_kernel.current_task;

        /* 触发调度 */
        rtos_schedule();

        /* 被唤醒后继续 */
        queue->wait_receive_count--;

        /* 再次检查队列是否有消息 */
        if (queue->msg_count == 0) {
            return RTOS_ERR_TIMEOUT;
        }
    }

    /* 从队列头部取出消息 */
    rtos_message_t *msg = queue->head;
    queue->head = msg->next;
    if (!queue->head) {
        queue->tail = NULL;
    }
    queue->msg_count--;

    /* 复制数据 */
    if (msg_id) {
        *msg_id = msg->msg_id;
    }
    if (data && msg->data_len > 0) {
        uint16_t copy_len = (msg->data_len > max_len) ? max_len : msg->data_len;
        memcpy(data, msg->data, copy_len);
    }

    printf("[消息队列] %s: %s 接收消息 (ID: %lu, 队列: %d/%d)\n",
           queue->name, g_kernel.current_task->name,
           (unsigned long)(msg_id ? *msg_id : 0),
           queue->msg_count, queue->depth);

    /* 释放消息缓冲区 */
    queue_free_message(msg);

    /* 如果有等待发送的任务，唤醒一个 */
    if (queue->wait_send_count > 0 && queue->wait_send) {
        rtos_tcb_t *sender = queue->wait_send;
        queue->wait_send = sender->next;
        if (queue->wait_send) {
            queue->wait_send->prev = NULL;
        }
        sender->next = NULL;
        sender->prev = NULL;

        sender->blocked = false;
        sender->block_event = NULL;
        sender->state = TASK_STATE_READY;
        queue->wait_send_count--;

        printf("[消息队列] %s: 唤醒发送者 %s\n",
               queue->name, sender->name);
    }

    /* 触发调度 */
    rtos_schedule();

    return RTOS_OK;
}
