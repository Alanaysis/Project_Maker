#ifndef KEYBOARD_H
#define KEYBOARD_H

#include "types.h"

// 键盘缓冲区大小
#define KEYBOARD_BUFFER_SIZE 256

// 特殊键定义
#define KEY_ESC        0x1B
#define KEY_BACKSPACE  0x08
#define KEY_TAB        0x09
#define KEY_ENTER      0x0D
#define KEY_LSHIFT     0x2A
#define KEY_RSHIFT     0x36
#define KEY_LCTRL      0x1D
#define KEY_LALT       0x38
#define KEY_CAPSLOCK   0x3A

// 键盘状态
typedef struct {
    uint8_t buffer[KEYBOARD_BUFFER_SIZE];
    uint8_t head;
    uint8_t tail;
    uint8_t size;
    uint8_t shift;
    uint8_t ctrl;
    uint8_t alt;
    uint8_t capslock;
} keyboard_state_t;

// 键盘函数
void keyboard_init();
char keyboard_getchar();
int keyboard_available();
char keyboard_read();
void keyboard_clear_buffer();

// 中断处理
void keyboard_interrupt_handler();

#endif /* KEYBOARD_H */
