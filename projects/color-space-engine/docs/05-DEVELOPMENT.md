# 开发手册

## 1. 环境搭建

```bash
cd projects/color-space-engine
cargo build
```

## 2. 项目结构

```
color-space-engine/
├── src/
│   ├── lib.rs        # 库入口
│   ├── main.rs       # 演示
│   ├── rgb.rs        # RGB 颜色
│   ├── hsl.rs        # HSL 颜色
│   ├── hsv.rs        # HSV 颜色
│   ├── lab.rs        # Lab 颜色
│   ├── cmyk.rs       # CMYK 颜色
│   └── converter.rs  # 转换器
├── tests/
├── examples/
└── docs/
```

## 3. 运行

```bash
cargo run --release          # 演示
cargo test                   # 测试
cargo run --example conversion_demo  # 示例
```
