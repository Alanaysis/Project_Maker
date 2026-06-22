; 主引导扇区 (boot.asm)
; 功能: BIOS 加载此扇区到 0x7C00, 然后加载加载器并跳转

[bits 16]           ; 16 位实模式
[org 0x7C00]        ; BIOS 加载地址

; 常量定义
LOADER_OFFSET  equ 0x1000      ; 加载器加载地址
LOADER_SECTORS equ 4           ; 加载器占用扇区数

start:
    ; 设置段寄存器和栈
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00              ; 栈顶设置在引导扇区下方

    ; 保存启动驱动器号
    mov [boot_drive], dl

    ; 显示启动信息
    mov si, msg_booting
    call print_string

    ; 加载加载器到 LOADER_OFFSET
    call load_loader

    ; 跳转到加载器
    jmp 0x0000:LOADER_OFFSET

; 函数: 加载加载器
load_loader:
    mov si, msg_loading
    call print_string

    ; 使用 BIOS int 13h 读取磁盘
    mov ah, 0x02                ; BIOS 读扇区功能
    mov al, LOADER_SECTORS      ; 读取扇区数
    mov ch, 0                   ; 柱面 0
    mov cl, 2                   ; 扇区 2 (引导扇区是扇区 1)
    mov dh, 0                   ; 磁头 0
    mov dl, [boot_drive]        ; 驱动器号
    mov bx, LOADER_OFFSET       ; 加载到 ES:BX
    int 0x13                    ; 调用 BIOS 磁盘服务

    jc disk_error               ; 如果 CF 置位，表示出错

    ; 验证读取的扇区数
    cmp al, LOADER_SECTORS
    jne disk_error

    mov si, msg_done
    call print_string
    ret

; 函数: 打印字符串
; 输入: SI = 字符串地址
print_string:
    pusha
.loop:
    lodsb                       ; 加载字节到 AL
    or al, al                   ; 检查是否为 0 (字符串结束)
    jz .done
    mov ah, 0x0E                ; BIOS 电传打字功能
    mov bh, 0                   ; 页码
    int 0x10                    ; 调用 BIOS 视频服务
    jmp .loop
.done:
    popa
    ret

; 磁盘错误处理
disk_error:
    mov si, msg_disk_error
    call print_string
    ; 等待按键后重启
    mov ah, 0x00
    int 0x16
    jmp 0xFFFF:0x0000           ; 重启

; 数据
boot_drive:     db 0
msg_booting:    db 'Simple OS Booting...', 13, 10, 0
msg_loading:    db 'Loading loader...', 13, 10, 0
msg_done:       db 'Loader loaded.', 13, 10, 0
msg_disk_error: db 'Disk error! Press any key to reboot.', 13, 10, 0

; 填充到 510 字节并添加引导标记
times 510-($-$$) db 0
dw 0xAA55                       ; 引导扇区标记
