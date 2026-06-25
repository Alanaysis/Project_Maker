# 开发手册

## 1. 环境搭建

```bash
cd projects/3d-modeling-engine
mkdir build && cd build
cmake ..
make
```

## 2. 项目结构

```
3d-modeling-engine/
├── include/3d_engine/
│   ├── 3d_engine.h
│   ├── vec3.h
│   ├── mat4.h
│   ├── mesh.h
│   ├── transform.h
│   └── primitive.h
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
./demo_mesh
./demo_transform
```
