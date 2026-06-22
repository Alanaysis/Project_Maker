# 开发手册

## 1. 环境搭建

### 1.1 系统要求

**操作系统**: Linux (推荐 Ubuntu 20.04+)

**硬件要求**:
- CPU: 任意
- 内存: 1GB+
- 磁盘: 1GB+

### 1.2 依赖安装

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install build-essential nasm qemu-system-x86 gdb make
```

**CentOS/RHEL**:
```bash
sudo yum groupinstall "Development Tools"
sudo yum install nasm qemu-system-x86 gdb make
```

**Arch Linux**:
```bash
sudo pacman -S base-devel nasm qemu-system-x86 gdb make
```

### 1.3 工具说明

| 工具 | 版本 | 用途 |
|------|------|------|
| GCC | 9.0+ | C 编译器 |
| NASM | 2.14+ | 汇编器 |
| QEMU | 4.0+ | 虚拟机 |
| GDB | 8.0+ | 调试器 |
| Make | 4.0+ | 构建工具 |

### 1.4 验证安装

```bash
# 检查 GCC
gcc --version

# 检查 NASM
nasm --version

# 检查 QEMU
qemu-system-i386 --version

# 检查 GDB
gdb --version

# 检查 Make
make --version
```

## 2. 项目结构

```
simple-os/
├── boot/                   # 引导加载程序
│   ├── boot.asm           # 主引导扇区 (512 字节)
│   └── loader.asm         # 加载器
├── kernel/                 # 内核核心
│   ├── main.c             # 内核入口
│   ├── gdt.c              # GDT 初始化
│   ├── idt.c              # IDT 初始化
│   ├── isr.c              # 中断服务程序
│   ├── irq.c              # 硬件中断
│   └── timer.c            # 定时器
├── drivers/                # 设备驱动
│   ├── screen.c           # 屏幕输出
│   └── keyboard.c         # 键盘输入
├── mm/                     # 内存管理
│   ├── memory.c           # 物理内存管理
│   ├── paging.c           # 分页管理
│   └── heap.c             # 内核堆
├── process/                # 进程管理
│   ├── process.c          # 进程管理
│   └── scheduler.c        # 进程调度
├── fs/                     # 文件系统
│   └── fs.c               # 简单文件系统
├── include/                # 头文件
│   ├── types.h            # 基本类型
│   ├── gdt.h              # GDT 定义
│   ├── idt.h              # IDT 定义
│   ├── memory.h           # 内存管理
│   ├── process.h          # 进程管理
│   ├── screen.h           # 屏幕驱动
│   └── keyboard.h         # 键盘驱动
├── tests/                  # 单元测试
│   ├── test_memory.c      # 内存管理测试
│   ├── test_process.c     # 进程管理测试
│   └── test_fs.c          # 文件系统测试
├── examples/               # 使用示例
│   ├── hello.c            # Hello World
│   └── shell.c            # 简单 Shell
├── docs/                   # 文档
│   ├── 01-RESEARCH.md     # 市场调研
│   ├── 02-REQUIREMENTS.md # 需求分析
│   ├── 03-DESIGN.md       # 技术设计
│   ├── 04-PRODUCT.md      # 产品思维
│   └── 05-DEVELOPMENT.md  # 开发手册
├── Makefile                # 构建脚本
├── linker.ld              # 链接脚本
├── README.md              # 项目说明
└── LEARNING_NOTES.md      # 学习笔记
```

## 3. 构建系统

### 3.1 Makefile 详解

```makefile
# 编译器和汇编器
CC = gcc
AS = nasm
LD = ld

# 编译选项
CFLAGS = -m32 -c -ffreestanding -fno-builtin -fno-stack-protector \
         -nostdinc -nostdlib -Wall -Wextra
LDFLAGS = -m elf_i386 -T linker.ld --oformat binary
ASFLAGS = -f elf32

# 源文件
BOOT_SOURCES = boot/boot.asm boot/loader.asm
KERNEL_SOURCES = kernel/main.c kernel/gdt.c kernel/idt.c \
                 kernel/isr.c kernel/irq.c kernel/timer.c
