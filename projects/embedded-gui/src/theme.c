/**
 * embedded-gui - 嵌入式 GUI 框架
 * src/theme.c - 主题/样式系统实现
 *
 * 主题系统:
 * - 定义 GUI 的外观 (颜色、字体、边框等)
 * - 支持多主题切换 (浅色/深色)
 * - 组件级样式覆盖
 *
 * 嵌入式系统的主题设计考虑:
 * - 颜色数量有限 (调色板)
 * - 字体嵌入在 flash 中
 * - 样式数据占用最小空间
 */

#include "embedded_gui.h"

/* ============================================================
 * 颜色转换 / Color Conversion
 *
 * RGB565 格式: 16-bit 颜色
 * |R:4|G:6|B:4|
 * R: bits 11-15
 * G: bits 5-10
 * B: bits 0-3
 *
 * 为什么用 RGB565?
 * - 16-bit 比 24-bit (RGB888) 节省 33% 内存
 * - 大多数嵌入式 LCD 控制器原生支持 RGB565
 * - 人眼对绿色更敏感，所以 G 占 6 bits
 */

/**
 * RGB888 -> RGB565 转换
 * 将 24-bit 颜色转换为 16-bit
 */
egui_color_t egui_rgb888_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
    /* 提取各通道的高位 / Extract MSB of each channel */
    uint16_t r5 = (r >> 3) & 0x1F;   /* 5-bit red */
    uint16_t g6 = (g >> 2) & 0x3F;   /* 6-bit green */
    uint16_t b5 = (b >> 3) & 0x1F;   /* 5-bit blue */

    /* 组合成 RGB565 / Combine into RGB565 */
    return (egui_color_t)((r5 << 11) | (g6 << 5) | b5);
}

/**
 * RGB565 -> RGB888 转换
 * 将 16-bit 颜色扩展为 24-bit (用于调试/分析)
 */
void egui_rgb565_to_rgb888(egui_color_t color, uint8_t *r, uint8_t *g, uint8_t *b) {
    if (r) *r = (uint8_t)(((color >> 11) & 0x1F) << 3);     /* 5-bit -> 8-bit */
    if (g) *g = (uint8_t)(((color >> 5) & 0x3F) << 2);       /* 6-bit -> 8-bit */
    if (b) *b = (uint8_t)((color & 0x1F) << 3);              /* 4-bit -> 8-bit */
}

/* ============================================================
 * 主题定义 / Theme Definitions
 * ============================================================ */

/**
 * 默认主题 (蓝色系)
 * 适合大多数嵌入式应用场景
 */
void egui_theme_default(egui_theme_t *theme, const egui_font_t *font) {
    /* 按钮: 蓝色背景，白色文字 / Button: blue bg, white text */
    theme->button.bg_color = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9);
    theme->button.fg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);
    theme->button.border_color = egui_rgb888_to_rgb565(0x35, 0x6E, 0xA8);
    theme->button.border_width = 2;
    theme->button.corner_radius = 4;
    theme->button.padding = 8;
    theme->button.opacity = 255;

    /* 标签: 黑色文字 / Label: black text */
    theme->label.bg_color = 0x0000; /* 透明 / Transparent */
    theme->label.fg_color = egui_rgb888_to_rgb565(0x00, 0x00, 0x00);
    theme->label.border_color = 0x0000;
    theme->label.border_width = 0;
    theme->label.corner_radius = 0;
    theme->label.padding = 2;
    theme->label.opacity = 255;

    /* 文本框: 白色背景，灰色边框 / Textbox: white bg, gray border */
    theme->textbox.bg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);
    theme->textbox.fg_color = egui_rgb888_to_rgb565(0x00, 0x00, 0x00);
    theme->textbox.border_color = egui_rgb888_to_rgb565(0x88, 0x88, 0x88);
    theme->textbox.border_width = 1;
    theme->textbox.corner_radius = 2;
    theme->textbox.padding = 4;
    theme->textbox.opacity = 255;

    /* 滑块: 蓝色指示器 / Slider: blue indicator */
    theme->slider.bg_color = egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC);
    theme->slider.fg_color = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9);
    theme->slider.border_color = egui_rgb888_to_rgb565(0x88, 0x88, 0x88);
    theme->slider.border_width = 1;
    theme->slider.corner_radius = 2;
    theme->slider.padding = 4;
    theme->slider.opacity = 255;

    /* 复选框: 白色背景，黑色边框 / Checkbox: white bg, black border */
    theme->checkbox.bg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);
    theme->checkbox.fg_color = egui_rgb888_to_rgb565(0x00, 0x00, 0x00);
    theme->checkbox.border_color = egui_rgb888_to_rgb565(0x88, 0x88, 0x88);
    theme->checkbox.border_width = 1;
    theme->checkbox.corner_radius = 2;
    theme->checkbox.padding = 4;
    theme->checkbox.opacity = 255;

    /* 窗口: 白色背景 / Window: white bg */
    theme->window_bg = egui_rgb888_to_rgb565(0xF5, 0xF5, 0xF5);
    theme->window_title_fg = egui_rgb888_to_rgb565(0x33, 0x33, 0x33);
    theme->highlight = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9);

    theme->font = font;
}

/**
 * 深色主题
 * 适合 OLED 屏幕或低功耗场景
 * 黑色背景节省 OLED 功耗 (黑色像素不发光)
 */
