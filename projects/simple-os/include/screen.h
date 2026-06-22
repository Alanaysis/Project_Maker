#ifndef SCREEN_H
#define SCREEN_H

#include "types.h"

// VGA 颜色定义
typedef enum {
    COLOR_BLACK = 0,
    COLOR_BLUE = 1,
    COLOR_GREEN = 2,
    COLOR_CYAN = 3,
    COLOR_RED = 4,
    COLOR_MAGENTA = 5,
    COLOR_BROWN = 6,
    COLOR_LIGHT_GREY = 7,
    COLOR_DARK_GREY = 8,
    COLOR_LIGHT_BLUE = 9,
    COLOR_LIGHT_GREEN = 10,
    COLOR_LIGHT_CYAN = 11,
    COLOR_LIGHT_RED = 12,
    COLOR_LIGHT_MAGENTA = 13,
    COLOR_YELLOW = 14,
    COLOR_WHITE = 15
} vga_color_t;

// 屏幕尺寸
#define SCREEN_WIDTH  80
#define SCREEN_HEIGHT 25

// 屏幕函数
void screen_init();
void screen_clear();
void screen_putchar(char c);
void screen_puts(const char *str);
void screen_put_int(int num);
void screen_put_hex(uint32_t num);
void screen_set_color(vga_color_t fg, vga_color_t bg);
void screen_set_cursor(uint8_t x, uint8_t y);
void screen_get_cursor(uint8_t *x, uint8_t *y);
void screen_scroll();
void screen_backspace();

// 格式化输出
void kprintf(const char *fmt, ...);

#endif /* SCREEN_H */
