"""
ARM Execution Trace Demo
==========================

Demonstrates the execution trace feature of the ARM simulator.
Shows step-by-step instruction execution with register state.

This example loads a small program and displays detailed execution traces.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cpu import ARMCore


def demo_trace():
    """Run a small program and display execution trace"""
    print("=" * 60)
    print("Demo: Execution Trace")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Small program: compute sum = 1 + 2 + 3 + 4 + 5
    # Using a loop with known addresses
    # Program layout:
    # 0x5000: MOV R0, #0       ; sum = 0
    # 0x5004: MOV R1, #1       ; i = 1
    # 0x5008: CMP R1, #6       ; compare i with 6
    # 0x500C: BGT done
    # 0x5010: ADD R0, R0, R1   ; sum += i
    # 0x5014: ADD R1, R1, #1   ; i++
    # 0x5018: B loop
    # 0x501C: done: MOV R2, R0 ; result = sum

    program = [
        # 0x5000: MOV R0, #0
        0xE3A00000,
        # 0x5004: MOV R1, #1
        0xE3A01001,
        # 0x5008: CMP R1, #6
        0xE3510006,
        # 0x500C: BGT done
        # offset = (0x501C - 0x500C) / 4 = 3
        0xCC000003,
        # 0x5010: ADD R0, R0, R1
        0xE0000001,
        # 0x5014: ADD R1, R1, #1
        0xE2811001,
        # 0x5018: B loop
        # offset = (0x5008 - 0x5018) / 4 = -4
        0xEEFFFFFC,
        # 0x501C: MOV R2, R0
        0xE1A02000,
    ]

    cpu.load_program(0x5000, program)
    cpu.regs.set_pc(0x5000)

    print("Running program with trace enabled...")
    print()

    # Run step by step to show trace
    cpu.running = True
    step = 0
    while cpu.running and step < 50:
        cpu.step()
        step += 1

    # Display trace
    print(f"Execution Trace ({step} steps):")
    print("-" * 60)
    print(f"{'Step':>5} | {'PC':>10} | {'Instruction':>12} | {'Condition':>10}")
    print("-" * 60)

    for entry in cpu.get_trace():
        mnemonic = entry['instruction']
        cond = entry['condition']
        pc = entry['pc']
        print(f"{entry['step']:>5} | 0x{pc:08X} | {mnemonic:>12} | {cond:>10}")

    print("-" * 60)
    print()

    # Display final state
    print("Final CPU State:")
    print("-" * 60)
    regs = cpu.regs
    for i in range(8):
        val = regs.read_reg(i)
        print(f"  R{i:2d}: 0x{val:08X} ({val:10d})")
    print(f"\n  SP:  0x{regs.get_sp():08X}")
    print(f"  LR:  0x{regs.get_lr():08X}")
    print(f"  PC:  0x{regs.get_pc():08X}")
    print(f"\n  CPSR: {regs.cpsr}")
    print("-" * 60)
    print()

    # Verify result
    result = regs.read_reg(2)
    expected = 15  # 1 + 2 + 3 + 4 + 5 = 15
    status = "PASS" if result == expected else "FAIL"
    print(f"Verification: sum = {result}, expected = {expected} -> {status}")
    print()


def demo_thumb_trace():
    """Demonstrate Thumb mode execution with trace"""
    print("=" * 60)
    print("Demo: Thumb Mode Execution Trace")
    print("=" * 60)
    print()

    cpu = ARMCore()
    cpu.enable_trace()

    # Set initial state to Thumb mode
    cpu.regs.cpsr.value |= cpu.regs.cpsr.T_FLAG

    # Thumb program: simple computation
    # MOV R0, #10
    # MOV R1, #20
    # ADD R2, R0, R1
    # CMP R2, #25
    # MOV R3, #1  (if greater)
    # MOV R3, #0  (if not greater)

    # Thumb encodings (16-bit):
    # MOV Rd, #imm8: 00100 imm8 Rd (for small immediates)
    # ADD Rd, Rn, Rm: 000 0100 Rn Rm Rd
    # ADD Rd, Rn, #imm3: 001 0100 Rn Rd imm3
    # CMP Rn, #imm3: 001 00111 Rn imm3

    thumb_program = [
        # MOV R0, #10  (0x200A)
        0x200A,
        # MOV R1, #20  (0x2014)
        0x2014,
        # ADD R2, R0, R1  (0x1892)
        0x1892,
        # CMP R2, #25  (0xB283, CMP R3, #imm)
        # Actually CMP with immediate in Thumb: 0xBxxx
        # Let me use a simpler approach
        0x2819,  # CMP R0, #25
        # BGT (conditional branch)
        # In Thumb, conditional branches use 0xBxxx encoding
        0xBF00,  # NOP (placeholder)
        # ADD R3, R0, R1  (0x189B)
        0x189B,
        # BKPT (breakpoint to stop)
        0xBE00,
    ]

    cpu.load_thumb_program(0x6000, thumb_program)
    cpu.regs.set_pc(0x6000)

    print("Running Thumb program with trace enabled...")
    print()

    # Run step by step
    cpu.running = True
    step = 0
    while cpu.running and step < 20:
        cpu.step()
        step += 1

    # Display trace
    print(f"Thumb Execution Trace ({step} steps):")
    print("-" * 60)
    print(f"{'Step':>5} | {'PC':>10} | {'Instruction':>12} | {'Mode':>6}")
    print("-" * 60)

    for entry in cpu.get_trace():
        mnemonic = entry['instruction']
        pc = entry['pc']
        mode = "Thumb" if cpu.regs.cpsr.t else "ARM"
        print(f"{entry['step']:>5} | 0x{pc:08X} | {mnemonic:>12} | {mode:>6}")

    print("-" * 60)
    print()

    # Display final state
    print("Final CPU State:")
    print("-" * 60)
    regs = cpu.regs
    for i in range(4):
        val = regs.read_reg(i)
        print(f"  R{i:2d}: 0x{val:08X} ({val:10d})")
    print(f"\n  CPSR: {regs.cpsr}")
    print("-" * 60)
    print()


if __name__ == "__main__":
    demo_trace()
    demo_thumb_trace()
    print("All trace demos completed!")
