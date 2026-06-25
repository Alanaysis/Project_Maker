# 技术设计文档

## 1. 架构概述

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Layers   │    │ Blending │    │  Masking │
│ (Opacity) │───▶│ (Modes)  │───▶│ (Alpha)  │
└──────────┘    └──────────┘    └──────────┘
       │                           │
       └──────────┬────────────────┘
                  ▼
           ┌──────────────┐
           │ Composite    │
           │ (Final)      │
           └──────────────┘
```

### 模块划分

| 模块 | 职责 | 文件 |
|------|------|------|
| Image | 图像数据结构 | `include/layer_compositing/image.h` |
| Blending | 混合模式 | `include/layer_compositing/blending.h` |
| Masking | 蒙版操作 | `include/layer_compositing/masking.h` |
| Layer | 图层管理 | `include/layer_compositing/layer.h` |

## 2. 混合模式

### Normal
`result = top * alpha + bottom * (1 - alpha)`

### Multiply
`result = top * bottom / 255`

### Screen
`result = 255 - (255 - top) * (255 - bottom) / 255`

### Overlay
`bottom < 128 ? Multiply(top, bottom*2) : Screen(top, bottom*2+1)`

## 3. 蒙版操作

### Alpha Mask
`alpha = src_alpha * mask_alpha / 255`

### Erode
取邻域最小 alpha 值

### Dilate
取邻域最大 alpha 值