DRIVER_SOURCES = drivers/screen.c drivers/keyboard.c
MM_SOURCES = mm/memory.c mm/paging.c mm/heap.c
PROCESS_SOURCES = process/process.c process/scheduler.c
FS_SOURCES = fs/fs.c

# 目标文件
BOOT_OBJECTS = $(BOOT_SOURCES:.asm=.bin)
KERNEL_OBJECTS = $(KERNEL_SOURCES:.c=.o) $(DRIVER_SOURCES:.c=.o) \
                 $(MM_SOURCES:.c=.o) $(PROCESS_SOURCES:.c=.o) \
                 $(FS_SOURCES:.c=.o)

# 最终目标
KERNEL_BIN = kernel.bin
OS_IMG = simple-os.img

# 默认目标
all: $(OS_IMG)

# 创建 OS 镜像
$(OS_IMG): $(BOOT_OBJECTS) $(KERNEL_BIN)
	cat boot/boot.bin boot/loader.bin $(KERNEL_BIN) > $@
	dd if=/dev/zero bs=1 count=512 >> $@

# 编译内核
$(KERNEL_BIN): $(KERNEL_OBJECTS)
	$(LD) $(LDFLAGS) -o $@ $^

# 编译 C 文件
%.o: %.c
	$(CC) $(CFLAGS) $< -o $@

# 编译汇编文件
%.bin: %.asm
	$(AS) $(ASFLAGS) $< -o $@

# 运行
run: $(OS_IMG)
	qemu-system-i386 -fda $<

# 调试
debug: $(OS_IMG)
	qemu-system-i386 -fda $< -s -S &
	gdb -ex "target remote localhost:1234" -ex "symbol-file kernel/kernel.elf"

# 清理
clean:
	rm -f $(BOOT_OBJECTS) $(KERNEL_OBJECTS) $(KERNEL_BIN) $(OS_IMG)

.PHONY: all run debug clean
```

### 3.2 链接脚本

```ld
/* linker.ld */
ENTRY(_start)

SECTIONS
{
    . = 0x100000;

    .text : {
        *(.text)
    }

    .rodata : {
        *(.rodata)
    }

    .data : {
        *(.data)
    }

    .bss : {
        *(.bss)
    }

    _end = .;
}
```

### 3.3 编译命令

```bash
# 完整编译
make

# 清理后重新编译
make clean && make

# 只编译内核
make kernel.bin

# 只编译引导程序
make boot.bin loader.bin
```

## 4. 核心模块解析

### 4.1 引导模块 (boot/)

#### boot.asm - 主引导扇区

**作用**: BIOS 加载的第一个程序，负责加载加载器

**关键代码**:
```nasm
; 主引导扇区入口
[bits 16]
[org 0x7C00]

start:
    ; 设置段寄存器
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    ; 加载加载器到 0x1000
    mov ah, 0x02        ; BIOS 读扇区功能
    mov al, 4           ; 读取 4 个扇区
    mov ch, 0           ; 柱面 0
    mov cl, 2           ; 扇区 2
    mov dh, 0           ; 磁头 0
    mov bx, 0x1000      ; 加载到 0x1000
    int 0x13            ; 调用 BIOS

    ; 跳转到加载器
    jmp 0x0000:0x1000

; 引导扇区结束标记
times 510-($-$$) db 0
dw 0xAA55
```

#### loader.asm - 加载器

**作用**: 设置保护模式，加载内核，跳转到内核入口

**关键代码**:
```nasm
; 加载器入口
[bits 16]
[org 0x1000]

loader_start:
    ; 显示加载信息
    mov si, msg_loading
    call print_string

    ; 检测内存
    call detect_memory

    ; 加载内核到 0x100000
    call load_kernel

    ; 切换到保护模式
    cli
    lgdt [gdt_descriptor]
    mov eax, cr0
    or eax, 1
    mov cr0, eax
    jmp 0x08:protected_mode

