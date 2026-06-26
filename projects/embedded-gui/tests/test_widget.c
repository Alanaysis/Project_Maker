/**
 * embedded-gui - 嵌入式 GUI 框架
 * tests/test_widget.c - Widget 系统测试
 *
 * 测试 Widget 的创建、操作和渲染
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

/* 测试 Widget 创建 / Test widget creation */
static void test_widget_creation(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    /* 创建窗口 / Create window */
    egui_window_t *win = egui_window_create("Test Window",
        (egui_rect_t){0, 0, TEST_WIDTH, TEST_HEIGHT});
    assert(win != NULL);
    assert(strlen(win->title) > 0);
    assert(win->root.type == EGUI_WIDGET_WINDOW);

    /* 创建按钮 / Create button */
    egui_widget_t *btn = egui_button_create(&win->root, "Test Button",
        (egui_rect_t){10, 10, 80, 30});
    assert(btn != NULL);
    assert(btn->type == EGUI_WIDGET_BUTTON);
    assert(btn->parent == &win->root);
    assert(btn->visible == 1);
    assert(btn->enabled == 1);

    /* 创建标签 / Create label */
    egui_widget_t *label = egui_label_create(&win->root, "Test Label",
        (egui_rect_t){10, 50, 80, 20});
    assert(label != NULL);
    assert(label->type == EGUI_WIDGET_LABEL);

    /* 创建文本框 / Create textbox */
    char text_buf[32] = "Hello";
    egui_widget_t *textbox = egui_textbox_create(&win->root, text_buf, sizeof(text_buf),
        (egui_rect_t){10, 80, 80, 25});
    assert(textbox != NULL);
    assert(textbox->type == EGUI_WIDGET_TEXTBOX);

    /* 创建滑块 / Create slider */
    egui_widget_t *slider = egui_slider_create(&win->root, 0, 100, 50,
        (egui_rect_t){10, 110, 80, 15});
    assert(slider != NULL);
    assert(slider->type == EGUI_WIDGET_SLIDER);

    /* 创建复选框 / Create checkbox */
    egui_widget_t *checkbox = egui_checkbox_create(&win->root, "Check", 0,
        (egui_rect_t){10, 140, 80, 20});
    assert(checkbox != NULL);
    assert(checkbox->type == EGUI_WIDGET_CHECKBOX);

    /* 创建容器 / Create container */
    egui_widget_t *container = egui_container_create(&win->root,
        (egui_rect_t){10, 170, 80, 60});
    assert(container != NULL);
    assert(container->type == EGUI_WIDGET_CONTAINER);

    printf("  [PASS] Widget creation\n");
}

/* 测试 Widget 操作 / Test widget operations */
static void test_widget_operations(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    egui_window_t *win = egui_window_create("Test",
        (egui_rect_t){0, 0, TEST_WIDTH, TEST_HEIGHT});
    assert(win != NULL);

    egui_widget_t *btn = egui_button_create(&win->root, "Test",
        (egui_rect_t){10, 10, 50, 30});
    assert(btn != NULL);

    /* 设置矩形 / Set rect */
    egui_rect_t new_rect = {20, 20, 60, 40};
    egui_widget_set_rect(btn, new_rect);
    assert(btn->rect.x == 20);
    assert(btn->rect.y == 20);
    assert(btn->rect.width == 60);
    assert(btn->rect.height == 40);

    /* 设置可见性 / Set visibility */
    egui_widget_set_visible(btn, 0);
    assert(btn->visible == 0);
    egui_widget_set_visible(btn, 1);
    assert(btn->visible == 1);

    /* 设置启用状态 / Set enabled */
    egui_widget_set_enabled(btn, 0);
    assert(btn->enabled == 0);
    egui_widget_set_enabled(btn, 1);
    assert(btn->enabled == 1);

    /* 设置文本 / Set text */
    egui_widget_set_text(btn, "New Text");

    /* 设置样式 / Set style */
    egui_style_t style;
    style.bg_color = egui_rgb888_to_rgb565(0xFF, 0x00, 0x00);
    style.fg_color = egui_rgb888_to_rgb565(0x00, 0xFF, 0x00);
    style.border_width = 3;
    style.corner_radius = 5;
    style.padding = 10;
    egui_widget_set_style(btn, &style);
    assert(btn->style.bg_color == style.bg_color);
    assert(btn->style.fg_color == style.fg_color);
    assert(btn->style.border_width == 3);

    /* 设置回调 / Set callbacks */
    egui_widget_set_on_event(btn, NULL);
    assert(btn->on_event == NULL);
    egui_widget_set_on_render(btn, NULL);
    assert(btn->on_render == NULL);

    printf("  [PASS] Widget operations\n");
}

