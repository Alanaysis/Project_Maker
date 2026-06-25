# 技术设计文档

## 1. 架构概述

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  空间滤波    │    │  颜色变换    │    │  几何变换    │
│  Filters    │    │  Color      │    │  Transform  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                      ┌──────────┐
                      │  Image   │
                      └──────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| Image | 图像数据结构 | `include/image_engine/image.h` |
| Filters | 空间滤波 | `include/image_engine/filters.h` |
| Color | 颜色变换 | `include/image_engine/color.h` |
| Transform | 几何变换 | `include/image_engine/transform.h` |

## 2. 数据设计

### Image 结构
```
width × height × channels
data: vector<uint8_t>
```

### 像素访问
- RGB: `set_pixel_rgb(x, y, r, g, b)` / `get_pixel_rgb(x, y, r, g, b)`
- Channel: `set_pixel(x, y, channel, value)`

## 3. 接口设计

### Filters
```cpp
Image gaussian_blur(const Image& src, int radius);
Image box_blur(const Image& src, int radius);
Image sharpen(const Image& src);
Image threshold(const Image& src, uint8_t thresh);
```

### Color
```cpp
Image grayscale(const Image& src);
Image invert(const Image& src);
Image sepia(const Image& src);
Image brightness_contrast(const Image& src, float brightness, float contrast);
Image histogram_equalize(const Image& src);
```

### Transform
```cpp
Image rotate90(const Image& src, bool clockwise);
Image scale(const Image& src, float factor);
Image crop(const Image& src, int x, int y, int w, int h);
Image flip_horizontal(const Image& src);
```
