# 实现细节 - 深度估计

## 1. 编码器实现

### 1.1 ConvBlock

基础卷积块：Conv + BatchNorm + ReLU

```python
class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))
```

### 1.2 ResidualBlock

残差块：两层卷积 + 跳跃连接

```python
class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = ConvBlock(channels, channels)
        self.conv2 = nn.Sequential(
            nn.Conv2d(channels, channels, 3, 1, 1),
            nn.BatchNorm2d(channels),
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.conv2(out)
        out = out + residual
        return self.relu(out)
```

### 1.3 DepthEncoder

多层编码器：

```python
class DepthEncoder(nn.Module):
    def __init__(self, in_channels=3, base_channels=64):
        super().__init__()

        # Stem: 快速降低分辨率
        self.stem = nn.Sequential(
            ConvBlock(in_channels, base_channels, kernel_size=7, stride=2, padding=3),
            nn.MaxPool2d(3, stride=2, padding=1),
        )

        # 编码器各层
        self.layer1 = self._make_layer(base_channels, base_channels * 2)
        self.layer2 = self._make_layer(base_channels * 2, base_channels * 4)
        self.layer3 = self._make_layer(base_channels * 4, base_channels * 8)
        self.layer4 = self._make_layer(base_channels * 8, base_channels * 16)

    def _make_layer(self, in_channels, out_channels):
        return nn.Sequential(
            ConvBlock(in_channels, out_channels, stride=2),
            ResidualBlock(out_channels),
            ResidualBlock(out_channels),
        )

    def forward(self, x):
        features = []
        x = self.stem(x)       # 1/4
        features.append(x)
        x = self.layer1(x)     # 1/8
        features.append(x)
        x = self.layer2(x)     # 1/16
        features.append(x)
        x = self.layer3(x)     # 1/32
        features.append(x)
        x = self.layer4(x)     # 1/64
        features.append(x)
        return features
```

## 2. 解码器实现

### 2.1 DecoderBlock

解码器块：反卷积 + 跳跃连接 + 卷积

```python
class DecoderBlock(nn.Module):
    def __init__(self, in_channels, skip_channels, out_channels):
        super().__init__()
        self.up = nn.ConvTranspose2d(
            in_channels, in_channels // 2, kernel_size=3, stride=2, padding=1, output_padding=1
        )
        self.conv = nn.Sequential(
            ConvBlock(in_channels // 2 + skip_channels, out_channels),
            ResidualBlock(out_channels),
        )

    def forward(self, x, skip=None):
        x = self.up(x)
        if skip is not None:
            x = torch.cat([x, skip], dim=1)
        return self.conv(x)
```

### 2.2 DepthDecoder

完整解码器：

```python
class DepthDecoder(nn.Module):
    def __init__(self, base_channels=64):
        super().__init__()
        encoder_channels = [
            base_channels,
            base_channels * 2,
            base_channels * 4,
            base_channels * 8,
            base_channels * 16,
        ]

        self.decoder4 = DecoderBlock(encoder_channels[4], encoder_channels[3], encoder_channels[3])
        self.decoder3 = DecoderBlock(encoder_channels[3], encoder_channels[2], encoder_channels[2])
        self.decoder2 = DecoderBlock(encoder_channels[2], encoder_channels[1], encoder_channels[1])
        self.decoder1 = DecoderBlock(encoder_channels[1], encoder_channels[0], encoder_channels[0])

        self.final_up = nn.Sequential(
            nn.ConvTranspose2d(encoder_channels[0], encoder_channels[0] // 2, 3, 2, 1, 1),
            ConvBlock(encoder_channels[0] // 2, encoder_channels[0] // 4),
        )

        self.depth_head = nn.Sequential(
            nn.Conv2d(encoder_channels[0] // 4, 32, 3, 1, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, features):
        x = features[4]
        x = self.decoder4(x, features[3])
        x = self.decoder3(x, features[2])
        x = self.decoder2(x, features[1])
        x = self.decoder1(x, features[0])
        x = self.final_up(x)
        depth = self.depth_head(x)
        return depth
```

