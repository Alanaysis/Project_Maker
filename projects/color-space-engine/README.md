# 颜色空间引擎 (Color Space Engine)

实现颜色空间转换和管理，支持 RGB、HSL、HSV、Lab、CMYK 之间的相互转换。

## 核心循环

```
颜色输入 → 空间转换 → 颜色操作 → 颜色输出
```

## 学习目标

- 理解颜色空间原理
- 掌握颜色转换
- 学会颜色管理

## 技术栈

- 主语言：Rust
- 依赖：无

## 项目结构

```
color-space-engine/
├── src/
│   ├── lib.rs        # 库入口
│   ├── main.rs       # 演示
│   ├── rgb.rs        # RGB
│   ├── hsl.rs        # HSL
│   ├── hsv.rs        # HSV
│   ├── lab.rs        # Lab
│   ├── cmyk.rs       # CMYK
│   └── converter.rs  # 转换器
├── tests/
├── examples/
└── docs/
```

## 快速开始

### 运行测试

```bash
cargo test
```

### 运行示例

```bash
cargo run --example conversion_demo
cargo run --example color_distance
```

### 演示

```bash
cargo run --release
```

## 核心功能

```rust
use color_space::{RGB, Converter};

let rgb = RGB::from_u8(255, 128, 64);
let hsl = Converter::rgb_to_hsl(&rgb);
let lab = Converter::rgb_to_lab(&rgb);

let rgb2 = Converter::hsl_to_rgb(&hsl);
let de = Converter::lab_delta_e(&lab, &other_lab);
```
