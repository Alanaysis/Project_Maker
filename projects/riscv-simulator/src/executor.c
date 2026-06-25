#include "executor.h"
#include "decoder.h"
#include <stdio.h>

/* ============================================================
 * 指令执行器实现
 * ============================================================ */

/* R-type ALU 指令 */
SimError execute_r_type(CPU* cpu, const DecodedInsn* insn) {
    u32 rs1_val = cpu_read_reg(cpu, insn->rs1);
    u32 rs2_val = cpu_read_reg(cpu, insn->rs2);
    u32 result = 0;

    /* 组合 funct7 和 funct3 为完整功能码 */
    u32 func = ((u32)insn->funct7 << 3) | (insn->funct3 & 0x7);

    switch (func) {
        case ALU_ADD:  result = rs1_val + rs2_val; break;
        case ALU_SUB:  result = rs1_val - rs2_val; break;
        case ALU_SLL:  result = rs1_val << (rs2_val & 0x1F); break;
        case ALU_SLT:  result = ((i32)rs1_val < (i32)rs2_val) ? 1 : 0; break;
        case ALU_SLTU: result = (rs1_val < rs2_val) ? 1 : 0; break;
        case ALU_XOR:  result = rs1_val ^ rs2_val; break;
        case ALU_SRL:  result = rs1_val >> (rs2_val & 0x1F); break;
        case ALU_SRA:  result = (u32)(((i32)rs1_val) >> (rs2_val & 0x1F)); break;
        case ALU_OR:   result = rs1_val | rs2_val; break;
        case ALU_AND:  result = rs1_val & rs2_val; break;
        default:
            fprintf(stderr, "Unknown R-type func: 0x%03X\n", func);
            return ERR_INVALID_INSN;
    }

    cpu_write_reg(cpu, insn->rd, result);
    return ERR_OK;
}

/* I-type ALU 指令 */
SimError execute_i_type(CPU* cpu, const DecodedInsn* insn) {
    u32 rs1_val = cpu_read_reg(cpu, insn->rs1);
    u32 imm = (u32)insn->imm;  /* 已符号扩展 */
    u32 result = 0;

    switch (insn->funct3) {
        case 0x0: result = rs1_val + imm; break;                         /* ADDI */
        case 0x1: result = rs1_val << (imm & 0x1F); break;              /* SLLI */
        case 0x2: result = ((i32)rs1_val < (i32)imm) ? 1 : 0; break;   /* SLTI */
        case 0x3: result = (rs1_val < imm) ? 1 : 0; break;             /* SLTIU */
        case 0x4: result = rs1_val ^ imm; break;                        /* XORI */
        case 0x5:
            if (insn->funct7 & 0x20) {
                result = (u32)(((i32)rs1_val) >> (imm & 0x1F));         /* SRAI */
            } else {
                result = rs1_val >> (imm & 0x1F);                       /* SRLI */
            }
            break;
        case 0x6: result = rs1_val | imm; break;                        /* ORI */
        case 0x7: result = rs1_val & imm; break;                        /* ANDI */
        default:
            fprintf(stderr, "Unknown I-type funct3: 0x%X\n", insn->funct3);
            return ERR_INVALID_INSN;
    }

    cpu_write_reg(cpu, insn->rd, result);
    return ERR_OK;
}

/* Load 指令 */
SimError execute_load(CPU* cpu, const DecodedInsn* insn) {
    u32 addr = cpu_read_reg(cpu, insn->rs1) + (u32)insn->imm;
    u32 result = 0;
    SimError err;

    switch (insn->funct3) {
        case MEM_BYTE: {
            u8 val;
            err = memory_read_byte(cpu->memory, addr, &val);
            if (err != ERR_OK) return err;
            result = (u32)(i32)(i8)val;  /* 符号扩展 */
            break;
        }
        case MEM_HALF: {
            u16 val;
            err = memory_read_half(cpu->memory, addr, &val);
            if (err != ERR_OK) return err;
            result = (u32)(i32)(i16)val;  /* 符号扩展 */
            break;
        }
        case MEM_WORD: {
            u32 val;
            err = memory_read_word(cpu->memory, addr, &val);
            if (err != ERR_OK) return err;
            result = val;
            break;
        }
        case MEM_UBYTE: {
            u8 val;
            err = memory_read_byte(cpu->memory, addr, &val);
            if (err != ERR_OK) return err;
            result = (u32)val;  /* 零扩展 */
            break;
        }
        case MEM_UHALF: {
            u16 val;
            err = memory_read_half(cpu->memory, addr, &val);
            if (err != ERR_OK) return err;
            result = (u32)val;  /* 零扩展 */
            break;
        }
        default:
            return ERR_INVALID_INSN;
    }

    cpu_write_reg(cpu, insn->rd, result);
    return ERR_OK;
}

/* Store 指令 */
SimError execute_store(CPU* cpu, const DecodedInsn* insn) {
    u32 addr = cpu_read_reg(cpu, insn->rs1) + (u32)insn->imm;
    u32 val = cpu_read_reg(cpu, insn->rs2);

    switch (insn->funct3) {
        case MEM_BYTE: return memory_write_byte(cpu->memory, addr, (u8)(val & 0xFF));
        case MEM_HALF: return memory_write_half(cpu->memory, addr, (u16)(val & 0xFFFF));
        case MEM_WORD: return memory_write_word(cpu->memory, addr, val);
        default: return ERR_INVALID_INSN;
    }
}

