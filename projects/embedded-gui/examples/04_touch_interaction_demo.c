/**
 * embedded-gui - 嵌入式 GUI 框架
 * examples/04_touch_interaction_demo.c
 *
 * 触摸交互演示
 * 展示触摸事件处理:
 * - 触摸按下/释放检测
 * - 拖拽操作
 * - 滑动操作
 * - 长按检测
 *
 * 这个演示展示了:
 * 1. 触摸事件的生命周期
 * 2. 拖拽 widget 的实现
 * 3. 滑动检测
 * 4. 交互反馈 (视觉)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "embedded_gui.h"

/* 模拟帧缓冲区 / Mock framebuffer */
#define SCREEN_WIDTH  480
#define SCREEN_HEIGHT 320
static egui_color_t framebuffer[SCREEN_WIDTH * SCREEN_HEIGHT];

/* 模拟输入驱动 / Mock input driver */
static bool mock_input_init(void) { return true; }
static bool mock_input_has_event(void) { return false; }
static bool mock_input_poll_event(egui_event_t *event) { (void)event; return false; }
static egui_input_driver_t mock_input_driver = {
    .init = mock_input_init,
    .poll_event = mock_input_poll_event,
    .has_event = mock_input_has_event,
};

/* 拖拽状态 / Drag state */
typedef struct {
    egui_widget_t *widget;
    int start_x;
    int start_y;
    int offset_x;
    int offset_y;
    bool dragging;
} drag_state_t;

static drag_state_t drag_state;

/* 滑动检测状态 / Swipe detection state */
typedef struct {
    int start_x;
    int start_y;
    int end_x;
    int end_y;
    bool active;
    int min_distance;
} swipe_state_t;

static swipe_state_t swipe_state;

/* 长按检测状态 / Long press detection state */
typedef struct {
    int press_x;
    int press_y;
    uint32_t press_time;
    uint32_t long_press_threshold;
    bool detected;
    bool active;
} long_press_state_t;

static long_press_state_t long_press_state;

/* ============================================================
 * 触摸事件处理 / Touch event handling
 * ============================================================ */

/**
 * 处理触摸按下事件
 * 记录起始位置，准备拖拽
 */
static void handle_touch_press(egui_t *gui, egui_event_t *event) {
    drag_state.dragging = false;
    drag_state.start_x = event->pos.x;
    drag_state.start_y = event->pos.y;
    drag_state.offset_x = 0;
    drag_state.offset_y = 0;

    /* 命中测试: 找到被点击的 widget / Hit test: find clicked widget */
    egui_widget_t *target = egui_hit_test(&gui->windows->root, event->pos);
    if (target) {
        drag_state.widget = target;
        printf("Touch press at (%d, %d) on widget type %d\n",
               event->pos.x, event->pos.y, target->type);
    }

    /* 记录长按起始时间 / Record long press start time */
    long_press_state.press_x = event->pos.x;
    long_press_state.press_y = event->pos.y;
    long_press_state.press_time = gui->tick_count;
    long_press_state.detected = false;
    long_press_state.active = true;

    /* 初始化滑动检测 / Init swipe detection */
    swipe_state.start_x = event->pos.x;
    swipe_state.start_y = event->pos.y;
    swipe_state.active = true;
}

/**
 * 处理触摸移动事件
 * 计算位移，更新 widget 位置
 */
static void handle_touch_move(egui_t *gui, egui_event_t *event) {
    int dx = event->pos.x - drag_state.start_x;
    int dy = event->pos.y - drag_state.start_y;

    /* 检测拖拽 (移动超过阈值) / Detect drag (movement exceeds threshold) */
    if (!drag_state.dragging && (abs(dx) > 5 || abs(dy) > 5)) {
        drag_state.dragging = true;
        printf("Drag started!\n");
    }

    if (drag_state.dragging && drag_state.widget) {
        /* 更新 widget 位置 / Update widget position */
        drag_state.offset_x = dx;
        drag_state.offset_y = dy;

        egui_rect_t new_rect = drag_state.widget->rect;
        new_rect.x += dx;
        new_rect.y += dy;

        /* 边界检查 / Boundary check */
        if (new_rect.x < 0) new_rect.x = 0;
        if (new_rect.y < 0) new_rect.y = 0;
        if (new_rect.x + new_rect.width > SCREEN_WIDTH) {
            new_rect.x = SCREEN_WIDTH - new_rect.width;
        }
        if (new_rect.y + new_rect.height > SCREEN_HEIGHT) {
            new_rect.y = SCREEN_HEIGHT - new_rect.height;
        }

        drag_state.widget->rect = new_rect;
        printf("Dragged to (%d, %d)\n", new_rect.x, new_rect.y);
    }

    /* 更新滑动状态 / Update swipe state */
    swipe_state.end_x = event->pos.x;
    swipe_state.end_y = event->pos.y;
}

/**
 * 处理触摸释放事件
 * 检测滑动、长按
 */