## 3. 损失函数实现

### 3.1 SILog Loss

尺度不变对数损失：

```python
class SILogLoss(nn.Module):
    def __init__(self, lambda_weight=0.5, min_depth=1e-3):
        super().__init__()
        self.lambda_weight = lambda_weight
        self.min_depth = min_depth

    def forward(self, pred, target, valid_mask=None):
        pred = torch.clamp(pred, min=self.min_depth)
        target = torch.clamp(target, min=self.min_depth)

        log_diff = torch.log(pred) - torch.log(target)

        if valid_mask is not None:
            log_diff = log_diff * valid_mask
            n = valid_mask.sum() + 1e-8
        else:
            n = log_diff.numel()

        first_term = (log_diff ** 2).sum() / n
        second_term = self.lambda_weight * (log_diff.sum() ** 2) / (n ** 2)

        return first_term - second_term
```

### 3.2 Gradient Loss

梯度损失：

```python
class GradientLoss(nn.Module):
    def forward(self, pred, target, valid_mask=None):
        # x 方向梯度
        pred_dx = pred[:, :, :, 1:] - pred[:, :, :, :-1]
        target_dx = target[:, :, :, 1:] - target[:, :, :, :-1]

        # y 方向梯度
        pred_dy = pred[:, :, 1:, :] - pred[:, :, :-1, :]
        target_dy = target[:, :, 1:, :] - target[:, :, :-1, :]

        loss_x = torch.abs(pred_dx - target_dx)
        loss_y = torch.abs(pred_dy - target_dy)

        return loss_x.mean() + loss_y.mean()
```

### 3.3 BerHu Loss

Reverse Huber 损失：

```python
class BerHuLoss(nn.Module):
    def __init__(self, threshold_ratio=0.2):
        super().__init__()
        self.threshold_ratio = threshold_ratio

    def forward(self, pred, target, valid_mask=None):
        diff = torch.abs(pred - target)
        c = self.threshold_ratio * diff.max()

        loss = torch.where(
            diff <= c,
            diff,
            (diff ** 2 + c ** 2) / (2 * c),
        )

        return loss.mean()
```

## 4. 数据集实现

### 4.1 合成深度生成

```python
def _generate_depth(self, scene_type):
    h, w = self.image_size
    y, x = torch.meshgrid(
        torch.linspace(-1, 1, h),
        torch.linspace(-1, 1, w),
        indexing="ij",
    )

    if scene_type == "plane":
        # 平面: 均匀深度
        depth_value = np.random.uniform(min_d, max_d)
        depth = torch.full((1, h, w), depth_value)

    elif scene_type == "slope":
        # 斜面: 深度随位置线性变化
        angle = np.random.uniform(0, 2 * np.pi)
        slope_dir = torch.cos(torch.tensor(angle)) * x + torch.sin(torch.tensor(angle)) * y
        depth = min_d + (max_d - min_d) * (slope_dir + 1) / 2

    elif scene_type == "stairs":
        # 阶梯: 多个深度层级
        num_steps = np.random.randint(3, 8)
        step_size = (max_d - min_d) / num_steps
        # ...

    elif scene_type == "sphere":
        # 球体: 中心近，边缘远
        cx = np.random.uniform(-0.5, 0.5)
        cy = np.random.uniform(-0.5, 0.5)
        dist = torch.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        depth = min_d + (max_d - min_d) * dist
```

### 4.2 合成图像生成

```python
def _generate_image(self, depth):
    # 归一化深度
    depth_norm = (depth - min_d) / (max_d - min_d)

    # 颜色通道
    r = 1.0 - 0.5 * depth_norm  # 近处偏红
    g = 0.5 + 0.3 * torch.sin(depth_norm * np.pi)  # 中间偏绿
    b = 0.3 + 0.7 * depth_norm  # 远处偏蓝

    image = torch.cat([r, g, b], dim=0)

    # 添加纹理
    texture = torch.rand(3, h, w) * 0.2
    image = image + texture

    return torch.clamp(image, 0, 1)
```

