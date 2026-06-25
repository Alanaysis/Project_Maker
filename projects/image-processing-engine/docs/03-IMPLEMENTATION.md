# 实现细节

## 1. 高斯模糊

### 算法
对每个像素计算邻域加权平均，权重由高斯分布确定。

### 核心代码
```cpp
for (int ky = -radius; ky <= radius; ky++) {
    for (int kx = -radius; kx <= radius; kx++) {
        float w = kernel[kx + radius] * kernel[ky + radius];
        // 累加加权值
    }
}
```

## 2. 方框模糊

### 算法
对每个像素计算邻域简单平均。

## 3. 锐化

### 算法
Unsharp Mask: `center * 5 - (neighbors sum)`

## 4. 灰度转换

### 公式
`gray = 0.299*r + 0.587*g + 0.114*b`

## 5. 直方图均衡化

### 算法
1. 计算直方图
2. 计算累积分布
3. 用 CDF 映射像素值
