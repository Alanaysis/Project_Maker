# 开发手册

## 1. 环境搭建

```bash
cd projects/rasterization-engine
cargo build
```

## 2. 项目结构

```
rasterization-engine/
├── src/
│   ├── lib.rs        # 库入口
│   ├── main.rs       # 演示
│   ├── geometry.rs   # 几何结构
│   ├── rasterizer.rs # 帧缓冲/光栅化
│   ├── renderer.rs   # 图层合成
│   └── shapes.rs     # 形状绘制
├── tests/            # 测试
├── examples/         # 示例
└── docs/             # 文档
```

## 3. 运行

```bash
cargo run --release          # 演示
cargo test                   # 测试
cargo run --example triangle_rasterization  # 示例
```
