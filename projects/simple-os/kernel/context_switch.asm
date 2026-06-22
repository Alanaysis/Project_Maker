; 上下文切换 (context_switch.asm)
; 功能: 保存和恢复进程上下文

[bits 32]

; 全局函数声明
global context_switch

; 上下文切换函数
; 参数: [esp+4] = 前一个进程的 PCB 指针
;        [esp+8] = 下一个进程的 PCB 指针
context_switch:
    ; 获取参数
    mov eax, [esp+4]    ; 前一个进程
    mov edx, [esp+8]    ; 下一个进程

    ; 保存前一个进程的上下文
    pushf               ; 保存 EFLAGS
    push cs             ; 保存 CS
    push .return        ; 保存返回地址
    push ebp            ; 保存 EBP
    push edi            ; 保存 EDI
    push esi            ; 保存 ESI
    push edx            ; 保存 EDX
    push ecx            ; 保存 ECX
    push ebx            ; 保存 EBX
    push eax            ; 保存 EAX

    ; 保存 ESP 到前一个进程的 PCB
    mov [eax + 4], esp  ; PCB.esp = 当前 ESP

    ; 恢复下一个进程的上下文
    mov esp, [edx + 4]  ; ESP = 下一个进程的 PCB.esp

    ; 恢复寄存器
    pop eax             ; 恢复 EAX
    pop ebx             ; 恢复 EBX
    pop ecx             ; 恢复 ECX
    pop edx             ; 恢复 EDX
    pop esi             ; 恢复 ESI
    pop edi             ; 恢复 EDI
    pop ebp             ; 恢复 EBP
    add esp, 4          ; 跳过返回地址
    pop cs              ; 恢复 CS
    popf                ; 恢复 EFLAGS

    ret

.return:
    ; 上下文切换完成
    ret
