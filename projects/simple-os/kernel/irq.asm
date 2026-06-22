; 硬件中断请求 (irq.asm)
; 功能: 处理硬件中断 (IRQ)

[bits 32]

; 外部 C 函数
extern interrupt_handler_c

; 全局函数声明
global irq0
global irq1
global irq2
global irq3
global irq4
global irq5
global irq6
global irq7
global irq8
global irq9
global irq10
global irq11
global irq12
global irq13
global irq14
global irq15

; 宏: IRQ 处理程序
%macro IRQ 2
irq%1:
    push dword 0            ; 伪错误码
    push dword %2           ; 中断号 (32 + IRQ号)
    jmp irq_common_stub
%endmacro

; IRQ 处理程序
IRQ 0, 32   ; 定时器
IRQ 1, 33   ; 键盘
IRQ 2, 34   ; 级联
IRQ 3, 35   ; COM2
IRQ 4, 36   ; COM1
IRQ 5, 37   ; LPT2
IRQ 6, 38   ; 软盘
IRQ 7, 39   ; LPT1
IRQ 8, 40   ; CMOS
IRQ 9, 41   ; 自由
IRQ 10, 42  ; 自由
IRQ 11, 43  ; 自由
IRQ 12, 44  ; PS/2 鼠标
IRQ 13, 45  ; FPU
IRQ 14, 46  ; 主 ATA
IRQ 15, 47  ; 从 ATA

; IRQ 通用处理程序
irq_common_stub:
    ; 保存寄存器
    pusha
    push ds
    push es
    push fs
    push gs

    ; 设置内核数据段
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; 传递栈指针作为参数
    mov eax, esp
    push eax

    ; 调用 C 处理函数
    mov eax, interrupt_handler_c
    call eax

    ; 恢复栈
    pop eax

    ; 恢复寄存器
    pop gs
    pop fs
    pop es
    pop ds
    popa

    ; 清除错误码和中断号
    add esp, 8

    ; 中断返回
    iret
