/**
 * GDT 初始化 (gdt.c)
 * 功能: 初始化全局描述符表
 */

#include "../include/gdt.h"
#include "../include/memory.h"

// GDT 表
static gdt_entry_t gdt[6];
static gdt_ptr_t gdt_ptr;

// 外部汇编函数
extern void gdt_flush(uint32_t gdt_ptr);

// GDT 初始化
void gdt_init() {
    // 设置 GDT 指针
    gdt_ptr.limit = sizeof(gdt) - 1;
    gdt_ptr.base = (uint32_t)&gdt;

    // 空描述符 (必须)
    gdt_set_gate(0, 0, 0, 0, 0);

    // 代码段描述符
    gdt_set_gate(1, 0, 0xFFFFFFFF, 0x9A, 0xCF);

    // 数据段描述符
    gdt_set_gate(2, 0, 0xFFFFFFFF, 0x92, 0xCF);

    // 用户代码段描述符
    gdt_set_gate(3, 0, 0xFFFFFFFF, 0xFA, 0xCF);

    // 用户数据段描述符
    gdt_set_gate(4, 0, 0xFFFFFFFF, 0xF2, 0xCF);

    // TSS 段描述符 (稍后设置)
    gdt_set_gate(5, 0, 0, 0, 0);

    // 加载 GDT
    gdt_flush((uint32_t)&gdt_ptr);
}

// 设置 GDT 门
void gdt_set_gate(int num, uint32_t base, uint32_t limit, uint8_t access, uint8_t gran) {
    // 设置基地址
    gdt[num].base_low = (base & 0xFFFF);
    gdt[num].base_middle = (base >> 16) & 0xFF;
    gdt[num].base_high = (base >> 24) & 0xFF;

    // 设置段限长
    gdt[num].limit_low = (limit & 0xFFFF);
    gdt[num].granularity = ((limit >> 16) & 0x0F);

    // 设置粒度和访问字节
    gdt[num].granularity |= (gran & 0xF0);
    gdt[num].access = access;
}
