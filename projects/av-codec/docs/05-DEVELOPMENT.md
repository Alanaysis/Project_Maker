# 05 - 开发文档

## 1. 开发环境

### 1.1 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Linux/macOS/Windows |
| 编译器 | GCC 9+ / Clang 10+ / MSVC 2019+ |
| 构建工具 | CMake 3.16+ |
| FFmpeg | 4.4+ |
| Git | 2.20+ |

### 1.2 开发工具

#### IDE推荐
- **VS Code**: 轻量级，插件丰富
- **CLion**: 功能强大，CMake支持好
- **Visual Studio**: Windows开发首选

#### VS Code插件
```json
{
  "recommendations": [
    "ms-vscode.cpptools",
    "ms-vscode.cmake-tools",
    "twxs.cmake",
    "cschlosser.doxdocgen"
  ]
}
```

### 1.3 代码规范

#### 命名规范
```cpp
// 类名: PascalCase
class VideoEncoder {};

// 函数名: camelCase
int encodeFrame();

// 变量名: camelCase
int frameCount;

// 常量: UPPER_SNAKE_CASE
const int MAX_BUFFER_SIZE = 1024;

// 成员变量: 带下划线后缀
int width_;

// 指针变量: 带p前缀
AVFrame* pFrame;
```

#### 注释规范
```cpp
/**
 * @brief 视频编码器类
 * 
 * 实现H.264视频编码功能
 */
class VideoEncoder {
public:
    /**
     * @brief 初始化编码器
     * @param config 编码器配置
     * @return 0成功，负数失败
     */
    int init(const VideoEncoderConfig& config);
    
    /**
     * @brief 编码一帧
     * @param frame 输入帧
     * @param pkt 输出数据包
     * @return 0成功，负数失败
     */
    int encode(const AVFrame* frame, AVPacket* pkt);
};
```

#### 代码格式
```cpp
// 使用4空格缩进
if (condition) {
    doSomething();
} else {
    doSomethingElse();
}

// 函数之间空一行
int func1() {
    // ...
}

int func2() {
    // ...
}
```

## 2. Git工作流

### 2.1 分支策略

```
main (生产分支)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/video-encoder (功能分支)
  │     ├── feature/audio-encoder
  │     └── feature/muxer
  │
  └── release/v1.0 (发布分支)
```

### 2.2 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type类型
- **feat**: 新功能
- **fix**: 修复bug
- **docs**: 文档修改
- **style**: 代码格式修改
- **refactor**: 重构
- **test**: 测试相关
- **chore**: 构建/工具修改

#### 示例
```
feat(video-encoder): 实现H.264编码功能

- 添加VideoEncoder类
- 实现init/encode/flush接口
- 添加单元测试

Closes #123
```

### 2.3 常用Git命令

```bash
# 创建功能分支
git checkout -b feature/video-encoder develop

# 提交更改
git add .
git commit -m "feat(video-encoder): 实现H.264编码功能"

# 推送到远程
git push origin feature/video-encoder

# 合并到develop
git checkout develop
git merge --no-ff feature/video-encoder

# 创建发布分支
git checkout -b release/v1.0 develop

# 合并到main
git checkout main
git merge --no-ff release/v1.0
git tag -a v1.0 -m "Release v1.0"
```

## 3. 构建系统

### 3.1 CMake配置详解

