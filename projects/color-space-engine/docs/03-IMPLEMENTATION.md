# 实现细节

## 1. RGB -> HSL

### 算法
根据最大/最小通道值计算亮度和饱和度。

### 核心代码
```rust
let max = rgb.r.max(rgb.g).max(rgb.b);
let min = rgb.r.min(rgb.g).min(rgb.b);
let l = (max + min) / 2.0;
```

## 2. RGB -> Lab (CIE)

### 算法
1. 逆 Gamma 校正
2. RGB -> XYZ (D65)
3. XYZ -> Lab

## 3. Delta E

### 算法
CIE76 公式：欧氏距离在 Lab 空间。
