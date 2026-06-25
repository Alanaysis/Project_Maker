# 实现细节 - 人体姿态估计

## 核心实现

### 1. 高斯热力图生成

```python
def generate_heatmaps(keypoints, keypoint_weights, heatmap_size, sigma=2.0):
    """
    从关键点坐标生成高斯热力图。
    
    公式: H(x,y) = exp(-((x-x_k)^2 + (y-y_k)^2) / (2*sigma^2))
    """
    # 创建坐标网格
    y_coords = torch.arange(h, device=device, dtype=torch.float32)
    x_coords = torch.arange(w, device=device, dtype=torch.float32)
    y_grid, x_grid = torch.meshgrid(y_coords, x_coords, indexing="ij")
    
    # 计算高斯热力图
    heatmaps = torch.exp(
        -((x_grid[None, None] - kx) ** 2 + (y_grid[None, None] - ky) ** 2)
        / (2 * sigma ** 2)
    )
    
    # 应用可见性权重
    heatmaps = heatmaps * weights
    
    return heatmaps
```

**关键点**:
- 使用 `torch.meshgrid` 创建坐标网格
- 归一化关键点坐标到热力图空间
- 应用可见性权重

### 2. Soft-Argmax 实现

```python
def soft_argmax(heatmaps, beta=100.0):
    """
    可微的关键点提取。
    
    公式: x = sum(x * softmax(beta * H))
    """
    # 应用 softmax
    attention = F.softmax(beta * heatmaps_flat, dim=2)
    
    # 计算期望坐标
    x_expect = (attention * x_flat).sum(dim=2)
    y_expect = (attention * y_flat).sum(dim=2)
    
    return keypoints, confidence
```

**关键点**:
- beta 参数控制"锐度"
- beta 越大越接近 argmax
- 可微，支持端到端训练

### 3. MSE 损失实现

```python
class KeypointMSELoss(nn.Module):
    def forward(self, pred, target, weights=None):
        if weights is not None:
            # 按关键点计算损失
            mse_per_kp = ((pred - target) ** 2).mean(dim=2)
            weighted_mse = mse_per_kp * weights
            loss = weighted_mse.sum() / weights.sum().clamp(min=1.0)
        else:
            loss = F.mse_loss(pred, target)
        return {"loss": loss}
```

**关键点**:
- 支持按关键点加权
- 处理不可见关键点
- 返回损失字典

### 4. OHKM 损失实现

```python
class KeypointOHKMLoss(nn.Module):
    def forward(self, pred, target, weights=None):
        # 计算每个关键点的损失
        mse_per_kp = ((pred - target) ** 2).mean(dim=2)
        
        # 应用权重
        mse_per_kp = mse_per_kp * weights
        
        # 选择 Top-K 困难关键点
        topk_loss, _ = torch.topk(mse_per_kp, self.topk, dim=1)
        
        return {"loss": topk_loss.mean()}
```

**关键点**:
- 只关注困难样本
- topk 参数控制关注数量
- 可以提升模型精度

### 5. 关键点提取实现

```python
def extract_keypoints(heatmaps, threshold=0.1):
    """从热力图中提取关键点坐标。"""
    # 展平空间维度
    heatmaps_flat = heatmaps.view(batch_size, num_keypoints, -1)
    
    # 找到最大值和位置
    confidence, max_idx = torch.max(heatmaps_flat, dim=2)
    
    # 转换为 2D 坐标
    y_coords = max_idx / w
    x_coords = max_idx % w
    
    # 归一化到 [0, 1]
    x_norm = x_coords / (w - 1)
    y_norm = y_coords / (h - 1)
    
    return keypoints, confidence
```

**关键点**:
- 使用 argmax 找峰值
- 转换为 2D 坐标
- 归一化到 [0, 1]

### 6. 亚像素精度提取

```python
def extract_keypoints_with_subpixel(heatmaps, threshold=0.1):
    """使用亚像素精度提取关键点。"""
    # 中心差分
    if 0 < xi < w - 1:
        left = heatmaps[b, k, yi, xi - 1]
        right = heatmaps[b, k, yi, xi + 1]
        center = heatmaps[b, k, yi, xi]
        x_offset = 0.5 * (left - right) / (left + right - 2 * center)
    
    return keypoints, confidence
```

**关键点**:
- 在 argmax 邻域内插值
- 提高精度
- 处理边界情况

### 7. PCK 评估实现

```python
def compute_pck(pred_keypoints, target_keypoints, threshold=0.2):
    """计算 PCK。"""
    # 计算欧氏距离
    dist = torch.norm(pred_keypoints - target_keypoints, dim=2)
    
    # 使用图像对角线作为参考长度
    ref_len = np.sqrt(2)
    
    # 计算正确率
    correct = (dist < threshold * ref_len).float()
    
    return correct.mean()
```

**关键点**:
- 使用归一化坐标
- 图像对角线作为参考
- 返回 0-1 的分数

## 训练流程

### 1. 数据准备

```python
dataset = SyntheticPoseDataset(
    num_samples=100,
    image_size=(128, 128),
    heatmap_size=(64, 64),
    num_keypoints=17,
)
loader = create_dataloader(dataset, batch_size=8)
```

### 2. 模型构建

```python
model = SimplePoseNet(num_keypoints=17, input_size=128)
criterion = KeypointMSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
```

### 3. 训练循环

```python
for epoch in range(num_epochs):
    for batch in loader:
        images = batch["image"]
        target_hm = batch["heatmaps"]
        target_w = batch["weights"]
        
        # 前向传播
        pred_hm = model(images)
        
        # 计算损失
        loss = criterion(pred_hm, target_hm, target_w)["loss"]
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

### 4. 验证

```python
model.eval()
with torch.no_grad():
    pred_hm = model(val_images)
    pred_kp, conf = extract_keypoints(pred_hm)
    pck = compute_pck(pred_kp, val_keypoints)
```

## 性能优化

### 1. 混合精度训练

```python
scaler = torch.cuda.amp.GradScaler()

with torch.cuda.amp.autocast():
    pred_hm = model(images)
    loss = criterion(pred_hm, target_hm)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 2. 数据加载优化

```python
loader = DataLoader(
    dataset,
    batch_size=16,
    num_workers=4,  # 多进程加载
    pin_memory=True,  # 锁页内存
    prefetch_factor=2,  # 预取
)
```

### 3. 模型优化

```python
# 使用 JIT 编译
model = torch.jit.script(model)

# 使用 ONNX 导出
torch.onnx.export(model, dummy_input, "model.onnx")
```

## 常见问题

### Q1: 热力图全为零

**原因**: 关键点坐标超出范围或权重为 0

**解决**: 检查数据预处理

### Q2: 训练不收敛

**原因**: 学习率过大或损失函数不当

**解决**: 使用更小的学习率，检查损失函数

### Q3: 关键点精度低

**原因**: sigma 不合适或分辨率太低

**解决**: 调整 sigma，使用更高的热力图分辨率