```cmake
cmake_minimum_required(VERSION 3.16)
project(av-codec VERSION 1.0.0 LANGUAGES CXX)

# C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(MSVC)
    add_compile_options(/W4)
endif

# 查找依赖
find_package(PkgConfig REQUIRED)
pkg_check_modules(AVCODEC REQUIRED libavcodec)
pkg_check_modules(AVFORMAT REQUIRED libavformat)
pkg_check_modules(AVUTIL REQUIRED libavutil)
pkg_check_modules(SWSCALE REQUIRED libswscale)
pkg_check_modules(SWRESAMPLE REQUIRED libswresample)

# 头文件目录
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${AVCODEC_INCLUDE_DIRS}
    ${AVFORMAT_INCLUDE_DIRS}
    ${AVUTIL_INCLUDE_DIRS}
    ${SWSCALE_INCLUDE_DIRS}
    ${SWRESAMPLE_INCLUDE_DIRS}
)

# 库目录
link_directories(
    ${AVCODEC_LIBRARY_DIRS}
    ${AVFORMAT_LIBRARY_DIRS}
    ${AVUTIL_LIBRARY_DIRS}
    ${SWSCALE_LIBRARY_DIRS}
    ${SWRESAMPLE_LIBRARY_DIRS}
)

# 源文件
set(LIB_SOURCES
    src/video_encoder.cpp
    src/video_decoder.cpp
    src/audio_encoder.cpp
    src/audio_decoder.cpp
    src/muxer.cpp
    src/demuxer.cpp
    src/utils.cpp
)

# 创建静态库
add_library(avcodec_lib STATIC ${LIB_SOURCES})
target_link_libraries(avcodec_lib
    ${AVCODEC_LIBRARIES}
    ${AVFORMAT_LIBRARIES}
    ${AVUTIL_LIBRARIES}
    ${SWSCALE_LIBRARIES}
    ${SWRESAMPLE_LIBRARIES}
)

# 示例程序
set(EXAMPLE_SOURCES
    examples/video_encoder_example.cpp
    examples/audio_encoder_example.cpp
    examples/muxer_example.cpp
)

foreach(EXAMPLE ${EXAMPLE_SOURCES})
    get_filename_component(EXAMPLE_NAME ${EXAMPLE} NAME_WE)
    add_executable(${EXAMPLE_NAME} ${EXAMPLE})
    target_link_libraries(${EXAMPLE_NAME} avcodec_lib)
endforeach()

# 测试
enable_testing()
set(TEST_SOURCES
    tests/test_video_codec.cpp
    tests/test_audio_codec.cpp
    tests/test_muxer.cpp
)

foreach(TEST ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST} NAME_WE)
    add_executable(${TEST_NAME} ${TEST})
    target_link_libraries(${TEST_NAME} avcodec_lib)
    add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
endforeach()

# 安装
install(TARGETS avcodec_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(DIRECTORY include/ DESTINATION include)
```

### 3.2 构建选项

```bash
# Debug构建
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release构建
cmake -DCMAKE_BUILD_TYPE=Release ..

# 自定义安装目录
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..

# 启用测试
cmake -DBUILD_TESTING=ON ..

# 启用示例
cmake -DBUILD_EXAMPLES=ON ..
```

### 3.3 交叉编译

```cmake
# toolchain.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

set(CMAKE_FIND_ROOT_PATH /usr/aarch64-linux-gnu)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

```bash
# 使用工具链文件
cmake -DCMAKE_TOOLCHAIN_FILE=toolchain.cmake ..
```

## 4. 调试技巧

### 4.1 GDB调试

```bash
# 编译Debug版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 运行GDB
gdb ./test_video_codec

# GDB常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) watch variable      # 监视变量变化
(gdb) info locals         # 查看局部变量
```

### 4.2 Valgrind内存检测

```bash
# 安装valgrind
sudo apt install valgrind

# 检测内存泄漏
valgrind --leak-check=full ./test_video_codec

# 检测内存错误
valgrind --tool=memcheck ./test_video_codec
```

### 4.3 AddressSanitizer

```bash
# 编译时启用
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..
make

# 运行测试
./test_video_codec
```

### 4.4 FFmpeg调试

```cpp
// 启用FFmpeg日志
av_log_set_level(AV_LOG_DEBUG);

// 自定义日志回调
void log_callback(void* ptr, int level, const char* fmt, va_list vl) {
    char line[1024];
    vsnprintf(line, sizeof(line), fmt, vl);
    printf("[FFmpeg] %s", line);
}
av_log_set_callback(log_callback);
```

## 5. 性能优化

### 5.1 编译优化

```bash
# 启用优化
cmake -DCMAKE_BUILD_TYPE=Release ..

# 针对特定CPU优化
cmake -DCMAKE_CXX_FLAGS="-march=native" ..