static void handle_touch_release(egui_t *gui, egui_event_t *event) {
    if (drag_state.dragging) {
        printf("Drag ended at (%d, %d)\n", event->pos.x, event->pos.y);
    }

    /* 检测滑动 / Detect swipe */
    if (swipe_state.active) {
        int dx = swipe_state.end_x - swipe_state.start_x;
        int dy = swipe_state.end_y - swipe_state.start_y;
        int distance = (int)sqrt((double)dx * dx + (double)dy * dy);

        if (distance > 30) { /* 最小滑动距离 / Minimum swipe distance */
            if (abs(dx) > abs(dy)) {
                printf("Swipe %s (%d px)\n", dx > 0 ? "RIGHT" : "LEFT", abs(dx));
            } else {
                printf("Swipe %s (%d px)\n", dy > 0 ? "DOWN" : "UP", abs(dy));
            }
        }
        swipe_state.active = false;
    }

    /* 检测长按 / Detect long press */
    if (long_press_state.active) {
        uint32_t duration = gui->tick_count - long_press_state.press_time;
        if (duration > long_press_state.long_press_threshold) {
            printf("Long press detected at (%d, %d) (%lu ms)\n",
                   long_press_state.press_x, long_press_state.press_y,
                   (unsigned long)duration);
            long_press_state.detected = true;
        }
        long_press_state.active = false;
    }

    drag_state.dragging = false;
}

/* ============================================================
 * 主程序
 * ============================================================ */

int main(void) {
    printf("=== Embedded GUI - Touch Interaction Demo ===\n");
    printf("Screen: %dx%d RGB565\n\n", SCREEN_WIDTH, SCREEN_HEIGHT);

    /* 初始化 / Initialize */
    egui_t gui;
    memset(&gui, 0, sizeof(gui));
    gui.input_driver = &mock_input_driver;
    egui_init(&gui, framebuffer, SCREEN_WIDTH, SCREEN_HEIGHT);
    egui_theme_light(&gui.theme, egui_font_get_builtin());

    /* 创建窗口 / Create window */
    egui_rect_t win_rect = {0, 0, SCREEN_WIDTH, SCREEN_HEIGHT};
    egui_window_t *win = egui_window_create("Touch Interaction", win_rect);
    egui_gui_add_window(&gui, win);

    /* 标题 / Title */
    egui_label_create(&win->root, "Touch & Drag Demo",
        (egui_rect_t){60, 15, 360, 35));

    /* 可拖拽的 widget / Draggable widget */
    egui_widget_t *draggable = egui_button_create(&win->root, "Drag Me!",
        (egui_rect_t){180, 80, 120, 60));
    draggable->style.bg_color = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9);

    /* 拖拽说明 / Drag instructions */
    egui_label_create(&win->root, "1. Press & drag the button",
        (egui_rect_t){80, 160, 320, 25));
    egui_label_create(&win->root, "2. Swipe anywhere",
        (egui_rect_t){80, 190, 320, 25));
    egui_label_create(&win->root, "3. Long press anywhere",
        (egui_rect_t){80, 220, 320, 25));

    /* 状态显示 / Status display */
    egui_widget_t *status_label = egui_label_create(&win->root, "Status: Idle",
        (egui_rect_t){80, 260, 320, 25));

    /* 布局 / Layout */
    egui_layout_absolute(&win->root);

    /* 渲染 / Render */
    printf("Rendering initial frame...\n");
    egui_widget_render(&win->root, &gui.fb);

    /* ============================================================
     * 模拟触摸交互 / Simulate touch interactions
     * ============================================================ */

    printf("\n--- Simulating Touch Interactions ---\n\n");

    /* 1. 触摸按下 (在按钮上) / Touch press (on button) */
    egui_event_t event = {
        .type = EGUI_EVENT_TOUCH_PRESS,
        .pos = {220, 100}, /* 在按钮上 / On button */
        .timestamp = 0,
    };
    handle_touch_press(&gui, &event);
    egui_event_dispatch(&gui, &event);

    /* 2. 触摸移动 (拖拽) / Touch move (drag) */
    event.type = EGUI_EVENT_TOUCH_MOVE;
    event.pos.x = 280;
    event.pos.y = 140;
    handle_touch_move(&gui, &event);
    egui_event_dispatch(&gui, &event);

    /* 重新渲染拖拽后的状态 / Re-render dragged state */
    egui_widget_render(&win->root, &gui.fb);
    printf("\nAfter drag: button moved to (%d, %d)\n",
           draggable->rect.x, draggable->rect.y);

    /* 3. 触摸释放 / Touch release */
    event.type = EGUI_EVENT_TOUCH_RELEASE;
    event.pos.x = 300;
    event.pos.y = 150;
    handle_touch_release(&gui, &event);

    /* 4. 模拟滑动 / Simulate swipe */
    printf("\nSimulating swipe...\n");
    swipe_state.active = true;
    swipe_state.start_x = 50;
    swipe_state.start_y = 160;
    swipe_state.end_x = 400;
    swipe_state.end_y = 160;
    handle_touch_release(&gui, &event);

    /* 5. 模拟长按 / Simulate long press */
    printf("\nSimulating long press...\n");
    long_press_state.active = true;
    long_press_state.press_x = 240;
    long_press_state.press_y = 160;
    long_press_state.press_time = gui.tick_count;
    long_press_state.long_press_threshold = 1000; /* 1秒 / 1 second */
    gui.tick_count += 1500; /* 模拟时间流逝 / Simulate time passing */
    handle_touch_release(&gui, &event);

    /* 6. 渲染最终状态 / Render final state */
    printf("\nFinal render...\n");
    egui_widget_render(&win->root, &gui.fb);

    /* 清理 / Cleanup */
    egui_deinit(&gui);

    printf("\n=== Demo Complete ===\n");
    printf("Touch interactions demonstrated:\n");
    printf("  - Touch press detection\n");
    printf("  - Drag and drop\n");
    printf("  - Swipe detection\n");
    printf("  - Long press detection\n");
    printf("  - Boundary constraints\n");
    return 0;
}
