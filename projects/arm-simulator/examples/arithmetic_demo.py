"""
ARM Arithmetic Operations Demo
================================

Demonstrates basic arithmetic operations in the ARM simulator:
- ADD, SUB, MOV
- AND, ORR, EOR, BIC
- CMP with conditional execution
- Shift operations (LSL, LSR, ASR)

This example shows how ARM data processing instructions work.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cpu import ARMCore


def demo_basic_arithmetic():
    """Demonstrate basic arithmetic: ADD, SUB, MOV"""
    print("=" * 60)
    print("Demo 1: Basic Arithmetic Operations")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Program:
    #   MOV R0, #10      ; R0 = 10
    #   MOV R1, #20      ; R1 = 20
    #   ADD R2, R0, R1   ; R2 = R0 + R1 = 30
    #   SUB R3, R1, R0   ; R3 = R1 - R0 = 10
    #   MOV R4, #5       ; R4 = 5
    #   ADD R5, R4, R4   ; R5 = R4 + R4 = 10

    # ARM encoding (32-bit instructions):
    # MOV Rd, #imm: 1010 0 0 0 0 Rn Rd imm12
    # ADD Rd, Rn, Rm: 0000 0 0 0 0 Rn Rd Rm shift
    # SUB Rd, Rn, Rm: 0000 0 0 1 1 Rn Rd Rm shift

    program = [
        # MOV R0, #10  (AL)
        0xA000000A,
        # MOV R1, #20  (AL)
        0xA0010014,
        # ADD R2, R0, R1  (AL)
        0xE0000001,
        # SUB R3, R1, R0  (AL)
        0xE0410000,
        # MOV R4, #5  (AL)
        0xA0040005,
        # ADD R5, R4, R4  (AL)
        0xE0040004,
    ]

    cpu.load_program(0x1000, program)
    cpu.regs.set_pc(0x1000)

    print("Executing program...")
    cpu.run(max_steps=20)

    # Print results
    regs = cpu.regs
    print(f"\nResults:")
    print(f"  R0 = {regs.read_reg(0)}    (expected: 10)")
    print(f"  R1 = {regs.read_reg(1)}    (expected: 20)")
    print(f"  R2 = {regs.read_reg(2)}    (expected: 30)")
    print(f"  R3 = {regs.read_reg(3)}    (expected: 10)")
    print(f"  R4 = {regs.read_reg(4)}    (expected: 5)")
    print(f"  R5 = {regs.read_reg(5)}    (expected: 10)")
    print(f"\nCPSR: {regs.cpsr}")
    print()


def demo_logical_operations():
    """Demonstrate logical operations: AND, ORR, EOR, BIC"""
    print("=" * 60)
    print("Demo 2: Logical Operations")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Program:
    #   MOV R0, #0xFF      ; R0 = 0xFF (255)
    #   MOV R1, #0xF0      ; R1 = 0xF0 (240)
    #   AND R2, R0, R1     ; R2 = R0 & R1 = 0xF0
    #   ORR R3, R0, R1     ; R3 = R0 | R1 = 0xFF
    #   EOR R4, R0, R1     ; R4 = R0 ^ R1 = 0x0F
    #   BIC R5, R0, R1     ; R5 = R0 & ~R1 = 0x0F

    program = [
        # MOV R0, #0xFF
        0xA00000FF,
        # MOV R1, #0xF0
        0xA00100F0,
        # AND R2, R0, R1
        0xE0000010,
        # ORR R3, R0, R1
        0xE1800010,
        # EOR R4, R0, R1
        0xE0200010,
        # BIC R5, R0, R1
        0xE1C00010,
    ]

    cpu.load_program(0x1000, program)
    cpu.regs.set_pc(0x1000)

    print("Executing program...")
    cpu.run(max_steps=20)

    print(f"\nResults:")
    print(f"  R0 = 0x{cpu.regs.read_reg(0):08X}  (expected: 0x000000FF)")
    print(f"  R1 = 0x{cpu.regs.read_reg(1):08X}  (expected: 0x000000F0)")
    print(f"  R2 = 0x{cpu.regs.read_reg(2):08X}  (expected: 0x000000F0)  [AND]")
    print(f"  R3 = 0x{cpu.regs.read_reg(3):08X}  (expected: 0x000000FF)  [ORR]")
    print(f"  R4 = 0x{cpu.regs.read_reg(4):08X}  (expected: 0x0000000F)  [EOR]")
    print(f"  R5 = 0x{cpu.regs.read_reg(5):08X}  (expected: 0x0000000F)  [BIC]")
    print(f"\nCPSR: {cpu.regs.cpsr}")
    print()


def demo_shift_operations():
    """Demonstrate shift operations: LSL, LSR, ASR"""
    print("=" * 60)
    print("Demo 3: Shift Operations")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Program:
    #   MOV R0, #1         ; R0 = 1
    #   ADD R1, R0, R0, LSL #4  ; R1 = R0 + (R0 << 4) = 1 + 16 = 17
    #   MOV R2, #256       ; R2 = 256
    #   LSR R3, R2, #4     ; R3 = R2 >> 4 = 16
    #   MOV R4, #0x80000000  ; R4 = -2147483648 (signed)
    #   ASR R5, R4, #1     ; R5 = R4 >> 1 (arithmetic) = -1073741824

    program = [
        # MOV R0, #1
        0xA0000001,
        # ADD R1, R0, R0, LSL #4
        0xE0010000 | (4 << 7) | (0 << 5),
        # MOV R2, #256
        0xA0020100,
        # LSR R3, R2, #4
        0xE0823003 | (4 << 7),
        # MOV R4, #0x80000000
        0xE3A04000,  # This won't work directly, use MOVW-like
        # Actually, 0x80000000 is not a valid ARM immediate
        # Let's use a different approach
        0xE3A04080,  # MOV R4, #128
        # ASR R5, R4, #1
        0xE0C42005 | (1 << 5),
    ]

    # Fix: use a valid immediate for R4
    program[5] = 0xE3A04080  # MOV R4, #128

    cpu.load_program(0x1000, program)
    cpu.regs.set_pc(0x1000)

    print("Executing program...")
    cpu.run(max_steps=20)

    r0 = cpu.regs.read_reg(0)
    r1 = cpu.regs.read_reg(1)
    r2 = cpu.regs.read_reg(2)
    r3 = cpu.regs.read_reg(3)
    r4 = cpu.regs.read_reg(4)
    r5 = cpu.regs.read_reg(5)

    print(f"\nResults:")
    print(f"  R0 = {r0}          (expected: 1)")
    print(f"  R1 = {r1}          (expected: 17)  [R0 + (R0 << 4)]")
    print(f"  R2 = {r2}          (expected: 256)")
    print(f"  R3 = {r3}          (expected: 16)  [R2 >> 4]")
    print(f"  R4 = {r4}          (expected: 128)")
    print(f"  R5 = {r5}          (expected: 64)  [R4 >> 1 arithmetic]")
    print(f"\nCPSR: {cpu.regs.cpsr}")
    print()


if __name__ == "__main__":
    demo_basic_arithmetic()
    demo_logical_operations()
    demo_shift_operations()
    print("All arithmetic demos completed!")
