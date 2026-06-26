#ifndef X86_EXECUTE_H
#define X86_EXECUTE_H

#include "x86_types.h"
#include "x86_cpu.h"
#include "x86_memory.h"
#include "x86_decode.h"

/*
 * x86_execute.h - Instruction execution interface
 *
 * Declares the main execution dispatch function that routes
 * decoded instructions to their appropriate handlers.
 */

/* Execute a single decoded instruction */
int x86_execute_instruction(x86_cpu_t *cpu, x86_memory_t *mem,
                            x86_instruction_t *instr);

#endif /* X86_EXECUTE_H */