/* 测试 Widget 层次结构 / Test widget hierarchy */
static void test_widget_hierarchy(void) {
    egui_window_t *win = egui_window_create("Hierarchy",
        (egui_rect_t){0, 0, 100, 100});
    assert(win != NULL);

    /* 创建容器 / Create container */
    egui_widget_t *container = egui_container_create(&win->root,
        (egui_rect_t){0, 0, 100, 100});
    assert(container != NULL);

    /* 创建子组件 / Create children */
    egui_widget_t *child1 = egui_button_create(container, "Child 1",
        (egui_rect_t){10, 10, 40, 30});
    egui_widget_t *child2 = egui_label_create(container, "Child 2",
        (egui_rect_t){60, 10, 40, 30});
    assert(child1 != NULL);
    assert(child2 != NULL);

    /* 检查父子关系 / Check parent-child relationship */
    assert(child1->parent == container);
    assert(child2->parent == container);

    /* 检查兄弟关系 / Check sibling relationship */
    assert(child1->next == child2 || child2->next == child1);

    /* 检查链表 / Check linked list */
    egui_widget_t *first = container->child;
    assert(first != NULL);
    assert(first->type == EGUI_WIDGET_BUTTON || first->type == EGUI_WIDGET_LABEL);

    printf("  [PASS] Widget hierarchy\n");
}

/* 测试 Widget 渲染 / Test widget rendering */
static void test_widget_render(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);

    egui_window_t *win = egui_window_create("Render",
        (egui_rect_t){0, 0, TEST_WIDTH, TEST_HEIGHT});
    assert(win != NULL);

    /* 创建可渲染的 widget / Create renderable widgets */
    egui_widget_t *btn = egui_button_create(&win->root, "Button",
        (egui_rect_t){10, 10, 50, 30});
    egui_widget_t *label = egui_label_create(&win->root, "Label",
        (egui_rect_t){10, 50, 50, 20});
    assert(btn != NULL);
    assert(label != NULL);

    /* 渲染 / Render */
    egui_widget_render(&win->root, &fb);

    /* 检查帧缓冲区有非零像素 (渲染产生了输出) / Check framebuffer has non-zero pixels */
    int has_pixels = 0;
    for (int i = 0; i < TEST_WIDTH * TEST_HEIGHT; i++) {
        if (test_fb_mem[i] != 0) {
            has_pixels = 1;
            break;
        }
    }
    assert(has_pixels);

    /* 渲染不可见 widget (不应产生输出) / Render invisible widget (should produce no output) */
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);
    egui_widget_set_visible(btn, 0);
    egui_widget_set_visible(label, 0);
    /* 隐藏窗口根组件 / Hide window root too */
    win->root.visible = 0;
    egui_widget_render(&win->root, &fb);

    /* 检查帧缓冲区仍为黑色 / Check framebuffer is still black */
    for (int i = 0; i < TEST_WIDTH * TEST_HEIGHT; i++) {
        assert(test_fb_mem[i] == 0);
    }

    printf("  [PASS] Widget rendering\n");
}

/* 测试 Widget 销毁 / Test widget destruction */
static void test_widget_destruction(void) {
    egui_window_t *win = egui_window_create("Destroy",
        (egui_rect_t){0, 0, 100, 100});
    assert(win != NULL);

    egui_widget_t *btn = egui_button_create(&win->root, "To Destroy",
        (egui_rect_t){10, 10, 50, 30});
    assert(btn != NULL);

    /* 销毁 / Destroy */
    egui_widget_destroy(btn);
    assert(btn->type == EGUI_WIDGET_NONE);
    assert(btn->visible == 0);

    printf("  [PASS] Widget destruction\n");
}

/* 测试命中测试 / Test hit testing */
static void test_hit_test(void) {
    egui_window_t *win = egui_window_create("Hit",
        (egui_rect_t){0, 0, 100, 100});
    assert(win != NULL);

    /* 创建 widget / Create widgets */
    egui_widget_t *btn1 = egui_button_create(&win->root, "Btn1",
        (egui_rect_t){20, 20, 60, 40});
    egui_widget_t *btn2 = egui_label_create(&win->root, "Btn2",
        (egui_rect_t){70, 10, 50, 30});
    assert(btn1 && btn2);

    /* 命中测试: 点在 widget 内 / Hit test: point inside widget */
    egui_point_t p1 = {40, 30}; /* 在 btn1 矩形内 / Inside btn1 rect */
    egui_widget_t *hit = egui_hit_test(&win->root, p1);
    assert(hit == btn1);

    /* 命中测试: 点在 widget 外 / Hit test: point outside widgets */
    egui_point_t p3 = {5, 5}; /* 在 widget 外 / Outside widgets */
    hit = egui_hit_test(&win->root, p3);
    /* 窗口根组件在 (0,0)，所以 (5,5) 在窗口内 / Window root at (0,0), so (5,5) is inside window */
    assert(hit == NULL || hit->type == EGUI_WIDGET_WINDOW);

    /* 命中测试: 不可见 widget / Hit test: invisible widget */
    egui_widget_set_visible(btn1, 0);
    hit = egui_hit_test(&win->root, p1);
    assert(hit == NULL);

    printf("  [PASS] Hit testing\n");
}

int main(void) {
    printf("=== Widget Tests ===\n");

    test_widget_creation();
    test_widget_operations();
    test_widget_hierarchy();
    test_widget_render();
    test_widget_destruction();
    test_hit_test();

    printf("\nAll widget tests passed!\n");
    return 0;
}
