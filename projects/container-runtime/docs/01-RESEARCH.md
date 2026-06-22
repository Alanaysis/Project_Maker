# 01 - 市场调研

## 调研目的

了解容器运行时技术的发展现状，分析主流实现方案，为 MiniContainer 项目提供技术参考。

## 容器运行时分类

### 1. 高级运行时（High-level Runtime）

高级运行时负责镜像管理、容器生命周期管理、网络和存储配置等。

| 项目 | 语言 | 特点 | GitHub Stars |
|------|------|------|--------------|
| [containerd](https://github.com/containerd/containerd) | Go | Docker 官方运行时，功能完整 | 15k+ |
| [CRI-O](https://github.com/cri-o/cri-o) | Go | Kubernetes 专用，轻量级 | 4k+ |
| [Podman](https://github.com/containers/podman) | Go | 无守护进程，兼容 Docker CLI | 20k+ |

### 2. 低级运行时（Low-level Runtime）

低级运行时负责实际的容器创建和执行，直接与 Linux 内核交互。

| 项目 | 语言 | 特点 | GitHub Stars |
|------|------|------|--------------|
| [runc](https://github.com/opencontainers/runc) | Go | OCI 参考实现，最广泛使用 | 11k+ |
| [crun](https://github.com/containers/crun) | C | 更快、更轻量 | 2k+ |
| [runhcs](https://github.com/microsoft/hcsshim) | Go | Windows 容器运行时 | 500+ |

### 3. 沙箱运行时（Sandbox Runtime）

提供更强的隔离性，适用于多租户场景。

| 项目 | 语言 | 特点 | GitHub Stars |
|------|------|------|--------------|
| [gVisor (runsc)](https://github.com/google/gvisor) | Go | 用户空间内核，安全性高 | 15k+ |
| [Kata Containers](https://github.com/kata-containers/kata-containers) | Go/Rust | 轻量级虚拟机，强隔离 | 4k+ |
| [Firecracker](https://github.com/firecracker-microvm/firecracker) | Rust | AWS 开发，极快启动 | 24k+ |

## 技术变体分析

### 1. 隔离技术演进

```
chroot (1979)
  ↓
Linux VServer (2001)
  ↓
OpenVZ (2005)
  ↓
Linux Namespaces + Cgroups (2006-2008)
  ↓
Docker (2013)
  ↓
OCI Standard (2015)
  ↓
Containerd (2017)
```

### 2. 存储驱动对比

| 驱动 | 特点 | 性能 | 适用场景 |
|------|------|------|----------|
| OverlayFS | 内核原生，稳定 | 快 | 生产环境（推荐） |
| AUFS | 早期 Docker 默认 | 中等 | 兼容旧系统 |
| Device Mapper | 块级存储 | 中等 | RHEL/CentOS |
| BTRFS | 快照支持 | 快 | 开发环境 |
| ZFS | 数据完整性 | 快 | 高可靠性场景 |

### 3. 网络方案对比

| 方案 | 特点 | 性能 | 复杂度 |
|------|------|------|--------|
| Bridge | 默认方案，简单 | 中等 | 低 |
| Macvlan | 直接使用物理网络 | 高 | 中 |
| IPvlan | 共享 MAC 地址 | 高 | 中 |
| VXLAN | 跨主机通信 | 中等 | 高 |
| Calico | BGP 路由 | 高 | 高 |
| Flannel | 覆盖网络 | 中等 | 中 |

## 主流项目发力方向

### containerd
- **定位**：工业级容器运行时
- **重点**：稳定性、可扩展性、插件架构
- **生态**：Kubernetes CRI、Docker、BuildKit

### CRI-O
- **定位**：Kubernetes 专用运行时
- **重点**：轻量级、稳定性、与 K8s 版本对齐
- **生态**：Red Hat、OpenShift

### Podman
- **定位**：无守护进程容器引擎
- **重点**：兼容 Docker、Rootless、Pod 支持
- **生态**：Red Hat、Buildah、Skopeo

### gVisor
- **定位**：安全容器运行时
- **重点**：用户空间内核、系统调用过滤
- **生态**：Google Cloud、GKE Sandbox

### Kata Containers
- **定位**：轻量级虚拟机容器
- **重点**：硬件级隔离、快速启动
- **生态**：OpenStack、Kubernetes

## 教育类项目分析

### 1. [naive-container-runtime](https://github.com/p8952/naive-container-runtime)
- **语言**：Go
- **特点**：极简实现，仅 200 行代码
- **学习价值**：理解容器基本原理

### 2. [containers-from-scratch](https://github.com/lizrice/containers-from-scratch)
- **语言**：Go
- **特点**：Liz Rice 的演讲配套代码
- **学习价值**：逐步构建容器

### 3. [build-your-own-container](https://github.com/sayden/build-your-own-container)
- **语言**：Rust
- **特点**：使用 Rust 实现
- **学习价值**：不同语言的实现对比

## 技术选型建议

### 语言选择：Go vs Rust vs C

| 维度 | Go | Rust | C |
|------|-----|------|---|
| 学习曲线 | 低 | 高 | 中 |
| 内存安全 | GC | 所有权 | 手动 |
| 性能 | 好 | 极好 | 极好 |
| 生态 | 丰富 | 增长中 | 成熟 |
| 调试 | 容易 | 中等 | 困难 |

**推荐**：Go（适合学习和快速实现）

### OCI 标准采用

建议采用 OCI 标准，原因：
1. 行业标准，兼容性好
2. 文档完善，社区活跃
3. 便于与现有工具集成

## 参考资源

### 官方文档
- [OCI Runtime Specification](https://github.com/opencontainers/runtime-spec)
- [OCI Image Specification](https://github.com/opencontainers/image-spec)
- [Linux Namespaces](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [Cgroups v2](https://www.kernel.org/doc/Documentation/cgroup-v2.txt)

### 技术博客
- [Linux Container Internals](https://medium.com/@sstelfox/linux-containers-from-scratch)
- [Build Your Own Container](https://ericchiang.github.io/post/containers-from-scratch/)
- [Understanding Docker](https://www.youtube.com/watch?v=sK5i-N34im8)

### 开源项目
- [runc](https://github.com/opencontainers/runc)
- [containerd](https://github.com/containerd/containerd)
- [crun](https://github.com/containers/crun)

## 总结

容器运行时技术已经相对成熟，但仍有许多创新空间：

1. **安全性**：gVisor、Kata 等项目探索更强的隔离方案
2. **性能**：crun 使用 C 语言实现，性能优于 runc
3. **易用性**：Podman 提供无守护进程的体验
4. **标准化**：OCI 标准推动了生态的统一

MiniContainer 项目作为学习项目，重点理解核心原理，为深入学习打下基础。
