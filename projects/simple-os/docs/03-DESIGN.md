# 技术设计文档

## 1. 系统架构

### 1.1 整体架构

```
+------------------------------------------+
|              用户程序                      |
+------------------------------------------+
|              系统调用层                     |
+------------------------------------------+
|         进程管理  |  文件系统               |
+------------------------------------------+
|              内存管理                       |
+------------------------------------------+
|         中断处理  |  设备驱动               |
+------------------------------------------+
|              引导加载                       |
+------------------------------------------+
|              硬件                          |
+------------------------------------------+
```

### 1.2 启动流程

```
BIOS
  ↓ (加载引导扇区到 0x7C00)
Boot Sector (boot.asm)
  ↓ (设置保护模式，加载内核)
Loader (loader.asm)
  ↓ (跳转到内核入口)
Kernel Entry (kernel/main.c)
  ↓ (初始化各子系统)
  ├→ 初始化 GDT
  ├→ 初始化 IDT
  ├→ 初始化内存管理
  ├→ 初始化进程管理
  ├→ 初始化设备驱动
  └→ 启动第一个进程
```

### 1.3 内存布局

```
物理地址空间:
+------------------+ 0xFFFFFFFF
|     保留区域      |
+------------------+ 0xF0000000
|     设备映射      |
+------------------+ 0x00100000 (1MB)
|     内核代码      |
+------------------+ 0x00010000 (64KB)
|     加载器        |
+------------------+ 0x00007C00
|     引导扇区      |
+------------------+ 0x00000000
```

## 2. 模块设计

### 2.1 引导模块 (boot/)

**职责**:
- 加载内核到内存
- 切换到保护模式
- 跳转到内核入口

**文件**:
- `boot.asm`: 主引导扇区，512 字节
- `loader.asm`: 加载器，加载内核并切换模式

**关键数据结构**:
```nasm
; GDT 条目结构
struc gdt_entry
    .limit_low:  resw 1    ; 段限长低 16 位
    .base_low:   resw 1    ; 基地址低 16 位
    .base_mid:   resb 1    ; 基地址中间 8 位
    .access:     resb 1    ; 访问字节
    .granularity: resb 1   ; 粒度字节
    .base_high:  resb 1    ; 基地址高 8 位
endstruc
```

### 2.2 内核模块 (kernel/)

**职责**:
- 内核主入口
- 初始化各子系统
- 提供核心服务

**文件**:
- `main.c`: 内核主函数
- `gdt.c`: GDT 初始化
- `idt.c`: IDT 初始化
- `isr.c`: 中断服务程序
- `irq.c`: 硬件中断请求
- `timer.c`: 定时器

**关键数据结构**:
```c
// GDT 条目
typedef struct {
    uint16_t limit_low;     // 段限长低 16 位
    uint16_t base_low;      // 基地址低 16 位
    uint8_t  base_middle;   // 基地址中间 8 位
    uint8_t  access;        // 访问字节
    uint8_t  granularity;   // 粒度字节
    uint8_t  base_high;     // 基地址高 8 位
} __attribute__((packed)) gdt_entry_t;

// IDT 条目
typedef struct {
    uint16_t base_low;      // 基地址低 16 位
    uint16_t selector;      // 段选择子
    uint8_t  zero;          // 保留
    uint8_t  flags;         // 标志
    uint16_t base_high;     // 基地址高 16 位
} __attribute__((packed)) idt_entry_t;

// 中断帧
typedef struct {
    uint32_t eip;
    uint32_t cs;
    uint32_t eflags;
    uint32_t esp;
    uint32_t ss;
} interrupt_frame_t;
```

### 2.3 内存管理模块 (mm/)

**职责**:
- 物理内存管理
- 虚拟内存管理
- 内核堆分配

**文件**:
- `memory.c`: 物理内存管理
- `paging.c`: 分页管理
- `heap.c`: 内核堆管理

**关键数据结构**:
```c
// 页目录项
typedef struct {
    uint32_t present    : 1;   // 是否在内存中
    uint32_t rw         : 1;   // 读写权限
    uint32_t user       : 1;   // 用户/超级用户
    uint32_t accessed   : 1;   // 是否被访问
    uint32_t dirty      : 1;   // 是否被写入
    uint32_t unused     : 7;   // 保留
    uint32_t frame      : 20;  // 页帧地址
} page_directory_entry_t;

// 页表项
typedef struct {
    uint32_t present    : 1;
    uint32_t rw         : 1;
    uint32_t user       : 1;
    uint32_t accessed   : 1;
    uint32_t dirty      : 1;
    uint32_t unused     : 7;
    uint32_t frame      : 20;
} page_table_entry_t;

// 内存块头部
typedef struct block_header {
    uint32_t size;              // 块大小
    uint8_t  free;              // 是否空闲
    struct block_header *next;  // 下一个块
} block_header_t;
```

