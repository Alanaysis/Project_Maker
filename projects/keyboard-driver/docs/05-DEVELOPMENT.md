# 开发手册

## 1. 环境搭建

### 1.1 系统要求

**操作系统**:
- Linux（推荐Ubuntu 20.04+）
- macOS（测试）
- Windows（WSL2）

**开发工具**:
- GCC编译器（9.0+）
- Make构建工具
- GDB调试器
- Git版本控制

**依赖库**:
- 标准C库
- POSIX线程库（可选）

### 1.2 安装步骤

**Ubuntu/Debian**:
```bash
# 更新包管理器
sudo apt update

# 安装编译工具
sudo apt install build-essential gcc make

# 安装调试工具
sudo apt install gdb

# 安装版本控制
sudo apt install git
```

**CentOS/RHEL**:
```bash
# 安装开发工具组
sudo yum groupinstall "Development Tools"

# 安装GCC
sudo yum install gcc

# 安装Make
sudo yum install make
```

**macOS**:
```bash
# 安装Xcode命令行工具
xcode-select --install

# 安装Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装GCC
brew install gcc
```

### 1.3 项目克隆

```bash
# 克隆项目
git clone https://github.com/your-username/keyboard-driver.git

# 进入项目目录
cd keyboard-driver

# 查看项目结构
ls -la
```

### 1.4 编译项目

```bash
# 查看可用目标
make help

# 编译所有目标
make

# 只编译测试
make test

# 只编译示例
make example

# 清理构建文件
make clean
```

## 2. 项目结构详解

### 2.1 目录结构

```
keyboard-driver/
├── README.md                 # 项目说明
├── Makefile                  # 构建脚本
├── docs/                     # 文档目录
│   ├── 01-RESEARCH.md       # 市场调研
│   ├── 02-REQUIREMENTS.md   # 需求分析
│   ├── 03-DESIGN.md         # 技术设计
│   ├── 04-PRODUCT.md        # 产品思维
│   └── 05-DEVELOPMENT.md    # 开发手册
├── src/                      # 源代码
│   ├── keyboard_driver.c    # 主驱动文件
│   ├── matrix_scanner.c     # 矩阵扫描模块
│   ├── interrupt_handler.c  # 中断处理模块
│   ├── keymap.c             # 按键映射模块
│   ├── debounce.c           # 去抖模块
│   └── input_event.c        # 输入事件模块
├── include/                  # 头文件
│   └── keyboard.h           # 主头文件
├── tests/                    # 测试文件
│   └── test_keyboard.c      # 单元测试
└── examples/                 # 使用示例
    └── example.c            # 示例代码
```

### 2.2 文件说明

**头文件 (include/keyboard.h)**:
- 定义所有数据结构
- 声明所有公共接口
- 定义常量和宏

**源文件 (src/)**:
- `keyboard_driver.c`: 主驱动逻辑，初始化和协调各模块
- `matrix_scanner.c`: 矩阵扫描实现
- `interrupt_handler.c`: 中断处理实现
- `debounce.c`: 去抖算法实现
- `input_event.c`: 输入事件系统实现

**测试文件 (tests/)**:
- `test_keyboard.c`: 单元测试，覆盖所有核心功能

**示例文件 (examples/)**:
- `example.c`: 使用示例，演示各种功能

## 3. 核心模块解析

### 3.1 主驱动模块 (keyboard_driver.c)

**功能**:
- 初始化键盘设备
- 协调各模块工作
- 管理事件队列

**关键函数**:
```c
// 初始化键盘设备
int keyboard_init(keyboard_dev_t *dev);

// 处理中断
int keyboard_interrupt_handler(keyboard_dev_t *dev);

// 报告事件
int keyboard_report_event(keyboard_dev_t *dev, key_event_t *event);
```

**实现要点**:
- 参数验证
- 状态管理
- 错误处理

### 3.2 矩阵扫描模块 (matrix_scanner.c)

**功能**:
- 扫描键盘矩阵
- 检测按键状态
- 检测按键变化

**关键函数**:
```c
// 完整矩阵扫描
int matrix_scan_full(matrix_t *matrix);

// 检测变化
int matrix_detect_changes(const matrix_t *matrix, key_event_t *events, int max_events);
```

