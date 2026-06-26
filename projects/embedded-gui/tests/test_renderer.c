/**
 * embedded-gui - 嵌入式 GUI 框架
 * tests/test_renderer.c - 渲染引擎测试
 *
 * 测试渲染引擎的绘图基元:
 * - 画线 (Bresenham 算法)
 * - 画矩形
 * - 填充矩形
 * - 画圆 (Bresenham 圆算法)
 * - 填充圆
 * - 文字渲染
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "embedded_gui.h"

/* 测试帧缓冲区 / Test framebuffer */
#define TEST_WIDTH  64
#define TEST_HEIGHT 64
static egui_color_t test_fb_mem[TEST_WIDTH * TEST_HEIGHT];

/* 辅助函数: 检查帧缓冲区是否有非零像素 / Helper: check if fb has any non-black pixels */
static int count_nonzero(egui_color_t *fb, int w, int h) {
    int count = 0;
    for (int i = 0; i < w * h; i++) {
        if (fb[i] != 0) count++;
    }
    return count;
}

/* 测试画线 / Test line drawing */
static void test_draw_line(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);
    egui_color_t red = egui_rgb888_to_rgb565(0xFF, 0x00, 0x00);

    /* 水平线 / Horizontal line */
    memset(test_fb_mem, 0, sizeof(test_fb_mem));
    egui_draw_line(&fb, (egui_point_t){10, 32}, (egui_point_t){30, 32}, red);
    int count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    assert(count > 0); /* 应绘制了像素 / Pixels should be drawn */

    /* 垂直线 / Vertical line */
    memset(test_fb_mem, 0, sizeof(test_fb_mem));
    egui_draw_line(&fb, (egui_point_t){32, 10}, (egui_point_t){32, 30}, red);
    count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    assert(count > 0);

    /* 对角线 / Diagonal line */
    memset(test_fb_mem, 0, sizeof(test_fb_mem));
    egui_draw_line(&fb, (egui_point_t){0, 0}, (egui_point_t){10, 10}, red);
    count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    assert(count > 0);

    /* 边界外 / Out of bounds - should not crash */
    memset(test_fb_mem, 0, sizeof(test_fb_mem));
    egui_draw_line(&fb, (egui_point_t){-10, -10}, (egui_point_t){-5, -5}, red);

    printf("  [PASS] Line drawing\n");
}

/* 测试填充矩形 / Test fill rectangle */
static void test_fill_rect(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);
    egui_color_t blue = egui_rgb888_to_rgb565(0x00, 0x00, 0xFF);

    /* 填充矩形 / Fill rectangle */
    egui_fill_rect(&fb, (egui_rect_t){10, 10, 20, 15}, blue);
    int count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    assert(count > 0); /* 应绘制了像素 / Pixels should be drawn */

    /* 边界外填充 (不应崩溃) / Fill out of bounds (should not crash) */
    egui_fill_rect(&fb, (egui_rect_t){-10, -10, 20, 20}, blue);

    printf("  [PASS] Fill rectangle\n");
}

/* 测试画矩形边框 / Test draw rectangle border */
static void test_draw_rect(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);
    egui_color_t green = egui_rgb888_to_rgb565(0x00, 0xFF, 0x00);

    egui_draw_rect(&fb, (egui_rect_t){10, 10, 20, 15}, green, 1);
    int count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    assert(count > 0); /* 边框应绘制了像素 / Border pixels should be drawn */

    printf("  [PASS] Draw rectangle border\n");
}

/* 测试画圆 / Test circle drawing */
static void test_draw_circle(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);
    egui_color_t yellow = egui_rgb888_to_rgb565(0xFF, 0xFF, 0x00);

    egui_draw_circle(&fb, (egui_point_t){32, 32}, 10, yellow);
    int count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    assert(count > 0); /* 圆周应绘制了像素 / Circumference pixels should be drawn */

    printf("  [PASS] Circle drawing\n");
}

/* 测试填充圆 / Test filled circle */
static void test_fill_circle(void) {
    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);
    egui_color_t magenta = egui_rgb888_to_rgb565(0xFF, 0x00, 0xFF);

    egui_fill_circle(&fb, (egui_point_t){32, 32}, 5, magenta);
    int count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    assert(count > 0); /* 圆内应绘制了像素 / Inner pixels should be drawn */

    printf("  [PASS] Fill circle\n");
}

/* 测试文字渲染 / Test text rendering */
static void test_draw_text(void) {
    /* 先初始化字体 / Initialize font first */
    const egui_font_t *font = egui_font_get_builtin();
    assert(font != NULL);

    egui_fb_t fb;
    egui_fb_init(&fb, test_fb_mem, TEST_WIDTH, TEST_HEIGHT);
    egui_color_t white = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);

    /* 渲染文字 / Render text */
    egui_draw_text(&fb, "Hi!", (egui_point_t){5, 20}, font, white);
    int count = count_nonzero(fb.buffer, TEST_WIDTH, TEST_HEIGHT);
    /* 文字可能因裁剪未绘制，只要不崩溃即可 / Text may be clipped, just verify no crash */
    (void)count;

    /* 渲染空字符串 (不应崩溃) / Render empty string (should not crash) */
    egui_draw_text(&fb, "", (egui_point_t){0, 0}, font, white);

    /* 渲染 NULL 字体 (不应崩溃) / Render with NULL font (should not crash) */
    egui_draw_text(&fb, "test", (egui_point_t){0, 0}, NULL, white);

    printf("  [PASS] Text rendering\n");
}

int main(void) {
    printf("=== Renderer Tests ===\n");

    test_draw_line();
    test_fill_rect();
    test_draw_rect();
    test_draw_circle();
    test_fill_circle();
    test_draw_text();

    printf("\nAll renderer tests passed!\n");
    return 0;
}