## 5. 训练实现

### 5.1 训练循环

```python
def train_epoch(self, dataloader):
    self.model.train()
    total_losses = {}
    num_batches = 0

    for images, depths, masks in dataloader:
        images = images.to(self.device)
        depths = depths.to(self.device)
        masks = masks.to(self.device)

        # 前向传播
        pred_depths = self.model(images)

        # 计算损失
        loss_dict = self.criterion(pred_depths, depths, masks)
        loss = loss_dict["total"]

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.gradient_clip)

        self.optimizer.step()

        # 记录损失
        for key, value in loss_dict.items():
            if key not in total_losses:
                total_losses[key] = 0
            total_losses[key] += value.item()
        num_batches += 1

    return {key: value / num_batches for key, value in total_losses.items()}
```

### 5.2 验证循环

```python
@torch.no_grad()
def validate(self, dataloader):
    self.model.eval()
    all_metrics = []

    for images, depths, masks in dataloader:
        images = images.to(self.device)
        depths = depths.to(self.device)
        masks = masks.to(self.device)

        pred_depths = self.model(images)
        metrics = compute_depth_metrics(pred_depths, depths, masks)
        all_metrics.append(metrics)

    # 平均指标
    avg_metrics = {}
    for key in all_metrics[0].keys():
        avg_metrics[key] = sum(m[key] for m in all_metrics) / len(all_metrics)

    return avg_metrics
```

## 6. 评估指标实现

### 6.1 指标计算

```python
def compute_depth_metrics(pred, target, valid_mask=None, min_depth=1e-3, max_depth=80.0):
    pred = torch.clamp(pred, min=min_depth, max=max_depth)
    target = torch.clamp(target, min=min_depth, max=max_depth)

    if valid_mask is not None:
        pred = pred[valid_mask > 0]
        target = target[valid_mask > 0]

    thresh = torch.max(pred / target, target / pred)

    delta1 = (thresh < 1.25).float().mean().item()
    delta2 = (thresh < 1.25 ** 2).float().mean().item()
    delta3 = (thresh < 1.25 ** 3).float().mean().item()

    abs_rel = (torch.abs(pred - target) / target).mean().item()
    sq_rel = (((pred - target) ** 2) / target).mean().item()
    rmse = torch.sqrt(((pred - target) ** 2).mean()).item()
    rmse_log = torch.sqrt(((torch.log(pred) - torch.log(target)) ** 2).mean()).item()

    return {
        "abs_rel": abs_rel,
        "sq_rel": sq_rel,
        "rmse": rmse,
        "rmse_log": rmse_log,
        "delta1": delta1,
        "delta2": delta2,
        "delta3": delta3,
    }
```

## 7. 可视化实现

### 7.1 深度着色

```python
def colorize_depth(depth, colormap="jet"):
    depth_np = normalize_depth(depth).cpu().numpy()
    colored = _jet_colormap(depth_np)
    return torch.from_numpy(colored).float()
```

### 7.2 Jet 颜色映射

```python
def _jet_colormap(depth):
    h, w = depth.shape
    colored = np.zeros((3, h, w), dtype=np.float32)

    for i in range(h):
        for j in range(w):
            val = depth[i, j]
            if val < 0.125:
                r, g, b = 0, 0, 0.5 + 4 * val
            elif val < 0.375:
                r, g, b = 0, 4 * (val - 0.125), 1
            elif val < 0.625:
                r, g, b = 4 * (val - 0.375), 1, 1 - 4 * (val - 0.375)
            elif val < 0.875:
                r, g, b = 1, 1 - 4 * (val - 0.625), 0
            else:
                r, g, b = 1 - 4 * (val - 0.875), 0, 0
            colored[0, i, j] = r
            colored[1, i, j] = g
            colored[2, i, j] = b

    return colored
```
