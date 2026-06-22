; calc.asm - 简单的计算器程序
; 演示基本的算术运算和输出

[BITS 16]
[ORG 0x7C00]

; 串口端口定义
%define COM1_PORT    0x3F8
%define COM1_THR     COM1_PORT + 0
%define COM1_LSR     COM1_PORT + 5

start:
    ; 初始化段寄存器
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    ; 输出标题
    mov si, msg_title
    call print_string

    ; 计算 10 + 20
    mov ax, 10
    mov bx, 20
    add ax, bx

    ; 输出结果
    mov si, msg_add
    call print_string
    call print_number

    ; 计算 50 - 15
    mov ax, 50
    mov bx, 15
    sub ax, bx

    ; 输出结果
    mov si, msg_sub
    call print_string
    call print_number

    ; 计算 6 * 7
    mov ax, 6
    mov bx, 7
    mul bx          ; 结果在 DX:AX

    ; 输出结果
    mov si, msg_mul
    call print_string
    call print_number

    ; 计算 100 / 4
    mov ax, 100
    xor dx, dx      ; 清除 DX
    mov bx, 4
    div bx          ; 商在 AX，余数在 DX

    ; 输出结果
    mov si, msg_div
    call print_string
    call print_number

    ; 输出完成消息
    mov si, msg_done
    call print_string

    ; 停机
    hlt

; 打印字符串函数
print_string:
    pusha
.loop:
    lodsb
    or al, al
    jz .done
    call wait_transmit_empty
    mov dx, COM1_THR
    out dx, al
    jmp .loop
.done:
    popa
    ret

; 打印数字函数（十进制）
; 输入: AX = 数字
print_number:
    pusha
    mov cx, 0       ; 计数器
    mov bx, 10      ; 除数

    ; 特殊情况：数字为 0
    test ax, ax
    jnz .convert
    mov al, '0'
    call print_char
    jmp .done

.convert:
    ; 转换数字到字符串
    xor dx, dx
    div bx          ; AX / 10，商在 AX，余数在 DX
    push dx         ; 保存余数
    inc cx          ; 增加计数器
    test ax, ax     ; 检查商是否为 0
    jnz .convert

.print:
    ; 打印数字
    pop dx          ; 获取余数
    add dl, '0'     ; 转换为 ASCII
    mov al, dl
    call print_char
    loop .print

.done:
    ; 打印换行
    mov al, 13
    call print_char
    mov al, 10
    call print_char

    popa
    ret

; 打印字符函数
; 输入: AL = 字符
print_char:
    push dx
    call wait_transmit_empty
    mov dx, COM1_THR
    out dx, al
    pop dx
    ret

; 等待发送缓冲区空
wait_transmit_empty:
    push ax
    push dx
.wait:
    mov dx, COM1_LSR
    in al, dx
    test al, 0x20
    jz .wait
    pop dx
    pop ax
    ret

; 数据段
msg_title db '=== Simple Calculator ===', 13, 10, 0
msg_add   db '10 + 20 = ', 0
msg_sub   db '50 - 15 = ', 0
msg_mul   db '6 * 7 = ', 0
msg_div   db '100 / 4 = ', 0
msg_done  db 'Calculation complete!', 13, 10, 0

; 填充引导扇区
times 510-($-$$) db 0
dw 0xAA55
