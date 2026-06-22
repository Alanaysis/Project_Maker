/**
 * IDT 初始化 (idt.c)
 * 功能: 初始化中断描述符表
 */

#include "../include/idt.h"
#include "../include/memory.h"
#include "../include/screen.h"

// IDT 表
static idt_entry_t idt[256];
static idt_ptr_t idt_ptr;

// 中断处理函数表
static interrupt_handler_t interrupt_handlers[256];

// 外部汇编函数
extern void idt_flush(uint32_t idt_ptr);

// 中断服务程序声明 (由汇编实现)
extern void isr0();
extern void isr1();
extern void isr2();
extern void isr3();
extern void isr4();
extern void isr5();
extern void isr6();
extern void isr7();
extern void isr8();
extern void isr9();
extern void isr10();
extern void isr11();
extern void isr12();
extern void isr13();
extern void isr14();
extern void isr15();
extern void isr16();
extern void isr17();
extern void isr18();
extern void isr19();
extern void isr20();
extern void isr21();
extern void isr22();
extern void isr23();
extern void isr24();
extern void isr25();
extern void isr26();
extern void isr27();
extern void isr28();
extern void isr29();
extern void isr30();
extern void isr31();

// 硬件中断
extern void irq0();
extern void irq1();
extern void irq2();
extern void irq3();
extern void irq4();
extern void irq5();
extern void irq6();
extern void irq7();
extern void irq8();
extern void irq9();
extern void irq10();
extern void irq11();
extern void irq12();
extern void irq13();
extern void irq14();
extern void irq15();

// 系统调用
extern void isr128();

// IDT 初始化
void idt_init() {
    // 设置 IDT 指针
    idt_ptr.limit = sizeof(idt) - 1;
    idt_ptr.base = (uint32_t)&idt;

    // 清空 IDT
    memset(idt, 0, sizeof(idt));

    // 清空中断处理函数表
    memset(interrupt_handlers, 0, sizeof(interrupt_handlers));

    // 重新映射 PIC (可编程中断控制器)
    // ICW1: 开始初始化
    outb(0x20, 0x11);  // 主 PIC
    outb(0xA0, 0x11);  // 从 PIC

    // ICW2: 设置中断向量偏移
    outb(0x21, 0x20);  // 主 PIC: IRQ 0-7 -> INT 32-39
    outb(0xA1, 0x28);  // 从 PIC: IRQ 8-15 -> INT 40-47

    // ICW3: 设置级联
    outb(0x21, 0x04);  // 主 PIC: IRQ 2 连接从 PIC
    outb(0xA1, 0x02);  // 从 PIC: 连接到主 PIC IRQ 2

    // ICW4: 设置模式
    outb(0x21, 0x01);  // 主 PIC: 8086 模式
    outb(0xA1, 0x01);  // 从 PIC: 8086 模式

    // 清空中断屏蔽
    outb(0x21, 0x00);  // 主 PIC: 允许所有中断
    outb(0xA1, 0x00);  // 从 PIC: 允许所有中断

    // 注册异常处理程序 (INT 0-31)
    idt_set_gate(0, (uint32_t)isr0, 0x08, 0x8E);   // 除零错误
    idt_set_gate(1, (uint32_t)isr1, 0x08, 0x8E);   // 调试异常
    idt_set_gate(2, (uint32_t)isr2, 0x08, 0x8E);   // NMI
    idt_set_gate(3, (uint32_t)isr3, 0x08, 0x8E);   // 断点
    idt_set_gate(4, (uint32_t)isr4, 0x08, 0x8E);   // 溢出
    idt_set_gate(5, (uint32_t)isr5, 0x08, 0x8E);   // 边界检查
    idt_set_gate(6, (uint32_t)isr6, 0x08, 0x8E);   // 无效操作码
    idt_set_gate(7, (uint32_t)isr7, 0x08, 0x8E);   // 设备不可用
    idt_set_gate(8, (uint32_t)isr8, 0x08, 0x8E);   // 双重错误
    idt_set_gate(9, (uint32_t)isr9, 0x08, 0x8E);   // 协处理器段溢出
    idt_set_gate(10, (uint32_t)isr10, 0x08, 0x8E); // 无效 TSS
    idt_set_gate(11, (uint32_t)isr11, 0x08, 0x8E); // 段不存在
    idt_set_gate(12, (uint32_t)isr12, 0x08, 0x8E); // 栈段错误
    idt_set_gate(13, (uint32_t)isr13, 0x08, 0x8E); // 通用保护错误
    idt_set_gate(14, (uint32_t)isr14, 0x08, 0x8E); // 页面错误
    idt_set_gate(15, (uint32_t)isr15, 0x08, 0x8E); // 保留
    idt_set_gate(16, (uint32_t)isr16, 0x08, 0x8E); // 浮点异常
    idt_set_gate(17, (uint32_t)isr17, 0x08, 0x8E); // 对齐检查
    idt_set_gate(18, (uint32_t)isr18, 0x08, 0x8E); // 机器检查
    idt_set_gate(19, (uint32_t)isr19, 0x08, 0x8E); // SIMD 浮点异常
    idt_set_gate(20, (uint32_t)isr20, 0x08, 0x8E);
    idt_set_gate(21, (uint32_t)isr21, 0x08, 0x8E);
    idt_set_gate(22, (uint32_t)isr22, 0x08, 0x8E);
    idt_set_gate(23, (uint32_t)isr23, 0x08, 0x8E);
    idt_set_gate(24, (uint32_t)isr24, 0x08, 0x8E);
    idt_set_gate(25, (uint32_t)isr25, 0x08, 0x8E);
    idt_set_gate(26, (uint32_t)isr26, 0x08, 0x8E);
    idt_set_gate(27, (uint32_t)isr27, 0x08, 0x8E);
    idt_set_gate(28, (uint32_t)isr28, 0x08, 0x8E);
    idt_set_gate(29, (uint32_t)isr29, 0x08, 0x8E);
    idt_set_gate(30, (uint32_t)isr30, 0x08, 0x8E);
    idt_set_gate(31, (uint32_t)isr31, 0x08, 0x8E);

    // 注册硬件中断 (IRQ 0-15 -> INT 32-47)
    idt_set_gate(32, (uint32_t)irq0, 0x08, 0x8E);  // 定时器
    idt_set_gate(33, (uint32_t)irq1, 0x08, 0x8E);  // 键盘
    idt_set_gate(34, (uint32_t)irq2, 0x08, 0x8E);  // 级联
    idt_set_gate(35, (uint32_t)irq3, 0x08, 0x8E);  // COM2
    idt_set_gate(36, (uint32_t)irq4, 0x08, 0x8E);  // COM1
    idt_set_gate(37, (uint32_t)irq5, 0x08, 0x8E);  // LPT2
    idt_set_gate(38, (uint32_t)irq6, 0x08, 0x8E);  // 软盘
    idt_set_gate(39, (uint32_t)irq7, 0x08, 0x8E);  // LPT1
    idt_set_gate(40, (uint32_t)irq8, 0x08, 0x8E);  // CMOS
    idt_set_gate(41, (uint32_t)irq9, 0x08, 0x8E);  // 自由
    idt_set_gate(42, (uint32_t)irq10, 0x08, 0x8E); // 自由
    idt_set_gate(43, (uint32_t)irq11, 0x08, 0x8E); // 自由
    idt_set_gate(44, (uint32_t)irq12, 0x08, 0x8E); // PS/2 鼠标
    idt_set_gate(45, (uint32_t)irq13, 0x08, 0x8E); // FPU
    idt_set_gate(46, (uint32_t)irq14, 0x08, 0x8E); // 主 ATA
    idt_set_gate(47, (uint32_t)irq15, 0x08, 0x8E); // 从 ATA

    // 注册系统调用 (INT 0x80)
    idt_set_gate(0x80, (uint32_t)isr128, 0x08, 0xEE); // 用户态可调用

    // 加载 IDT
    idt_flush((uint32_t)&idt_ptr);
}

