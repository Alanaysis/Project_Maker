# 图层合成引擎 (Layer Compositing Engine)

实现图层混合和蒙版系统，支持多种混合模式和形态学蒙版操作。

## 核心循环

```
图层输入 → 混合计算 → 遮罩应用 → 合成输出
```

## 学习目标

- 理解图层合成原理
- 掌握混合模式
- 学会遮罩处理

## 技术栈

- 主语言：C++17
- 框架：无
- 依赖：无

## 项目结构

```
layer-compositing-engine/
├── include/layer_compositing/
│   ├── layer_compositing.h
│   ├── image.h
│   ├── blending.h
│   ├── masking.h
│   └── layer.h
├── src/
├── tests/
├── examples/
└── docs/
```

## 快速开始

### 编译

```bash
cd projects/layer-compositing-engine
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
./demo_blending
./demo_masking
```

## 核心功能

### 混合模式

```cpp
#include "layer_compositing/blending.h"

Image top = ...;
Image bottom = ...;
Image result = blend_multiply(top, bottom);
Image result2 = blend_screen(top, bottom);
Image result3 = blend_overlay(top, bottom);
```

### 蒙版操作

```cpp
#include "layer_compositing/masking.h"

Image masked = apply_mask(src, mask);
Image eroded = erode(mask, 2);
Image dilated = dilate(mask, 2);
```

### 图层合成

```cpp
#include "layer_compositing/layer.h"

std::vector<Layer> layers;
layers.emplace_back(bg, "background", 1.0f);
layers.emplace_back(overlay, "overlay", 0.8f);
layers.back().blend_mode = 1; // multiply

Image result = composite_layers(layers, width, height);
```
