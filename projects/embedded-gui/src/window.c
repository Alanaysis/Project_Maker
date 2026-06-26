/**
 * embedded-gui - 嵌入式 GUI 框架
 * src/window.c - 窗口管理系统实现
 *
 * 窗口管理:
 * - 维护窗口链表
 * - Z-order 管理 (窗口堆叠顺序)
 * - 焦点管理
 * - 窗口层级控制
 */

#include "embedded_gui.h"
#include <string.h>

/* ============================================================
 * 窗口创建/销毁 / Window Creation/Destruction
 * ============================================================ */

/**
 * 创建窗口
 * 窗口是 widget 的顶层容器
 * 每个窗口有独立的渲染区域和 z-order
 */
egui_window_t *egui_window_create(const char *title, egui_rect_t frame) {
    /* 静态窗口池 (无 malloc) / Static window pool (no malloc) */
    static egui_window_t windows[16];
    static bool initialized = false;

    if (!initialized) {
        memset(windows, 0, sizeof(windows));
        initialized = true;
    }

    /* 查找空槽位 / Find empty slot */
    for (int i = 0; i < 16; i++) {
        if (!windows[i].root.type) {
            /* 初始化窗口 / Initialize window */
            windows[i].root.type = EGUI_WIDGET_WINDOW;
            windows[i].root.visible = 1;
            windows[i].root.enabled = 1;
            windows[i].root.rect = frame;

            /* 复制标题 / Copy title */
            if (title) {
                strncpy(windows[i].title, title, sizeof(windows[i].title) - 1);
                windows[i].title[sizeof(windows[i].title) - 1] = '\0';
            } else {
                windows[i].title[0] = '\0';
            }

            windows[i].frame = frame;
            windows[i].z_order = 0;
            windows[i].focused = 0;

            return &windows[i];
        }
    }
    return NULL; /* 窗口池已满 / Window pool full */
}

/**
 * 销毁窗口
 * 仅标记为无效
 */
void egui_window_destroy(egui_window_t *win) {
    if (!win) return;
    win->root.type = EGUI_WIDGET_NONE;
    win->root.visible = 0;
    if (win->root.parent) {
        egui_widget_remove_child(win->root.parent, &win->root);
    }
}

/**
 * 聚焦窗口
 * 将窗口设为活动窗口，接收键盘事件
 */
void egui_window_focus(egui_window_t *win) {
    if (!win) return;

    /* 取消其他窗口的焦点 / Unfocus other windows */
    /* 实际实现中会遍历所有窗口 / In real implementation, iterate all windows */
    win->focused = 1;
}

/**
 * 提升窗口 (z-order +1)
 * 使窗口显示在其他窗口之上
 */
void egui_window_raise(egui_window_t *win) {
    if (!win) return;
    win->z_order++;
}

/**
 * 降低窗口 (z_order -1)
 * 使窗口显示在其他窗口之下
 */
void egui_window_lower(egui_window_t *win) {
    if (!win) return;
    if (win->z_order > 0) {
        win->z_order--;
    }
}

/* ============================================================
 * 窗口管理 (GUI 集成) / Window Management (GUI Integration)
 * ============================================================ */

/**
 * 初始化 GUI
 * 设置帧缓冲区、默认主题、显示/输入驱动
 */
void egui_init(egui_t *gui, egui_color_t *fb_mem, uint16_t width, uint16_t height) {
    /* 初始化帧缓冲区 / Init framebuffer */
    egui_fb_init(&gui->fb, fb_mem, width, height);

    /* 初始化窗口链表 / Init window list */
    gui->windows = NULL;
    gui->focused_window = NULL;

    /* 初始化事件队列 / Init event queue */
    memset(&gui->pending_event, 0, sizeof(egui_event_t));

    /* 初始化默认主题 / Init default theme */
    egui_theme_default(&gui->theme, NULL);

    /* 初始化显示/输入驱动 / Init display/input drivers */
    if (gui->display_driver) {
        gui->display_driver->init();
    }
    if (gui->input_driver) {
        gui->input_driver->init();
    }

    /* 系统状态 / System state */
    gui->tick_count = 0;
    gui->running = true;
}

/**
 * 反初始化 GUI
 */
void egui_deinit(egui_t *gui) {
    if (!gui) return;
    gui->running = false;
}

/**
 * 添加窗口到 GUI
 * 将窗口 root widget 添加到 GUI 的窗口链表
 */
void egui_gui_add_window(egui_t *gui, egui_window_t *win) {
    if (!gui || !win) return;

    /* 添加到窗口链表 / Add to window list */
    win->next = gui->windows;
    gui->windows = win;

    /* 聚焦新窗口 / Focus new window */
    gui->focused_window = win;
}

/**
 * 移除窗口从 GUI
 */
void egui_gui_remove_window(egui_t *gui, egui_window_t *win) {
    if (!gui || !win) return;

    /* 从链表移除 / Remove from list */
    if (gui->windows == win) {
        gui->windows = win->next;
        if (gui->focused_window == win) {
            gui->focused_window = gui->windows;
        }
    } else {
        egui_window_t *prev = gui->windows;
        while (prev && prev->next != win) {
            prev = prev->next;
        }
        if (prev) {
            prev->next = win->next;
        }
    }
    win->next = NULL;
}
