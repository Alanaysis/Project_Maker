/**
 * embedded-gui - 嵌入式 GUI 框架
 * src/event.c - 事件处理系统实现
 *
 * 事件处理是 GUI 框架的核心组件
 * 它负责:
 * 1. 收集输入事件 (触摸、按键)
 * 2. 分发到正确的 widget
 * 3. 处理事件传播 (冒泡/捕获)
 * 4. 管理焦点
 *
 * 嵌入式系统的特殊考虑:
 * - 事件队列大小有限
 * - 需要去抖动 (触摸/按键)
 * - 事件优先级 (触摸 > 按键)
 */

#include "embedded_gui.h"
#include <string.h>

/* ============================================================
 * 事件队列 / Event Queue
 *
 * 嵌入式系统中使用固定大小的环形队列
 * 避免动态内存分配
 */

#define EVENT_QUEUE_SIZE 32
static egui_event_t egui_event_queue[EVENT_QUEUE_SIZE];
static uint16_t egui_event_head = 0;
static uint16_t egui_event_tail = 0;
static uint16_t egui_event_count = 0;

/**
 * 检查事件队列是否为空
 */
bool egui_event_queue_empty(void) {
    return egui_event_count == 0;
}

/**
 * 检查事件队列是否已满
 */
bool egui_event_queue_full(void) {
    return egui_event_count >= EVENT_QUEUE_SIZE;
}

/**
 * 向事件队列推送事件
 * 如果队列满，丢弃最旧的事件
 */
void egui_event_queue_push(egui_event_t *event) {
    if (!event) return;

    if (egui_event_queue_full()) {
        /* 队列满: 丢弃最旧的事件 / Queue full: discard oldest */
        egui_event_head = (egui_event_head + 1) % EVENT_QUEUE_SIZE;
        egui_event_count--;
    }

    /* 复制事件到队列 / Copy event to queue */
    memcpy(&egui_event_queue[egui_event_tail], event, sizeof(egui_event_t));
    egui_event_tail = (egui_event_tail + 1) % EVENT_QUEUE_SIZE;
    egui_event_count++;
}

/**
 * 从事件队列获取事件
 */
bool egui_event_queue_pop(egui_event_t *event) {
    if (egui_event_queue_empty()) return false;

    memcpy(event, &egui_event_queue[egui_event_head], sizeof(egui_event_t));
    egui_event_head = (egui_event_head + 1) % EVENT_QUEUE_SIZE;
    egui_event_count--;
    return true;
}

/* ============================================================
 * 命中测试 / Hit Testing
 *
 * 确定哪个 widget 被触摸/点击
 * 从最顶层 (最后渲染) 的 widget 开始检查
 * 找到第一个包含该点的 widget
 */

/**
 * 检查点是否在 widget 矩形内
 */
static bool egui_point_in_rect(egui_point_t point, egui_rect_t rect) {
    return point.x >= rect.x && point.x < (int16_t)(rect.x + rect.width) &&
           point.y >= rect.y && point.y < (int16_t)(rect.y + rect.height);
}

/**
 * 命中测试: 从最深层 widget 开始查找
 * 递归: 先检查子组件，再检查自身
 */
egui_widget_t *egui_hit_test(egui_widget_t *w, egui_point_t pos) {
    if (!w || !w->visible || !w->enabled) return NULL;

    /* 先检查子组件 (从最顶层开始) / Check children first (from top layer) */
    egui_widget_t *child = w->child;
    while (child) {
        egui_widget_t *hit = egui_hit_test(child, pos);
        if (hit) return hit;
        child = child->next;
    }

    /* 检查自身 / Check self */
    if (egui_point_in_rect(pos, w->rect)) {
        return w;
    }

    return NULL;
}

/* ============================================================
 * 事件分发 / Event Dispatch
 *
 * 事件分发流程:
 * 1. 获取事件
 * 2. 命中测试: 找到目标 widget
 * 3. 设置焦点
 * 4. 调用 widget 的事件回调
 * 5. 事件冒泡: 向父组件传播
 */

