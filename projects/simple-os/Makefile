# Simple OS Makefile
# 功能: 编译和运行 Simple OS

# 编译器和汇编器
CC = gcc
AS = nasm
LD = ld

# 编译选项
CFLAGS = -m32 -c -ffreestanding -fno-builtin -fno-stack-protector \
         -nostdinc -nostdlib -Wall -Wextra -Werror \
         -I include -g -O0
LDFLAGS = -m elf_i386 -T linker.ld --oformat binary
ASFLAGS = -f elf32 -g

# 源文件目录
BOOT_DIR = boot
KERNEL_DIR = kernel
DRIVERS_DIR = drivers
MM_DIR = mm
PROCESS_DIR = process
FS_DIR = fs
INCLUDE_DIR = include

# 汇编源文件
BOOT_ASM = $(BOOT_DIR)/boot.asm $(BOOT_DIR)/loader.asm
KERNEL_ASM = $(KERNEL_DIR)/isr.asm $(KERNEL_DIR)/irq.asm \
             $(KERNEL_DIR)/gdt_flush.asm $(KERNEL_DIR)/idt_flush.asm \
             $(KERNEL_DIR)/context_switch.asm

# C 源文件
KERNEL_C = $(KERNEL_DIR)/main.c $(KERNEL_DIR)/gdt.c $(KERNEL_DIR)/idt.c \
           $(KERNEL_DIR)/timer.c
DRIVERS_C = $(DRIVERS_DIR)/screen.c $(DRIVERS_DIR)/keyboard.c
MM_C = $(MM_DIR)/memory.c $(MM_DIR)/paging.c $(MM_DIR)/heap.c
PROCESS_C = $(PROCESS_DIR)/process.c
FS_C = $(FS_DIR)/fs.c

# 目标文件
BOOT_BIN = $(BOOT_DIR)/boot.bin $(BOOT_DIR)/loader.bin
KERNEL_OBJ = $(KERNEL_C:.c=.o) $(KERNEL_ASM:.asm=.o)
DRIVERS_OBJ = $(DRIVERS_C:.c=.o)
MM_OBJ = $(MM_C:.c=.o)
PROCESS_OBJ = $(PROCESS_C:.c=.o)
FS_OBJ = $(FS_C:.c=.o)

# 所有目标文件
ALL_OBJ = $(KERNEL_OBJ) $(DRIVERS_OBJ) $(MM_OBJ) $(PROCESS_OBJ) $(FS_OBJ)

# 最终目标
KERNEL_BIN = kernel.bin
OS_IMG = simple-os.img

# 调试符号文件
KERNEL_ELF = kernel.elf

# 默认目标
all: $(OS_IMG)
	@echo "Build complete: $(OS_IMG)"
	@echo "Run with: make run"

# 创建 OS 镜像
$(OS_IMG): $(BOOT_BIN) $(KERNEL_BIN)
	@echo "Creating OS image..."
	cat $(BOOT_DIR)/boot.bin $(BOOT_DIR)/loader.bin $(KERNEL_BIN) > $@
	@echo "OS image created: $@"

# 编译内核 (二进制格式)
$(KERNEL_BIN): $(ALL_OBJ)
	@echo "Linking kernel..."
	$(LD) $(LDFLAGS) -o $@ $^
	@echo "Kernel linked: $@"

# 编译内核 (ELF 格式，用于调试)
$(KERNEL_ELF): $(ALL_OBJ)
	@echo "Linking kernel (ELF)..."
	$(LD) -m elf_i386 -T linker.ld -o $@ $^
	@echo "Kernel linked: $@"

# 编译 C 文件
%.o: %.c
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) $< -o $@

# 编译汇编文件
%.o: %.asm
	@echo "Assembling $<..."
	$(AS) $(ASFLAGS) $< -o $@

# 编译引导程序 (二进制格式)
$(BOOT_DIR)/boot.bin: $(BOOT_DIR)/boot.asm
	@echo "Assembling boot sector..."
	$(AS) -f bin $< -o $@

$(BOOT_DIR)/loader.bin: $(BOOT_DIR)/loader.asm
	@echo "Assembling loader..."
	$(AS) -f bin $< -o $@

# 运行
run: $(OS_IMG)
	@echo "Starting QEMU..."
	qemu-system-i386 \
		-fda $(OS_IMG) \
		-m 32 \
		-boot a \
		-serial stdio \
		-display gtk

# 调试模式运行
debug: $(OS_IMG) $(KERNEL_ELF)
	@echo "Starting QEMU in debug mode..."
	@echo "In another terminal, run:"
	@echo "  gdb -ex 'target remote localhost:1234' -ex 'symbol-file $(KERNEL_ELF)'"
	qemu-system-i386 \
		-fda $(OS_IMG) \
		-m 32 \
		-boot a \
		-s -S \
		-serial stdio \
		-display gtk

# 测试
test: $(OS_IMG)
	@echo "Running tests..."
	@echo "Test 1: Check boot sector signature..."
	@xxd $(BOOT_DIR)/boot.bin | tail -1 | grep -q "55aa" && echo "PASS" || echo "FAIL"
	@echo "Test 2: Check kernel size..."
	@ls -la $(KERNEL_BIN) | awk '{print $$5}' | \
		awk '{if ($$1 > 0 && $$1 < 100000) print "PASS"; else print "FAIL"}'

# 反汇编
disasm: $(KERNEL_ELF)
	@echo "Disassembling kernel..."
	objdump -d -M intel $(KERNEL_ELF) > kernel_disasm.txt
	@echo "Disassembly saved to kernel_disasm.txt"

# 清理
clean:
	@echo "Cleaning build files..."
	rm -f $(BOOT_BIN)
	rm -f $(ALL_OBJ)
	rm -f $(KERNEL_BIN) $(KERNEL_ELF)
	rm -f $(OS_IMG)
	rm -f kernel_disasm.txt
	@echo "Clean complete."

# 帮助
help:
	@echo "Simple OS Build System"
	@echo ""
	@echo "Usage:"
	@echo "  make          - Build the OS image"
	@echo "  make run      - Build and run in QEMU"
	@echo "  make debug    - Build and run in debug mode"
	@echo "  make test     - Run basic tests"
	@echo "  make disasm   - Generate disassembly"
	@echo "  make clean    - Clean build files"
	@echo "  make help     - Show this help"
	@echo ""
	@echo "Dependencies:"
	@echo "  - GCC (32-bit support)"
	@echo "  - NASM"
	@echo "  - QEMU"
	@echo "  - Make"
	@echo ""
	@echo "Install dependencies (Ubuntu/Debian):"
	@echo "  sudo apt-get install gcc nasm qemu-system-x86 make"

.PHONY: all run debug test disasm clean help
