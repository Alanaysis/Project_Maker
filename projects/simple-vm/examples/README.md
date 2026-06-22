# 示例程序

本目录包含用于 Simple VM 的示例程序。

## 示例列表

### 1. hello.asm - Hello World

最简单的示例程序，通过串口输出 "Hello, World!"。

**功能**:
- 初始化段寄存器
- 通过串口输出字符串
- 停机

**运行**:
```bash
./build/simple-vm build/examples/hello.bin
```

**预期输出**:
```
Hello, World!
```

**学习要点**:
- 理解实模式下的段寄存器
- 学习串口编程
- 理解 I/O 端口操作

### 2. calc.asm - 简单计算器

演示基本的算术运算和输出。

**功能**:
- 执行加法、减法、乘法、除法
- 将结果转换为十进制并输出
- 演示循环和函数调用

**运行**:
```bash
./build/simple-vm build/examples/calc.bin
```

**预期输出**:
```
=== Simple Calculator ===
10 + 20 = 30
50 - 15 = 35
6 * 7 = 42
100 / 4 = 25
Calculation complete!
```

**学习要点**:
- 理解 x86 算术指令
- 学习数字到字符串的转换
- 理解函数调用约定

## 编译示例

### 前提条件

需要安装 NASM 汇编器:

```bash
# Ubuntu/Debian
sudo apt install nasm

# Fedora/RHEL
sudo dnf install nasm

# Arch Linux
sudo pacman -S nasm
```

### 编译方法

```bash
# 使用 Make
make

# 或使用 CMake
mkdir build && cd build
cmake ..
make
```

### 手动编译单个示例

```bash
nasm -f bin examples/hello.asm -o hello.bin
./build/simple-vm hello.bin
```

## 编写自己的示例

### 基本模板

```asm
[BITS 16]           ; 16 位实模式
[ORG 0x7C00]        ; 引导扇区加载地址

start:
    ; 初始化段寄存器
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    ; 你的代码在这里

    ; 停机
    hlt

; 填充引导扇区
times 510-($-$$) db 0
dw 0xAA55           ; 引导扇区签名
```

### 串口输出

```asm
; 串口端口定义
%define COM1_PORT    0x3F8
%define COM1_THR     COM1_PORT + 0
%define COM1_LSR     COM1_PORT + 5

; 输出字符
mov al, 'A'
mov dx, COM1_THR
out dx, al
```

### 等待发送缓冲区空

```asm
wait_transmit_empty:
    push ax
    push dx
.wait:
    mov dx, COM1_LSR
    in al, dx
    test al, 0x20   ; 检查 THRE 位
    jz .wait
    pop dx
    pop ax
    ret
```

## 调试技巧

### 使用 GDB 调试

```bash
# 编译调试版本
make debug

# 使用 GDB
gdb ./build/simple-vm

# 在 GDB 中设置断点
(gdb) break main
(gdb) run build/examples/hello.bin
```

### 查看寄存器状态

```bash
# 在 GDB 中
(gdb) info registers
(gdb) x/10x $rip
```

## 常见问题

### Q: 程序没有输出

**可能原因**:
1. 串口初始化不正确
2. 等待发送缓冲区空的逻辑错误
3. 字符串没有正确终止

**解决方案**:
1. 检查串口端口地址
2. 确保等待 THRE 位
3. 确保字符串以 0 结尾

### Q: 程序崩溃

**可能原因**:
1. 段寄存器设置不正确
2. 栈指针设置错误
3. 内存访问越界

**解决方案**:
1. 检查段寄存器初始化
2. 确保栈指针指向有效内存
3. 检查内存地址范围

## 参考资源

- [x86 指令集参考](https://c9x.me/x86/)
- [NASM 文档](https://www.nasm.us/doc/)
- [OSDev Wiki](https://wiki.osdev.org/)