/* Branch 指令 */
SimError execute_branch(CPU* cpu, const DecodedInsn* insn) {
    u32 rs1_val = cpu_read_reg(cpu, insn->rs1);
    u32 rs2_val = cpu_read_reg(cpu, insn->rs2);
    bool taken = false;

    switch (insn->funct3) {
        case BRANCH_BEQ:  taken = (rs1_val == rs2_val); break;
        case BRANCH_BNE:  taken = (rs1_val != rs2_val); break;
        case BRANCH_BLT:  taken = ((i32)rs1_val < (i32)rs2_val); break;
        case BRANCH_BGE:  taken = ((i32)rs1_val >= (i32)rs2_val); break;
        case BRANCH_BLTU: taken = (rs1_val < rs2_val); break;
        case BRANCH_BGEU: taken = (rs1_val >= rs2_val); break;
        default: return ERR_INVALID_INSN;
    }

    if (taken) {
        cpu->pc = cpu->pc + (u32)insn->imm - 4;  /* -4 因为后面会 +4 */
    }

    return ERR_OK;
}

/* Jump 指令 */
SimError execute_jump(CPU* cpu, const DecodedInsn* insn) {
    if (insn->opcode == OP_JAL) {
        /* JAL: rd = PC + 4, PC = PC + imm */
        cpu_write_reg(cpu, insn->rd, cpu->pc);  /* PC 已经 +4 */
        cpu->pc = cpu->pc - 4 + (u32)insn->imm;  /* 跳转目标 */
    } else if (insn->opcode == OP_JALR) {
        /* JALR: rd = PC + 4, PC = (rs1 + imm) & ~1 */
        u32 rs1_val = cpu_read_reg(cpu, insn->rs1);
        cpu_write_reg(cpu, insn->rd, cpu->pc);  /* PC 已经 +4 */
        cpu->pc = (rs1_val + (u32)insn->imm) & ~1u;
    }

    return ERR_OK;
}

/* U-type 指令 */
SimError execute_u_type(CPU* cpu, const DecodedInsn* insn) {
    if (insn->opcode == OP_LUI) {
        /* LUI: rd = imm << 12 */
        cpu_write_reg(cpu, insn->rd, (u32)insn->imm);
    } else if (insn->opcode == OP_AUIPC) {
        /* AUIPC: rd = PC + (imm << 12) */
        cpu_write_reg(cpu, insn->rd, cpu->pc - 4 + (u32)insn->imm);
    }

    return ERR_OK;
}

/* System 指令 */
SimError execute_system(CPU* cpu, const DecodedInsn* insn) {
    if (insn->funct3 != 0) return ERR_INVALID_INSN;

    if (insn->imm == 0) {
        /* ECALL: 系统调用 */
        /* 在简单模拟器中，使用 a7 寄存器作为系统调用号 */
        u32 syscall_num = cpu_read_reg(cpu, REG_A7);

        switch (syscall_num) {
            case 1: {
                /* sys_write: a0=fd, a1=buf_addr, a2=len */
                u32 fd  = cpu_read_reg(cpu, REG_A0);
                u32 buf = cpu_read_reg(cpu, REG_A1);
                u32 len = cpu_read_reg(cpu, REG_A2);

                if (fd == 1 || fd == 2) {  /* stdout / stderr */
                    for (u32 i = 0; i < len; i++) {
                        u8 ch;
                        if (memory_read_byte(cpu->memory, buf + i, &ch) == ERR_OK) {
                            putchar(ch);
                        }
                    }
                    cpu_write_reg(cpu, REG_A0, len);
                }
                break;
            }
            case 93: {
                /* sys_exit: a0=exit_code */
                u32 exit_code = cpu_read_reg(cpu, REG_A0);
                printf("\n[ECALL] Exit with code %u\n", exit_code);
                printf("Instructions executed: %lu\n", (unsigned long)cpu->insn_count);
                return ERR_HALT;
            }
            default:
                fprintf(stderr, "Unknown syscall: %u\n", syscall_num);
                break;
        }
    } else if (insn->imm == 1) {
        /* EBREAK: 断点 */
        printf("[EBREAK] Breakpoint at PC=0x%08X\n", cpu->pc - 4);
        return ERR_BREAKPOINT;
    }

    return ERR_OK;
}

/* 主执行函数 */
SimError execute_insn(CPU* cpu, const DecodedInsn* insn) {
    if (!cpu || !insn) return ERR_INVALID_INSN;

    /* 调试输出 */
    if (cpu->debug >= DEBUG_TRACE) {
        char buf[128];
        format_insn(insn, buf, sizeof(buf));
        printf("[TRACE] PC=0x%08X: %s\n", cpu->pc - 4, buf);
    }

    switch (insn->format) {
        case FMT_R:  return execute_r_type(cpu, insn);
        case FMT_I:
            if (insn->opcode == OP_LOAD)   return execute_load(cpu, insn);
            if (insn->opcode == OP_JALR)   return execute_jump(cpu, insn);
            if (insn->opcode == OP_SYSTEM) return execute_system(cpu, insn);
            return execute_i_type(cpu, insn);
        case FMT_S:  return execute_store(cpu, insn);
        case FMT_B:  return execute_branch(cpu, insn);
        case FMT_J:  return execute_jump(cpu, insn);
        case FMT_U:  return execute_u_type(cpu, insn);
        default:     return ERR_INVALID_INSN;
    }
}
