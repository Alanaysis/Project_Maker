# 开发手册

## 1. 环境搭建

```bash
cd projects/image-processing-engine
mkdir build && cd build
cmake ..
make
```

## 2. 项目结构

```
image-processing-engine/
├── include/image_engine/  # 头文件
│   ├── image_engine.h    # 聚合头
│   ├── image.h           # 图像类
│   ├── filters.h         # 滤镜
│   ├── color.h           # 颜色变换
│   ├── transform.h       # 几何变换
│   └── vec2.h            # 2D向量
├── src/                   # 源码
├── tests/                 # 测试
├── examples/              # 示例
└── docs/                  # 文档
```

## 3. 编译

```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```

## 4. 运行测试

```bash
ctest -V
```

## 5. 运行示例

```bash
./basic_filters
./color_transform
./edge_detection
```
