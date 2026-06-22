/**
 * 屏幕驱动 (screen.c)
 * 功能: 控制 VGA 文本模式输出
 */

#include "../include/screen.h"
#include "../include/memory.h"

// VGA 显示内存地址
static uint16_t *video_memory = (uint16_t *)0xB8000;

// 光标位置
static uint8_t cursor_x = 0;
static uint8_t cursor_y = 0;

// 当前颜色属性
static uint8_t attribute = 0x07;  // 黑底白字

// 端口输出函数 (在 idt.c 中定义)
extern void outb(uint16_t port, uint8_t value);
extern uint8_t inb(uint16_t port);

// 初始化屏幕
void screen_init() {
    cursor_x = 0;
    cursor_y = 0;
    attribute = 0x07;
    screen_clear();
}

// 清屏
void screen_clear() {
    for (int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; i++) {
        video_memory[i] = (attribute << 8) | ' ';
    }
    cursor_x = 0;
    cursor_y = 0;
    screen_set_cursor(cursor_x, cursor_y);
}

// 设置颜色
void screen_set_color(vga_color_t fg, vga_color_t bg) {
    attribute = (bg << 4) | fg;
}

// 移动光标
void screen_set_cursor(uint8_t x, uint8_t y) {
    cursor_x = x;
    cursor_y = y;

    uint16_t pos = y * SCREEN_WIDTH + x;

    // 发送光标位置到 VGA 控制器
    outb(0x3D4, 14);                  // 光标高字节寄存器
    outb(0x3D5, (pos >> 8) & 0xFF);
    outb(0x3D4, 15);                  // 光标低字节寄存器
    outb(0x3D5, pos & 0xFF);
}

// 获取光标位置
void screen_get_cursor(uint8_t *x, uint8_t *y) {
    *x = cursor_x;
    *y = cursor_y;
}

// 滚屏
void screen_scroll() {
    // 将所有行上移一行
    for (int i = 0; i < SCREEN_WIDTH * (SCREEN_HEIGHT - 1); i++) {
        video_memory[i] = video_memory[i + SCREEN_WIDTH];
    }

    // 清空最后一行
    for (int i = SCREEN_WIDTH * (SCREEN_HEIGHT - 1); i < SCREEN_WIDTH * SCREEN_HEIGHT; i++) {
        video_memory[i] = (attribute << 8) | ' ';
    }

    cursor_y = SCREEN_HEIGHT - 1;
}

// 退格
void screen_backspace() {
    if (cursor_x > 0) {
        cursor_x--;
        uint16_t *location = video_memory + (cursor_y * SCREEN_WIDTH + cursor_x);
        *location = (attribute << 8) | ' ';
        screen_set_cursor(cursor_x, cursor_y);
    }
}

// 输出字符
void screen_putchar(char c) {
    switch (c) {
        case '\n':  // 换行
            cursor_x = 0;
            cursor_y++;
            break;

        case '\r':  // 回车
            cursor_x = 0;
            break;

        case '\t':  // 制表符
            cursor_x = (cursor_x + 8) & ~7;
            break;

        case '\b':  // 退格
            screen_backspace();
            return;

        default:    // 普通字符
            {
                uint16_t *location = video_memory + (cursor_y * SCREEN_WIDTH + cursor_x);
                *location = (attribute << 8) | c;
                cursor_x++;
            }
            break;
    }

    // 换行处理
    if (cursor_x >= SCREEN_WIDTH) {
        cursor_x = 0;
        cursor_y++;
    }

    // 滚屏处理
    if (cursor_y >= SCREEN_HEIGHT) {
        screen_scroll();
    }

    // 更新光标位置
    screen_set_cursor(cursor_x, cursor_y);
}

// 输出字符串
void screen_puts(const char *str) {
    while (*str) {
        screen_putchar(*str++);
    }
}

// 输出整数
void screen_put_int(int num) {
    if (num == 0) {
        screen_putchar('0');
        return;
    }

    if (num < 0) {
        screen_putchar('-');
        num = -num;
    }

    char buffer[12];  // 足够存储 32 位整数
    int i = 0;

    while (num > 0) {
        buffer[i++] = '0' + (num % 10);
        num /= 10;
    }

    // 反转输出
    while (i > 0) {
        screen_putchar(buffer[--i]);
    }
}

// 输出十六进制数
void screen_put_hex(uint32_t num) {
    screen_puts("0x");

    if (num == 0) {
        screen_putchar('0');
        return;
    }

    char buffer[9];  // 8 位十六进制数
    int i = 0;

    while (num > 0) {
        uint8_t digit = num & 0xF;
        if (digit < 10) {
            buffer[i++] = '0' + digit;
        } else {
            buffer[i++] = 'A' + (digit - 10);
        }
        num >>= 4;
    }

    // 反转输出
    while (i > 0) {
        screen_putchar(buffer[--i]);
    }
}

// 格式化输出 (简化版)
void kprintf(const char *fmt, ...) {
    // 简化的 kprintf，不支持完整的格式化
    // 只支持 %s, %d, %x
    const char *p = fmt;

    while (*p) {
        if (*p == '%' && *(p + 1)) {
            p++;
            switch (*p) {
                case 's':
                    // 字符串参数需要从栈获取
                    // 这里简化处理，只输出 %s
                    screen_puts("(string)");
                    break;
                case 'd':
                    screen_put_int(0);  // 简化处理
                    break;
                case 'x':
                    screen_put_hex(0);  // 简化处理
                    break;
                case '%':
                    screen_putchar('%');
                    break;
                default:
                    screen_putchar('%');
                    screen_putchar(*p);
                    break;
            }
        } else {
            screen_putchar(*p);
        }
        p++;
    }
}
