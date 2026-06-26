#ifndef X86_DECODE_H
#define X86_DECODE_H

#include "x86_types.h"

/*
 * x86_decode.h - x86 instruction decoder
 *
 * x86 is a CISC (Complex Instruction Set Computer) architecture with
 * variable-length instructions (1-15 bytes). The decoder must handle:
 *
 * 1. Prefixes: REPNZ, REPZ, LOCK, segment override, operand size, address size
 * 2. Opcode: 1-2 bytes identifying the instruction
 * 3. MOD/RM: Modifying register/memory operand specification
 * 4. SIB: Scale-Index-Base for 32-bit addressing
 * 5. Displacement: 0, 1, 2, or 4 bytes
 * 6. Immediate: 1, 2, or 4 bytes
 *
 * Common instruction encodings:
 *   MOV r/m, r   : C0h + reg field (r/m = reg)
 *   MOV r, r/m   : 8Ah/8Bh
 *   ADD r/m, r   : 00h-01h
 *   SUB r/m, r   : 28h-29h
 *   JMP rel16/32 : EBh (short) / E9h (near) / EAh (far)
 *   CALL rel16/32: E8h (near)
 *   RET          : C3h (near) / CBh (far)
 *   PUSH r/m16   : 50h+reg
 *   POP r/m16    : 58h+reg
 *
 * MOD/RM byte layout:
 *   +---+---+---+---+---+---+---+---+
 *   |MOD |REG/OP|    R/M              |
 *   +---+---+---+---+---+---+---+---+
 *    7   6   5   4   3   2   1   0
 *
 * SIB byte layout:
 *   +---+---+---+---+---+---+---+---+
 *   |SCA | IDX  |          BAS         |
 *   +---+---+---+---+---+---+---+---+
 *    7   6   5   4   3   2   1   0
 *
 * The decoding order is:
 *   Prefixes -> Opcode -> MOD/RM -> SIB (if needed) -> Displacement -> Immediate
 */

/* Maximum instruction size in bytes */
#define X86_MAX_INSTR_SIZE 15

/* Read bytes from the instruction stream */
typedef struct {
    const uint8_t *bytes;
    uint32_t       pos;
    uint32_t       length;
} x86_instr_stream_t;

/* Initialize instruction stream */
static inline void x86_instr_init(x86_instr_stream_t *stream,
                                   const uint8_t *bytes, uint32_t length) {
    stream->bytes = bytes;
    stream->pos = 0;
    stream->length = length;
}

/* Read a byte from the stream */
static inline uint8_t x86_instr_read_byte(x86_instr_stream_t *stream) {
    if (stream->pos < stream->length) {
        return stream->bytes[stream->pos++];
    }
    return 0;
}

/* Read a 16-bit word from the stream (little-endian) */
static inline uint16_t x86_instr_read_word(x86_instr_stream_t *stream) {
    uint16_t w = 0;
    w |= x86_instr_read_byte(stream);
    w |= ((uint16_t)x86_instr_read_byte(stream) << 8);
    return w;
}

/* Read a 32-bit dword from the stream (little-endian) */
static inline uint32_t x86_instr_read_dword(x86_instr_stream_t *stream) {
    uint32_t d = 0;
    d |= x86_instr_read_byte(stream);
    d |= ((uint32_t)x86_instr_read_byte(stream) << 8);
    d |= ((uint32_t)x86_instr_read_byte(stream) << 16);
    d |= ((uint32_t)x86_instr_read_byte(stream) << 24);
    return d;
}

/* Get current position in stream */
static inline uint32_t x86_instr_pos(x86_instr_stream_t *stream) {
    return stream->pos;
}

/* Decode one x86 instruction from the instruction stream */
int x86_decode(x86_cpu_t *cpu, x86_instr_stream_t *stream,
               x86_instruction_t *instr);

/* Decode the MOD/RM byte and populate instruction fields */
void x86_decode_modrm(x86_cpu_t *cpu, x86_instruction_t *instr,
                       x86_instr_stream_t *stream, uint8_t modrm);

/* Decode the SIB byte and populate instruction fields */
void x86_decode_sib(x86_cpu_t *cpu, x86_instruction_t *instr,
                     x86_instr_stream_t *stream, uint8_t sib);

/* Print decoded instruction for debugging */
void x86_instr_dump(x86_instruction_t *instr);

#endif /* X86_DECODE_H */
