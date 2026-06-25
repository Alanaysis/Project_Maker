/* ============================================================
 * RISC-V 指令集模拟器 - 主程序
 *
 * 用法:
 *   riscv-sim [选项] <程序>
 *
 * 选项:
 *   -h          显示帮助
 *   -d <level>  调试级别 (0-4)
 *   -s          单步执行模式
 *   -a          汇编模式 (输入为汇编文本)
 *   -n <cycles> 最大执行周期数
 * ============================================================ */

#include "riscv.h"
#include "cpu.h"
#include "memory.h"
#include "decoder.h"
#include "assembler.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* 打印帮助信息 */
static void print_help(const char* prog) {
    printf("RISC-V Simulator v%s\n\n", RISCV_SIM_VERSION);
    printf("Usage: %s [options] <program>\n\n", prog);
    printf("Options:\n");
    printf("  -h          Show this help\n");
    printf("  -d <level>  Debug level (0=none, 1=error, 2=warn, 3=info, 4=trace)\n");
    printf("  -s          Single-step mode\n");
    printf("  -a          Assembly mode (input is assembly text file)\n");
    printf("  -n <cycles> Max execution cycles\n");
    printf("\nExamples:\n");
    printf("  %s program.bin           # Run binary\n", prog);
    printf("  %s -a program.s          # Assemble and run\n", prog);
    printf("  %s -d 4 -s program.bin   # Trace single-step\n", prog);
}

/* 运行二进制程序 */
static int run_binary(const char* filename, DebugLevel debug, bool single_step, u64 max_cycles) {
    /* 创建内存 (1MB, 基地址 0x80000000) */
    Memory* mem = memory_create(DEFAULT_MEM_SIZE, DEFAULT_MEM_BASE);
    if (!mem) {
        fprintf(stderr, "Error: failed to create memory\n");
        return 1;
    }

    /* 加载二进制 */
    SimError err = memory_load_binary(mem, filename, DEFAULT_MEM_BASE);
    if (err != ERR_OK) {
        memory_destroy(mem);
        return 1;
    }

    /* 创建 CPU */
    CPU* cpu = cpu_create(mem);
    if (!cpu) {
        fprintf(stderr, "Error: failed to create CPU\n");
        memory_destroy(mem);
        return 1;
    }
    cpu->debug = debug;

    printf("Starting execution at PC=0x%08X\n", cpu->pc);
    printf("Debug level: %d\n", debug);
    printf("Max cycles: %lu\n\n", (unsigned long)max_cycles);

    /* 执行 */
    if (single_step) {
        /* 单步模式 */
        char cmd[16];
        while (cpu->state != CPU_HALTED && cpu->state != CPU_ERROR) {
            /* 读取当前指令 */
            u32 raw;
            if (memory_read_word(mem, cpu->pc, &raw) == ERR_OK) {
                DecodedInsn decoded;
                if (decode_insn(raw, &decoded) == ERR_OK) {
                    char buf[128];
                    format_insn(&decoded, buf, sizeof(buf));
                    printf("PC=0x%08X: %s\n", cpu->pc, buf);
                }
            }

            printf("Press Enter to step, 'r' to run, 'q' to quit: ");
            if (fgets(cmd, sizeof(cmd), stdin) == NULL) break;

            if (cmd[0] == 'q') break;
            if (cmd[0] == 'r') {
                cpu_run(cpu, max_cycles - cpu->insn_count);
                break;
            }

            err = cpu_step(cpu);
            if (err != ERR_OK && err != ERR_BREAKPOINT) {
                fprintf(stderr, "Error: %d\n", err);
                break;
            }
        }
    } else {
        /* 自动运行模式 */
        err = cpu_run(cpu, max_cycles);
        if (err != ERR_OK && err != ERR_HALT) {
            fprintf(stderr, "Execution error: %d\n", err);
        }
    }

    /* 输出最终状态 */
    printf("\n=== Execution Complete ===\n");
    cpu_dump_state(cpu);

    cpu_destroy(cpu);
    memory_destroy(mem);
    return 0;
}

