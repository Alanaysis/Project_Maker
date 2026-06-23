# 🎬 多媒体模块

> 音视频编解码、流媒体传输、多媒体处理、图形渲染相关项目

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [audio-engine](audio-engine/) | 音频处理引擎 | Python, NumPy | ⭐⭐⭐⭐ | ✅ 完成 |
| [av-codec](av-codec/) | 音视频编解码器 | C++, FFmpeg | ⭐⭐⭐⭐⭐⭐ | ✅ 完成 |
| [media-server](media-server/) | 流媒体服务器 | Go | ⭐⭐⭐⭐⭐ | ✅ 完成 |
| [physics-engine](physics-engine/) | 2D 物理引擎 | C++ | ⭐⭐⭐⭐ | ✅ 完成 |
| [ray-tracer](ray-tracer/) | 光线追踪渲染器 | C++ | ⭐⭐⭐⭐ | ✅ 完成 |

---

## 🛤️ 学习路径

### 推荐学习顺序

```
1. av-codec (编解码基础)
   │
   ├── 理解音视频编码原理
   ├── 学习容器格式 (MP4/FLV)
   └── 掌握 FFmpeg 使用
   │
   ▼
2. media-server (流媒体传输)
   │
   ├── 理解 RTMP/HLS 协议
   ├── 学习服务器架构
   └── 掌握推流拉流
   │
   ▼
3. ray-tracer (图形渲染)
   │
   ├── 理解光线追踪算法
   ├── 掌握光线-物体求交
   └── 学会材质和光照模型
   │
   ▼
4. physics-engine (物理引擎)
   │
   ├── 理解刚体动力学
   ├── 掌握碰撞检测算法
   └── 学会约束求解
```

### 学习目标

**阶段一：编解码基础**
- 理解 H.264/H.265 视频编码
- 理解 AAC 音频编码
- 掌握容器格式封装

**阶段二：流媒体传输**
- 理解 RTMP 协议原理
- 理解 HLS 协议原理
- 掌握流媒体服务器架构

**阶段三：图形渲染**
- 理解光线追踪算法
- 掌握光线-物体求交
- 学会材质和光照模型

**阶段四：物理引擎**
- 理解刚体动力学
- 掌握碰撞检测算法
- 学会约束求解

---

## 🔧 技术栈说明

### 编解码技术

| 技术 | 用途 | 项目 |
|------|------|------|
| H.264/H.265 | 视频编码 | av-codec |
| AAC | 音频编码 | av-codec |
| FFmpeg | 多媒体处理 | av-codec |
| MP4/FLV | 容器格式 | av-codec |

### 流媒体技术

| 技术 | 用途 | 项目 |
|------|------|------|
| RTMP | 推流协议 | media-server |
| HLS | 拉流协议 | media-server |
| TCP | 传输层 | media-server |
| HTTP | 分发协议 | media-server |

### 图形渲染技术

| 技术 | 用途 | 项目 |
|------|------|------|
| 光线追踪 | 渲染算法 | ray-tracer |
| 向量运算 | 几何计算 | ray-tracer |
| 材质模型 | 光照计算 | ray-tracer |
| PPM | 图像输出 | ray-tracer |

### 音频处理技术

| 技术 | 用途 | 项目 |
|------|------|------|
| FFT/IFFT | 频域变换 | audio-engine |
| 频谱减法 | 降噪 | audio-engine |
| Schroeder 混响 | 音频特效 | audio-engine |
| 参数均衡器 | 频率均衡 | audio-engine |

### 物理引擎技术

| 技术 | 用途 | 项目 |
|------|------|------|
| 刚体动力学 | 物理模拟 | physics-engine |
| AABB 碰撞检测 | 碰撞检测 | physics-engine |
| 约束求解 | 物理约束 | physics-engine |
| 数值积分 | 物理计算 | physics-engine |

---

## 📖 项目详情

### audio-engine - 音频处理引擎

**核心功能**：
- FFT/IFFT 快速傅里叶变换
- 音频滤波（低通、高通、带通、陷波）
- 音频特效（延迟、混响、合唱、失真、压缩）
- 混音器
- 频谱减法降噪
- 参数均衡器和图示均衡器

**快速开始**：
```bash
cd projects/audio-engine

# 运行测试
pytest tests/ -v

# 运行示例
python examples/basic_fft.py
python examples/audio_filtering.py
python examples/audio_effects.py
```

**学习要点**：
- FFT 算法（Cooley-Tukey）
- 频域滤波原理
- 音频特效算法（Schroeder 混响等）
- 频谱减法降噪

📖 [详细文档](audio-engine/README.md)

---

### av-codec - 音视频编解码器

**核心功能**：
- H.264 视频编码
- AAC 音频编码
- MP4/FLV 容器封装
- 编解码完整流程