; 保护模式入口
[bits 32]
protected_mode:
    ; 设置段寄存器
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000

    ; 跳转到内核
    jmp 0x100000
```

### 4.2 内核模块 (kernel/)

#### main.c - 内核入口

**作用**: 初始化各子系统，启动第一个进程

**关键代码**:
```c
// 内核入口函数
void kernel_main() {
    // 初始化屏幕
    screen_init();
    screen_clear();
    screen_puts("Simple OS Kernel Starting...\n");

    // 初始化 GDT
    screen_puts("Initializing GDT...\n");
    gdt_init();

    // 初始化 IDT
    screen_puts("Initializing IDT...\n");
    idt_init();

    // 初始化内存管理
    screen_puts("Initializing Memory Management...\n");
    mm_init();

    // 初始化进程管理
    screen_puts("Initializing Process Management...\n");
    process_init();

    // 初始化定时器
    screen_puts("Initializing Timer...\n");
    timer_init();

    // 初始化键盘驱动
    screen_puts("Initializing Keyboard...\n");
    keyboard_init();

    // 创建第一个进程
    screen_puts("Creating init process...\n");
    process_create(init_process);

    // 启动调度器
    screen_puts("Starting Scheduler...\n");
    scheduler_start();

    // 不应该到达这里
    while (1) {
        asm volatile("hlt");
    }
}

// 初始化进程
void init_process() {
    screen_puts("Hello from init process!\n");

    // 创建子进程
    process_create(user_process);

    while (1) {
        yield();
    }
}

// 用户进程
void user_process() {
    screen_puts("Hello from user process!\n");

    while (1) {
        // 做一些工作
        for (int i = 0; i < 1000000; i++) {
            asm volatile("nop");
        }
        yield();
    }
}
```

### 4.3 内存管理模块 (mm/)

#### memory.c - 物理内存管理

**作用**: 管理物理内存的分配和释放

**关键数据结构**:
```c
// 物理内存位图
#define PAGE_SIZE 4096
#define BITMAP_SIZE (1024 * 1024 / 8)  // 1MB 内存

static uint8_t memory_bitmap[BITMAP_SIZE];
static uint32_t total_pages;
static uint32_t used_pages;

// 初始化内存管理
void mm_init(uint32_t total_memory) {
    total_pages = total_memory / PAGE_SIZE;
    used_pages = 0;
    memset(memory_bitmap, 0, sizeof(memory_bitmap));

    // 标记内核使用的内存
    uint32_t kernel_pages = ((uint32_t)&_end - 0x100000) / PAGE_SIZE;
    for (uint32_t i = 0; i < kernel_pages; i++) {
        mm_mark_page_used(i);
    }
}

// 分配一个物理页
uint32_t mm_alloc_page() {
    for (uint32_t i = 0; i < total_pages; i++) {
        if (!mm_is_page_used(i)) {
            mm_mark_page_used(i);
            used_pages++;
            return i * PAGE_SIZE;
        }
    }
    return 0;  // 内存不足
}

// 释放一个物理页
void mm_free_page(uint32_t page) {
    uint32_t page_num = page / PAGE_SIZE;
    mm_mark_page_free(page_num);
    used_pages--;
}
```

#### paging.c - 分页管理

**作用**: 管理虚拟内存的分页机制

**关键代码**:
```c
// 页目录和页表
static page_directory_t *page_directory = NULL;
static page_table_t *page_tables[1024];

// 初始化分页
void paging_init() {
    // 分配页目录
    page_directory = (page_directory_t *)mm_alloc_page();
    memset(page_directory, 0, PAGE_SIZE);

    // 映射内核空间
    for (uint32_t i = 0; i < 1024; i++) {
        page_directory->entries[i].present = 0;
    }

    // 创建内核页表
    page_table_t *kernel_table = (page_table_t *)mm_alloc_page();
    memset(kernel_table, 0, PAGE_SIZE);

    // 映射前 4MB 内存
    for (uint32_t i = 0; i < 1024; i++) {
        kernel_table->entries[i].frame = i;
        kernel_table->entries[i].present = 1;
        kernel_table->entries[i].rw = 1;
    }

    // 设置页目录项
    page_directory->entries[0].frame = (uint32_t)kernel_table >> 12;
    page_directory->entries[0].present = 1;
    page_directory->entries[0].rw = 1;

    // 启用分页
    asm volatile("mov %0, %%cr3" : : "r"(page_directory));
    uint32_t cr0;
    asm volatile("mov %%cr0, %0" : "=r"(cr0));
    cr0 |= 0x80000000;
    asm volatile("mov %0, %%cr0" : : "r"(cr0));
}

