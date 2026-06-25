# 实现细节

## 1. 混合模式

### 核心实现
每个混合模式对应一个函数，对 RGB 三个通道分别计算。

### 关键代码
```cpp
uint8_t blend_multiply(uint8_t top, uint8_t bottom) {
    return static_cast<uint8_t>((top * bottom) / 255);
}
```

## 2. 图层合成

### 算法
从底层到顶层逐层混合，考虑图层不透明度。

## 3. 蒙版操作

### 腐蚀/膨胀
形态学操作，取邻域的最小/最大值。
