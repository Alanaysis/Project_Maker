# 技术设计文档

## 1. 架构概述

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│   RGB    │    │  HSL/HSV  │    │   Lab    │
│  CMYK    │    │  色相环   │    │  Delta E │
└──────────┘    └──────────┘    └──────────┘
       │                    │
       └───────┬────────────┘
               ▼
         ┌─────────────┐
         │  Converter  │
         └─────────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| RGB | 红绿蓝颜色 | `src/rgb.rs` |
| HSL | 色相/饱和度/亮度 | `src/hsl.rs` |
| HSV | 色相/饱和度/明度 | `src/hsv.rs` |
| Lab | CIE 感知均匀空间 | `src/lab.rs` |
| CMYK | 印刷颜色空间 | `src/cmyk.rs` |
| Converter | 转换工具 | `src/converter.rs` |

## 2. 颜色空间转换

### RGB -> HSL
1. 计算 max, min
2. L = (max + min) / 2
3. 如果 max != min, 计算 S 和 H

### RGB -> Lab (CIE)
1. RGB -> XYZ (D65 白点)
2. XYZ -> Lab

### Delta E
```
delta_e = sqrt((L1-L2)² + (a1-a2)² + (b1-b2)²)
```

## 3. 接口设计

```rust
Converter::rgb_to_hsl(rgb) -> HSL
Converter::hsl_to_rgb(hsl) -> RGB
Converter::rgb_to_lab(rgb) -> Lab
Converter::lab_delta_e(lab1, lab2) -> f64
```
