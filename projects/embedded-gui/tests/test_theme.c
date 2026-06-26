/**
 * embedded-gui - 嵌入式 GUI 框架
 * tests/test_theme.c - 主题系统测试
 *
 * 测试主题的创建和应用
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "embedded_gui.h"

/* 测试默认主题 / Test default theme */
static void test_default_theme(void) {
    egui_theme_t theme;
    egui_theme_default(&theme, egui_font_get_builtin());

    /* 验证按钮样式 / Verify button style */
    assert(theme.button.bg_color != 0x0000); /* 非黑色 / Non-black */
    assert(theme.button.fg_color != 0x0000); /* 非透明 / Non-transparent */
    assert(theme.button.border_width == 2);

    /* 验证窗口背景 / Verify window background */
    assert(theme.window_bg != 0x0000);

    /* 验证高亮色 / Verify highlight color */
    assert(theme.highlight != 0x0000);

    printf("  [PASS] Default theme\n");
}

/* 测试深色主题 / Test dark theme */
static void test_dark_theme(void) {
    egui_theme_t theme;
    egui_theme_dark(&theme, egui_font_get_builtin());

    /* 深色主题应该有深色背景 / Dark theme should have dark background */
    uint8_t r, g, b;
    egui_rgb565_to_rgb888(theme.window_bg, &r, &g, &b);
    assert(r < 50 && g < 50 && b < 50); /* 所有通道 < 50 = 深色 / All channels < 50 = dark */

    /* 文字应该是浅色 / Text should be light */
    egui_rgb565_to_rgb888(theme.label.fg_color, &r, &g, &b);
    assert(r > 150 && g > 150 && b > 150); /* 所有通道 > 150 = 浅色 / All channels > 150 = light */

    printf("  [PASS] Dark theme\n");
}

/* 测试浅色主题 / Test light theme */
static void test_light_theme(void) {
    egui_theme_t theme;
    egui_theme_light(&theme, egui_font_get_builtin());

    /* 浅色主题应该有浅色背景 / Light theme should have light background */
    uint8_t r, g, b;
    egui_rgb565_to_rgb888(theme.window_bg, &r, &g, &b);
    assert(r > 200 && g > 200 && b > 200); /* 所有通道 > 200 = 浅色 / All channels > 200 = light */

    /* 文字应该是深色 / Text should be dark */
    egui_rgb565_to_rgb888(theme.label.fg_color, &r, &g, &b);
    assert(r < 100 && g < 100 && b < 100); /* 所有通道 < 100 = 深色 / All channels < 100 = dark */

    printf("  [PASS] Light theme\n");
}

/* 测试主题切换 / Test theme switching */
static void test_theme_switching(void) {
    egui_theme_t dark, light;
    egui_theme_dark(&dark, egui_font_get_builtin());
    egui_theme_light(&light, egui_font_get_builtin());

    /* 两种主题应该有不同的高亮色 / Two themes should have different highlight colors */
    assert(dark.highlight != light.highlight);

    /* 两种主题应该有不同的高亮色 / Two themes should have different highlight colors */
    uint8_t dr, dg, db;
    egui_rgb565_to_rgb888(dark.highlight, &dr, &dg, &db);
    uint8_t lr, lg, lb;
    egui_rgb565_to_rgb888(light.highlight, &lr, &lg, &lb);
    assert(dr != lr || dg != lg || db != lb);

    printf("  [PASS] Theme switching\n");
}

int main(void) {
    printf("=== Theme Tests ===\n");

    test_default_theme();
    test_dark_theme();
    test_light_theme();
    test_theme_switching();

    printf("\nAll theme tests passed!\n");
    return 0;
}
