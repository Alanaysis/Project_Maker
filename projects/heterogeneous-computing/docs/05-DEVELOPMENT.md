# 开发手册

## 1. 环境搭建

### 1.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 18.04 / Windows 10 | Ubuntu 22.04 / Windows 11 |
| 编译器 | GCC 7 / Clang 6 / MSVC 2017 | GCC 11 / Clang 14 / MSVC 2022 |
| CMake | 3.16 | 3.24+ |
| CUDA Toolkit | 11.0 (可选) | 12.0+ |
| OpenCL SDK | 2.0 (可选) | 3.0+ |
| 内存 | 4GB | 16GB+ |
| GPU | NVIDIA GPU (可选) | NVIDIA RTX 3060+ |

### 1.2 Ubuntu 环境搭建

#### 安装基础依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装编译工具
sudo apt install -y build-essential cmake git

# 安装 C++ 开发库
sudo apt install -y libstdc++-11-dev

# 验证安装
gcc --version
cmake --version
```

#### 安装 CUDA Toolkit (可选)

```bash
# 添加 NVIDIA 仓库
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update

# 安装 CUDA Toolkit
sudo apt install -y cuda-toolkit-12-0

# 配置环境变量
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证安装
nvcc --version
nvidia-smi
```

#### 安装 OpenCL SDK (可选)

```bash
# NVIDIA GPU
sudo apt install -y nvidia-opencl-dev

# AMD GPU
sudo apt install -y mesa-opencl-icd

# Intel GPU
sudo apt install -y intel-opencl-icd

# 验证安装
clinfo
```

### 1.3 Windows 环境搭建

#### 安装 Visual Studio

1. 下载 Visual Studio 2022
2. 安装 "Desktop development with C++" 工作负载
3. 安装 CMake 工具

#### 安装 CUDA Toolkit

1. 下载 CUDA Toolkit 12.0+
2. 运行安装程序
3. 选择 "Custom" 安装
4. 确保选中 "Development" 和 "Runtime" 组件

#### 安装 OpenCL SDK

1. 下载 Intel OpenCL SDK 或 AMD APP SDK
2. 运行安装程序
3. 配置环境变量

### 1.4 macOS 环境搭建

```bash
# 安装 Xcode 命令行工具
xcode-select --install

# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install cmake git

# 注意: macOS 不支持 CUDA，仅支持 OpenCL (已弃用)
# 推荐使用 Metal Performance Shaders 或 MoltenVK
```

## 2. 项目构建

### 2.1 获取源码

```bash
# 克隆项目
git clone https://github.com/yourusername/heterogeneous-computing.git
cd heterogeneous-computing
```

### 2.2 构建项目

```bash
# 创建构建目录
mkdir build && cd build

# 配置项目 (无 GPU)
cmake .. -DENABLE_CUDA=OFF -DENABLE_OPENCL=OFF

# 配置项目 (有 NVIDIA GPU)
cmake .. -DENABLE_CUDA=ON -DENABLE_OPENCL=OFF

# 配置项目 (有 OpenCL GPU)
cmake .. -DENABLE_CUDA=OFF -DENABLE_OPENCL=ON

# 配置项目 (全功能)
cmake .. -DENABLE_CUDA=ON -DENABLE_OPENCL=ON

# 编译
make -j$(nproc)

# 安装 (可选)
sudo make install
```

### 2.3 构建选项

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `ENABLE_CUDA` | OFF | 启用 CUDA 支持 |
| `ENABLE_OPENCL` | OFF | 启用 OpenCL 支持 |
| `BUILD_TESTS` | ON | 构建测试 |
| `BUILD_EXAMPLES` | ON | 构建示例 |
| `BUILD_DOCS` | OFF | 构建文档 |
| `CMAKE_BUILD_TYPE` | Release | 构建类型 |

### 2.4 常见构建问题

#### 问题 1: CMake 版本过低

```
CMake Error: CMake was unable to find a build program corresponding to "Unix Makefiles"
```

**解决方案**:
```bash
# 安装最新 CMake
sudo apt install -y cmake
# 或从源码编译
wget https://github.com/Kitware/CMake/releases/download/v3.24.0/cmake-3.24.0.tar.gz
tar -xzf cmake-3.24.0.tar.gz
cd cmake-3.24.0
./bootstrap && make && sudo make install
```

#### 问题 2: CUDA 编译失败

```
nvcc fatal: Unsupported gpu architecture 'compute_86'
```

**解决方案**:
```bash
# 检查 GPU 架构
nvidia-smi --query-gpu=compute_cap --format=csv

