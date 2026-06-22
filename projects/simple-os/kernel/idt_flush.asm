; IDT 刷新 (idt_flush.asm)
; 功能: 加载新的 IDT

[bits 32]

; 全局函数声明
global idt_flush

; IDT 刷新函数
; 参数: [esp+4] = IDT 描述符地址
idt_flush:
    mov eax, [esp+4]    ; 获取 IDT 描述符地址
    lidt [eax]          ; 加载 IDT
    ret
