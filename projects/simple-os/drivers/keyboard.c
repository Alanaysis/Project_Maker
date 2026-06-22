/**
 * 键盘驱动 (keyboard.c)
 * 功能: 处理键盘输入
 */

#include "../include/keyboard.h"
#include "../include/screen.h"
#include "../include/idt.h"

// 端口函数 (在 idt.c 中定义)
extern void outb(uint16_t port, uint8_t value);
extern uint8_t inb(uint16_t port);

// 键盘状态
static keyboard_state_t kbd_state;

// 扫描码到 ASCII 的映射表 (无 Shift)
static const char scancode_to_ascii[] = {
    0, 0, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\b',
    '\t', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\n',
    0, 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`',
    0, '\\', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0,
    '*', 0, ' '
};

// 扫描码到 ASCII 的映射表 (有 Shift)
static const char scancode_to_ascii_shift[] = {
    0, 0, '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '\b',
    '\t', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '{', '}', '\n',
    0, 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ':', '"', '~',
    0, '|', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '<', '>', '?', 0,
    '*', 0, ' '
};

// 初始化键盘
void keyboard_init() {
    // 清空状态
    memset(&kbd_state, 0, sizeof(keyboard_state_t));

    // 注册键盘中断处理函数
    interrupt_register(33, keyboard_interrupt_handler);  // IRQ 1 = INT 33

    // 启用键盘中断
    uint8_t mask = inb(0x21);
    mask &= ~0x02;  // 清除 IRQ 1 的屏蔽位
    outb(0x21, mask);

    screen_puts("[KEYBOARD] Keyboard initialized.\n");
}

// 键盘中断处理函数
void keyboard_interrupt_handler() {
    // 读取扫描码
    uint8_t scancode = inb(0x60);

    // 检查是否是释放键 (最高位为 1)
    if (scancode & 0x80) {
        // 键释放
        scancode &= 0x7F;

        // 更新 Shift 状态
        if (scancode == KEY_LSHIFT || scancode == KEY_RSHIFT) {
            kbd_state.shift = 0;
        }
        return;
    }

    // 键按下
    switch (scancode) {
        case KEY_LSHIFT:
        case KEY_RSHIFT:
            kbd_state.shift = 1;
            return;

        case KEY_LCTRL:
            kbd_state.ctrl = 1;
            return;

        case KEY_LALT:
            kbd_state.alt = 1;
            return;

        case KEY_CAPSLOCK:
            kbd_state.capslock = !kbd_state.capslock;
            return;

        default:
            break;
    }

    // 转换为 ASCII
    char ascii = 0;
    if (scancode < sizeof(scancode_to_ascii)) {
        if (kbd_state.shift) {
            ascii = scancode_to_ascii_shift[scancode];
        } else {
            ascii = scancode_to_ascii[scancode];
        }

        // Caps Lock 处理
        if (kbd_state.capslock && ascii >= 'a' && ascii <= 'z') {
            ascii -= 32;  // 转换为大写
        } else if (kbd_state.capslock && ascii >= 'A' && ascii <= 'Z') {
            ascii += 32;  // 转换为小写
        }
    }

    // 如果有有效字符，放入缓冲区
    if (ascii && kbd_state.size < KEYBOARD_BUFFER_SIZE) {
        kbd_state.buffer[kbd_state.tail] = ascii;
        kbd_state.tail = (kbd_state.tail + 1) % KEYBOARD_BUFFER_SIZE;
        kbd_state.size++;
    }

    // 释放修饰键状态
    if (scancode == KEY_LCTRL || scancode == 0x1D + 0x80) {
        kbd_state.ctrl = 0;
    }
    if (scancode == KEY_LALT) {
        kbd_state.alt = 0;
    }
}

// 获取字符 (阻塞)
char keyboard_getchar() {
    // 等待缓冲区有数据
    while (kbd_state.size == 0) {
        asm volatile("hlt");
    }

    // 从缓冲区读取
    char c = kbd_state.buffer[kbd_state.head];
    kbd_state.head = (kbd_state.head + 1) % KEYBOARD_BUFFER_SIZE;
    kbd_state.size--;

    return c;
}

// 检查缓冲区是否有数据
int keyboard_available() {
    return kbd_state.size > 0;
}

// 读取字符 (非阻塞)
char keyboard_read() {
    if (kbd_state.size == 0) {
        return 0;
    }

    char c = kbd_state.buffer[kbd_state.head];
    kbd_state.head = (kbd_state.head + 1) % KEYBOARD_BUFFER_SIZE;
    kbd_state.size--;

    return c;
}

// 清空缓冲区
void keyboard_clear_buffer() {
    kbd_state.head = 0;
    kbd_state.tail = 0;
    kbd_state.size = 0;
}
