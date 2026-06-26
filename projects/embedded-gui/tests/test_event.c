/**
 * embedded-gui - 嵌入式 GUI 框架
 * tests/test_event.c - 事件处理测试
 *
 * 测试事件队列、命中测试和事件分发
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "embedded_gui.h"

/* 测试帧缓冲区 / Test framebuffer */
#define TEST_WIDTH  100
#define TEST_HEIGHT 100
static egui_color_t test_fb_mem[TEST_WIDTH * TEST_HEIGHT];

/* 事件回调计数器 / Event callback counter */
static int event_call_count = 0;

/* 事件回调 / Event callback */
static void test_event_callback(egui_widget_t *w, const egui_event_t *event) {
    (void)w;
    (void)event;
    event_call_count++;
}

/* 测试事件队列 / Test event queue */
static void test_event_queue(void) {
    /* 清空队列 / Clear queue */
    egui_event_head = 0;
    egui_event_tail = 0;
    egui_event_count = 0;

    /* 测试空队列 / Test empty queue */
    assert(egui_event_queue_empty());
    assert(!egui_event_queue_full());

    /* 推送事件 / Push events */
    egui_event_t e1 = {.type = EGUI_EVENT_TOUCH_PRESS, .timestamp = 1};
    egui_event_t e2 = {.type = EGUI_EVENT_TOUCH_RELEASE, .timestamp = 2};
    egui_event_t e3 = {.type = EGUI_EVENT_KEY_PRESS, .timestamp = 3};

    egui_event_queue_push(&e1);
    assert(!egui_event_queue_empty());
    assert(egui_event_count == 1);

    egui_event_queue_push(&e2);
    assert(egui_event_count == 2);

    egui_event_queue_push(&e3);
    assert(egui_event_count == 3);

    /* 弹出事件 (FIFO) / Pop events (FIFO) */
    egui_event_t popped;
    assert(egui_event_queue_pop(&popped));
    assert(popped.type == EGUI_EVENT_TOUCH_PRESS);
    assert(popped.timestamp == 1);

    assert(egui_event_queue_pop(&popped));
    assert(popped.type == EGUI_EVENT_TOUCH_RELEASE);
    assert(popped.timestamp == 2);

    assert(egui_event_queue_pop(&popped));
    assert(popped.type == EGUI_EVENT_KEY_PRESS);
    assert(popped.timestamp == 3);

    assert(egui_event_queue_empty());

    /* 测试队列满 / Test queue full */
    for (int i = 0; i < EVENT_QUEUE_SIZE; i++) {
        egui_event_t e = {.type = (egui_event_type_t)(EGUI_EVENT_TOUCH_PRESS + i), .timestamp = (uint32_t)(i + 1)};
        egui_event_queue_push(&e);
    }
    assert(egui_event_queue_full());

    /* 超出时丢弃最旧的事件 / Discard oldest when full */
    egui_event_t overflow = {.type = EGUI_EVENT_CUSTOM, .timestamp = 999};
    egui_event_queue_push(&overflow);
    assert(!egui_event_queue_full()); /* 应释放一个槽位 / Should free a slot */

    printf("  [PASS] Event queue\n");
}

/* 测试命中测试 / Test hit testing */
static void test_hit_test(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    egui_window_t *win = egui_window_create("HitTest",
        (egui_rect_t){0, 0, TEST_WIDTH, TEST_HEIGHT});
    assert(win != NULL);

    /* 创建 widget / Create widgets */
    egui_widget_t *btn1 = egui_button_create(&win->root, "Btn1",
        (egui_rect_t){10, 10, 50, 30));
    egui_widget_t *btn2 = egui_label_create(&win->root, "Btn2",
        (egui_rect_t){70, 10, 50, 30));
    assert(btn1 && btn2);

    /* 命中测试: 在 btn1 上 / Hit test: on btn1 */
    egui_point_t p1 = {30, 20}; /* 在 btn1 矩形内 / Inside btn1 rect */
    egui_widget_t *hit = egui_hit_test(&win->root, p1);
    assert(hit == btn1);

    /* 命中测试: 在 btn2 上 / Hit test: on btn2 */
    egui_point_t p2 = {90, 20}; /* 在 btn2 矩形内 / Inside btn2 rect */
    hit = egui_hit_test(&win->root, p2);
    assert(hit == btn2);

    /* 命中测试: 在 widget 外 / Hit test: outside widgets */
    egui_point_t p3 = {5, 5}; /* 在 widget 外 / Outside widgets */
    hit = egui_hit_test(&win->root, p3);
    assert(hit == NULL);

    /* 命中测试: 不可见 widget / Hit test: invisible widget */
    egui_widget_set_visible(btn1, 0);
    hit = egui_hit_test(&win->root, p1);
    assert(hit == NULL);

    printf("  [PASS] Hit testing\n");
}