/**
 * 分发事件到 widget 及其父组件
 * 实现事件冒泡: 从目标 widget 向上传播
 */
void egui_event_dispatch(egui_t *gui, const egui_event_t *event) {
    if (!gui || !event || event->type == EGUI_EVENT_NONE) return;

    /* 对于触摸事件，进行命中测试 / For touch events, do hit testing */
    if (event->type == EGUI_EVENT_TOUCH_PRESS || event->type == EGUI_EVENT_TOUCH_MOVE) {
        egui_widget_t *target = NULL;

        /* 从最顶层窗口开始 / Start from top window */
        egui_window_t *win = gui->windows;
        while (win) {
            target = egui_hit_test(&win->root, event->pos);
            if (target) break;
            win = win->next;
        }

        if (target) {
            /* 设置焦点 / Set focus */
            if (gui->focused_window) {
                gui->focused_window->root.state &= ~EGUI_STATE_FOCUSED;
            }
            /* 沿着 widget 路径设置 FOCUSED 状态 / Set FOCUSED along widget path */
            egui_widget_t *w = target;
            while (w) {
                w->state |= EGUI_STATE_FOCUSED;
                w = w->parent;
            }

            /* 调用目标 widget 的事件回调 / Call target widget event callback */
            if (target->on_event) {
                target->on_event(target, event);
            }

            /* 事件冒泡: 向父组件传播 / Bubble: propagate to parents */
            egui_widget_t *parent = target->parent;
            while (parent) {
                if (parent->on_event) {
                    parent->on_event(parent, event);
                }
                parent = parent->parent;
            }
        }
    } else {
        /* 非触摸事件: 发送到聚焦窗口 / Non-touch events: send to focused window */
        if (gui->focused_window && gui->focused_window->root.on_event) {
            gui->focused_window->root.on_event(&gui->focused_window->root, event);
        }
    }

    /* 更新系统滴答 / Update system tick */
    gui->tick_count++;
}

/* ============================================================
 * 核心事件循环 / Core Event Loop
 *
 * GUI 的核心循环:
 * 1. 轮询输入事件
 * 2. 分发事件到 widget
 * 3. 重新布局 (如果需要)
 * 4. 渲染所有可见 widget
 * 5. 刷新到显示
 *
 * 这是一个典型的 "事件驱动" GUI 架构
 */

/**
 * 运行 GUI 主循环
 * 返回 0 表示正常退出，-1 表示错误
 */
int egui_run(egui_t *gui) {
    if (!gui || !gui->running) return -1;

    while (gui->running) {
        /* 1. 轮询输入事件 / Poll input events */
        if (gui->input_driver && gui->input_driver->has_event()) {
            egui_event_t event;
            if (gui->input_driver->poll_event(&event)) {
                event.timestamp = gui->tick_count;
                egui_event_dispatch(gui, &event);
            }
        }

        /* 2. 处理事件队列 / Process event queue */
        egui_event_t event;
        while (egui_event_queue_pop(&event)) {
            egui_event_dispatch(gui, &event);
        }

        /* 3. 渲染所有窗口 / Render all windows */
        egui_window_t *win = gui->windows;
        while (win) {
            if (win->root.visible) {
                /* 渲染窗口 / Render window */
                egui_widget_render(&win->root, &gui->fb);
            }
            win = win->next;
        }

        /* 4. 刷新到显示 / Flush to display */
        if (gui->display_driver && gui->display_driver->flush) {
            egui_rect_t dirty_rect = {0, 0, gui->fb.width, gui->fb.height};
            gui->display_driver->flush(&gui->fb, &dirty_rect);
        }

        /* 5. 短暂延迟 (嵌入式系统需要控制刷新率) / Brief delay (control refresh rate) */
        /* 实际实现中会使用定时器或 RTOS 任务延迟 / Real implementation uses timer or RTOS delay */
        /* 这里简化处理 / Simplified here */
    }

    return 0;
}

/**
 * 停止 GUI
 */
void egui_stop(egui_t *gui) {
    if (gui) {
        gui->running = false;
    }
}
