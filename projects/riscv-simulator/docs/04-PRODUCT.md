# 产品说明

## 1. 产品概述

RISC-V Simulator 是一个用 C 语言实现的 RISC-V 指令集模拟器，支持 RV32I 基本整数指令集。它包含一个汇编器，可以直接运行 RISC-V 汇编源代码。

## 2. 功能特性

### 2.1 指令集支持
- 完整的 RV32I 基本整数指令集 (40+ 条指令)
- R-type, I-type, S-type, B-type, U-type, J-type 全部格式
- ECALL 系统调用模拟 (write, exit)
- EBREAK 断点支持

### 2.2 汇编器
- 支持所有 RV32I 指令
- ABI 寄存器名称 (zero, ra, sp, a0, t0 等)
- 标签 (labels) 支持
- 注释 (# 和 ;)
- 两遍汇编

### 2.3 调试功能
- 单步执行模式
- 指令跟踪 (trace)
- 寄存器状态查看
- 内存内容查看

## 3. 使用方法

### 3.1 编译
```bash
make          # 编译模拟器
make test     # 运行所有测试
make verify   # 完整验证
```

### 3.2 运行汇编程序
```bash
./riscv-sim -a examples/sum_1_to_10.s
```

### 3.3 运行二进制程序
```bash
./riscv-sim program.bin
```

### 3.4 调试模式
```bash
./riscv-sim -d 4 -s program.bin    # 跟踪 + 单步
./riscv-sim -d 3 program.bin       # 信息级别
```

### 3.5 内置测试
```bash
./riscv-sim --test
```

## 4. 示例程序

### 4.1 计算 1+2+...+10
```asm
addi a0, zero, 0     # sum = 0
addi t0, zero, 11    # upper bound
addi t1, zero, 1     # i = 1
loop:
  add a0, a0, t1     # sum += i
  addi t1, t1, 1     # i++
  blt t1, t0, loop   # if i < 11, goto loop
ebreak
# 结果: a0 = 55
```

### 4.2 斐波那契数列
```asm
addi t0, zero, 0     # fib(0) = 0
addi t1, zero, 1     # fib(1) = 1
addi t2, zero, 10    # count = 10
addi t3, zero, 2     # i = 2
loop:
  add t4, t0, t1     # next = fib(n-2) + fib(n-1)
  add t0, t1, zero   # fib(n-2) = fib(n-1)
  add t1, t4, zero   # fib(n-1) = next
  addi t3, t3, 1     # i++
  blt t3, t2, loop   # if i < count, goto loop
add a0, t1, zero
ebreak
# 结果: a0 = 55
```

## 5. 测试覆盖

### 5.1 单元测试 (28 个测试)
- 内存模块: 7 个测试
- 解码器模块: 11 个测试
- 汇编器模块: 10 个测试

### 5.2 集成测试 (11 个测试)
- ADD/ADDI, SUB, AND/OR/XOR, SLL/SRL
- BEQ/BNE/BLT/BGE
- LUI/AUIPC, JAL, Load/Store
- SLT/SLTU, JALR, x0 硬连线零

## 6. 已知限制

- 仅支持 RV32I，不支持扩展 (M/A/F/D/C)
- 不支持虚拟内存
- ECALL 仅支持 write 和 exit
- 不支持中断和异常
- 单核模拟，不支持多核
