# 快速开始指南

## 1. 环境准备

### 1.1 安装依赖

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y build-essential libnetfilter-queue-dev libpcap-dev
```

**CentOS/RHEL**:
```bash
sudo yum install -y gcc make libnetfilter_queue-devel libpcap-devel
```

### 1.2 验证环境

```bash
gcc --version
pkg-config --libs libnetfilter_queue
pkg-config --libs libpcap
```

## 2. 编译项目

### 2.1 使用构建脚本

```bash
# 给脚本添加执行权限
chmod +x build.sh

# 编译所有内容
./build.sh build

# 或者只编译主程序
./build.sh
```

### 2.2 使用 Makefile

```bash
# 编译所有内容
make

# 只编译主程序
make all

# 编译并运行测试
make test

# 清理构建文件
make clean
```

## 3. 运行防火墙

### 3.1 查看帮助

```bash
./build/firewall --help
```

输出：
```
Usage: ./build/firewall [OPTIONS]

Options:
  -c, --config FILE    Configuration file path
  -i, --interface IF   Network interface
  -l, --log FILE       Log file path
  -v, --verbose        Verbose output
  -d, --daemon         Run as daemon
  -h, --help           Show this help
  -V, --version        Show version
```

### 3.2 使用配置文件运行

```bash
# 使用默认配置
sudo ./build/firewall -i eth0 -c configs/default.conf

# 使用自定义配置
sudo ./build/firewall -i wlan0 -c my_rules.conf

# 详细输出模式
sudo ./build/firewall -i eth0 -c configs/default.conf -v

# 指定日志文件
sudo ./build/firewall -i eth0 -c configs/default.conf -l /var/log/firewall.log
```

### 3.3 后台运行

```bash
sudo ./build/firewall -i eth0 -c configs/default.conf -d
```

## 4. 运行测试

### 4.1 运行所有测试

```bash
./build.sh test
```

或者：

```bash
make test
```

### 4.2 运行单个测试

```bash
# 包解析测试
./build/test_packet

# 规则引擎测试
./build/test_rules

# 状态管理测试
./build/test_state

# IDS 测试
./build/test_ids
```

## 5. 运行示例

```bash
# 简单过滤示例
./build/simple_filter
```

## 6. 配置规则

### 6.1 规则格式

```
ACTION PROTOCOL [条件...]
```

### 6.2 动作类型

- `ACCEPT` - 允许数据包
- `DROP` - 丢弃数据包
- `REJECT` - 拒绝数据包（发送 ICMP 错误）
- `LOG` - 仅记录日志

### 6.3 协议类型

- `tcp` - TCP 协议
- `udp` - UDP 协议
- `icmp` - ICMP 协议
- `all` - 所有协议

### 6.4 匹配条件

- `src_ip IP/MASK` - 源 IP 地址
- `dst_ip IP/MASK` - 目的 IP 地址
- `src_port PORT` - 源端口
- `dst_port PORT` - 目的端口
- `ESTABLISHED` - 已建立的连接

### 6.5 示例配置

```conf
# 允许 HTTP
ACCEPT tcp dst_port 80

# 允许 HTTPS
ACCEPT tcp dst_port 443

# 允许 DNS
ACCEPT udp dst_port 53

# 允许 SSH 从内部网络
ACCEPT tcp src_ip 192.168.1.0/24 dst_port 22

# 允许已建立的连接
ACCEPT tcp ESTABLISHED

# 允许本地回环
ACCEPT all src_ip 127.0.0.0/8

# 默认拒绝
DROP all all
```

## 7. 调试

### 7.1 使用 GDB

```bash
# 编译调试版本
./build.sh build

# 启动 GDB
sudo gdb ./build/firewall

# 在 GDB 中运行
(gdb) run -i eth0 -c configs/default.conf
```

### 7.2 使用 Valgrind

```bash
# 检测内存泄漏
sudo valgrind --leak-check=full ./build/firewall -i eth0 -c configs/default.conf
```

## 8. 常见问题

### 8.1 权限问题

**问题**: `Permission denied`

**解决**: 使用 `sudo` 运行防火墙

```bash
sudo ./build/firewall -i eth0 -c configs/default.conf
```

### 8.2 依赖缺失

**问题**: `libnetfilter_queue not found`

**解决**: 安装开发库

```bash
sudo apt-get install libnetfilter-queue-dev
```

### 8.3 接口不存在

**问题**: `Interface eth0 not found`

**解决**: 查看可用接口

```bash
ip link show
# 或
ifconfig -a
```

然后使用正确的接口名称。

### 8.4 编译错误

**问题**: 编译时出现错误

**解决**:
1. 确保安装了所有依赖
2. 检查 GCC 版本（需要 >= 7.0）
3. 查看错误信息并修复

## 9. 学习建议

### 9.1 阅读代码

1. 从 `main.c` 开始，了解程序入口
2. 阅读 `packet.c`，理解包解析
3. 阅读 `rules.c`，理解规则匹配
4. 阅读 `state.c`，理解状态检测
5. 阅读 `ids.c`，理解入侵检测

### 9.2 修改和实验

1. 尝试添加新的规则
2. 修改阈值参数
3. 添加新的检测功能
4. 优化性能

### 9.3 阅读文档

1. 阅读 `docs/` 目录下的文档
2. 查看 `LEARNING_NOTES.md` 记录学习笔记
3. 参考 RFC 文档理解协议

## 10. 下一步

完成基本学习后，可以尝试：

1. 添加 IPv6 支持
2. 实现 NAT 功能
3. 添加应用层过滤
4. 优化规则匹配算法
5. 添加 Web 管理界面
