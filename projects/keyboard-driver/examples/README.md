# 键盘驱动示例

本目录包含键盘驱动的各种示例代码。

## 示例文件

### 1. example.c - 用户空间示例

这是用户空间的示例代码，演示了键盘驱动的基本功能。

**功能**:
- 基本使用示例
- 去抖算法示例
- 矩阵扫描示例
- 中断处理示例
- 完整工作流程示例

**编译运行**:
```bash
# 编译
make example

# 运行
./build/keyboard_example
```

**学习要点**:
- 理解键盘驱动的基本架构
- 学习去抖算法的实现
- 掌握事件处理机制

### 2. kernel_module_example.c - 内核模块示例

这是一个Linux内核模块示例，展示真正的键盘驱动实现。

**功能**:
- GPIO配置和控制
- 矩阵键盘扫描
- 中断处理
- 输入设备注册
- 去抖定时器

**注意**: 这是一个教学示例，需要内核开发环境才能编译。

**编译环境要求**:
```bash
# 安装内核头文件
sudo apt install linux-headers-$(uname -r)

# 安装构建工具
sudo apt install build-essential
```

**编译命令**:
```bash
# 创建Makefile
cat > Makefile << 'EOF'
obj-m += keyboard_module.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
EOF

# 编译模块
make
```

**加载卸载**:
```bash
# 加载模块
sudo insmod keyboard_module.ko

# 查看模块信息
lsmod | grep keyboard

# 查看内核日志
dmesg | tail

# 卸载模块
sudo rmmod keyboard_module
```

**学习要点**:
- 理解Linux内核模块开发
- 学习GPIO编程
- 掌握中断处理机制
- 了解输入子系统

## 示例对比

| 特性 | 用户空间示例 | 内核模块示例 |
|------|-------------|-------------|
| 运行环境 | 用户空间 | 内核空间 |
| 编译难度 | 简单 | 复杂 |
| 调试难度 | 简单 | 困难 |
| 性能 | 一般 | 优秀 |
| 硬件访问 | 模拟 | 直接 |
| 学习价值 | 入门 | 进阶 |

## 学习路径

### 初级阶段
1. 阅读 `example.c` 代码
2. 理解每个示例的功能
3. 编译运行示例
4. 修改代码实验

### 中级阶段
1. 阅读 `kernel_module_example.c` 代码
2. 理解内核模块结构
3. 学习GPIO和中断编程
4. 尝试编译内核模块

### 高级阶段
1. 修改内核模块代码
2. 添加新功能
3. 优化性能
4. 移植到实际硬件

## 常见问题

### Q: 用户空间示例无法运行？
A: 检查编译是否成功，确保所有依赖都已安装。

### Q: 内核模块编译失败？
A: 确保安装了正确的内核头文件，检查Makefile格式。

### Q: 如何在实际硬件上运行？
A: 需要修改GPIO引脚定义，适配具体的硬件平台。

### Q: 如何调试内核模块？
A: 使用 `printk` 输出日志，通过 `dmesg` 查看。

## 扩展阅读

- [Linux内核模块编程指南](https://tldp.org/LDP/lkmpg/2.6/html/)
- [Linux GPIO接口](https://www.kernel.org/doc/html/latest/driver-api/gpio/)
- [Linux输入子系统](https://www.kernel.org/doc/html/latest/driver-api/input.html)
- [Linux中断处理](https://www.kernel.org/doc/html/latest/core-api/irq/irq-domain.html)

## 贡献

欢迎提交改进建议和新的示例代码！