// 昆拟地址映射
void page_map(uint32_t virtual, uint32_t physical, uint32_t flags) {
    uint32_t page_dir_idx = virtual >> 22;
    uint32_t page_table_idx = (virtual >> 12) & 0x3FF;

    // 获取或创建页表
    page_table_t *table;
    if (!page_directory->entries[page_dir_idx].present) {
        table = (page_table_t *)mm_alloc_page();
        memset(table, 0, PAGE_SIZE);
        page_directory->entries[page_dir_idx].frame = (uint32_t)table >> 12;
        page_directory->entries[page_dir_idx].present = 1;
        page_directory->entries[page_dir_idx].rw = 1;
    } else {
        table = (page_table_t *)(page_directory->entries[page_dir_idx].frame << 12);
    }

    // 设置页表项
    table->entries[page_table_idx].frame = physical >> 12;
    table->entries[page_table_idx].present = 1;
    table->entries[page_table_idx].rw = (flags & PAGE_WRITABLE) ? 1 : 0;
    table->entries[page_table_idx].user = (flags & PAGE_USER) ? 1 : 0;

    // 刷新 TLB
    asm volatile("invlpg (%0)" : : "r"(virtual) : "memory");
}
```

### 4.4 进程管理模块 (process/)

#### process.c - 进程管理

**作用**: 创建、销毁和管理进程

**关键代码**:
```c
// 进程表
static process_t *process_table[MAX_PROCESSES];
static process_t *current_process = NULL;
static uint32_t next_pid = 1;

// 初始化进程管理
void process_init() {
    memset(process_table, 0, sizeof(process_table));
    current_process = NULL;
}

// 创建新进程
process_t *process_create(void (*entry_point)()) {
    // 分配进程控制块
    process_t *process = (process_t *)kmalloc(sizeof(process_t));
    if (!process) return NULL;

    // 初始化进程
    process->pid = next_pid++;
    process->state = PROCESS_READY;
    process->priority = 1;

    // 分配内核栈
    process->kernel_stack = (uint32_t)kmalloc(KERNEL_STACK_SIZE);
    if (!process->kernel_stack) {
        kfree(process);
        return NULL;
    }

    // 设置初始上下文
    process->esp = process->kernel_stack + KERNEL_STACK_SIZE;
    process->ebp = process->esp;
    process->eip = (uint32_t)entry_point;

    // 创建页目录
    process->page_directory = paging_create_directory();

    // 添加到进程表
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if (!process_table[i]) {
            process_table[i] = process;
            break;
        }
    }

    // 添加到就绪队列
    scheduler_add_process(process);

    return process;
}

// 销毁进程
void process_destroy(process_t *process) {
    if (!process) return;

    // 从进程表中移除
    for (int i = 0; i < MAX_PROCESSES; i++) {
        if (process_table[i] == process) {
            process_table[i] = NULL;
            break;
        }
    }

    // 从调度队列中移除
    scheduler_remove_process(process);

    // 释放资源
    kfree((void *)process->kernel_stack);
    paging_destroy_directory(process->page_directory);
    kfree(process);
}

// 进程退出
void process_exit(int status) {
    current_process->state = PROCESS_ZOMBIE;
    current_process->exit_status = status;

    // 唤醒父进程
    if (current_process->parent) {
        wake(current_process->parent);
    }

    // 调度到其他进程
    schedule();
}
```

### 4.5 中断处理模块 (kernel/)

#### idt.c - 中断描述符表

**作用**: 设置中断描述符表，注册中断处理函数

**关键代码**:
```c
// IDT 表
static idt_entry_t idt[256];
static idt_ptr_t idt_ptr;

