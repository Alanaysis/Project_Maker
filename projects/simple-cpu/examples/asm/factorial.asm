; Factorial Program - 阶乘程序
; Demonstrates computation with loops
; 演示带循环的计算

; This program computes 5! = 120
; 计算 5! = 120

    LUI x1, 5         ; x1 = n (counter = 5)
    LUI x2, 1         ; x2 = result (accumulator = 1)
    LUI x3, 1         ; x3 = 1 (for comparison and decrement)

factorial_loop:
    ; Check if n > 1
    SUB x4, x1, x3    ; x4 = n - 1
    LUI x5, 0
    BEQ x4, x5, factorial_done  ; if n == 1, done

    ; result = result * n
    MUL x2, x2, x1    ; result *= n

    ; n = n - 1
    SUB x1, x1, x3    ; n--

    JUMP factorial_loop

factorial_done:
    ; Store result to memory[0]
    LUI x6, 0
    STORE x2, 0(x6)   ; mem[0] = result (120)

    HALT
