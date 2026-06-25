# GPU 着色器库

一个全面的 GPU 着色器库，包含 GLSL 和 HLSL 实现的各种图形学技术。

## 项目简介

本项目是一个学习和参考用的 GPU 着色器库，涵盖了从基础光照到高级渲染技术的完整实现。每个着色器都有详细的中文注释，适合图形学学习者和开发者参考。

## 快速开始

### 环境要求

- CMake 3.20+
- OpenGL 4.5+ 兼容 GPU
- C++17/20 编译器
- GLFW 3.3+
- GLM 0.9.9+

### 编译

```bash
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 运行示例

```bash
./bin/demo_basic_rendering   # 基础渲染
./bin/demo_pbr              # PBR 渲染
./bin/demo_postprocess      # 后处理效果
./bin/demo_particles        # 粒子系统
./bin/demo_water            # 水面渲染
```

## 着色器分类

### 基础着色器 (Basic)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 顶点变换 | `basic/vertex_transform.glsl` | MVP 矩阵变换 |
| 片段输出 | `basic/fragment_output.glsl` | 颜色输出和 Gamma 校正 |
| 几何着色器 | `basic/geometry_passthrough.glsl` | 图元处理 |
| 曲面细分 | `basic/tessellation_control.glsl` | 自适应细分控制 |
| 曲面细分求值 | `basic/tessellation_evaluation.glsl` | 置换贴图 |
| 计算着色器 | `basic/compute_prefix_sum.glsl` | 并行前缀和 |

### 光照模型 (Lighting)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 环境光 | `lighting/ambient_light.glsl` | 全局环境光 |
| 漫反射 | `lighting/diffuse_light.glsl` | Lambert 模型 |
| 镜面反射 | `lighting/specular_light.glsl` | Phong 高光 |
| Blinn-Phong | `lighting/blinn_phong.glsl` | 经典光照模型 |
| PBR | `lighting/pbr_lighting.glsl` | Cook-Torrance BRDF |
| 阴影映射 | `lighting/shadow_mapping.glsl` | PCF 软阴影 |

### 材质效果 (Material)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 法线贴图 | `material/normal_mapping.glsl` | 切线空间法线 |
| 视差贴图 | `material/parallax_mapping.glsl` | POM 视差效果 |
| 环境遮蔽 | `material/ambient_occlusion.glsl` | SSAO |
| 反射 | `material/reflection.glsl` | 环境/SSR 反射 |
| 折射 | `material/refraction.glsl` | Snell 定律 |
| 透明度 | `material/transparency.glsl` | Alpha 混合 |

### 后处理效果 (Post-Process)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 高斯模糊 | `postprocess/gaussian_blur.glsl` | 可分离模糊 |
| 运动模糊 | `postprocess/motion_blur.glsl` | 速度缓冲 |
| 景深 | `postprocess/depth_of_field.glsl` | 散景效果 |
| Bloom | `postprocess/bloom.glsl` | HDR 泛光 |
| 色调映射 | `postprocess/tone_mapping.glsl` | ACES/Reinhard |
| 色彩校正 | `postprocess/color_correction.glsl` | LUT 颜色分级 |
| 锐化 | `postprocess/sharpening.glsl` | Unsharp Mask |
| 边缘检测 | `postprocess/edge_detection.glsl` | Sobel/Laplacian |

### 粒子系统 (Particle)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 粒子发射 | `particle/particle_emitter.glsl` | GPU 粒子发射 |
| 粒子更新 | `particle/particle_update.glsl` | 物理更新 |
| 粒子渲染 | `particle/particle_render.glsl` | Billboard 渲染 |
| 粒子片段 | `particle/particle_fragment.glsl` | 软粒子 |
| 粒子物理 | `particle/particle_physics.glsl` | 碰撞检测 |

### 水体渲染 (Water)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 水面 | `water/water_surface.glsl` | Gerstner 波浪 |
| 焦散 | `water/water_caustics.glsl` | 水底光斑 |

### 天空和大气 (Sky)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 大气散射 | `sky/atmospheric_scattering.glsl` | Rayleigh/Mie |
| 体积云 | `sky/volumetric_clouds.glsl` | 噪声云层 |
| 天空盒 | `sky/skybox.glsl` | 立方体贴图 |

### 体积效果 (Volume)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 体积雾 | `volume/volumetric_fog.glsl` | 高度雾 |
| 体积光 | `volume/volumetric_light.glsl` | 光轴效果 |
| 烟雾模拟 | `volume/smoke_simulation.glsl` | Navier-Stokes |

### 优化技术 (Optimization)
| 着色器 | 文件 | 说明 |
|--------|------|------|
| 实例化渲染 | `optimization/instanced_rendering.glsl` | 硬件实例化 |
| 间接渲染 | `optimization/indirect_rendering.glsl` | GPU 驱动 |
| 遮挡剔除 | `optimization/occlusion_culling.glsl` | Hi-Z 剔除 |
| LOD 计算 | `optimization/lod_computation.glsl` | 自动 LOD |

## 学习路径

### 初学者
1. 基础着色器 → 光照模型 → 材质效果
2. 理解 MVP 变换和光照方程

### 中级
3. 后处理效果 → 粒子系统
4. 掌握多 Pass 渲染和计算着色器

### 高级
5. 水体渲染 → 天空大气 → 体积效果
6. 优化技术 → 性能调优

## 项目结构

```
gpu-shader-library/
├── shaders/
│   ├── glsl/                    # GLSL 着色器
│   │   ├── basic/              # 基础着色器
│   │   ├── lighting/           # 光照模型
│   │   ├── material/           # 材质效果
│   │   ├── postprocess/        # 后处理
│   │   ├── particle/           # 粒子系统
│   │   ├── water/              # 水体渲染
│   │   ├── sky/                # 天空大气
│   │   ├── volume/             # 体积效果
│   │   └── optimization/       # 优化技术
│   └── hlsl/                   # HLSL 着色器
├── include/                     # C++ 头文件
├── src/                         # C++ 源文件
│   ├── core/                   # 核心模块
│   └── utils/                  # 工具类
├── examples/                    # 示例程序
├── docs/                        # 文档
├── CMakeLists.txt
└── README.md
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
