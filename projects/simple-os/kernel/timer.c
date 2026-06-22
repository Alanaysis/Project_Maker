/**
 * 定时器 (timer.c)
 * 功能: 处理定时器中断，实现时间片调度
 */

#include "../include/idt.h"
#include "../include/screen.h"

// 端口函数 (在 idt.c 中定义)
extern void outb(uint16_t port, uint8_t value);
extern uint8_t inb(uint16_t port);

// 时钟滴答计数
static uint32_t timer_ticks = 0;

// 定时器频率 (Hz)
#define TIMER_FREQ 100

// 定时器中断处理函数
void timer_interrupt_handler() {
    timer_ticks++;

    // 调用调度器
    extern void scheduler_tick();
    scheduler_tick();
}

// 初始化定时器
void timer_init() {
    // 注册定时器中断处理函数
    interrupt_register(32, timer_interrupt_handler);  // IRQ 0 = INT 32

    // 设置 PIT (可编程间隔定时器)
    uint32_t divisor = 1193180 / TIMER_FREQ;

    // 发送命令字节
    outb(0x43, 0x36);  // 通道 0, 方式 3 (方波), 二进制

    // 发送频率除数
    outb(0x40, divisor & 0xFF);        // 低字节
    outb(0x40, (divisor >> 8) & 0xFF); // 高字节

    screen_puts("[TIMER] Timer initialized.\n");
}

// 获取时钟滴答数
uint32_t timer_get_ticks() {
    return timer_ticks;
}

// 延时 (毫秒)
void timer_sleep(uint32_t milliseconds) {
    uint32_t target_ticks = timer_ticks + (milliseconds * TIMER_FREQ / 1000);
    while (timer_ticks < target_ticks) {
        asm volatile("hlt");
    }
}