/* 测试事件分发 / Test event dispatch */
static void test_event_dispatch(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    egui_t gui;
    memset(&gui, 0, sizeof(gui));
    egui_init(&gui, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    egui_window_t *win = egui_window_create("Dispatch",
        (egui_rect_t){0, 0, TEST_WIDTH, TEST_HEIGHT});
    egui_gui_add_window(&gui, win);
    assert(win != NULL);

    /* 创建带回调的 widget / Create widget with callback */
    event_call_count = 0;
    egui_widget_t *btn = egui_button_create(&win->root, "Click",
        (egui_rect_t){20, 20, 60, 30));
    btn->on_event = test_event_callback;
    assert(btn != NULL);

    /* 分发触摸事件 (在 widget 上) / Dispatch touch event (on widget) */
    egui_event_t event = {
        .type = EGUI_EVENT_TOUCH_PRESS,
        .pos = {40, 30}, /* 在 widget 内 / Inside widget */
        .timestamp = 100,
    };
    egui_event_dispatch(&gui, &event);

    /* 验证回调被调用 / Verify callback was called */
    assert(event_call_count > 0);
    printf("  [PASS] Event dispatch (touch on widget)\n");

    /* 分发触摸事件 (不在 widget 上) / Dispatch touch event (not on widget) */
    event_call_count = 0;
    event.pos.x = 5;
    event.pos.y = 5;
    egui_event_dispatch(&gui, &event);
    assert(event_call_count == 0);

    /* 分发无效事件 / Dispatch invalid event */
    event_call_count = 0;
    egui_event_t invalid = {.type = EGUI_EVENT_NONE};
    egui_event_dispatch(&gui, &invalid);
    assert(event_call_count == 0);

    printf("  [PASS] Event dispatch (off widget / invalid)\n");
}

/* 测试焦点管理 / Test focus management */
static void test_focus_management(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    egui_t gui;
    memset(&gui, 0, sizeof(gui));
    egui_init(&gui, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    egui_window_t *win = egui_window_create("Focus",
        (egui_rect_t){0, 0, TEST_WIDTH, TEST_HEIGHT});
    egui_gui_add_window(&gui, win);
    assert(win != NULL);

    egui_widget_t *btn = egui_button_create(&win->root, "Focus",
        (egui_rect_t){20, 20, 60, 30));
    assert(btn != NULL);

    /* 初始状态: 无焦点 / Initial: no focus */
    assert((btn->state & EGUI_STATE_FOCUSED) == 0);

    /* 分发事件 (在 widget 上) / Dispatch event (on widget) */
    egui_event_t event = {
        .type = EGUI_EVENT_TOUCH_PRESS,
        .pos = {40, 30},
        .timestamp = 0,
    };
    egui_event_dispatch(&gui, &event);

    /* 验证焦点设置 / Verify focus set */
    assert(btn->state & EGUI_STATE_FOCUSED);

    printf("  [PASS] Focus management\n");
}

int main(void) {
    printf("=== Event Tests ===\n");

    test_event_queue();
    test_hit_test();
    test_event_dispatch();
    test_focus_management();

    printf("\nAll event tests passed!\n");
    return 0;
}
