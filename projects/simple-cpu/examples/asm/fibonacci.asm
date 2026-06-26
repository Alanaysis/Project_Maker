; Fibonacci Sequence - 斐波那契数列
; Demonstrates arithmetic, memory operations, and control flow
; 演示算术运算、内存操作和流程控制

    LUI x1, 10        ; n = 10 (number of terms)
    LUI x2, 0         ; F(0) = 0
    LUI x3, 1         ; F(1) = 1
    LUI x4, 2         ; i = 2 (loop counter)
    LUI x5, 1         ; one = 1
    LUI x6, 0         ; zero = 0

fib_loop:
    ; Check if i >= n: SLT x7, x4, x1 -> if i < n, x7=1, else x7=0
    SLT x7, x4, x1
    BEQ x7, x6, fib_done  ; if i >= n, exit

    ; F(i) = F(i-1) + F(i-2)
    ADD x8, x2, x3    ; x8 = F(i-2) + F(i-1)

    ; Shift: F(i-2) = F(i-1), F(i-1) = F(i)
    LUI x9, 0
    STORE x3, 0(x9)   ; mem[0] = F(i-1)
    STORE x8, 4(x9)   ; mem[4] = F(i)

    LOAD x2, 0(x9)    ; x2 = F(i-1) (from mem)
    LOAD x3, 4(x9)    ; x3 = F(i) (from mem)

    ; i = i + 1
    ADD x4, x4, x5

    JUMP fib_loop

fib_done:
    ; Store final count
    LUI x9, 8
    STORE x4, 0(x9)

    HALT