# 在 CMakeLists.txt 中设置正确的架构
set(CMAKE_CUDA_ARCHITECTURES 75 86)  # 根据你的 GPU 调整
```

#### 问题 3: OpenCL 头文件找不到

```
fatal error: CL/cl.h: No such file or directory
```

**解决方案**:
```bash
# 安装 OpenCL 开发包
sudo apt install -y opencl-headers ocl-icd-opencl-dev
```

## 3. 核心模块解析

### 3.1 模块架构

```
heterogeneous-computing/
├── include/
│   └── heterogeneous/
│       ├── core.h         # 框架核心定义
│       ├── task.h         # 任务抽象
│       ├── device.h       # 设备抽象
│       ├── memory.h       # 内存管理
│       ├── scheduler.h    # 任务调度
│       └── executor.h     # 任务执行
├── src/
│   ├── core.cpp           # 框架实现
│   ├── task.cpp           # 任务实现
│   ├── device.cpp         # 设备实现
│   ├── memory.cpp         # 内存实现
│   ├── scheduler.cpp      # 调度实现
│   └── executor.cpp       # 执行实现
└── backends/
    ├── cpu/               # CPU 后端
    ├── cuda/              # CUDA 后端
    └── opencl/            # OpenCL 后端
```

### 3.2 核心模块详解

#### 3.2.1 Task 模块

**职责**: 定义和管理计算任务

**核心类**:
- `Task`: 任务基类
- `TaskManager`: 任务管理器
- `TaskBuilder`: 任务构建器

**关键实现**:

```cpp
// task.h
class Task {
public:
    Task(const std::string& name, TaskFunc func);
    
    // 设置输入输出
    Task& set_input(const void* data, size_t size);
    Task& set_output(void* data, size_t size);
    
    // 设置执行偏好
    Task& prefer_device(DeviceType type);
    Task& set_priority(TaskPriority priority);
    
    // 执行任务
    void execute();
    
    // 获取结果
    TaskResult get_result() const;
    
private:
    std::string id_;
    std::string name_;
    TaskFunc func_;
    TaskStatus status_;
    // ...
};
```

**使用示例**:

```cpp
// 创建任务
auto task = Task("vector_add", [](const void* in, void* out, size_t size) {
    const float* input = static_cast<const float*>(in);
    float* output = static_cast<float*>(out);
    size_t count = size / sizeof(float);
    
    for (size_t i = 0; i < count; i++) {
        output[i] = input[i] + input[i + count];
    }
});

// 配置任务
task.set_input(input_data, data_size)
    .set_output(output_data, data_size)
    .prefer_device(DeviceType::GPU_CUDA)
    .set_priority(TaskPriority::High);

// 执行任务
task.execute();
```

#### 3.2.2 Device 模块

**职责**: 管理计算设备

**核心类**:
- `Device`: 设备基类
- `CPUDevice`: CPU 设备
- `CUDADevice`: CUDA 设备
- `OpenCLDevice`: OpenCL 设备
- `DeviceManager`: 设备管理器

**关键实现**:

```cpp
// device.h
class Device {
public:
    virtual ~Device() = default;
    
    // 设备信息
    virtual DeviceInfo get_info() const = 0;
    
    // 内存管理
    virtual void* allocate(size_t size) = 0;
    virtual void deallocate(void* ptr) = 0;
    virtual void copy_to(void* dst, const void* src, size_t size) = 0;
    virtual void copy_from(void* dst, const void* src, size_t size) = 0;
    
    // 任务执行
    virtual void execute(const Task& task) = 0;
    virtual void synchronize() = 0;
    
