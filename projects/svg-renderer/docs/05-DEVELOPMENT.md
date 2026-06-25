# 开发手册

## 1. 环境搭建

```bash
cd projects/svg-renderer
cargo build
```

## 2. 项目结构

```
svg-renderer/
├── src/
│   ├── lib.rs        # 库入口
│   ├── main.rs       # 演示
│   ├── parser.rs     # SVG 解析
│   ├── path.rs       # 路径
│   ├── shapes.rs     # 形状
│   ├── renderer.rs   # 渲染器
│   └── color.rs      # 颜色
├── tests/
├── examples/
└── docs/
```

## 3. 运行

```bash
cargo run --release          # 演示
cargo test                   # 测试
cargo run --example star_rendering  # 示例
```
