# 05 开发手册 - 音视频编解码器

## 1. 编译说明

### 1.1 系统要求

- 操作系统：Linux/macOS/Windows
- 编译器：GCC 9+ / Clang 10+ / MSVC 2019+
- CMake：3.16+
- 内存：8GB+
- 磁盘空间：1GB+

### 1.2 依赖安装

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install build-essential cmake
sudo apt install libavcodec-dev libavformat-dev libavutil-dev
sudo apt install libswscale-dev libswresample-dev
```

#### macOS

```bash
brew install cmake ffmpeg
```

#### Windows (vcpkg)

```powershell
vcpkg install ffmpeg
```

### 1.3 编译步骤

```bash
# 进入项目目录
cd projects/av-codec

# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译
make -j$(nproc)

# 运行测试
make test
```

### 1.4 编译选项

```bash
# 禁用FFmpeg依赖
cmake -DUSE_FFMPEG=OFF ..

# 启用SIMD优化
cmake -DUSE_SIMD=ON ..

# 启用GPU加速
cmake -DUSE_GPU=ON ..

# 构建示例程序
cmake -DBUILD_EXAMPLES=ON ..

# 构建测试
cmake -DBUILD_TESTS=ON ..
```

## 2. 运行方式

### 2.1 视频编码示例

```bash
./build/bin/video_encoder_example
```

### 2.2 音频编码示例

```bash
./build/bin/audio_encoder_example
```

### 2.3 容器封装示例

```bash
./build/bin/container_example
```

### 2.4 流媒体示例

```bash
./build/bin/streaming_example
```

### 2.5 转码示例

```bash
./build/bin/transcoder_example
```

### 2.6 播放器示例

```bash
./build/bin/player_example
```

### 2.7 会议示例

```bash
./build/bin/conference_example
```

## 3. 测试

### 3.1 运行所有测试

```bash
cd build
make test
```

### 3.2 运行单个测试

```bash
./build/bin/test_video_codec
./build/bin/test_audio_codec
./build/bin/test_container
./build/bin/test_protocol
./build/bin/test_optimization
```

### 3.3 测试覆盖率

```bash
cmake -DCMAKE_BUILD_TYPE=Coverage ..
make
make test
gcov -r src/
```

## 4. 调试

### 4.1 调试模式编译

```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
```

### 4.2 使用GDB调试

```bash
gdb ./build/bin/video_encoder_example
```

### 4.3 使用Valgrind检查内存

```bash
valgrind --leak-check=full ./build/bin/test_video_codec
```

## 5. 性能分析

### 5.1 使用gprof

```bash
cmake -DCMAKE_BUILD_TYPE=Profile ..
make
./build/bin/video_encoder_example
gprof ./build/bin/video_encoder_example gmon.out > analysis.txt
```

### 5.2 使用perf

```bash
perf record ./build/bin/video_encoder_example
perf report
```

### 5.3 使用Intel VTune

```bash
vtune -collect hotspots ./build/bin/video_encoder_example
```

## 6. 代码规范

### 6.1 命名规范

- 类名：PascalCase（如 `H264Encoder`）
- 函数名：camelCase（如 `encodeFrame`）
- 变量名：snake_case（如 `frame_size`）
- 常量名：UPPER_SNAKE_CASE（如 `MAX_FRAME_SIZE`）
- 枚举值：UPPER_SNAKE_CASE（如 `I_FRAME`）

### 6.2 注释规范

- 使用 Doxygen 风格注释
- 类和函数必须有文档注释
- 复杂算法必须有详细注释
- 使用中文注释

### 6.3 代码风格

- 使用 4 空格缩进
- 每行不超过 100 字符
- 使用 C++17/20 特性
- 使用智能指针管理内存

## 7. 发布

### 7.1 版本号

- 主版本号：重大更新
- 次版本号：新功能
- 修订号：bug修复

### 7.2 发布流程

1. 更新版本号
2. 更新 CHANGELOG
3. 运行所有测试
4. 创建发布包
5. 上传到发布平台

### 7.3 发布包内容

```
av-codec-1.0.0/
├── bin/              # 可执行文件
├── lib/              # 库文件
├── include/          # 头文件
├── examples/         # 示例程序
├── tests/            # 测试程序
├── docs/             # 文档
├── README.md         # 项目说明
├── LICENSE           # 许可证
└── CHANGELOG.md      # 更新日志
```
