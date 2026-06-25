# 开发手册

## 1. 环境搭建

```bash
cd projects/layer-compositing-engine
mkdir build && cd build
cmake ..
make
```

## 2. 项目结构

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

## 3. 编译

```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
make
```

## 4. 运行

```bash
ctest -V
./demo_blending
./demo_masking
```