// 中断处理函数表
static interrupt_handler_t interrupt_handlers[256];

// 初始化 IDT
void idt_init() {
    // 设置 IDT 指针
    idt_ptr.limit = sizeof(idt) - 1;
    idt_ptr.base = (uint32_t)&idt;

    // 清空 IDT
    memset(idt, 0, sizeof(idt));

    // 注册异常处理程序
    idt_set_gate(0, (uint32_t)isr0, 0x08, 0x8E);   // 除零错误
    idt_set_gate(1, (uint32_t)isr1, 0x08, 0x8E);   // 调试异常
    idt_set_gate(13, (uint32_t)isr13, 0x08, 0x8E); // 通用保护错误
    idt_set_gate(14, (uint32_t)isr14, 0x08, 0x8E); // 页面错误

    // 注册硬件中断
    idt_set_gate(32, (uint32_t)irq0, 0x08, 0x8E);  // 定时器
    idt_set_gate(33, (uint32_t)irq1, 0x08, 0x8E);  // 键盘

    // 注册系统调用
    idt_set_gate(0x80, (uint32_t)isr128, 0x08, 0xEE);

    // 加载 IDT
    asm volatile("lidt %0" : : "m"(idt_ptr));
}

// 设置 IDT 门
void idt_set_gate(uint8_t num, uint32_t base, uint16_t selector, uint8_t flags) {
    idt[num].base_low = base & 0xFFFF;
    idt[num].base_high = (base >> 16) & 0xFFFF;
    idt[num].selector = selector;
    idt[num].zero = 0;
    idt[num].flags = flags;
}

// 注册中断处理函数
void interrupt_register(uint8_t num, interrupt_handler_t handler) {
    interrupt_handlers[num] = handler;
}

// 中断分发
void interrupt_handler(interrupt_frame_t *frame) {
    if (interrupt_handlers[frame->int_no]) {
        interrupt_handlers[frame->int_no](frame);
    }

    // 发送 EOI
    if (frame->int_no >= 32) {
        outb(0x20, 0x20);
    }
}
```

### 4.6 设备驱动模块 (drivers/)

#### screen.c - 屏幕驱动

**作用**: 控制 VGA 文本模式输出

**关键代码**:
```c
// VGA 显示内存
static uint16_t *video_memory = (uint16_t *)0xB8000;
static uint8_t cursor_x = 0;
static uint8_t cursor_y = 0;
static uint8_t attribute = 0x07;  // 黑底白字

// 初始化屏幕
void screen_init() {
    cursor_x = 0;
    cursor_y = 0;
    attribute = 0x07;
    screen_clear();
}

// 清屏
void screen_clear() {
    for (int i = 0; i < 80 * 25; i++) {
        video_memory[i] = (attribute << 8) | ' ';
    }
    cursor_x = 0;
    cursor_y = 0;
    move_cursor();
}

// 输出字符
void screen_putchar(char c) {
    if (c == '\n') {
        cursor_x = 0;
        cursor_y++;
    } else if (c == '\r') {
        cursor_x = 0;
    } else if (c == '\t') {
        cursor_x = (cursor_x + 8) & ~7;
    } else {
        uint16_t *location = video_memory + (cursor_y * 80 + cursor_x);
        *location = (attribute << 8) | c;
        cursor_x++;
    }

    // 换行处理
    if (cursor_x >= 80) {
        cursor_x = 0;
        cursor_y++;
    }

    // 滚屏处理
    if (cursor_y >= 25) {
        scroll();
    }

    move_cursor();
}

// 输出字符串
void screen_puts(const char *str) {
    while (*str) {
        screen_putchar(*str++);
    }
}

// 移动光标
void move_cursor() {
    uint16_t pos = cursor_y * 80 + cursor_x;
    outb(0x3D4, 14);
    outb(0x3D5, (pos >> 8) & 0xFF);
    outb(0x3D4, 15);
    outb(0x3D5, pos & 0xFF);
}

