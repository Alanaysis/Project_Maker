; 中断服务程序 (isr.asm)
; 功能: 处理 CPU 异常和系统调用

[bits 32]

; 外部 C 函数
extern interrupt_handler_c

; 全局函数声明
global isr0
global isr1
global isr2
global isr3
global isr4
global isr5
global isr6
global isr7
global isr8
global isr9
global isr10
global isr11
global isr12
global isr13
global isr14
global isr15
global isr16
global isr17
global isr18
global isr19
global isr20
global isr21
global isr22
global isr23
global isr24
global isr25
global isr26
global isr27
global isr28
global isr29
global isr30
global isr31

; 系统调用
global isr128

; 宏: ISR 无错误码
%macro ISR_NOERRCODE 1
isr%1:
    push dword 0            ; 压入伪错误码
    push dword %1           ; 压入中断号
    jmp isr_common_stub
%endmacro

; 宏: ISR 有错误码
%macro ISR_ERRCODE 1
isr%1:
    push dword %1           ; 压入中断号
    jmp isr_common_stub
%endmacro

; ISR 处理程序
ISR_NOERRCODE 0     ; 除零错误
ISR_NOERRCODE 1     ; 调试异常
ISR_NOERRCODE 2     ; NMI
ISR_NOERRCODE 3     ; 断点
ISR_NOERRCODE 4     ; 溢出
ISR_NOERRCODE 5     ; 边界检查
ISR_NOERRCODE 6     ; 无效操作码
ISR_NOERRCODE 7     ; 设备不可用
ISR_ERRCODE   8     ; 双重错误
ISR_NOERRCODE 9     ; 协处理器段溢出
ISR_ERRCODE   10    ; 无效 TSS
ISR_ERRCODE   11    ; 段不存在
ISR_ERRCODE   12    ; 栈段错误
ISR_ERRCODE   13    ; 通用保护错误
ISR_ERRCODE   14    ; 页面错误
ISR_NOERRCODE 15    ; 保留
ISR_NOERRCODE 16    ; 浮点异常
ISR_ERRCODE   17    ; 对齐检查
ISR_NOERRCODE 18    ; 机器检查
ISR_NOERRCODE 19    ; SIMD 浮点异常
ISR_NOERRCODE 20
ISR_NOERRCODE 21
ISR_NOERRCODE 22
ISR_NOERRCODE 23
ISR_NOERRCODE 24
ISR_NOERRCODE 25
ISR_NOERRCODE 26
ISR_NOERRCODE 27
ISR_NOERRCODE 28
ISR_NOERRCODE 29
ISR_NOERRCODE 30
ISR_NOERRCODE 31

; 系统调用
ISR_NOERRCODE 128

; ISR 通用处理程序
isr_common_stub:
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

    ; 传递栈指针作为参数 (指向保存的寄存器)
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
