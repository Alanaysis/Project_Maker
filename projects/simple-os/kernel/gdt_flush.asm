; GDT 刷新 (gdt_flush.asm)
; 功能: 加载新的 GDT 并刷新段寄存器

[bits 32]

; 全局函数声明
global gdt_flush

; GDT 刷新函数
; 参数: [esp+4] = GDT 描述符地址
gdt_flush:
    mov eax, [esp+4]    ; 获取 GDT 描述符地址
    lgdt [eax]          ; 加载 GDT

    ; 刷新段寄存器
    mov ax, 0x10        ; 数据段选择子 (GDT 第 3 项)
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax

    ; 远跳转刷新代码段寄存器
    jmp 0x08:.flush     ; 代码段选择子 (GDT 第 2 项)

.flush:
    ret
