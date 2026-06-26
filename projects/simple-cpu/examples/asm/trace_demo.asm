; Step-by-step execution trace for addition program
; 逐步执行追踪演示

; CPU Pipeline Stages:
; 1. FETCH (取指): PC -> Memory -> IR
; 2. DECODE (译码): IR -> Decoder -> Control signals
; 3. EXECUTE (执行): ALU performs computation
; 4. MEMORY (访存): Load/Store access RAM
; 5. WRITEBACK (写回): Result -> Register file

    LUI x1, 10        ; Load 10 into x1
    LUI x2, 20        ; Load 20 into x2
    ADD x3, x1, x2    ; x3 = x1 + x2
    LUI x4, 0
    STORE x3, 0(x4)   ; Store result to memory[0]
    HALT              ; Stop