**实现要点**:
- 行列扫描
- 状态保存
- 变化检测

### 3.3 中断处理模块 (interrupt_handler.c)

**功能**:
- 初始化中断
- 处理中断事件
- 中断统计

**关键函数**:
```c
// 初始化中断
int interrupt_init(void);

// 中断服务程序
int interrupt_service_routine(keyboard_dev_t *dev);

// 模拟中断
int interrupt_simulate_trigger(keyboard_dev_t *dev);
```

**实现要点**:
- 快速响应
- 最小化处理
- 统计信息

### 3.4 去抖模块 (debounce.c)

**功能**:
- 实现多种去抖算法
- 管理按键状态
- 去抖参数配置

**关键函数**:
```c
// 初始化去抖器
int debounce_init(debounce_type_t type, uint32_t debounce_time);

// 去抖处理
bool debounce_process(uint8_t row, uint8_t col, bool pressed, uint32_t current_time);

// 获取状态
key_state_t debounce_get_state(uint8_t row, uint8_t col);
```

**实现要点**:
- 多种算法支持
- 状态机管理
- 时间管理

### 3.5 输入事件模块 (input_event.c)

**功能**:
- 管理事件队列
- 事件分发
- 事件回调

**关键函数**:
```c
// 初始化事件系统
int input_event_init(void);

// 注册处理器
int input_event_register_handler(event_handler_t handler);

// 报告事件
int input_event_report(const key_event_t *event);
```

**实现要点**:
- 队列管理
- 处理器注册
- 事件分发

## 4. 开发流程

### 4.1 功能开发流程

**步骤**:
1. 理解需求
2. 设计接口
3. 实现功能
4. 编写测试
5. 代码审查
6. 文档更新

**示例**:
```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 实现功能
# 编辑 src/new_feature.c
# 编辑 include/keyboard.h

# 3. 编写测试
# 编辑 tests/test_new_feature.c

# 4. 运行测试
make test
./build/keyboard_test

# 5. 提交代码
git add .
git commit -m "feat: add new feature"

# 6. 推送分支
git push origin feature/new-feature
```

### 4.2 调试流程

**使用GDB调试**:
```bash
# 编译带调试信息
make CFLAGS="-Wall -Wextra -g -O0"

# 启动GDB
gdb ./build/keyboard_test

# 设置断点
(gdb) break keyboard_init
(gdb) break keyboard_scan

# 运行程序
(gdb) run

# 单步执行
(gdb) step
(gdb) next

# 查看变量
(gdb) print dev
(gdb) print dev.matrix.state

# 继续执行
(gdb) continue
```

**使用printf调试**:
```c
// 添加调试输出
printf("[DEBUG] %s: row=%d, col=%d\n", __func__, row, col);

// 条件编译
#ifdef DEBUG
printf("[DEBUG] Variable value: %d\n", value);
#endif
```

### 4.3 测试流程

**运行所有测试**:
```bash
make test
./build/keyboard_test
```

**运行特定测试**:
```bash
# 编辑测试文件，注释掉不需要的测试
# 然后编译运行
make test
./build/keyboard_test
```

**测试覆盖率**:
```bash
# 编译时添加覆盖率选项
make CFLAGS="-Wall -Wextra -g --coverage"
make LDFLAGS="--coverage"

# 运行测试
./build/keyboard_test

# 生成覆盖率报告
gcov src/*.c
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage-report
```

## 5. 编码规范

### 5.1 命名规范

**变量命名**:
- 使用小写字母和下划线
- 有意义的名字
- 避免缩写

```c
// 好的命名
int key_count;
uint32_t debounce_time;
matrix_t keyboard_matrix;

// 不好的命名
int kc;
uint32_t dt;
matrix_t m;
```

**函数命名**:
- 使用小写字母和下划线
- 动词开头
- 模块前缀

```c
// 好的命名
int keyboard_init(keyboard_dev_t *dev);
bool debounce_process(uint8_t row, uint8_t col, bool pressed, uint32_t time);

// 不好的命名
int init(keyboard_dev_t *dev);
bool process(uint8_t row, uint8_t col, bool pressed, uint32_t time);
```

