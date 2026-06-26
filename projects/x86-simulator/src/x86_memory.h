#ifndef X86_MEMORY_H
#define X86_MEMORY_H

#include "x86_types.h"

/*
 * x86_memory.h - Memory management and address translation
 *
 * x86 Address Translation:
 *
 * Real Mode (16-bit):
 *   Physical Address = (Segment << 4) + Offset
 *   Example: DS=0x1000, offset=0x2000 -> physical = 0x12000
 *   Maximum: 0xFFFFF (1 MB)
 *
 * Protected Mode (32-bit):
 *   1. Linear Address = Base + Offset (from segment descriptor)
 *   2. Physical Address = Linear Address (unless paging enabled in CR0)
 *
 * Segment descriptors in GDT contain:
 *   - Base address (32 bits)
 *   - Limit (20 bits, with granularity)
 *   - Type (code/data, read/write, executable, etc.)
 *   - DPL (Descriptor Privilege Level: 0-3)
 *   - Present flag
 *
 * Paging (not fully implemented, but structure is here):
 *   CR0.PE = 0 -> Real mode
 *   CR0.PE = 1 -> Protected mode
 *   CR0.PG = 1 -> Paging enabled (linear -> physical translation)
 */

/* Initialize memory */
void x86_mem_init(x86_memory_t *mem);

/* Read/write with address bounds checking */
uint8_t  x86_mem_read_byte(x86_memory_t *mem, uint32_t address);
uint16_t x86_mem_read_word(x86_memory_t *mem, uint32_t address);
uint32_t x86_mem_read_dword(x86_memory_t *mem, uint32_t address);

void x86_mem_write_byte(x86_memory_t *mem, uint32_t address, uint8_t value);
void x86_mem_write_word(x86_memory_t *mem, uint32_t address, uint16_t value);
void x86_mem_write_dword(x86_memory_t *mem, uint32_t address, uint32_t value);

/* Read stack (uses SS segment in real mode, or default stack segment) */
uint16_t x86_mem_read_word_seg(x86_memory_t *mem, x86_cpu_t *cpu,
                                  uint16_t segment, uint16_t offset);
uint32_t x86_mem_read_dword_seg(x86_memory_t *cpu, x86_cpu_t *cpu,
                                   uint16_t segment, uint32_t offset);

void x86_mem_write_word_seg(x86_memory_t *mem, x86_cpu_t *cpu,
                              uint16_t segment, uint16_t offset, uint16_t value);
void x86_mem_write_dword_seg(x86_memory_t *mem, x86_cpu_t *cpu,
                               uint16_t segment, uint32_t offset, uint32_t value);

/* Stack operations (uses SS:ESP) */
uint32_t x86_stack_push(x86_cpu_t *cpu, x86_memory_t *mem, uint32_t value);
uint32_t x86_stack_pop(x86_cpu_t *cpu, x86_memory_t *mem);

/* Address translation: segment + offset -> physical/linear address */
uint32_t x86_translate_address(x86_cpu_t *cpu, uint16_t segment, uint32_t offset);

/* Get effective linear address from MOD/RM/SIB decoding */
uint32_t x86_get_linear_address(x86_cpu_t *cpu, x86_instruction_t *instr,
                                 uint8_t modrm, uint8_t sib, uint8_t addr_size);

/* Memory dump for debugging */
void x86_mem_dump(x86_memory_t *mem, uint32_t start, uint32_t length);

/* Load binary data into memory */
int x86_mem_load_binary(x86_memory_t *mem, uint32_t addr,
                         const uint8_t *data, uint32_t length);

#endif /* X86_MEMORY_H */