**快速开始**：
```bash
cd projects/av-codec
mkdir build && cd build
cmake ..
make
```

**学习要点**：
- 视频编码原理 (I/P/B 帧)
- 运动估计和运动补偿
- 容器格式封装
- FFmpeg API 使用

📖 [详细文档](av-codec/README.md)

---

### media-server - 流媒体服务器

**核心功能**：
- RTMP 推流服务
- HLS 拉流服务
- 多流并发管理
- M3U8 播放列表生成

**快速开始**：
```bash
cd projects/media-server
go mod tidy
go build ./cmd/server/

# 运行服务器
./media-server

# 推流测试
ffmpeg -re -i test.mp4 -c copy -f flv rtmp://localhost:1935/live/test

# 拉流测试
ffplay http://localhost:8080/live/test/index.m3u8
```

**学习要点**：
- RTMP 协议握手和消息解析
- AMF 编解码
- HLS 分片和播放列表
- 并发服务器设计

📖 [详细文档](media-server/README.md)

---

### ray-tracer - 光线追踪渲染器

**核心功能**：
- 基本的光线追踪算法
- 球体和平面求交
- 多种材质（漫反射、金属、电介质）
- 多重采样抗锯齿
- PPM 图像输出

**快速开始**：
```bash
cd projects/ray-tracer
mkdir build && cd build
cmake ..
make

# 渲染默认场景
./ray-tracer --scene default --output output.ppm

# 运行测试
ctest
```

**学习要点**：
- 光线追踪算法原理
- 光线-球体求交算法
- Lambertian/Metal/Dielectric 材质模型
- 相机系统和景深效果
- 多重采样抗锯齿

📖 [详细文档](ray-tracer/README.md)

---

### physics-engine - 2D 物理引擎

**核心功能**：
- 刚体动力学（质量、速度、力、冲量）
- AABB 碰撞检测（轴对齐包围盒）
- 约束求解（距离约束、钉子约束、铰链约束、焊接约束）
- 物理模拟（重力、摩擦力、弹性碰撞、阻尼）

**快速开始**：
```bash
cd projects/physics-engine
mkdir build && cd build
cmake ..
make
ctest --output-on-failure
./examples/example_basic
```

**学习要点**：
- 刚体动力学原理（牛顿运动定律）
- 碰撞检测算法（AABB、圆形碰撞）
- 约束求解算法
- 数值积分方法

📖 [详细文档](physics-engine/README.md)

---

## 📚 学习资源

### 书籍

- 《音视频开发进阶指南》- 雷霄骅
- 《FFmpeg 从入门到精通》- 刘歧
- 《流媒体技术原理与应用》
- 《Ray Tracing in One Weekend》- Peter Shirley
- 《Fundamentals of Computer Graphics》- Marschner & Shirley
- 《Game Physics Engine Development》- Ian Millington
- 《Real-Time Collision Detection》- Christer Ericson

### 在线课程

- [FFmpeg 官方文档](https://ffmpeg.org/documentation.html)
- [RTMP 规范](https://wwwimages2.adobe.com/content/dam/acom/en/devnet/pdf/rtmp_specification_1.0.pdf)
- [HLS 规范](https://developer.apple.com/documentation/http-live-streaming)

### 开源项目

| 项目 | 语言 | 特点 |
|------|------|------|
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | C | 最强大的多媒体处理库 |
| [SRS](https://github.com/ossrs/srs) | C++ | 高性能流媒体服务器 |
| [LiveGo](https://github.com/gwuhaolin/livego) | Go | 简单的流媒体服务器 |
| [MediaSoup](https://github.com/versatica/mediasoup) | C++ | WebRTC SFU |
| [smallpt](http://www.kevinbeason.com/smallpt/) | C++ | 99行光线追踪器 |
| [pbrt](https://github.com/mmp/pbrt-v3) | C++ | 物理基础渲染器 |
| [Box2D](https://github.com/erincatto/box2d) | C++ | 2D 物理引擎 |
| [Bullet](https://github.com/bulletphysics/bullet3) | C++ | 3D 物理引擎 |
| [Chipmunk](https://github.com/slembcke/Chipmunk2D) | C | 轻量级 2D 物理引擎 |

### 工具

| 工具 | 用途 |
|------|------|
| FFmpeg | 多媒体处理 |
| FFplay | 媒体播放 |
| VLC | 媒体播放 |
| Wireshark | 协议分析 |
| MediaInfo | 媒体信息查看 |

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [自动驾驶模块](ADAS_README.md)
- [区块链模块](BLOCKCHAIN_README.md)
- [AI 模块](AI_README.md)
- [系统模块](SYSTEM_README.md)
- [网络模块](NETWORK_README.md)
- [异构计算模块](HETERO_README.md)
- [分布式模块](DISTRIBUTED_README.md)
- [应用模块](APPS_README.md)
