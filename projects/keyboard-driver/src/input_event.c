#include "../include/keyboard.h"
#include <stdio.h>
#include <string.h>

/* 输入事件系统配置 */
#define MAX_EVENT_HANDLERS  8
#define EVENT_BUFFER_SIZE   128

/* 事件系统 */
typedef struct {
    event_handler_t handlers[MAX_EVENT_HANDLERS];   /* 事件处理器列表 */
    int handler_count;                              /* 处理器数量 */
    key_event_t buffer[EVENT_BUFFER_SIZE];          /* 事件缓冲区 */
    int buffer_head;                                /* 缓冲区头 */
    int buffer_tail;                                /* 缓冲区尾 */
    bool initialized;                               /* 初始化标志 */
} input_event_system_t;

/* 全局事件系统实例 */
static input_event_system_t g_event_system;

/* 初始化输入事件系统 */
int input_event_init(void)
{
    printf("[Input] Initializing input event system\n");

    memset(&g_event_system, 0, sizeof(input_event_system_t));
    g_event_system.initialized = true;

    printf("[Input] Event system initialized\n");
    printf("[Input] Max handlers: %d\n", MAX_EVENT_HANDLERS);
    printf("[Input] Buffer size: %d\n", EVENT_BUFFER_SIZE);

    return KB_OK;
}

/* 注册事件处理器 */
int input_event_register_handler(event_handler_t handler)
{
    if (handler == NULL) {
        return KB_ERR_INIT;
    }

    if (g_event_system.handler_count >= MAX_EVENT_HANDLERS) {
        printf("[Input] Error: Max handlers reached\n");
        return KB_ERR_INIT;
    }

    g_event_system.handlers[g_event_system.handler_count++] = handler;
    printf("[Input] Event handler registered (total: %d)\n", g_event_system.handler_count);

    return KB_OK;
}

/* 注销事件处理器 */
int input_event_unregister_handler(event_handler_t handler)
{
    if (handler == NULL) {
        return KB_ERR_INIT;
    }

    for (int i = 0; i < g_event_system.handler_count; i++) {
        if (g_event_system.handlers[i] == handler) {
            /* 移除处理器，后面的前移 */
            for (int j = i; j < g_event_system.handler_count - 1; j++) {
                g_event_system.handlers[j] = g_event_system.handlers[j + 1];
            }
            g_event_system.handler_count--;
            printf("[Input] Event handler unregistered (total: %d)\n", g_event_system.handler_count);
            return KB_OK;
        }
    }

    printf("[Input] Warning: Handler not found\n");
    return KB_ERR_INIT;
}

/* 分发事件给所有处理器 */
static void dispatch_event(const key_event_t *event)
{
    for (int i = 0; i < g_event_system.handler_count; i++) {
        if (g_event_system.handlers[i] != NULL) {
            g_event_system.handlers[i](event);
        }
    }
}

/* 提交输入事件 */
int input_event_report(const key_event_t *event)
{
    if (event == NULL || !g_event_system.initialized) {
        return KB_ERR_INIT;
    }

    /* 检查缓冲区是否已满 */
    int next_tail = (g_event_system.buffer_tail + 1) % EVENT_BUFFER_SIZE;
    if (next_tail == g_event_system.buffer_head) {
        printf("[Input] Warning: Event buffer full, dropping event\n");
        return KB_ERR_INIT;
    }

    /* 将事件加入缓冲区 */
    g_event_system.buffer[g_event_system.buffer_tail] = *event;
    g_event_system.buffer_tail = next_tail;

    /* 分发事件 */
    dispatch_event(event);

    return KB_OK;
}

/* 获取输入事件 */
int input_event_get(key_event_t *event)
{
    if (event == NULL || !g_event_system.initialized) {
        return KB_ERR_INIT;
    }

    /* 检查缓冲区是否为空 */
    if (g_event_system.buffer_head == g_event_system.buffer_tail) {
        return -1;
    }

    /* 从缓冲区取出事件 */
    *event = g_event_system.buffer[g_event_system.buffer_head];
    g_event_system.buffer_head = (g_event_system.buffer_head + 1) % EVENT_BUFFER_SIZE;

    return KB_OK;
}

/* 清空事件缓冲区 */
void input_event_clear(void)
{
    g_event_system.buffer_head = 0;
    g_event_system.buffer_tail = 0;
}

/* 获取缓冲区中的事件数量 */
int input_event_count(void)
{
    if (g_event_system.buffer_tail >= g_event_system.buffer_head) {
        return g_event_system.buffer_tail - g_event_system.buffer_head;
    } else {
        return EVENT_BUFFER_SIZE - g_event_system.buffer_head + g_event_system.buffer_tail;
    }
}

/* 打印事件信息 */
void input_event_dump(const key_event_t *event)
{
    if (event == NULL) {
        return;
    }

    const char *state_str = (event->state == EV_KEY_PRESS) ? "PRESS" : "RELEASE";
    printf("[Input] Event: key=0x%02X, state=%s, row=%d, col=%d, time=%u\n",
           event->keycode, state_str, event->row, event->col, event->timestamp);
}

/* 打印事件系统状态 */
void input_event_dump_status(void)
{
    printf("\n[Input] Event System Status:\n");
    printf("  Initialized: %s\n", g_event_system.initialized ? "Yes" : "No");
    printf("  Handlers: %d/%d\n", g_event_system.handler_count, MAX_EVENT_HANDLERS);
    printf("  Events in buffer: %d/%d\n", input_event_count(), EVENT_BUFFER_SIZE);
    printf("\n");
}
