/**
 * embedded-gui - 嵌入式 GUI 框架
 * tests/test_layout.c - 布局引擎测试
 *
 * 测试各种布局算法
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "embedded_gui.h"

/* 辅助函数: 创建带子组件的容器 / Helper: create container with children */
static egui_widget_t *create_test_container(egui_window_t *win,
    const char *name, egui_rect_t rect, int child_count, int child_width, int child_height) {
    (void)name;
    egui_widget_t *container = egui_container_create(&win->root, rect);
    assert(container != NULL);

    for (int i = 0; i < child_count; i++) {
        char label_buf[16];
        snprintf(label_buf, sizeof(label_buf), "%d", i);
        egui_widget_t *child = egui_label_create(container, label_buf,
            (egui_rect_t){0, 0, (uint16_t)child_width, (uint16_t)child_height));
        child->margin_left = 10;
        child->margin_top = 10;
    }

    return container;
}

/* 测试绝对定位布局 / Test absolute positioning layout */
static void test_absolute_layout(void) {
    egui_window_t *win = egui_window_create("AbsLayout",
        (egui_rect_t){0, 0, 480, 320});
    assert(win != NULL);

    /* 创建固定位置的 widget / Create widgets at fixed positions */
    egui_widget_t *w1 = egui_button_create(&win->root, "W1",
        (egui_rect_t){10, 10, 100, 40));
    egui_widget_t *w2 = egui_label_create(&win->root, "W2",
        (egui_rect_t){200, 50, 80, 30));
    egui_widget_t *w3 = egui_textbox_create(&win->root, "W3", 4,
        (egui_rect_t){50, 100, 120, 35));
    assert(w1 && w2 && w3);

    /* 布局计算 / Layout calculation */
    egui_layout_absolute(&win->root);

    /* 验证位置未改变 (绝对定位 = 手动指定) / Verify positions unchanged (absolute = manual) */
    assert(w1->rect.x == 10 && w1->rect.y == 10);
    assert(w2->rect.x == 200 && w2->rect.y == 50);
    assert(w3->rect.x == 50 && w3->rect.y == 100);

    printf("  [PASS] Absolute positioning layout\n");
}

/* 测试相对定位布局 / Test relative positioning layout */
static void test_relative_layout(void) {
    egui_window_t *win = egui_window_create("RelLayout",
        (egui_rect_t){0, 0, 480, 320});
    assert(win != NULL);

    /* 创建容器 / Create container */
    egui_widget_t *container = egui_container_create(&win->root,
        (egui_rect_t){50, 50, 200, 150));
    assert(container != NULL);

    /* 创建子组件 / Create children */
    egui_widget_t *w1 = egui_button_create(container, "Left",
        (egui_rect_t){0, 0, 60, 30));
    w1->margin_left = 10;
    w1->align = EGUI_ALIGN_LEFT | EGUI_ALIGN_TOP;

    egui_widget_t *w2 = egui_label_create(container, "Right",
        (egui_rect_t){0, 0, 60, 30));
    w2->margin_right = 10;
    w2->align = EGUI_ALIGN_RIGHT | EGUI_ALIGN_TOP;

    egui_widget_t *w3 = egui_label_create(container, "Center",
        (egui_rect_t){0, 0, 60, 30));
    w3->align = EGUI_ALIGN_CENTER | EGUI_ALIGN_MIDDLE;

    assert(w1 && w2 && w3);

    /* 布局计算 / Layout calculation */
    egui_layout_relative(container, &container->rect);

    /* 验证位置 / Verify positions */
    /* w1 应在左侧 / w1 should be on the left */
    assert(w1->rect.x == container->rect.x + 10);
    /* w2 应在右侧 / w2 should be on the right */
    assert(w2->rect.x == container->rect.x + 200 - 60 - 10);
    /* w3 应在居中 / w3 should be centered */
    assert(w3->rect.x == container->rect.x + (200 - 60) / 2);
    assert(w3->rect.y == container->rect.y + (150 - 30) / 2);

    printf("  [PASS] Relative positioning layout\n");
}

/* 测试重力对齐布局 / Test gravity layout */
static void test_gravity_layout(void) {
    egui_window_t *win = egui_window_create("Gravity",
        (egui_rect_t){0, 0, 480, 320});
    assert(win != NULL);

    /* 容器 / Container */
    egui_widget_t *container = egui_container_create(&win->root,
        (egui_rect_t){0, 0, 400, 200));
    assert(container != NULL);

    /* 底部对齐的 widget / Bottom-aligned widget */
    egui_widget_t *bottom = egui_button_create(container, "Bottom",
        (egui_rect_t){0, 0, 100, 40));
    bottom->align = EGUI_ALIGN_RIGHT | EGUI_ALIGN_BOTTOM;

    /* 居中对齐的 widget / Center-aligned widget */
    egui_widget_t *center = egui_label_create(container, "Center",
        (egui_rect_t){0, 0, 80, 30));
    center->align = EGUI_ALIGN_CENTER | EGUI_ALIGN_MIDDLE;

    assert(bottom && center);

    /* 布局计算 / Layout calculation */
    egui_layout_gravity(container, &container->rect, EGUI_ALIGN_LEFT | EGUI_ALIGN_TOP);

    /* 验证 / Verify */
    assert(bottom->rect.x == container->rect.x + 400 - 100);
    assert(bottom->rect.y == container->rect.y + 200 - 40);
    assert(center->rect.x == container->rect.x + (400 - 80) / 2);
    assert(center->rect.y == container->rect.y + (200 - 30) / 2);

    printf("  [PASS] Gravity layout\n");
}

/* 测试布局结果 / Test layout result */
static void test_layout_result(void) {
    egui_layout_result_t result = egui_layout_result_create();
    assert(result.bounds.x == 0);
    assert(result.bounds.y == 0);
    assert(result.bounds.width == 0);
    assert(result.bounds.height == 0);
    assert(result.child_count == 0);

    printf("  [PASS] Layout result creation\n");
}

int main(void) {
    printf("=== Layout Tests ===\n");

    test_absolute_layout();
    test_relative_layout();
    test_gravity_layout();
    test_layout_result();

    printf("\nAll layout tests passed!\n");
    return 0;
}