/* 汇编并运行 */
static int assemble_and_run(const char* filename, DebugLevel debug, u64 max_cycles) {
    /* 读取汇编文件 */
    FILE* f = fopen(filename, "r");
    if (!f) {
        fprintf(stderr, "Error: cannot open '%s'\n", filename);
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);

    char* text = (char*)malloc(size + 1);
    if (!text) {
        fclose(f);
        return 1;
    }
    if (fread(text, 1, size, f) != (size_t)size) {
        fprintf(stderr, "Error: short read\n");
        free(text);
        fclose(f);
        return 1;
    }
    text[size] = '\0';
    fclose(f);

    /* 汇编 */
    AsmContext* asm_ctx = asm_create(DEFAULT_MEM_BASE);
    if (!asm_ctx) {
        free(text);
        return 1;
    }

    SimError err = asm_assemble(asm_ctx, text);
    free(text);

    if (err != ERR_OK) {
        fprintf(stderr, "Assembly error: %d\n", err);
        asm_destroy(asm_ctx);
        return 1;
    }

    printf("Assembled %u bytes\n", asm_ctx->code_size);
    asm_dump(asm_ctx);

    /* 创建内存并加载代码 */
    Memory* mem = memory_create(DEFAULT_MEM_SIZE, DEFAULT_MEM_BASE);
    if (!mem) {
        asm_destroy(asm_ctx);
        return 1;
    }

    err = memory_load(mem, DEFAULT_MEM_BASE, (const u8*)asm_ctx->code, asm_ctx->code_size);
    asm_destroy(asm_ctx);

    if (err != ERR_OK) {
        memory_destroy(mem);
        return 1;
    }

    /* 创建 CPU 并运行 */
    CPU* cpu = cpu_create(mem);
    if (!cpu) {
        memory_destroy(mem);
        return 1;
    }
    cpu->debug = debug;

    printf("\nStarting execution...\n");
    err = cpu_run(cpu, max_cycles);

    if (err != ERR_OK && err != ERR_HALT) {
        fprintf(stderr, "Execution error: %d\n", err);
    }

    cpu_dump_state(cpu);

    cpu_destroy(cpu);
    memory_destroy(mem);
    return 0;
}

/* 内置测试程序 */
static int run_builtin_test(void) {
    printf("Running built-in test program...\n\n");

    /* 创建内存和 CPU */
    Memory* mem = memory_create(DEFAULT_MEM_SIZE, DEFAULT_MEM_BASE);
    CPU* cpu = cpu_create(mem);
    if (!mem || !cpu) return 1;

    cpu->debug = DEBUG_TRACE;

    /* 使用汇编器生成测试程序 */
    AsmContext* asm_ctx = asm_create(DEFAULT_MEM_BASE);
    if (!asm_ctx) return 1;

    const char* test_program =
        "# RISC-V Test Program\n"
        "# 计算 1+2+...+10\n"
        "\n"
        "addi a0, zero, 0     # sum = 0\n"
        "addi t0, zero, 11    # upper bound (exclusive)\n"
        "addi t1, zero, 1     # i = 1\n"
        "\n"
        "loop:\n"
        "  add a0, a0, t1     # sum += i\n"
        "  addi t1, t1, 1     # i++\n"
        "  blt t1, t0, loop   # if i < 11, goto loop\n"
        "\n"
        "# 结果在 a0 中\n"
        "ebreak               # 停止\n";

    SimError err = asm_assemble(asm_ctx, test_program);
    if (err != ERR_OK) {
        fprintf(stderr, "Assembly error\n");
        asm_destroy(asm_ctx);
        cpu_destroy(cpu);
        memory_destroy(mem);
        return 1;
    }

    printf("Assembled %u bytes:\n", asm_ctx->code_size);
    asm_dump(asm_ctx);
    printf("\n");

    /* 加载到内存 */
    memory_load(mem, DEFAULT_MEM_BASE, (const u8*)asm_ctx->code, asm_ctx->code_size);
    asm_destroy(asm_ctx);

    /* 运行 */
    err = cpu_run(cpu, 1000);

    printf("\n=== Test Result ===\n");
    if (err == ERR_BREAKPOINT || err == ERR_OK) {
        u32 result = cpu_read_reg(cpu, REG_A0);
        printf("a0 (sum of 1..10) = %u (expected: 55)\n", result);
        if (result == 55) {
            printf("TEST PASSED!\n");
        } else {
            printf("TEST FAILED!\n");
        }
    } else {
        printf("TEST ERROR: %d\n", err);
    }

    cpu_dump_state(cpu);

    cpu_destroy(cpu);
    memory_destroy(mem);
    return 0;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        print_help(argv[0]);
        return 1;
    }

    DebugLevel debug = DEBUG_NONE;
    bool single_step = false;
    bool asm_mode = false;
    u64 max_cycles = 1000000;  /* 默认 100 万周期 */
    const char* filename = NULL;

    /* 解析参数 */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_help(argv[0]);
            return 0;
        } else if (strcmp(argv[i], "-d") == 0 && i + 1 < argc) {
            debug = (DebugLevel)atoi(argv[++i]);
        } else if (strcmp(argv[i], "-s") == 0) {
            single_step = true;
        } else if (strcmp(argv[i], "-a") == 0) {
            asm_mode = true;
        } else if (strcmp(argv[i], "-n") == 0 && i + 1 < argc) {
            max_cycles = (u64)atol(argv[++i]);
        } else if (strcmp(argv[i], "--test") == 0) {
            return run_builtin_test();
        } else if (argv[i][0] != '-') {
            filename = argv[i];
        }
    }

    if (!filename) {
        fprintf(stderr, "Error: no input file specified\n");
        return 1;
    }

    if (asm_mode) {
        return assemble_and_run(filename, debug, max_cycles);
    } else {
        return run_binary(filename, debug, single_step, max_cycles);
    }
}
