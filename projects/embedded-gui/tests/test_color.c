/**
 * embedded-gui - 嵌入式 GUI 框架
 * tests/test_color.c - 颜色系统测试
 *
 * 测试 RGB565 颜色转换和工具函数
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "embedded_gui.h"

/* 测试 RGB565 转换 / Test RGB565 conversion */
static void test_rgb888_to_rgb565(void) {
    /* 黑色 / Black */
    egui_color_t black = egui_rgb888_to_rgb565(0x00, 0x00, 0x00);
    assert(black == 0x0000);

    /* 白色 / White */
    egui_color_t white = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);
    assert(white == 0xFFFF);

    /* 红色 / Red */
    egui_color_t red = egui_rgb888_to_rgb565(0xFF, 0x00, 0x00);
    assert(red == 0xF800);

    /* 绿色 / Green */
    egui_color_t green = egui_rgb888_to_rgb565(0x00, 0xFF, 0x00);
    assert(green == 0x07E0);

    /* 蓝色 / Blue */
    egui_color_t blue = egui_rgb888_to_rgb565(0x00, 0x00, 0xFF);
    assert(blue == 0x001F);

    /* 中等灰色 / Medium gray */
    egui_color_t gray = egui_rgb888_to_rgb565(0x80, 0x80, 0x80);
    assert(gray == 0x8410);

    printf("  [PASS] RGB888 to RGB565 conversion\n");
}

/* 测试 RGB565 反向转换 / Test RGB565 reverse conversion */
static void test_rgb565_to_rgb888(void) {
    uint8_t r, g, b;

    /* 黑色 / Black */
    egui_rgb565_to_rgb888(0x0000, &r, &g, &b);
    assert(r == 0x00 && g == 0x00 && b == 0x00);

    /* 白色 / White - RGB565 to RGB888 has precision loss */
    egui_rgb565_to_rgb888(0xFFFF, &r, &g, &b);
    assert(r >= 0xF8 && g >= 0xFC && b >= 0xF8);

    /* 红色 / Red - RGB565 precision loss expected */
    egui_rgb565_to_rgb888(0xF800, &r, &g, &b);
    assert(r >= 0xF8 && g <= 0x07 && b <= 0x07);

    /* 绿色 / Green - RGB565 precision loss expected */
    egui_rgb565_to_rgb888(0x07E0, &r, &g, &b);
    assert(r <= 0x07 && g >= 0xFC && b <= 0x07);

    /* 蓝色 / Blue - RGB565 precision loss expected */
    egui_rgb565_to_rgb888(0x001F, &r, &g, &b);
    assert(r <= 0x07 && g <= 0x07 && b >= 0xF8);

    printf("  [PASS] RGB565 to RGB888 conversion\n");
}

/* 测试往返转换 / Test roundtrip conversion */
static void test_roundtrip(void) {
    uint8_t orig_r = 0x5A;
    uint8_t orig_g = 0xB2;
    uint8_t orig_b = 0x7C;

    egui_color_t converted = egui_rgb888_to_rgb565(orig_r, orig_g, orig_b);
    uint8_t r, g, b;
    egui_rgb565_to_rgb888(converted, &r, &g, &b);

    /* RGB565 有精度损失，允许小的误差 / Allow small error due to RGB565 precision */
    assert(abs((int)r - (int)orig_r) <= 7);
    assert(abs((int)g - (int)orig_g) <= 3);
    assert(abs((int)b - (int)orig_b) <= 7);

    printf("  [PASS] Roundtrip conversion (within tolerance)\n");
}

int main(void) {
    printf("=== Color System Tests ===\n");

    test_rgb888_to_rgb565();
    test_rgb565_to_rgb888();
    test_roundtrip();

    printf("\nAll color tests passed!\n");
    return 0;
}
