; Addition Program - 加法程序
; Demonstrates basic data movement and arithmetic operations
; 演示基本的数据移动和算术运算

; This program computes: result = 10 + 20 + 30
; The data path:
;   1. LUI loads immediate values into registers
;   2. ADD performs arithmetic
;   3. STORE saves result to memory

    LUI x1, 10        ; x1 = 10
    LUI x2, 20        ; x2 = 20
    LUI x3, 30        ; x3 = 30

    ADD x4, x1, x2    ; x4 = x1 + x2 = 30
    ADD x5, x4, x3    ; x5 = x4 + x3 = 60

    LUI x6, 0         ; x6 = 0 (base address)
    STORE x5, 0(x6)   ; mem[0] = x5 (store result to memory)

    LUI x7, 0         ; x7 = 0
    LOAD x8, 0(x7)    ; x8 = mem[0] (load result back)

    HALT              ; Stop execution
