#ifndef IDT_H
#define IDT_H

#include "types.h"

// IDT 条目
typedef struct {
    uint16_t base_low;
    uint16_t selector;
    uint8_t  zero;
    uint8_t  flags;
    uint16_t base_high;
} __attribute__((packed)) idt_entry_t;

// IDT 指针
typedef struct {
    uint16_t limit;
    uint32_t base;
} __attribute__((packed)) idt_ptr_t;

// 中断帧
typedef struct {
    uint32_t ds;
    uint32_t edi, esi, ebp, useless_esp, ebx, edx, ecx, eax;
    uint32_t int_no, err_code;
    uint32_t eip, cs, eflags, esp, ss;
} interrupt_frame_t;

// 中断处理函数类型
typedef void (*interrupt_handler_t)(interrupt_frame_t *frame);

// IDT 函数
void idt_init();
void idt_set_gate(uint8_t num, uint32_t base, uint16_t selector, uint8_t flags);
void interrupt_register(uint8_t num, interrupt_handler_t handler);
void interrupt_unregister(uint8_t num);

#endif /* IDT_H */