// 滚屏
void scroll() {
    // 将所有行上移一行
    for (int i = 0; i < 80 * 24; i++) {
        video_memory[i] = video_memory[i + 80];
    }

    // 清空最后一行
    for (int i = 80 * 24; i < 80 * 25; i++) {
        video_memory[i] = (attribute << 8) | ' ';
    }

    cursor_y = 24;
}
```

### 4.7 文件系统模块 (fs/)

#### fs.c - 简单文件系统

**作用**: 实现基本的文件操作

**关键代码**:
```c
// 文件系统根目录
static file_node_t *root_directory = NULL;

// 初始化文件系统
void fs_init() {
    // 创建根目录
    root_directory = (file_node_t *)kmalloc(sizeof(file_node_t));
    strcpy(root_directory->name, "/");
    root_directory->type = FILE_TYPE_DIRECTORY;
    root_directory->size = 0;
    root_directory->permissions = 0755;
    root_directory->parent = NULL;
    root_directory->children = NULL;
    root_directory->next = NULL;

    // 创建一些示例文件
    fs_create("/hello.txt", 0644);
    fs_write_file("/hello.txt", "Hello, Simple OS!", 17);
}

// 创建文件
int fs_create(const char *path, uint32_t permissions) {
    // 解析路径
    char *filename = get_filename(path);
    file_node_t *parent = get_parent_directory(path);

    if (!parent) return -ERROR_NOENT;

    // 检查文件是否已存在
    if (find_file(parent, filename)) return -ERROR_EXIST;

    // 创建新文件节点
    file_node_t *file = (file_node_t *)kmalloc(sizeof(file_node_t));
    strcpy(file->name, filename);
    file->type = FILE_TYPE_REGULAR;
    file->size = 0;
    file->permissions = permissions;
    file->created = get_system_time();
    file->modified = file->created;
    file->data = NULL;
    file->parent = parent;
    file->children = NULL;

    // 添加到父目录
    file->next = parent->children;
    parent->children = file;

    return SUCCESS;
}

// 读取文件
int fs_read(int fd, void *buf, size_t count) {
    file_descriptor_t *desc = get_file_descriptor(fd);
    if (!desc) return -ERROR_INVAL;

    file_node_t *file = desc->file;
    if (!file || file->type != FILE_TYPE_REGULAR) return -ERROR_INVAL;

    // 计算实际读取大小
    size_t available = file->size - desc->position;
    size_t to_read = (count < available) ? count : available;

    // 复制数据
    if (file->data && to_read > 0) {
        memcpy(buf, file->data + desc->position, to_read);
        desc->position += to_read;
    }

    return to_read;
}

// 写入文件
int fs_write(int fd, const void *buf, size_t count) {
    file_descriptor_t *desc = get_file_descriptor(fd);
    if (!desc) return -ERROR_INVAL;

    file_node_t *file = desc->file;
    if (!file || file->type != FILE_TYPE_REGULAR) return -ERROR_INVAL;

    // 扩展文件大小
    uint32_t new_size = desc->position + count;
    if (new_size > file->size) {
        file->data = krealloc(file->data, new_size);
        file->size = new_size;
    }

    // 写入数据
    memcpy(file->data + desc->position, buf, count);
    desc->position += count;
    file->modified = get_system_time();

    return count;
}
```

## 5. 调试技巧

### 5.1 使用 QEMU 调试

```bash
# 启动 QEMU 调试模式
qemu-system-i386 -fda simple-os.img -s -S

# 在另一个终端启动 GDB
gdb
(gdb) target remote localhost:1234
(gdb) symbol-file kernel/kernel.elf
(gdb) break kernel_main
(gdb) continue
```

### 5.2 常用 GDB 命令

```bash
# 设置断点
break kernel_main
break *0x100000

# 单步执行
step
next
stepi
nexti

# 查看寄存器
info registers
info registers eip esp ebp

# 查看内存
x/10x $esp
x/10i $eip
x/s 0x1000

