; Logic Operations Demo - 逻辑运算演示
; Demonstrates bitwise logic operations
; 演示按位逻辑运算

    LUI x1, 0xFF      ; x1 = 255 (0b11111111)
    LUI x2, 0x0F      ; x2 = 15 (0b00001111)

    ; AND: 0xFF & 0x0F = 0x0F
    AND x3, x1, x2
    LUI x4, 0
    STORE x3, 0(x4)

    ; OR: 0xFF | 0x0F = 0xFF
    OR x5, x1, x2
    LUI x4, 4
    STORE x5, 0(x4)

    ; XOR: 0xFF ^ 0x0F = 0xF0
    XOR x6, x1, x2
    LUI x4, 8
    STORE x6, 0(x4)

    ; NOT: ~0xFF = 0xFFFFFF00
    NOT x7, x1
    LUI x4, 12
    STORE x7, 0(x4)

    ; Shift left: 1 << 4 = 16
    LUI x8, 1
    LUI x9, 4
    SLL x10, x8, x9
    LUI x4, 16
    STORE x10, 0(x4)

    ; Set less than: 5 < 10 = 1
    LUI x11, 5
    LUI x12, 10
    SLT x13, x11, x12
    LUI x4, 20
    STORE x13, 0(x4)

    ; Add immediate: 100 + 50 = 150
    LUI x14, 100
    ADDI x15, x14, 50
    LUI x4, 24
    STORE x15, 0(x4)

    HALT