**关键接口**:
```c
// 物理内存管理
void mm_init(uint32_t total_memory);
uint32_t mm_alloc_page();
void mm_free_page(uint32_t page);

// 虚拟内存管理
void paging_init();
void page_map(uint32_t virtual, uint32_t physical, uint32_t flags);
void page_unmap(uint32_t virtual);

// 内核堆
void heap_init();
void *kmalloc(uint32_t size);
void kfree(void *ptr);
```

### 2.4 进程管理模块 (process/)

**职责**:
- 进程创建和销毁
- 进程调度
- 上下文切换

**文件**:
- `process.c`: 进程管理
- `scheduler.c`: 进程调度

**关键数据结构**:
```c
// 进程状态
typedef enum {
    PROCESS_READY,
    PROCESS_RUNNING,
    PROCESS_BLOCKED,
    PROCESS_ZOMBIE
} process_state_t;

// 进程控制块
typedef struct {
    uint32_t pid;               // 进程 ID
    process_state_t state;      // 进程状态
    uint32_t esp;               // 栈指针
    uint32_t ebp;               // 基址指针
    uint32_t eip;               // 指令指针
    uint32_t page_directory;    // 页目录
    uint32_t kernel_stack;      // 内核栈
    uint32_t priority;          // 优先级
    struct process *next;       // 下一个进程
} process_t;

// 进程队列
typedef struct {
    process_t *head;
    process_t *tail;
    uint32_t size;
} process_queue_t;
```

**关键接口**:
```c
// 进程管理
void process_init();
process_t *process_create(void (*entry_point)());
void process_destroy(process_t *process);
process_t *process_fork();

// 进程调度
void scheduler_init();
void schedule();
void yield();
void sleep();
void wake(process_t *process);
```

### 2.5 中断处理模块 (kernel/)

**职责**:
- 中断分发
- 异常处理
- 系统调用

**关键数据结构**:
```c
// 中断处理函数类型
typedef void (*interrupt_handler_t)(interrupt_frame_t *frame);

// 系统调用处理函数类型
typedef uint32_t (*syscall_handler_t)(uint32_t arg1, uint32_t arg2, uint32_t arg3);

// 系统调用表
typedef struct {
    syscall_handler_t handlers[256];
} syscall_table_t;
```

**关键接口**:
```c
// 中断处理
void interrupt_register(uint8_t num, interrupt_handler_t handler);
void interrupt_unregister(uint8_t num);

// 系统调用
void syscall_init();
void syscall_register(uint8_t num, syscall_handler_t handler);
uint32_t syscall_dispatch(uint32_t num, uint32_t arg1, uint32_t arg2, uint32_t arg3);
```

### 2.6 设备驱动模块 (drivers/)

**职责**:
- 屏幕输出
- 键盘输入

**文件**:
- `screen.c`: VGA 文本模式输出
- `keyboard.c`: 键盘驱动

**关键数据结构**:
```c
// VGA 颜色
typedef enum {
    COLOR_BLACK = 0,
    COLOR_BLUE = 1,
    COLOR_GREEN = 2,
    COLOR_CYAN = 3,
    COLOR_RED = 4,
    COLOR_MAGENTA = 5,
    COLOR_BROWN = 6,
    COLOR_LIGHT_GREY = 7,
    COLOR_DARK_GREY = 8,
    COLOR_LIGHT_BLUE = 9,
    COLOR_LIGHT_GREEN = 10,
    COLOR_LIGHT_CYAN = 11,
    COLOR_LIGHT_RED = 12,
    COLOR_LIGHT_MAGENTA = 13,
    COLOR_YELLOW = 14,
    COLOR_WHITE = 15
} vga_color_t;

// 屏幕状态
typedef struct {
    uint16_t *video_memory;
    uint8_t cursor_x;
    uint8_t cursor_y;
    uint8_t attribute;
} screen_state_t;

// 键盘缓冲区
typedef struct {
    char buffer[256];
    uint8_t head;
    uint8_t tail;
    uint8_t size;
} keyboard_buffer_t;
```

### 2.7 文件系统模块 (fs/)

**职责**:
- 文件管理
- 目录管理
- 磁盘 I/O

**文件**:
- `fs.c`: 简单文件系统

**关键数据结构**:
```c
// 文件类型
typedef enum {
    FILE_TYPE_REGULAR,
    FILE_TYPE_DIRECTORY
} file_type_t;

// 文件节点
typedef struct {
    char name[64];              // 文件名
    file_type_t type;           // 文件类型
    uint32_t size;              // 文件大小
    uint32_t permissions;       // 权限
    uint32_t created;           // 创建时间
    uint32_t modified;          // 修改时间
    uint8_t *data;              // 文件数据
    struct file_node *parent;   // 父目录
    struct file_node *children; // 子节点
    struct file_node *next;     // 下一个兄弟节点
} file_node_t;

// 文件描述符
typedef struct {
    file_node_t *file;          // 文件节点
    uint32_t position;          // 读写位置
    uint32_t flags;             // 打开标志
} file_descriptor_t;
```

