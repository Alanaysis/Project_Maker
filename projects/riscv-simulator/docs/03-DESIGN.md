# 架构设计

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     命令行接口 (main.c)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ 汇编器    │  │ 解码器    │  │ 执行器    │  │ CPU    │ │
│  │assembler │  │ decoder  │  │ executor │  │ cpu    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │             │             │             │       │
│       └─────────────┼─────────────┼─────────────┘       │
│                     │             │                     │
│               ┌─────┴─────────────┴─────┐               │
│               │       内存模型          │               │
│               │       memory            │               │
│               └─────────────────────────┘               │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                    公共类型定义 (riscv.h)                 │
└─────────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 公共类型定义 (riscv.h)

定义所有模块共享的类型和常量:

```
- 基础类型: u8, u16, u32, u64, i8, i16, i32, i64
- 寄存器定义: NUM_REGS, RegIndex, REG_ABI_NAMES
- 指令格式: InsnFormat (R/I/S/B/U/J)
- 操作码: Opcode
- ALU 操作: AluOp
- 分支/内存功能码: BranchFunc, MemFunc
- 解码后指令: DecodedInsn
- 错误码: SimError
- 调试级别: DebugLevel
```

### 2.2 内存模块 (memory.h / memory.c)

职责: 管理模拟器的内存空间

```
接口:
  memory_create(size, base_addr)  -> Memory*
  memory_destroy(mem)
  memory_load(mem, addr, data, len)
  memory_read_byte/half/word(mem, addr, out)
  memory_write_byte/half/word(mem, addr, val)
  memory_dump(mem, addr, len)
```

设计要点:
- 支持可配置的大小和基地址
- 小端序存储
- 对齐访问检查
- 越界检查

### 2.3 指令解码器 (decoder.h / decoder.c)

职责: 将 32 位原始指令解码为结构化的 DecodedInsn

```
接口:
  decode_insn(raw, out)        -> SimError
  get_insn_format(opcode)      -> InsnFormat
  get_insn_name(insn)          -> const char*
  format_insn(insn, buf, size) -> int
```

解码流程:
1. 提取 opcode (bits[6:0])
2. 确定指令格式 (R/I/S/B/U/J)
3. 提取 rd, rs1, rs2, funct3, funct7
4. 根据格式提取立即数并符号扩展

### 2.4 指令执行器 (executor.h / executor.c)

职责: 执行解码后的指令，更新 CPU 状态

```
接口:
  execute_insn(cpu, insn) -> SimError
  execute_r_type/cpu, insn)
  execute_i_type(cpu, insn)
  execute_load(cpu, insn)
  execute_store(cpu, insn)
  execute_branch(cpu, insn)
  execute_jump(cpu, insn)
  execute_u_type(cpu, insn)
  execute_system(cpu, insn)
```

### 2.5 CPU 模块 (cpu.h / cpu.c)

职责: 管理 CPU 状态，执行取指-解码-执行循环

```
接口:
  cpu_create(mem)         -> CPU*
  cpu_destroy(cpu)
  cpu_reset(cpu)
  cpu_set_pc(cpu, pc)
  cpu_read_reg(cpu, reg)  -> u32
  cpu_write_reg(cpu, reg, val)
  cpu_step(cpu)           -> SimError
  cpu_run(cpu, max_cycles) -> SimError
  cpu_dump_regs(cpu)
  cpu_dump_state(cpu)
```

执行循环 (Fetch-Decode-Execute):
```
┌─────────────────────────────────────────────┐
│  1. 取指 (Fetch): 从内存读取 32 位指令      │
│  2. 解码 (Decode): 解析指令各字段           │
│  3. PC += 4                                 │
│  4. 执行 (Execute): 执行指令，更新寄存器     │
│  5. 检查状态 (Halt/Error/Continue)          │
└─────────────────────────────────────────────┘
```

### 2.6 汇编器 (assembler.h / assembler.c)

职责: 将汇编文本转换为机器码

```
接口:
  asm_create(start_pc)              -> AsmContext*
  asm_destroy(ctx)
  asm_assemble(ctx, text)           -> SimError
  asm_assemble_one_wrapper(line, pc, out) -> SimError
  asm_parse_register(name)          -> int
  asm_parse_imm(str, out)           -> SimError
```

两遍汇编:
1. 第一遍: 扫描标签，建立符号表
2. 第二遍: 汇编指令，解析标签引用

## 3. 数据流

```
汇编源代码 ──→ 汇编器 ──→ 机器码 ──→ 内存
                                      │
                                      ▼
                              ┌─── CPU 循环 ───┐
                              │               │
                              │  取指 ←── PC   │
                              │    │           │
                              │  解码          │
                              │    │           │
                              │  执行 ──→ 寄存器│
                              │    │           │
                              │  PC += 4      │
                              │    │           │
                              └────┘           │
                                      │
                                      ▼
                              最终状态输出
```

## 4. 指令编码格式详解

### R-type (寄存器-寄存器运算)
```
 31      25 24  20 19  15 14  12 11   7 6      0
┌─────────┬──────┬──────┬──────┬──────┬────────┐
│ funct7  │ rs2  │ rs1  │func3│  rd  │ opcode │
│  7 bit  │5 bit │5 bit │3 bit│5 bit │ 7 bit  │
└─────────┴──────┴──────┴──────┴──────┴────────┘
```

### I-type (立即数运算 / 加载)
```
 31              20 19  15 14  12 11   7 6      0
┌──────────────────┬──────┬──────┬──────┬────────┐
│   imm[11:0]      │ rs1  │func3│  rd  │ opcode │
│     12 bit       │5 bit │3 bit│5 bit │ 7 bit  │
└──────────────────┴──────┴──────┴──────┴────────┘
```

### B-type (条件分支)
```
 31 30    25 24  20 19  15 14  12 11  8  7 6      0
┌────┬────────┬──────┬──────┬──────┬────┬────────┐
│12  │10:5    │ rs2  │ rs1  │func3│4:1 │11 opcode│
│1bit│ 6 bit  │5 bit │5 bit │3 bit│4bit│1bit 7bit│
└────┴────────┴──────┴──────┴──────┴────┴────────┘
```
