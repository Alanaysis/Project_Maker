# 安装指南

## 系统要求

### 操作系统

- Linux（推荐 Ubuntu 20.04+, CentOS 7+, Fedora 30+）
- 内核版本 >= 3.10

### 编译器

- GCC >= 7.0
- 或 Clang >= 6.0

### 依赖库

- libnetfilter_queue
- libpcap
- pthread

## 安装步骤

### 1. 安装依赖

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    libnetfilter-queue-dev \
    libpcap-dev \
    pkg-config
```

#### CentOS/RHEL

```bash
sudo yum install -y \
    gcc \
    make \
    libnetfilter_queue-devel \
    libpcap-devel \
    pkgconfig
```

#### Fedora

```bash
sudo dnf install -y \
    gcc \
    make \
    libnetfilter_queue-devel \
    libpcap-devel \
    pkgconfig
```

#### Arch Linux

```bash
sudo pacman -S \
    base-devel \
    libnetfilter_queue \
    libpcap
```

### 2. 验证依赖

```bash
# 检查编译器
gcc --version

# 检查依赖库
pkg-config --libs libnetfilter_queue
pkg-config --libs libpcap
```

### 3. 获取源代码

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/firewall.git
cd firewall

# 或者解压源代码包
tar -xzf firewall-1.0.0.tar.gz
cd firewall-1.0.0
```

### 4. 编译

#### 使用构建脚本

```bash
# 给脚本添加执行权限
chmod +x build.sh

# 编译所有内容
./build.sh build
```

#### 使用 Makefile

```bash
# 编译所有内容
make

# 编译调试版本
make debug

# 编译发布版本
make release
```

### 5. 运行测试

```bash
# 使用构建脚本
./build.sh test

# 或者使用 Makefile
make test
```

### 6. 安装（可选）

```bash
# 安装到 /usr/local/bin
sudo make install

# 或者手动安装
sudo cp build/firewall /usr/local/bin/
```

### 7. 配置

#### 创建配置目录

```bash
sudo mkdir -p /etc/firewall
```

#### 复制配置文件

```bash
sudo cp configs/default.conf /etc/firewall/firewall.conf
```

#### 编辑配置文件

```bash
sudo nano /etc/firewall/firewall.conf
```

### 8. 运行

```bash
# 直接运行
sudo ./build/firewall -i eth0 -c configs/default.conf

# 或者安装后运行
sudo firewall -i eth0 -c /etc/firewall/firewall.conf
```

## 故障排除

### 问题 1：编译错误

**错误信息**：
```
fatal error: libnetfilter_queue/libnetfilter_queue.h: No such file or directory
```

**解决方案**：
```bash
sudo apt-get install libnetfilter-queue-dev
```

### 问题 2：权限错误

**错误信息**：
```
Permission denied
```

**解决方案**：
```bash
sudo ./build/firewall -i eth0 -c configs/default.conf
```

### 问题 3：接口不存在

**错误信息**：
```
Interface eth0 not found
```

**解决方案**：
```bash
# 查看可用接口
ip link show

# 或者
ifconfig -a

# 使用正确的接口名称
sudo ./build/firewall -i ens33 -c configs/default.conf
```

### 问题 4：内核模块缺失

**错误信息**：
```
nf_queue: no such module
```

**解决方案**：
```bash
sudo modprobe nfnetlink_queue
sudo modprobe nf_conntrack
```

### 问题 5：端口被占用

**错误信息**：
```
Address already in use
```

**解决方案**：
```bash
# 查找占用端口的进程
sudo netstat -tulnp | grep :80

# 停止占用端口的进程
sudo kill <PID>
```

## 卸载

### 1. 停止防火墙

```bash
# 如果以后台模式运行
sudo killall firewall
```

### 2. 删除文件

```bash
# 删除可执行文件
sudo rm -f /usr/local/bin/firewall

# 删除配置文件
sudo rm -rf /etc/firewall

# 删除日志文件
sudo rm -f /var/log/firewall.log
```

### 3. 清理编译文件

```bash
make clean
```

## 开发环境设置

### 1. IDE 配置

#### VS Code

安装 C/C++ 扩展：

```bash
code --install-extension ms-vscode.cpptools
```

创建 `.vscode/c_cpp_properties.json`：

```json
{
    "configurations": [
        {
            "name": "Linux",
            "includePath": [
                "${workspaceFolder}/**",
                "/usr/include",
                "/usr/local/include"
            ],
            "defines": [],
            "compilerPath": "/usr/bin/gcc",
            "cStandard": "c11",
            "cppStandard": "c++17",
            "intelliSenseMode": "linux-gcc-x64"
        }
    ],
    "version": 4
}
```

#### CLion

1. 打开项目目录
2. 配置 CMake（如果使用 CMake）
3. 配置工具链

### 2. 调试配置

#### GDB

```bash
# 编译调试版本
make debug

# 启动 GDB
sudo gdb ./build/firewall

# 常用命令
(gdb) break main
(gdb) run -i eth0 -c configs/default.conf
(gdb) next
(gdb) print variable
(gdb) backtrace
```

#### Valgrind

```bash
# 检测内存泄漏
sudo valgrind --leak-check=full ./build/firewall -i eth0 -c configs/default.conf
```

### 3. 代码分析

#### cppcheck

```bash
# 安装
sudo apt-get install cppcheck

# 运行分析
cppcheck --enable=all src/ include/
```

#### clang-tidy

```bash
# 安装
sudo apt-get install clang-tidy

# 运行分析
clang-tidy src/*.c -- -I include/
```

## 性能优化

### 1. 编译优化

```bash
# 使用 -O2 优化
make CFLAGS="-O2"

# 使用 -O3 优化（更激进）
make CFLAGS="-O3"

# 针对特定架构优化
make CFLAGS="-O2 -march=native"
```

### 2. 运行时优化

- 使用更快的网络接口
- 调整内核参数
- 使用 DPDK（高级）

## 安全注意事项

### 1. 权限管理

- 防火墙需要 root 权限运行
- 考虑使用 capabilities 精细控制权限
- 避免以 root 身份运行不必要的服务

### 2. 配置安全

- 仔细审查规则配置
- 避免过于宽松的规则
- 定期更新规则

### 3. 日志安全

- 保护日志文件权限
- 定期轮转日志
- 监控异常日志

## 更多资源

- [项目文档](docs/)
- [快速开始](QUICKSTART.md)
- [学习笔记](LEARNING_NOTES.md)
- [更新日志](CHANGELOG.md)
