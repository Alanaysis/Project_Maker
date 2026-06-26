"""
ARM Loop Example
=================

Demonstrates loop construction in ARM assembly:
- Using CMP for comparison
- Using B for conditional branching
- Counter-based loops
- Sum of numbers calculation

This example shows how to implement loops in ARM, which lack
a dedicated LOOP instruction (unlike x86's LOOP).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cpu import ARMCore


def demo_counter_loop():
    """Demonstrate a counter-based loop: sum = 0; for(i=1; i<=10; i++) sum += i"""
    print("=" * 60)
    print("Demo: Counter-Based Loop (Sum 1 to 10)")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # ARM assembly (conceptual):
    #   MOV R0, #0       ; sum = 0 (accumulator)
    #   MOV R1, #1       ; i = 1 (counter)
    # loop:
    #   CMP R1, #10      ; compare i with 10
    #   BGT done         ; if i > 10, exit loop
    #   ADD R0, R0, R1   ; sum += i
    #   ADD R1, R1, #1   ; i++
    #   B loop           ; jump back to loop
    # done:
    #   MOV R2, R0       ; result = sum

    # ARM encoding:
    # MOV Rd, #imm: 1010 0 0 0 0 Rn Rd imm12
    # CMP Rn, #imm: 1111 0 0 0 0 Rn imm12 (using data processing with CMP)
    # B condition: 010 imm24
    # ADD Rd, Rn, Rm: 0000 0 0 0 0 Rn Rd Rm (with shift)

    # Actually, let me use proper ARM encodings:
    # MOV R0, #0: 0xE3A00000
    # MOV R1, #1: 0xE3A01001
    # CMP R1, #10: 0xE351000A
    # BGT label: 0x1A000000 + offset
    # ADD R0, R0, R1: 0xE0000001
    # ADD R1, R1, #1: 0xE2811001
    # B: 0x1A000000 + offset
    # MOV R2, R0: 0xE1A02000

    # For branches, we need to calculate offsets
    # Branch target addresses (in words from PC):
    # PC at branch = target_addr / 4 - current_pc / 4
    # Branch offset = (target - pc) / 4

    # Layout:
    # 0x1000: MOV R0, #0        (addr 0)
    # 0x1004: MOV R1, #1        (addr 1)
    # 0x1008: CMP R1, #10       (addr 2)  <- loop start
    # 0x100C: BGT done          (addr 3)
    # 0x1010: ADD R0, R0, R1   (addr 4)
    # 0x1014: ADD R1, R1, #1   (addr 5)
    # 0x1018: B loop            (addr 6)  <- back to addr 2
    # 0x101C: MOV R2, R0       (addr 7)  <- done

    # BGT offset: target is at 0x101C (done), PC at 0x1010
    # offset = (0x101C - 0x1010) / 4 = 2
    # BGT encoding: cond=0xC (GT), imm24=2
    # BGT = 0xCC000002

    # B offset: target is at 0x1008 (loop), PC at 0x101C
    # offset = (0x1008 - 0x101C) / 4 = -4
    # B encoding: cond=0xE (AL), imm24=-4
    # B = 0xEEFFFFFC

    program = [
        # 0x1000: MOV R0, #0  (sum = 0)
        0xE3A00000,
        # 0x1004: MOV R1, #1  (i = 1)
        0xE3A01001,
        # 0x1008: CMP R1, #10  (loop start)
        0xE351000A,
        # 0x100C: BGT done  (if i > 10, jump to done)
        # offset = 2 (words)
        0xCC000002,
        # 0x1010: ADD R0, R0, R1  (sum += i)
        0xE0000001,
        # 0x1014: ADD R1, R1, #1  (i++)
        0xE2811001,
        # 0x1018: B loop  (jump back to 0x1008)
        # offset = -4 (words)
        0xEEFFFFFC,
        # 0x101C: MOV R2, R0  (result = sum)
        0xE1A02000,
    ]

    cpu.load_program(0x1000, program)
    cpu.regs.set_pc(0x1000)

    print("Executing loop program...")
    steps = cpu.run(max_steps=100)
    print(f"Executed {steps} steps")
    print()

    print(f"Results:")
    print(f"  R0 (sum) = {cpu.regs.read_reg(0)}  (expected: 55)")
    print(f"  R1 (i)   = {cpu.regs.read_reg(1)}  (expected: 11)")
    print(f"  R2 (result) = {cpu.regs.read_reg(2)}  (expected: 55)")
    print(f"\nCPSR: {cpu.regs.cpsr}")
    print()


def demo_while_loop():
    """Demonstrate a while loop: find first power of 2 greater than 100"""
    print("=" * 60)
    print("Demo: While Loop (Find Power of 2 > 100)")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Conceptual ARM assembly:
    #   MOV R0, #1       ; power = 1
    # while:
    #   CMP R0, #100
    #   BGE done
    #   ADD R0, R0, R0  ; power *= 2 (power << 1)
    #   B while
    # done:
    #   MOV R1, R0      ; result = power

    # Layout:
    # 0x2000: MOV R0, #1      (addr 0)
    # 0x2004: CMP R0, #100    (addr 1)  <- while
    # 0x2008: BGE done        (addr 2)
    # 0x200C: ADD R0, R0, R0 (addr 3)
    # 0x2010: B while         (addr 4)
    # 0x2014: MOV R1, R0     (addr 5)  <- done

    # BGE offset: (0x2014 - 0x200C) / 4 = 2
    # BGE = 0xD0000002

    # B offset: (0x2004 - 0x2010) / 4 = -2
    # B = 0xEEFFFFFE

    program = [
        # 0x2000: MOV R0, #1
        0xE3A00001,
        # 0x2004: CMP R0, #100
        0xE3500064,
        # 0x2008: BGE done
        0xD0000002,
        # 0x200C: ADD R0, R0, R0
        0xE0000000,
        # 0x2010: B while
        0xEEFFFEFE,
        # 0x2014: MOV R1, R0
        0xE1A01000,
    ]

    cpu.load_program(0x2000, program)
    cpu.regs.set_pc(0x2000)

    print("Executing while loop program...")
    steps = cpu.run(max_steps=50)
    print(f"Executed {steps} steps")
    print()

    print(f"Results:")
    print(f"  R0 (power) = {cpu.regs.read_reg(0)}  (expected: 128)")
    print(f"  R1 (result) = {cpu.regs.read_reg(1)}  (expected: 128)")
    print(f"\nCPSR: {cpu.regs.cpsr}")
    print()


if __name__ == "__main__":
    demo_counter_loop()
    demo_while_loop()
    print("All loop demos completed!")