## 3. 接口设计

### 3.1 系统调用接口

```c
// 系统调用号定义
#define SYS_EXIT    1
#define SYS_FORK    2
#define SYS_READ    3
#define SYS_WRITE   4
#define SYS_OPEN    5
#define SYS_CLOSE   6
#define SYS_CREATE  7
#define SYS_DELETE  8
#define SYS_SLEEP   9
#define SYS_YIELD   10

// 系统调用包装函数
uint32_t syscall(uint32_t num, uint32_t arg1, uint32_t arg2, uint32_t arg3);

// 用户空间 API
void exit(int status);
pid_t fork();
int read(int fd, void *buf, size_t count);
int write(int fd, const void *buf, size_t count);
int open(const char *pathname, int flags);
int close(int fd);
int create(const char *pathname, uint32_t permissions);
int delete(const char *pathname);
void sleep(uint32_t milliseconds);
void yield();
```

### 3.2 内核内部接口

```c
// 内存管理接口
void *kmalloc(uint32_t size);
void kfree(void *ptr);
void *kmalloc_aligned(uint32_t size);
void *kmalloc_physical(uint32_t size, uint32_t *physical);

// 进程管理接口
process_t *current_process;
process_t *process_create(void (*entry)());
void process_exit(int status);
pid_t process_fork();
void schedule();

// 文件系统接口
int fs_open(const char *path, int flags);
int fs_close(int fd);
int fs_read(int fd, void *buf, size_t count);
int fs_write(int fd, const void *buf, size_t count);
int fs_create(const char *path, uint32_t permissions);
int fs_delete(const char *path);

// 设备驱动接口
void screen_init();
void screen_putchar(char c);
void screen_puts(const char *str);
void screen_clear();
void screen_set_color(vga_color_t fg, vga_color_t bg);

void keyboard_init();
char keyboard_getchar();
int keyboard_available();
```

## 4. 错误处理

### 4.1 错误码定义

```c
#define SUCCESS         0
#define ERROR_NOMEM    -1
#define ERROR_INVAL    -2
#define ERROR_NOENT    -3
#define ERROR_EXIST    -4
#define ERROR_PERM     -5
#define ERROR_IO       -6
#define ERROR_NOSYS    -7
```

### 4.2 异常处理

```c
// 异常处理函数
void divide_by_zero_handler(interrupt_frame_t *frame);
void page_fault_handler(interrupt_frame_t *frame);
void general_protection_fault_handler(interrupt_frame_t *frame);

// 异常信息结构
typedef struct {
    uint32_t error_code;
    uint32_t eip;
    uint32_t cs;
    uint32_t eflags;
    const char *description;
} exception_info_t;
```

## 5. 并发控制

### 5.1 中断控制

```c
// 禁用中断
static inline void interrupt_disable() {
    asm volatile("cli");
}

// 启用中断
static inline void interrupt_enable() {
    asm volatile("sti");
}

// 保存并禁用中断
static inline uint32_t interrupt_save_disable() {
    uint32_t flags;
    asm volatile("pushfl; popl %0; cli" : "=r"(flags));
    return flags;
}

// 恢复中断状态
static inline void interrupt_restore(uint32_t flags) {
    asm volatile("pushl %0; popfl" : : "r"(flags));
}
```

### 5.2 临界区保护

```c
// 临界区宏
#define CRITICAL_SECTION_BEGIN() \
    uint32_t __flags = interrupt_save_disable()

#define CRITICAL_SECTION_END() \
    interrupt_restore(__flags)
```

## 6. 性能考虑

### 6.1 内存管理优化

- 使用位图管理物理内存
- 页表缓存
- 内存池预分配

### 6.2 调度优化

- 多级反馈队列
- 优先级继承
- 时间片动态调整

### 6.3 I/O 优化

- 缓冲区缓存
- 异步 I/O
- 批量处理

## 7. 测试策略

### 7.1 单元测试

- 每个模块独立测试
- Mock 外部依赖
- 覆盖核心功能

### 7.2 集成测试

- 模块间交互测试
- 端到端测试
- 性能测试

### 7.3 系统测试

- QEMU 自动化测试
- 边界条件测试
- 压力测试

## 8. 扩展性设计

### 8.1 模块化设计

- 清晰的模块边界
- 标准化接口
- 插件式架构

### 8.2 配置化

- 编译时配置
- 运行时配置
- 动态加载