# 启用LTO
cmake -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON ..
```

### 5.2 代码优化

#### 减少内存分配
```cpp
// 不好：频繁分配释放
for (int i = 0; i < 1000; i++) {
    AVFrame* frame = av_frame_alloc();
    // ...
    av_frame_free(&frame);
}

// 好：复用帧
AVFrame* frame = av_frame_alloc();
for (int i = 0; i < 1000; i++) {
    av_frame_unref(frame);
    // ...
}
av_frame_free(&frame);
```

#### 使用零拷贝
```cpp
// 不好：拷贝数据
memcpy(dst, src, size);

// 好：使用引用
av_frame_ref(dst, src);
```

#### 多线程编码
```cpp
// 启用多线程
codec_ctx_->thread_count = 4;
codec_ctx_->thread_type = FF_THREAD_FRAME;
```

### 5.3 FFmpeg优化选项

```cpp
// 设置编码预设
av_opt_set(codec_ctx_->priv_data, "preset", "fast", 0);

// 设置编码档次
av_opt_set(codec_ctx_->priv_data, "profile", "baseline", 0);

// 设置量化参数
av_opt_set_int(codec_ctx_->priv_data, "crf", 23, 0);
```

## 6. 文档编写

### 6.1 Doxygen配置

```xml
# Doxyfile
PROJECT_NAME = "AV-Codec"
PROJECT_NUMBER = "1.0.0"
OUTPUT_DIRECTORY = docs/doxygen
INPUT = include src
RECURSIVE = YES
EXTRACT_ALL = YES
GENERATE_HTML = YES
GENERATE_LATEX = NO
```

### 6.2 生成文档

```bash
# 安装doxygen
sudo apt install doxygen graphviz

# 生成文档
doxygen Doxyfile

# 查看文档
open docs/doxygen/html/index.html
```

## 7. 发布流程

### 7.1 版本号规范

```
主版本号.次版本号.修订号

示例：1.0.0

- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正
```

### 7.2 发布检查清单

```markdown
## 发布前检查

### 代码质量
- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 文档更新

### 构建
- [ ] Debug版本构建正常
- [ ] Release版本构建正常
- [ ] 交叉编译测试

### 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能测试通过

### 文档
- [ ] README更新
- [ ] API文档生成
- [ ] 变更日志更新

### 打包
- [ ] 创建Git标签
- [ ] 生成发布包
- [ ] 上传到发布平台
```

### 7.3 发布脚本

```bash
#!/bin/bash
# release.sh

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

# 更新版本号
sed -i "s/VERSION .*/VERSION $VERSION/" CMakeLists.txt

# 提交更改
git add .
git commit -m "chore: release v$VERSION"

# 创建标签
git tag -a "v$VERSION" -m "Release v$VERSION"

# 推送
git push origin main
git push origin "v$VERSION"

# 构建发布包
mkdir -p build-release
cd build-release
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
make package

echo "Release v$VERSION created successfully!"
```

## 8. 常见问题

### 8.1 编译问题

**问题**: CMake找不到FFmpeg
```bash
# 解决方案
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
```

**问题**: 链接错误
```bash
# 解决方案
cmake -DCMAKE_LIBRARY_PATH=/usr/local/lib ..
```

### 8.2 运行问题

**问题**: 编码器初始化失败
- 检查FFmpeg版本
- 检查编码器是否支持

**问题**: 内存泄漏
- 使用valgrind检测
- 检查资源释放

### 8.3 性能问题

**问题**: 编码速度慢
- 调整编码预设
- 启用多线程
- 使用硬件加速

**问题**: 内存占用高
- 减少缓冲区大小
- 使用内存池
- 及时释放资源

## 9. 参考资源

### 9.1 官方文档
- [FFmpeg文档](https://ffmpeg.org/documentation.html)
- [CMake文档](https://cmake.org/documentation/)
- [GCC文档](https://gcc.gnu.org/onlinedocs/)

### 9.2 教程
- [FFmpeg教程](http://dranger.com/ffmpeg/)
- [CMake教程](https://cliutils.gitlab.io/modern-cmake/)

### 9.3 社区
- [FFmpeg邮件列表](https://ffmpeg.org/mailman/listinfo/ffmpeg-devel)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/ffmpeg)
