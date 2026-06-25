# 图像处理引擎 (Image Processing Engine)

实现常见的图像处理算法，包括空间滤波、颜色变换和几何变换。

## 核心循环

```
图像输入 → 算法处理 → 图像输出
```

## 学习目标

- 理解常见图像处理算法原理
- 掌握空间滤波和颜色空间变换
- 学会几何变换的实现

## 技术栈

- 主语言：C++17
- 框架：无
- 依赖：无

## 项目结构

```
image-processing-engine/
├── include/image_engine/
│   ├── image_engine.h  # 聚合头
│   ├── image.h         # 图像类
│   ├── filters.h       # 滤镜
│   ├── color.h         # 颜色变换
│   ├── transform.h     # 几何变换
│   └── vec2.h          # 2D向量
├── src/                # 源码
├── tests/              # 测试
├── examples/           # 示例
└── docs/               # 文档
```

## 快速开始

### 编译

```bash
cd projects/image-processing-engine
mkdir build && cd build
cmake ..
make
```

### 运行测试

```bash
ctest
```

### 运行示例

```bash
./basic_filters
./color_transform
./edge_detection
```

## 核心功能

### 空间滤波

```cpp
#include "image_engine/filters.h"

Image img = ...;
Image blurred = gaussian_blur(img, 3);
Image sharp = sharpen(img);
Image thresh = threshold(img, 128);
```

### 颜色变换

```cpp
#include "image_engine/color.h"

Image gray = grayscale(img);
Image sepia = sepia(img);
Image eq = histogram_equalize(img);
```

### 几何变换

```cpp
#include "image_engine/transform.h"

Image rotated = rotate90(img, true);
Image scaled = scale(img, 0.5f);
Image flipped = flip_horizontal(img);
```