**常量命名**:
- 使用大写字母和下划线
- 有意义的名字

```c
// 好的命名
#define MATRIX_ROWS     6
#define DEBOUNCE_MS     5
#define MAX_KEYS        84

// 不好的命名
#define ROWS            6
#define MS              5
#define MAX             84
```

### 5.2 代码风格

**缩进**:
- 使用4个空格缩进
- 不使用Tab
- 保持一致

**大括号**:
- 函数定义：大括号另起一行
- 控制语句：大括号另起一行
- 单行语句：可省略大括号

```c
// 函数定义
int keyboard_init(keyboard_dev_t *dev)
{
    // 函数体
}

// 控制语句
if (condition)
{
    // 语句
}

// 单行语句
if (condition)
    return true;
```

**空格**:
- 操作符前后加空格
- 逗号后加空格
- 括号内不加空格

```c
// 好的风格
int result = a + b;
function(arg1, arg2);
if (condition)

// 不好的风格
int result=a+b;
function(arg1,arg2);
if(condition)
```

### 5.3 注释规范

**文件注释**:
```c
/**
 * @file keyboard_driver.c
 * @brief 键盘驱动主文件
 * @author Your Name
 * @date 2024-01-01
 */
```

**函数注释**:
```c
/**
 * @brief 初始化键盘设备
 * @param dev 键盘设备指针
 * @return 成功返回KB_OK，失败返回错误码
 */
int keyboard_init(keyboard_dev_t *dev);
```

**行内注释**:
```c
// 检查参数有效性
if (dev == NULL) {
    return KB_ERR_INIT;
}
```

### 5.4 错误处理

**错误码定义**:
```c
#define KB_OK           0       // 成功
#define KB_ERR_INIT     -1      // 初始化错误
#define KB_ERR_SCAN     -2      // 扫描错误
#define KB_ERR_IRQ      -3      // 中断错误
#define KB_ERR_MAP      -4      // 映射错误
```

**错误处理模式**:
```c
int function()
{
    int ret;
    
    // 调用可能失败的函数
    ret = some_function();
    if (ret != KB_OK) {
        // 记录错误
        printf("[ERROR] %s failed: %d\n", __func__, ret);
        return ret;
    }
    
    return KB_OK;
}
```

## 6. 性能优化

### 6.1 编译优化

**优化级别**:
```bash
# 调试版本（无优化）
make CFLAGS="-Wall -Wextra -g -O0"

# 发布版本（优化）
make CFLAGS="-Wall -Wextra -O2"

# 最大优化
make CFLAGS="-Wall -Wextra -O3"
```

**架构特定优化**:
```bash
# 针对当前CPU优化
make CFLAGS="-Wall -Wextra -O2 -march=native"

# 针对特定架构
make CFLAGS="-Wall -Wextra -O2 -march=x86-64"
```

### 6.2 代码优化

**减少函数调用**:
```c
// 优化前
for (int i = 0; i < count; i++) {
    process(array[i]);
}

// 优化后
for (int i = 0; i < count; i++) {
    // 内联处理
    array[i] = array[i] * 2 + 1;
}
```

**减少内存访问**:
```c
// 优化前
for (int i = 0; i < count; i++) {
    dev->matrix.state[i] = 0;
}

// 优化后
uint8_t *state = dev->matrix.state;
for (int i = 0; i < count; i++) {
    state[i] = 0;
}
```

**使用位操作**:
```c
// 优化前
if (value % 2 == 0) {
    // 偶数
}

// 优化后
if ((value & 1) == 0) {
    // 偶数
}
```

### 6.3 内存优化

**结构体对齐**:
```c
// 优化前
typedef struct {
    char a;     // 1字节
    int b;      // 4字节
    char c;     // 1字节
} bad_struct_t;  // 总共12字节（有填充）

// 优化后
typedef struct {
    int b;      // 4字节
    char a;     // 1字节
    char c;     // 1字节
} good_struct_t;  // 总共8字节
```

**减少动态分配**:
```c
// 优化前
int *array = malloc(count * sizeof(int));
// 使用array
free(array);

// 优化后
int array[MAX_COUNT];  // 栈上分配
// 使用array
```

## 7. 常见问题

