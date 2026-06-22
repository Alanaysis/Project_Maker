; 加载器 (loader.asm)
; 功能: 设置保护模式，加载内核，跳转到内核入口

[bits 16]
[org 0x1000]

; 常量定义
KERNEL_OFFSET   equ 0x100000    ; 内核加载地址 (1MB)
KERNEL_SECTORS  equ 50          ; 内核占用扇区数
VIDEO_MEMORY    equ 0xB8000     ; VGA 文本模式内存

; 代码段
loader_start:
    ; 设置段寄存器
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x9000              ; 设置栈

    ; 显示加载器信息
    mov si, msg_loader_start
    call print_string_16

    ; 检测内存
    call detect_memory

    ; 加载内核到 KERNEL_OFFSET
    call load_kernel

    ; 切换到保护模式
    call switch_to_protected_mode

    ; 不应该到达这里
    jmp $

; 函数: 检测内存
detect_memory:
    mov si, msg_detecting_memory
    call print_string_16

    ; 使用 BIOS int 15h, eax=0xE820 检测内存
    mov di, memory_map_buffer
    xor ebx, ebx               ; 第一次调用，ebx=0
    mov edx, 0x534D4150         ; 'SMAP'
    mov ecx, 20                 ; 缓冲区大小
    mov eax, 0xE820
    int 0x15

    jc .error                   ; CF 置位表示错误
    cmp eax, 0x534D4150         ; 验证返回值
    jne .error

    mov si, msg_memory_detected
    call print_string_16
    ret

.error:
    mov si, msg_memory_error
    call print_string_16
    ret

; 函数: 加载内核
load_kernel:
    mov si, msg_loading_kernel
    call print_string_16

    ; 使用 BIOS int 13h 读取内核
    mov ah, 0x02                ; BIOS 读扇区功能
    mov al, KERNEL_SECTORS      ; 读取扇区数
    mov ch, 0                   ; 柱面 0
    mov cl, 6                   ; 扇区 6 (引导扇区 + 加载器)
    mov dh, 0                   ; 磁头 0
    mov dl, [boot_drive]        ; 驱动器号

    ; 由于内核加载到 1MB 以上，需要使用扩展读取
    ; 这里简化处理，使用临时缓冲区
    mov bx, kernel_temp_buffer
    int 0x13

    jc .error

    ; 将内核复制到 1MB 地址
    ; 注意: 这需要 A20 地址线已启用
    call enable_a20

    ; 复制内核到高地址
    call copy_kernel_to_high

    mov si, msg_kernel_loaded
    call print_string_16
    ret

.error:
    mov si, msg_kernel_error
    call print_string_16
    ret

; 函数: 启用 A20 地址线
enable_a20:
    ; 使用键盘控制器启用 A20
    cli

    call .wait_input
    mov al, 0xAD                ; 禁用键盘
    out 0x64, al

    call .wait_input
    mov al, 0xD0                ; 读取输出端口
    out 0x64, al

    call .wait_output
    in al, 0x60                 ; 读取当前值
    push eax

    call .wait_input
    mov al, 0xD1                ; 写入输出端口
    out 0x64, al

    call .wait_input
    pop eax
    or al, 2                    ; 启用 A20 (位 1)
    out 0x60, al

    call .wait_input
    mov al, 0xAE                ; 启用键盘
    out 0x64, al

    call .wait_input
    sti
    ret

.wait_input:
    in al, 0x64
    test al, 2
    jnz .wait_input
    ret

.wait_output:
    in al, 0x64
    test al, 1
    jz .wait_output
    ret

; 函数: 复制内核到高地址
copy_kernel_to_high:
    ; 使用实模式段复制
    ; 注意: 这是一个简化实现
    push es

    ; 设置源段 (临时缓冲区)
    mov ax, 0x0000
    mov ds, ax
    mov si, kernel_temp_buffer

    ; 设置目标段 (1MB 地址)
    mov ax, 0x1000
    mov es, ax
    xor di, di

    ; 复制内核
    mov cx, KERNEL_SECTORS * 512 / 2  ; 字数
    rep movsw

    pop es
    ret

; 函数: 切换到保护模式
switch_to_protected_mode:
    cli                         ; 禁用中断

    ; 加载 GDT
    lgdt [gdt_descriptor]

    ; 设置 CR0 的 PE 位 (保护模式启用)
    mov eax, cr0
    or eax, 1
    mov cr0, eax

    ; 远跳转刷新流水线，进入保护模式
    jmp 0x08:protected_mode_entry

; 函数: 打印字符串 (16 位模式)
; 输入: SI = 字符串地址
print_string_16:
    pusha
.loop:
    lodsb
    or al, al
    jz .done
    mov ah, 0x0E
    mov bh, 0
    int 0x10
    jmp .loop
.done:
    popa
    ret

; 保护模式入口
[bits 32]
protected_mode_entry:
    ; 设置段寄存器
    mov ax, 0x10                ; 数据段选择子
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000            ; 设置栈顶

    ; 跳转到内核
    jmp KERNEL_OFFSET

; GDT 定义
gdt_start:
    ; 空描述符 (必须)
    dq 0

; 代码段描述符
gdt_code:
    dw 0xFFFF                   ; 段限长 (低 16 位)
    dw 0x0000                   ; 基地址 (低 16 位)
    db 0x00                     ; 基地址 (中间 8 位)
    db 10011010b                ; 访问字节: 存在, ring 0, 代码段, 可读
    db 11001111b                ; 粒度: 4KB, 32 位
    db 0x00                     ; 基地址 (高 8 位)

; 数据段描述符
gdt_data:
    dw 0xFFFF                   ; 段限长 (低 16 位)
    dw 0x0000                   ; 基地址 (低 16 位)
    db 0x00                     ; 基地址 (中间 8 位)
    db 10010010b                ; 访问字节: 存在, ring 0, 数据段, 可写
    db 11001111b                ; 粒度: 4KB, 32 位
    db 0x00                     ; 基地址 (高 8 位)

gdt_end:

; GDT 描述符
gdt_descriptor:
    dw gdt_end - gdt_start - 1 ; GDT 大小
    dd gdt_start                ; GDT 地址

; GDT 选择子常量
CODE_SEG equ gdt_code - gdt_start
DATA_SEG equ gdt_data - gdt_start

; 数据段
boot_drive:             db 0
msg_loader_start:       db 'Loader starting...', 13, 10, 0
msg_detecting_memory:   db 'Detecting memory...', 13, 10, 0
msg_memory_detected:    db 'Memory detected.', 13, 10, 0
msg_memory_error:       db 'Memory detection error!', 13, 10, 0
msg_loading_kernel:     db 'Loading kernel...', 13, 10, 0
msg_kernel_loaded:      db 'Kernel loaded.', 13, 10, 0
msg_kernel_error:       db 'Kernel load error!', 13, 10, 0

; 内存映射缓冲区
memory_map_buffer:      times 256 db 0

; 内核临时缓冲区 (实模式下使用)
kernel_temp_buffer:     times KERNEL_SECTORS * 512 db 0
