// CPU Architecture Types
// Defines all instruction types, register IDs, and data structures
// for the simple CPU simulator.

#ifndef CPU_TYPES_H
#define CPU_TYPES_H

#include <cstdint>
#include <string>
#include <vector>
#include <functional>

// Maximum memory size (1MB for learning purposes)
constexpr int MAX_MEMORY_SIZE = 1024 * 1024;

// Number of general purpose registers
constexpr int NUM_REGISTERS = 16;

// Maximum program counter value
constexpr int MAX_PC = MAX_MEMORY_SIZE;

// Instruction encoding format (28-bit instructions)
// | opcode(4) | rd(4) | rs1(4) | operand/imm(16) |
//
// Operand interpretation by opcode:
//   LOAD/STORE: 16-bit signed offset
//   LUI:         16-bit immediate value
//   others:      rs2 register ID (lower 4 bits)
//   JUMP:        target offset (when rs1=0)
//   HALT:        no operand needed

// Opcode definitions (4 bits, max 16 opcodes)
enum class Opcode : uint8_t {
    NOP     = 0x0,  // No operation
    LOAD    = 0x1,  // rd = mem[rs1 + imm16]
    STORE   = 0x2,  // mem[rs1 + imm16] = rd
    LUI     = 0x3,  // rd = imm16 << 12
    ADD     = 0x4,  // rd = rs1 + rs2
    SUB     = 0x5,  // rd = rs1 - rs2
    MUL     = 0x6,  // rd = rs1 * rs2
    DIV     = 0x7,  // rd = rs1 / rs2
    AND     = 0x8,  // rd = rs1 & rs2
    OR      = 0x9,  // rd = rs1 | rs2
    XOR     = 0xA,  // rd = rs1 ^ rs2
    NOT     = 0xB,  // rd = ~rs1
    SLL     = 0xC,  // rd = rs1 << rs2
    SRL     = 0xD,  // rd = rs1 >> rs2
    JUMP    = 0xE,  // PC = rs1 + imm16 (or PC += imm16 if rs1=0)
    JAL     = 0xF,  // rd = PC+4, PC = rs1 + imm16
};

// Register IDs (4 bits, 0-15)
enum class RegID : uint8_t {
    ZERO = 0,   // Hardwired zero
    RA   = 1,   // Return address
    SP   = 2,   // Stack pointer
    T0   = 3,   // Temporary
    T1   = 4,
    T2   = 5,
    S0   = 6,   // Saved register
    S1   = 7,
    A0   = 8,   // Function argument/return value
    A1   = 9,
    A2   = 10,
    A3   = 11,
    A4   = 12,
    A5   = 13,
    A6   = 14,
    A7   = 15,
};

// ALU operation codes
enum class ALUOp : uint8_t {
    ADD, SUB, MUL, DIV, AND, OR, XOR, NOT, SLL, SRL, SLT, MOVE,
};

// CPU execution state
enum class CPUState {
    RUNNING,
    HALTED,
    ERROR
};

// Execution trace entry for debugging/visualization
struct TraceEntry {
    uint32_t pc;
    uint32_t ir;
    uint32_t op;
    uint32_t rd, rs1, rs2;
    uint32_t result;
    uint32_t mem_addr;
    uint32_t mem_data;
    uint32_t reg[NUM_REGISTERS];
    bool branch_taken;
    std::string step;
};

// CPU statistics
struct CPUStats {
    uint64_t cycles = 0;
    uint64_t instructions_executed = 0;
    uint64_t load_instructions = 0;
    uint64_t store_instructions = 0;
    uint64_t branch_instructions = 0;
    uint64_t branches_taken = 0;
    uint32_t min_pc = MAX_MEMORY_SIZE;
    uint32_t max_pc = 0;
    std::string last_error;
};

#endif // CPU_TYPES_H