// 设置 IDT 门
void idt_set_gate(uint8_t num, uint32_t base, uint16_t selector, uint8_t flags) {
    idt[num].base_low = (base & 0xFFFF);
    idt[num].base_high = (base >> 16) & 0xFFFF;
    idt[num].selector = selector;
    idt[num].zero = 0;
    idt[num].flags = flags;
}

// 注册中断处理函数
void interrupt_register(uint8_t num, interrupt_handler_t handler) {
    interrupt_handlers[num] = handler;
}

// 注销中断处理函数
void interrupt_unregister(uint8_t num) {
    interrupt_handlers[num] = 0;
}

// 中断处理函数 (由汇编调用)
void interrupt_handler_c(interrupt_frame_t *frame) {
    // 调用注册的处理函数
    if (interrupt_handlers[frame->int_no]) {
        interrupt_handlers[frame->int_no](frame);
    }
    // 如果是硬件中断，发送 EOI
    else if (frame->int_no >= 32 && frame->int_no < 48) {
        // 发送 EOI 到主 PIC
        outb(0x20, 0x20);

        // 如果是从 PIC 的中断，也发送 EOI 到从 PIC
        if (frame->int_no >= 40) {
            outb(0xA0, 0x20);
        }
    }
    // 未处理的异常
    else if (frame->int_no < 32) {
        screen_set_color(COLOR_LIGHT_RED, COLOR_BLACK);
        screen_puts("[EXCEPTION] Unhandled exception: ");
        screen_put_int(frame->int_no);
        screen_puts("\n");
        screen_puts("[EXCEPTION] Error code: ");
        screen_put_int(frame->err_code);
        screen_puts("\n");
        screen_puts("[EXCEPTION] EIP: ");
        screen_put_hex(frame->eip);
        screen_puts("\n");
        screen_puts("[EXCEPTION] System halted.\n");

        // 停机
        while (1) {
            asm volatile("hlt");
        }
    }
}

// 端口输出函数
void outb(uint16_t port, uint8_t value) {
    asm volatile("outb %1, %0" : : "dN"(port), "a"(value));
}

// 端口输入函数
uint8_t inb(uint16_t port) {
    uint8_t ret;
    asm volatile("inb %1, %0" : "=a"(ret) : "dN"(port));
    return ret;
}