    // 状态查询
    virtual bool is_available() const = 0;
    virtual double get_utilization() const = 0;
};

class CUDADevice : public Device {
public:
    CUDADevice(int device_id);
    
    void* allocate(size_t size) override {
        void* ptr;
        cudaMalloc(&ptr, size);
        return ptr;
    }
    
    void execute(const Task& task) override {
        // 启动 CUDA 内核
        launch_kernel(task);
    }
    
private:
    int device_id_;
    cudaStream_t stream_;
};
```

#### 3.2.3 Memory 模块

**职责**: 管理内存分配和数据传输

**核心类**:
- `MemoryManager`: 内存管理器
- `MemoryPool`: 内存池
- `MemoryBlock`: 内存块

**关键实现**:

```cpp
// memory.h
class MemoryManager {
public:
    // 分配内存
    void* allocate(size_t size, MemoryLocation location);
    
    // 释放内存
    void deallocate(void* ptr);
    
    // 数据传输
    void transfer(const void* src, void* dst, size_t size,
                  MemoryLocation src_loc, MemoryLocation dst_loc);
    
    // 异步传输
    std::future<void> transfer_async(const void* src, void* dst, size_t size,
                                      MemoryLocation src_loc, MemoryLocation dst_loc);
    
    // 内存使用统计
    size_t get_total_allocated() const;
    size_t get_peak_allocated() const;
    
private:
    std::unordered_map<void*, MemoryBlock> blocks_;
    std::unique_ptr<MemoryPool> pool_;
};
```

#### 3.2.4 Scheduler 模块

**职责**: 调度任务到合适的设备

**核心类**:
- `Scheduler`: 调度器基类
- `RoundRobinScheduler`: 轮询调度器
- `LoadBalancingScheduler`: 负载均衡调度器
- `AdaptiveScheduler`: 自适应调度器

**关键实现**:

```cpp
// scheduler.h
class Scheduler {
public:
    virtual ~Scheduler() = default;
    
    // 调度任务
    virtual std::shared_ptr<Device> schedule(const Task& task) = 0;
    
    // 获取统计信息
    virtual SchedulingStats get_stats() const = 0;
};

class AdaptiveScheduler : public Scheduler {
public:
    std::shared_ptr<Device> schedule(const Task& task) override {
        // 分析任务特征
        TaskFeatures features = analyze_task(task);
        
        // 获取历史性能数据
        auto history = get_performance_history(task.name());
        
        // 预测各设备执行时间
        std::map<std::string, double> predictions;
        for (auto& device : DeviceManager::instance().get_devices()) {
            predictions[device->id()] = predict_time(features, device, history);
        }
        
        // 选择最优设备
        return select_best_device(predictions);
    }
    
private:
    TaskFeatures analyze_task(const Task& task);
    double predict_time(const TaskFeatures& features, 
                       std::shared_ptr<Device> device,
                       const PerformanceHistory& history);
};
```

#### 3.2.5 Executor 模块

**职责**: 执行任务

**核心类**:
- `Executor`: 执行器基类
- `CPUExecutor`: CPU 执行器
- `GPUExecutor`: GPU 执行器

**关键实现**:

```cpp
// executor.h
class Executor {
public:
    virtual ~Executor() = default;
    
    // 执行任务
    virtual TaskResult execute(const Task& task) = 0;
    
    // 批量执行
    virtual std::vector<TaskResult> execute_batch(
        const std::vector<Task>& tasks) = 0;
    
    // 获取执行统计
    virtual ExecutionStats get_stats() const = 0;
};