void egui_theme_dark(egui_theme_t *theme, const egui_font_t *font) {
    /* 按钮: 深蓝背景，白色文字 / Button: dark blue bg, white text */
    theme->button.bg_color = egui_rgb888_to_rgb565(0x1A, 0x3A, 0x5A);
    theme->button.fg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);
    theme->button.border_color = egui_rgb888_to_rgb565(0x2A, 0x5A, 0x8A);
    theme->button.border_width = 1;
    theme->button.corner_radius = 4;
    theme->button.padding = 8;
    theme->button.opacity = 255;

    /* 标签: 白色文字 / Label: white text */
    theme->label.bg_color = 0x0000;
    theme->label.fg_color = egui_rgb888_to_rgb565(0xE0, 0xE0, 0xE0);
    theme->label.border_color = 0x0000;
    theme->label.border_width = 0;
    theme->label.corner_radius = 0;
    theme->label.padding = 2;
    theme->label.opacity = 255;

    /* 文本框: 深色背景 / Textbox: dark bg */
    theme->textbox.bg_color = egui_rgb888_to_rgb565(0x2A, 0x2A, 0x2A);
    theme->textbox.fg_color = egui_rgb888_to_rgb565(0xE0, 0xE0, 0xE0);
    theme->textbox.border_color = egui_rgb888_to_rgb565(0x44, 0x44, 0x44);
    theme->textbox.border_width = 1;
    theme->textbox.corner_radius = 2;
    theme->textbox.padding = 4;
    theme->textbox.opacity = 255;

    /* 滑块: 深色背景，蓝色指示器 / Slider: dark bg, blue indicator */
    theme->slider.bg_color = egui_rgb888_to_rgb565(0x33, 0x33, 0x33);
    theme->slider.fg_color = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9);
    theme->slider.border_color = egui_rgb888_to_rgb565(0x44, 0x44, 0x44);
    theme->slider.border_width = 1;
    theme->slider.corner_radius = 2;
    theme->slider.padding = 4;
    theme->slider.opacity = 255;

    /* 复选框: 深色背景 / Checkbox: dark bg */
    theme->checkbox.bg_color = egui_rgb888_to_rgb565(0x2A, 0x2A, 0x2A);
    theme->checkbox.fg_color = egui_rgb888_to_rgb565(0xE0, 0xE0, 0xE0);
    theme->checkbox.border_color = egui_rgb888_to_rgb565(0x44, 0x44, 0x44);
    theme->checkbox.border_width = 1;
    theme->checkbox.corner_radius = 2;
    theme->checkbox.padding = 4;
    theme->checkbox.opacity = 255;

    /* 窗口: 深灰背景 / Window: dark gray bg */
    theme->window_bg = egui_rgb888_to_rgb565(0x1A, 0x1A, 0x1A);
    theme->window_title_fg = egui_rgb888_to_rgb565(0xE0, 0xE0, 0xE0);
    theme->highlight = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9);

    theme->font = font;
}

/**
 * 浅色主题
 * 适合 LCD 屏幕，高对比度
 */
void egui_theme_light(egui_theme_t *theme, const egui_font_t *font) {
    /* 按钮: 浅蓝背景，深蓝文字 / Button: light blue bg, dark blue text */
    theme->button.bg_color = egui_rgb888_to_rgb565(0xE8, 0xF0, 0xFE);
    theme->button.fg_color = egui_rgb888_to_rgb565(0x1A, 0x47, 0x8A);
    theme->button.border_color = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9);
    theme->button.border_width = 1;
    theme->button.corner_radius = 4;
    theme->button.padding = 8;
    theme->button.opacity = 255;

    /* 标签: 深色文字 / Label: dark text */
    theme->label.bg_color = 0x0000;
    theme->label.fg_color = egui_rgb888_to_rgb565(0x33, 0x33, 0x33);
    theme->label.border_color = 0x0000;
    theme->label.border_width = 0;
    theme->label.corner_radius = 0;
    theme->label.padding = 2;
    theme->label.opacity = 255;

    /* 文本框: 白色背景 / Textbox: white bg */
    theme->textbox.bg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);
    theme->textbox.fg_color = egui_rgb888_to_rgb565(0x00, 0x00, 0x00);
    theme->textbox.border_color = egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC);
    theme->textbox.border_width = 1;
    theme->textbox.corner_radius = 2;
    theme->textbox.padding = 4;
    theme->textbox.opacity = 255;

    /* 滑块: 浅色背景，蓝色指示器 / Slider: light bg, blue indicator */
    theme->slider.bg_color = egui_rgb888_to_rgb565(0xDD, 0xDD, 0xDD);
    theme->slider.fg_color = egui_rgb888_to_rgb565(0x1A, 0x47, 0x8A);
    theme->slider.border_color = egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC);
    theme->slider.border_width = 1;
    theme->slider.corner_radius = 2;
    theme->slider.padding = 4;
    theme->slider.opacity = 255;

    /* 复选框: 白色背景 / Checkbox: white bg */
    theme->checkbox.bg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF);
    theme->checkbox.fg_color = egui_rgb888_to_rgb565(0x33, 0x33, 0x33);
    theme->checkbox.border_color = egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC);
    theme->checkbox.border_width = 1;
    theme->checkbox.corner_radius = 2;
    theme->checkbox.padding = 4;
    theme->checkbox.opacity = 255;

    /* 窗口: 白色背景 / Window: white bg */
    theme->window_bg = egui_rgb888_to_rgb565(0xFA, 0xFA, 0xFA);
    theme->window_title_fg = egui_rgb888_to_rgb565(0x1A, 0x47, 0x8A);
    theme->highlight = egui_rgb888_to_rgb565(0x1A, 0x47, 0x8A);

    theme->font = font;
}
