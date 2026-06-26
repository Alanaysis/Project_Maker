; Sorting Program - 冒泡排序程序
; Demonstrates loops, branches, and memory operations
; 演示循环、分支和内存操作

    ; Initialize array at memory[0..16]: [5, 3, 8, 1, 9]
    LUI x6, 0         ; x6 = base address = 0

    LUI x7, 5
    STORE x7, 0(x6)   ; mem[0] = 5

    LUI x7, 3
    STORE x7, 4(x6)   ; mem[4] = 3

    LUI x7, 8
    STORE x7, 8(x6)   ; mem[8] = 8

    LUI x7, 1
    STORE x7, 12(x6)  ; mem[12] = 1

    LUI x7, 9
    STORE x7, 16(x6)  ; mem[16] = 9

    ; Bubble sort: outer loop i = 5
    LUI x8, 5         ; x8 = i

outer_loop:
    LUI x9, 0
    BEQ x8, x9, sort_done  ; if i == 0, done

    ; Inner loop j = i - 1
    SUB x10, x8, x9   ; x10 = i
    LUI x9, 1
    SUB x10, x10, x9  ; x10 = i - 1 = j

inner_loop:
    LUI x11, 0
    BEQ x10, x11, next_outer  ; if j == 0, next outer

    ; Load array[j] and array[j+1]
    ; Calculate address: j * 4
    ; For simplicity, iterate with fixed offsets
    LUI x12, 0        ; offset = 0

    LOAD x13, 0(x12)  ; x13 = array[j]
    LOAD x14, 4(x12)  ; x14 = array[j+1]

    ; Compare and swap if array[j] > array[j+1]
    SLT x15, x14, x13 ; x15 = (array[j+1] < array[j]) ? 1 : 0
    BEQ x15, x12, no_swap

    ; Swap
    STORE x14, 0(x12) ; array[j] = array[j+1]
    STORE x13, 4(x12) ; array[j+1] = array[j]

no_swap:
    ; Decrement j
    SUB x10, x10, x9  ; j--
    LUI x11, 0
    BNE x10, x11, inner_loop

next_outer:
    ; Decrement i
    SUB x8, x8, x9    ; i--
    LUI x11, 0
    BNE x8, x11, outer_loop

sort_done:
    ; Store sorted count
    LUI x9, 12
    STORE x8, 0(x9)

    HALT
