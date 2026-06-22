; hello.asm - 简单的 Hello World 程序
; 这个程序通过串口输出 "Hello, World!"

[BITS 16]           ; 16 位实模式
[ORG 0x7C00]        ; 引导扇区加载地址

; 串口端口定义
%define COM1_PORT    0x3F8
%define COM1_THR     COM1_PORT + 0  ; 发送保持寄存器
%define COM1_LSR     COM1_PORT + 5  ; 线路状态寄存器

start:
    ; 初始化段寄存器
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00  ; 栈指针指向加载地址

    ; 输出字符串
    mov si, message
    call print_string

    ; 停机
    hlt

; 打印字符串函数
; 输入: SI = 字符串地址
print_string:
    pusha
.loop:
    lodsb           ; 从 [SI] 读取一个字节到 AL
    or al, al       ; 检查是否是字符串结尾（0）
    jz .done        ; 如果是，跳转到结束

    ; 等待发送缓冲区空
    call wait_transmit_empty

    ; 发送字符
    mov dx, COM1_THR
    out dx, al

    jmp .loop       ; 继续下一个字符

.done:
    popa
    ret

; 等待发送缓冲区空
wait_transmit_empty:
    push ax
    push dx
.wait:
    mov dx, COM1_LSR
    in al, dx
    test al, 0x20   ; 检查 THRE 位
    jz .wait        ; 如果为空，继续等待
    pop dx
    pop ax
    ret

; 数据段
message db 'Hello, World!', 13, 10, 0

; 填充引导扇区
times 510-($-$$) db 0
dw 0xAA55           ; 引导扇区签名
