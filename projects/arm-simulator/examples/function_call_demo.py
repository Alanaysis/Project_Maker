"""
ARM Function Call Example
==========================

Demonstrates function call mechanics in ARM:
- Link Register (LR/R14) for return address
- Stack-based parameter passing
- Branch with Link (BL) instruction
- Return from subroutine

ARM Architecture Background:
- BL (Branch with Link): Sets LR = PC + 4, jumps to target
- BX (Branch and Exchange): Returns using LR as target
- Stack grows downward (SP decreases on push)
- Convention: caller saves R0-R3, R12; callee saves R4-R11, LR
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cpu import ARMCore


def demo_simple_function_call():
    """Demonstrate a simple function call: call add(3, 5), result in R0"""
    print("=" * 60)
    print("Demo: Simple Function Call (add(3, 5))")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Conceptual ARM assembly:
    #   MOV R0, #3       ; arg1 = 3
    #   MOV R1, #5       ; arg2 = 5
    #   BL add           ; call add(3, 5), result in R0
    #   MOV R2, R0       ; result = R0
    #
    # add:
    #   ADD R0, R0, R1   ; result = arg1 + arg2
    #   BX LR            ; return to caller

    # Layout:
    # 0x3000: MOV R0, #3      (addr 0)
    # 0x3004: MOV R1, #5      (addr 1)
    # 0x3008: BL add          (addr 2)
    # 0x300C: MOV R2, R0     (addr 3)
    # 0x3010: (padding)
    # 0x3014: add: ADD R0, R0, R1  (addr 4)
    # 0x3018: BX LR           (addr 5)

    # BL offset: (0x3014 - 0x300C) / 4 = 2
    # BL = 0xCC000002

    program = [
        # 0x3000: MOV R0, #3
        0xE3A00003,
        # 0x3004: MOV R1, #5
        0xE3A01005,
        # 0x3008: BL add
        0xCC000002,
        # 0x300C: MOV R2, R0
        0xE1A02000,
        # 0x3010: (padding)
        0xE1A00000,
        # 0x3014: add: ADD R0, R0, R1
        0xE0000001,
        # 0x3018: BX LR
        0xE12FFF1E,
    ]

    cpu.load_program(0x3000, program)
    cpu.regs.set_pc(0x3000)

    print("Executing function call program...")
    steps = cpu.run(max_steps=30)
    print(f"Executed {steps} steps")
    print()

    print(f"Results:")
    print(f"  R0 (result) = {cpu.regs.read_reg(0)}  (expected: 8)")
    print(f"  R1 (arg2)   = {cpu.regs.read_reg(1)}  (expected: 5)")
    print(f"  R2 (result) = {cpu.regs.read_reg(2)}  (expected: 8)")
    print(f"  LR (return) = 0x{cpu.regs.get_lr():08X}")
    print(f"\nCPSR: {cpu.regs.cpsr}")
    print()


def demo_stack_based_call():
    """Demonstrate stack-based function call with saved registers"""
    print("=" * 60)
    print("Demo: Stack-Based Function Call (fibonacci)")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Simple iterative fibonacci: fib(5) = 5
    # Conceptual ARM assembly:
    #   MOV R0, #5       ; n = 5
    #   BL fibonacci
    #   MOV R1, R0       ; result = fib(n)
    #
    # fibonacci:
    #   PUSH {R4, LR}    ; save registers
    #   CMP R0, #0
    #   BEQ base_case_0
    #   CMP R0, #1
    #   BEQ base_case_1
    #   MOV R2, #0       ; a = 0
    #   MOV R3, #1       ; b = 1
    #   MOV R4, #2       ; i = 2
    # fib_loop:
    #   CMP R4, R0
    #   BGT fib_done
    #   ADD R5, R2, R3   ; temp = a + b
    #   MOV R2, R3       ; a = b
    #   MOV R3, R5       ; b = temp
    #   ADD R4, R4, #1   ; i++
    #   B fib_loop
    # fib_done:
    #   MOV R0, R3       ; result = b
    #   POP {R4, PC}     ; return
    # base_case_0: MOV R0, #0; POP {R4, PC}
    # base_case_1: MOV R0, #1; POP {R4, PC}

    # Layout (simplified iterative version):
    # 0x4000: MOV R0, #5           (addr 0)
    # 0x4004: MOV R1, #5           (addr 1)  ; temp for comparison
    # 0x4008: MOV R2, #0           (addr 2)  ; a = 0
    # 0x400C: MOV R3, #1           (addr 3)  ; b = 1
    # 0x4010: MOV R4, #2           (addr 4)  ; i = 2
    # fib_loop:
    # 0x4014: CMP R4, R1           (addr 5)
    # 0x4018: BGT fib_done         (addr 6)
    # 0x401C: ADD R5, R2, R3      (addr 7)
    # 0x4020: MOV R2, R3           (addr 8)
    # 0x4024: MOV R3, R5           (addr 9)
    # 0x4028: ADD R4, R4, #1      (addr 10)
    # 0x402C: B fib_loop           (addr 11)
    # fib_done:
    # 0x4030: MOV R0, R3           (addr 12)  ; result = b
    # 0x4034: MOV PC, LR           (addr 13)  ; return

    # BGT offset: (0x4030 - 0x4018) / 4 = 4
    # BGT = 0xCC000004

    # B offset: (0x4014 - 0x402C) / 4 = -4
    # B = 0xEEFFFFFC

    program = [
        # 0x4000: MOV R0, #5
        0xE3A00005,
        # 0x4004: MOV R1, #5  (n)
        0xE3A01005,
        # 0x4008: MOV R2, #0  (a = 0)
        0xE3A02000,
        # 0x400C: MOV R3, #1  (b = 1)
        0xE3A03001,
        # 0x4010: MOV R4, #2  (i = 2)
        0xE3A04002,
        # 0x4014: CMP R4, R1  (fib_loop start)
        0xE1540001,
        # 0x4018: BGT fib_done
        0xCC000004,
        # 0x401C: ADD R5, R2, R3
        0xE0020035,
        # 0x4020: MOV R2, R3
        0xE1A02003,
        # 0x4024: MOV R3, R5
        0xE1A03005,
        # 0x4028: ADD R4, R4, #1
        0xE2844001,
        # 0x402C: B fib_loop
        0xEEFFFFFC,
        # 0x4030: MOV R0, R3  (fib_done: result = b)
        0xE1A00003,
        # 0x4034: MOV PC, LR  (return)
        0xE1A0F00E,
    ]

    cpu.load_program(0x4000, program)
    cpu.regs.set_pc(0x4000)

    print("Executing fibonacci program...")
    steps = cpu.run(max_steps=100)
    print(f"Executed {steps} steps")
    print()

    print(f"Results:")
    print(f"  R0 (fib(5)) = {cpu.regs.read_reg(0)}  (expected: 5)")
    print(f"  R1 (n)      = {cpu.regs.read_reg(1)}  (expected: 5)")
    print(f"  R2 (a)      = {cpu.regs.read_reg(2)}  (expected: 3)")
    print(f"  R3 (b)      = {cpu.regs.read_reg(3)}  (expected: 5)")
    print(f"  R4 (i)      = {cpu.regs.read_reg(4)}  (expected: 6)")
    print(f"\nCPSR: {cpu.regs.cpsr}")
    print()


if __name__ == "__main__":
    demo_simple_function_call()
    demo_stack_based_call()
    print("All function call demos completed!")