# 查看变量
print current_process
print process_table[0]

# 继续执行
continue
```

### 5.3 打印调试信息

```c
// 调试宏
#ifdef DEBUG
#define DEBUG_PRINT(fmt, ...) \
    kprintf("[DEBUG] %s:%d: " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__)
#else
#define DEBUG_PRINT(fmt, ...)
#endif

// 使用示例
void process_create(void (*entry)()) {
    DEBUG_PRINT("Creating process with entry %p", entry);
    // ...
    DEBUG_PRINT("Process created with PID %d", process->pid);
}
```

### 5.4 内存检查

```c
// 检查内存泄漏
void memory_check() {
    uint32_t free_pages = mm_get_free_pages();
    uint32_t total_pages = mm_get_total_pages();
    kprintf("Memory: %d/%d pages free\n", free_pages, total_pages);

    if (free_pages < total_pages / 10) {
        kprintf("WARNING: Low memory!\n");
    }
}

// 检查栈溢出
#define STACK_CANARY 0xDEADBEEF

void process_check_stack(process_t *process) {
    uint32_t *stack_bottom = (uint32_t *)process->kernel_stack;
    if (*stack_bottom != STACK_CANARY) {
        kprintf("Stack overflow detected in process %d!\n", process->pid);
    }
}
```

## 6. 常见问题

### 6.1 编译错误

**问题**: `fatal error: stdio.h: No such file or directory`
**解决**: 添加 `-ffreestanding -nostdinc` 编译选项

**问题**: `undefined reference to 'memcpy'`
**解决**: 实现自己的 `memcpy` 函数

**问题**: `relocation truncated to fit: R_386_PC32`
**解决**: 使用 `-m32` 编译选项

### 6.2 运行错误

**问题**: QEMU 黑屏
**解决**: 检查引导扇区是否正确加载，检查内核入口地址

**问题**: 重启循环
**解决**: 检查中断处理，检查栈设置

**问题**: 页面错误
**解决**: 检查分页设置，检查内存映射

### 6.3 调试困难

**问题**: 无法设置断点
**解决**: 确保编译时包含调试信息 (`-g`)

**问题**: 变量值显示 `<optimized out>`
**解决**: 使用 `-O0` 编译选项

## 7. 最佳实践

### 7.1 代码规范

- 使用 4 空格缩进
- 函数名使用小写字母和下划线
- 常量使用大写字母和下划线
- 结构体名使用 `_t` 后缀
- 每个函数添加注释说明

### 7.2 版本控制

- 使用 Git 管理代码
- 每个功能一个分支
- 提交前测试代码
- 编写清晰的提交信息

### 7.3 文档习惯

- 代码中添加注释
- 修改后更新文档
- 记录遇到的问题
- 分享学习心得

## 8. 学习建议

### 8.1 学习路径

1. **第一周**: 引导加载
   - 理解 BIOS 启动过程
   - 学习实模式汇编
   - 实现引导扇区

2. **第二周**: 内核初始化
   - 学习保护模式
   - 实现 GDT/IDT
   - 学习中断处理

3. **第三周**: 内存管理
   - 理解分页机制
   - 实现物理内存管理
   - 实现虚拟内存

4. **第四周**: 进程管理
   - 理解进程概念
   - 实现进程创建
   - 实现进程调度

### 8.2 学习方法

1. **先理解，后实现**
   - 阅读文档理解概念
   - 看示例代码理解实现
   - 自己动手实现

2. **循序渐进**
   - 从简单开始
   - 逐步增加复杂度
   - 不要急于求成

3. **多调试**
   - 使用 GDB 调试
   - 打印调试信息
   - 观察运行状态

4. **多实践**
   - 修改代码实验
   - 添加新功能
   - 解决实际问题

### 8.3 参考资源

- [OSDev Wiki](https://wiki.osdev.org)
- [xv6 源码](https://github.com/mit-pdos/xv6-public)
- [MIT 6.S081 课程](https://pdos.csail.mit.edu/6.828/2020/)
- [Intel 手册](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
