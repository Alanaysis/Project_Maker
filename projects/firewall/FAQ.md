# 常见问题解答 (FAQ)

## 基本问题

### Q1: 这个项目是什么？

**A**: 这是一个用 C 语言实现的网络防火墙项目，主要用于学习网络协议、防火墙原理和系统编程。它支持基本的包过滤、状态检测和入侵检测功能。

### Q2: 这个项目适合谁？

**A**: 本项目适合：
- 计算机科学学生
- 网络工程师学习者
- 安全研究人员
- 系统编程爱好者

### Q3: 需要什么基础知识？

**A**: 建议具备以下基础：
- C 语言编程基础
- 基本的网络知识（IP、TCP、UDP）
- Linux 基本操作
- 了解编译和调试

### Q4: 这个项目可以用于生产环境吗？

**A**: 不建议。本项目是学习项目，主要用于理解防火墙原理。生产环境请使用成熟的防火墙解决方案，如 iptables、nftables 或商业防火墙。

## 技术问题

### Q5: 为什么选择 Netfilter 而不是 raw socket？

**A**: Netfilter 提供了以下优势：
1. 可以真正拦截和阻止数据包
2. 性能更好，减少用户态/内核态切换
3. 与 Linux 内核网络栈集成
4. 支持连接跟踪

### Q6: 为什么使用用户态实现而不是内核模块？

**A**: 用户态实现的优势：
1. 调试方便
2. 不会 crash 内核
3. 开发周期短
4. 适合学习

缺点是性能不如内核实现。

### Q7: 如何提高性能？

**A**: 可以从以下方面优化：
1. 使用更高效的规则匹配算法（如哈希表、Trie 树）
2. 批量处理数据包
3. 使用多线程
4. 使用 DPDK 等高性能网络框架

### Q8: 如何添加新的协议支持？

**A**: 步骤：
1. 在 `packet.h` 中定义协议头部结构
2. 在 `packet.c` 中添加解析函数
3. 在 `rules.c` 中添加匹配逻辑
4. 更新配置文件格式

### Q9: 如何添加新的检测规则？

**A**: 步骤：
1. 在 `ids.h` 中定义告警类型
2. 在 `ids.c` 中实现检测算法
3. 在配置文件中添加阈值配置
4. 编写测试

## 编译问题

### Q10: 编译时提示找不到头文件

**A**: 安装开发库：
```bash
# Ubuntu/Debian
sudo apt-get install libnetfilter-queue-dev libpcap-dev

# CentOS/RHEL
sudo yum install libnetfilter_queue-devel libpcap-devel
```

### Q11: 链接时提示找不到库

**A**: 确保安装了运行时库：
```bash
# Ubuntu/Debian
sudo apt-get install libnetfilter-queue libpcap

# CentOS/RHEL
sudo yum install libnetfilter_queue libpcap
```

### Q12: 如何编译调试版本？

**A**: 使用以下命令：
```bash
make debug
# 或者
./build.sh build
```

## 运行问题

### Q13: 提示权限不足

**A**: 防火墙需要 root 权限：
```bash
sudo ./build/firewall -i eth0 -c configs/default.conf
```

### Q14: 提示接口不存在

**A**: 查看可用接口：
```bash
ip link show
# 或者
ifconfig -a
```

### Q15: 如何后台运行？

**A**: 使用 `-d` 参数：
```bash
sudo ./build/firewall -i eth0 -c configs/default.conf -d
```

### Q16: 如何查看日志？

**A**: 日志文件位置：
```bash
# 默认日志文件
tail -f /var/log/firewall.log

# 或者指定日志文件
sudo ./build/firewall -i eth0 -c configs/default.conf -l /path/to/logfile
```

## 配置问题

### Q17: 规则格式是什么？

**A**: 规则格式：
```
ACTION PROTOCOL [条件...]
```

示例：
```conf
ACCEPT tcp dst_port 80
DROP tcp src_ip 192.168.1.100
ACCEPT tcp ESTABLISHED
```

### Q18: 如何允许已建立的连接？

**A**: 使用 ESTABLISHED 关键字：
```conf
ACCEPT tcp ESTABLISHED
```

### Q19: 如何配置 CIDR？

**A**: 使用标准 CIDR 表示法：
```conf
ACCEPT tcp src_ip 192.168.1.0/24
```

### Q20: 默认动作是什么？

**A**: 默认动作是 DROP（拒绝）。可以在配置文件最后指定：
```conf
DROP all all
```

## 学习问题

### Q21: 如何开始学习？

**A**: 建议的学习路径：
1. 阅读 README.md 了解项目概况
2. 阅读 docs/ 目录下的文档
3. 从 main.c 开始阅读代码
4. 运行测试和示例
5. 修改代码并实验

### Q22: 有哪些重点难点？

**A**: 主要难点：
1. 网络字节序转换
2. TCP 状态机
3. 规则匹配算法
4. 连接表管理

### Q23: 有哪些值得思考的问题？

**A**: 一些思考点：
1. 为什么需要状态检测？
2. 如何优化规则匹配性能？
3. 如何降低入侵检测误报率？
4. 无状态和有状态防火墙的区别？

### Q24: 推荐哪些参考资料？

**A**: 推荐资源：
- RFC 791 (IP 协议)
- RFC 793 (TCP 协议)
- 《TCP/IP 详解》
- 《Linux 防火墙》
- Netfilter 官方文档

## 开发问题

### Q25: 如何贡献代码？

**A**: 参考 CONTRIBUTING.md 文件。基本步骤：
1. Fork 项目
2. 创建分支
3. 修改代码
4. 编写测试
5. 提交 Pull Request

### Q26: 如何报告 bug？

**A**: 创建 Issue，包含：
1. 问题描述
2. 复现步骤
3. 期望行为
4. 实际行为
5. 环境信息

### Q27: 如何添加新功能？

**A**: 步骤：
1. 创建 Issue 描述功能
2. Fork 项目
3. 实现功能
4. 编写测试
5. 更新文档
6. 提交 Pull Request

### Q28: 代码风格是什么？

**A**: 遵循以下规范：
- 4 空格缩进
- 函数名小写下划线
- 常量大写下划线
- 详细注释

## 其他问题

### Q29: 项目许可证是什么？

**A**: MIT License

### Q30: 如何联系开发者？

**A**: 通过 GitHub Issues 联系

### Q31: 项目还在维护吗？

**A**: 是的，这是一个活跃的学习项目

### Q32: 可以用于商业用途吗？

**A**: 可以，但请注意 MIT License 的要求。本项目不提供任何担保。

---

**还有其他问题？** 请创建 GitHub Issue 或查看项目文档。