### 7.1 编译错误

**问题**: 找不到头文件
```
fatal error: keyboard.h: No such file or directory
```

**解决**:
```bash
# 检查include路径
make CFLAGS="-Wall -Wextra -g -I./include"
```

**问题**: 链接错误
```
undefined reference to `keyboard_init'
```

**解决**:
```bash
# 确保所有源文件都编译了
make clean
make
```

### 7.2 运行错误

**问题**: 段错误 (Segmentation fault)
```
Segmentation fault (core dumped)
```

**解决**:
```bash
# 使用GDB调试
gdb ./build/keyboard_test
(gdb) run
(gdb) bt  # 查看调用栈
```

**问题**: 内存泄漏
```
Memory leak detected
```

**解决**:
```bash
# 使用Valgrind检查
valgrind --leak-check=full ./build/keyboard_test
```

### 7.3 测试失败

**问题**: 测试断言失败
```
FAIL: keyboard_init should return KB_OK
```

**解决**:
```bash
# 检查测试代码
# 确保初始化正确
# 检查返回值
```

## 8. 最佳实践

### 8.1 代码质量

**代码审查**:
- 每次提交前自我审查
- 使用静态分析工具
- 遵循编码规范

**测试覆盖**:
- 单元测试覆盖所有函数
- 集成测试覆盖关键路径
- 边界条件测试

**文档完整**:
- 函数注释完整
- 使用示例齐全
- 错误说明清晰

### 8.2 版本控制

**提交规范**:
```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建过程或辅助工具的变动
```

**分支管理**:
- `main`: 稳定版本
- `develop`: 开发版本
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复

### 8.3 持续集成

**GitHub Actions示例**:
```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build
      run: make
    - name: Test
      run: make test && ./build/keyboard_test
```

## 9. 扩展开发

### 9.1 添加新模块

**步骤**:
1. 创建源文件 `src/new_module.c`
2. 创建头文件 `include/new_module.h`
3. 更新 `Makefile`
4. 编写测试
5. 更新文档

**示例**:
```c
// include/new_module.h
#ifndef NEW_MODULE_H
#define NEW_MODULE_H

int new_module_init(void);
int new_module_process(void);

#endif

// src/new_module.c
#include "../include/new_module.h"

int new_module_init(void)
{
    // 初始化代码
    return 0;
}

int new_module_process(void)
{
    // 处理代码
    return 0;
}
```

### 9.2 添加新算法

**步骤**:
1. 在相应模块中添加函数
2. 更新头文件声明
3. 编写测试用例
4. 更新文档

**示例**:
```c
// 在 debounce.c 中添加
bool debounce_new_algorithm(uint8_t row, uint8_t col, bool pressed, uint32_t time)
{
    // 新算法实现
    return false;
}
```

### 9.3 添加新配置

**步骤**:
1. 定义配置结构
2. 添加配置加载函数
3. 更新初始化函数
4. 编写配置文件

**示例**:
```c
typedef struct {
    int rows;
    int cols;
    int debounce_time;
    debounce_type_t debounce_type;
} keyboard_config_t;

int keyboard_load_config(const char *filename, keyboard_config_t *config);
```

## 10. 资源链接

### 10.1 官方文档

- [GCC文档](https://gcc.gnu.org/onlinedocs/)
- [Make文档](https://www.gnu.org/software/make/manual/)
- [GDB文档](https://sourceware.org/gdb/documentation/)
- [Linux内核文档](https://www.kernel.org/doc/html/latest/)

### 10.2 学习资源

- [C语言教程](https://www.runoob.com/cprogramming/c-tutorial.html)
- [Linux系统编程](https://www.oreilly.com/library/view/linux-system-programming/9781491903896/)
- [嵌入式开发](https://www.oreilly.com/library/view/embedded-systems-programming/9781491903896/)

### 10.3 工具资源

- [Valgrind](https://valgrind.org/)
- [AddressSanitizer](https://github.com/google/sanitizers)
- [Cppcheck](http://cppcheck.sourceforge.net/)

### 10.4 社区资源

- [Stack Overflow](https://stackoverflow.com/)
- [GitHub](https://github.com/)
- [Reddit](https://www.reddit.com/r/embedded/)