class GPUExecutor : public Executor {
public:
    TaskResult execute(const Task& task) override {
        // 1. 准备数据
        prepare_data(task);
        
        // 2. 传输数据到 GPU
        transfer_to_gpu(task);
        
        // 3. 执行内核
        launch_kernel(task);
        
        // 4. 传输结果回 CPU
        transfer_from_gpu(task);
        
        // 5. 返回结果
        return get_result(task);
    }
    
private:
    void prepare_data(const Task& task);
    void transfer_to_gpu(const Task& task);
    void launch_kernel(const Task& task);
    void transfer_from_gpu(const Task& task);
};
```

## 4. 开发流程

### 4.1 代码规范

#### 命名规范
- **类名**: PascalCase (`TaskManager`)
- **函数名**: snake_case (`create_task`)
- **变量名**: snake_case (`task_count`)
- **常量名**: UPPER_SNAKE_CASE (`MAX_TASKS`)
- **命名空间**: snake_case (`heterogeneous`)

#### 代码风格
- 使用 4 空格缩进
- 行宽限制 100 字符
- 使用 `auto` 进行类型推导
- 使用 `nullptr` 替代 `NULL`

#### 注释规范
```cpp
/**
 * @brief 创建一个新的计算任务
 * 
 * @param name 任务名称
 * @param func 计算函数
 * @return std::shared_ptr<Task> 任务指针
 * 
 * @note 任务创建后需要调用 submit_task() 提交执行
 * @warning 不要在任务执行过程中修改任务参数
 */
std::shared_ptr<Task> create_task(const std::string& name, TaskFunc func);
```

### 4.2 Git 工作流

```bash
# 创建功能分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: add new feature"

# 推送到远程
git push origin feature/new-feature

# 创建 Pull Request
gh pr create --title "feat: add new feature" --body "Description"

# 合并后删除分支
git checkout main
git pull
git branch -d feature/new-feature
```

### 4.3 测试流程

```bash
# 运行所有测试
cd build
ctest

# 运行特定测试
./tests/test_task

# 运行带详细输出的测试
./tests/test_task --verbose

# 生成测试覆盖率报告
cmake .. -DENABLE_COVERAGE=ON
make -j$(nproc)
make test
gcov src/*.cpp
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 5. 调试技巧

### 5.1 日志系统

```cpp
#include "heterogeneous/log.h"

// 设置日志级别
heterogeneous::set_log_level(LogLevel::DEBUG);

// 使用日志
HETERO_LOG_DEBUG("Task {} created", task_id);
HETERO_LOG_INFO("Device {} initialized", device_name);
HETERO_LOG_WARN("Memory usage high: {}%", usage);
HETERO_LOG_ERROR("Task {} failed: {}", task_id, error_msg);
```

### 5.2 性能分析

```cpp
#include "heterogeneous/profiler.h"

// 开始性能分析
heterogeneous::Profiler::start("task_execution");

// 执行任务
execute_task(task);

// 结束性能分析
heterogeneous::Profiler::stop("task_execution");

// 生成报告
heterogeneous::Profiler::report("profile_report.txt");
```

### 5.3 内存调试

```cpp
// 启用内存调试
cmake .. -DENABLE_MEMORY_DEBUG=ON

// 使用内存检查工具
valgrind --leak-check=full ./tests/test_memory

// 使用 AddressSanitizer
cmake .. -DENABLE_ASAN=ON
```

## 6. 发布流程

### 6.1 版本号规范

```
主版本号.次版本号.修订号
  │        │        │
  │        │        └── 修复 bug
  │        └────────── 新增功能
  └─────────────────── 重大变更
```

### 6.2 发布检查清单

- [ ] 所有测试通过
- [ ] 文档更新完成
- [ ] 版本号更新
- [ ] CHANGELOG 更新
- [ ] 构建测试通过
- [ ] 性能测试通过

### 6.3 发布命令

```bash
# 更新版本号
# CMakeLists.txt: project(heterogeneous-computing VERSION 0.2.0)

# 创建发布分支
git checkout -b release/v0.2.0

# 构建发布版本
mkdir build-release && cd build-release
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# 打包
cpack

# 创建 Git 标签
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# 创建 GitHub Release
gh release create v0.2.0 ./heterogeneous-computing-0.2.0-Linux.tar.gz \
    --title "v0.2.0" --notes-file CHANGELOG.md
```

## 7. 参考资源

- [CMake Documentation](https://cmake.org/cmake/help/latest/)
- [CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-c-programming-guide/)
- [OpenCL Programming Guide](https://www.khronos.org/opencl/)
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [Git Flow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
