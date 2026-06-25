# 开发指南

## 1. 开发环境设置

### 1.1 环境要求

- **Python**：3.8 或更高版本
- **PyTorch**：2.0 或更高版本
- **CUDA**：11.7 或更高版本（可选，用于 GPU 加速）
- **操作系统**：Linux、macOS 或 Windows

### 1.2 安装步骤

```bash
# 克隆项目
cd projects/diffusion-model

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 1.3 IDE 配置

**VS Code 推荐配置**：

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=100"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

**PyCharm 配置**：
1. 设置 Python 解释器为虚拟环境
2. 启用 pytest 作为测试运行器
3. 配置代码风格为 Black

## 2. 代码规范

### 2.1 代码风格

遵循 PEP 8 规范，使用 Black 格式化：

```bash
# 格式化代码
black src/ tests/ examples/

# 检查代码风格
flake8 src/ tests/ examples/

# 类型检查
mypy src/
```

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写 + 下划线 | `scheduler.py` |
| 类 | 大驼峰 | `NoiseScheduler` |
| 函数 | 小写 + 下划线 | `add_noise()` |
| 常量 | 大写 + 下划线 | `NUM_TIMESTEPS` |
| 私有 | 前缀下划线 | `_private_method()` |

### 2.3 文档规范

**模块文档**：
```python
"""
Module Name

Brief description of the module.

This module provides...
"""
```

**类文档**：
```python
class ClassName:
    """
    Brief description of the class.

    Longer description if needed.

    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2

    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """
```

**函数文档**：
```python
def function_name(param1: int, param2: str) -> bool:
    """
    Brief description of the function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input

    Example:
        >>> result = function_name(1, "test")
        >>> print(result)
        True
    """
```

### 2.4 类型提示

使用类型提示提高代码可读性：

```python
from typing import Optional, Tuple, List
import torch

def add_noise(
    self,
    x_0: torch.Tensor,
    t: torch.Tensor,
    noise: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """添加噪声到图像"""
    pass
```

## 3. 开发流程

### 3.1 Git 工作流

```bash
# 创建新分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: add new feature"

# 推送分支
git push origin feature/new-feature

# 创建 Pull Request
# 合并后删除分支
git checkout master
git branch -d feature/new-feature
```

### 3.2 提交规范

使用 Conventional Commits：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**类型**：
- `feat`：新功能
- `fix`：修复 bug
- `docs`：文档更新
- `style`：代码格式（不影响功能）
- `refactor`：重构
- `test`：测试相关
- `chore`：构建/工具相关

**示例**：
```
feat(scheduler): add cosine noise schedule

Implement cosine noise schedule from Improved DDPM paper.
This schedule avoids the issue of too much noise at later timesteps.

Closes #123
```

### 3.3 分支策略

- `master`：稳定版本
- `develop`：开发分支
- `feature/*`：功能分支
- `bugfix/*`：修复分支
- `release/*`：发布分支

## 4. 添加新功能

### 4.1 添加新的噪声调度

**步骤**：

1. **在 `scheduler.py` 中添加方法**：

```python
def _new_schedule(self) -> torch.Tensor:
    """
    新的噪声调度方法

    实现细节...
    """
    # 实现代码
    return betas
```

2. **在 `__init__` 中添加选项**：

```python
def __init__(self, ..., schedule_type: str = "linear"):
    if schedule_type == "linear":
        self.betas = self._linear_schedule()
    elif schedule_type == "cosine":
        self.betas = self._cosine_schedule()
    elif schedule_type == "new":  # 新增
        self.betas = self._new_schedule()
    else:
        raise ValueError(f"Unknown schedule type: {schedule_type}")
```

3. **编写测试**：

```python
def test_new_schedule(self):
    """测试新的噪声调度"""
    scheduler = NoiseScheduler(schedule_type="new")

    # 验证基本属性
    assert len(scheduler.betas) == 100
    assert torch.all(scheduler.betas > 0)
    assert torch.all(scheduler.betas < 1)

    # 验证数学性质
    # ...
```

4. **更新文档**：

在 `README.md` 和 `docs/01-RESEARCH.md` 中添加说明。

### 4.2 添加新的模型架构

**步骤**：

1. **在 `unet.py` 中添加类**：

```python
class NewModel(nn.Module):
    """
    新的模型架构

    特点：
    - ...
    """

    def __init__(self, in_channels, out_channels, ...):
        super().__init__()
        # 初始化代码

    def forward(self, x, t):
        """
        前向传播

        Args:
            x: 输入张量 [B, C, H, W]
            t: 时间步 [B]

        Returns:
            预测的噪声 [B, C, H, W]
        """
        # 实现代码
        return output
```

2. **在 `diffusion.py` 中集成**：

```python
def __init__(self, ..., model_type: str = "simple"):
    if model_type == "simple":
        self.model = SimpleUNet(...)
    elif model_type == "full":
        self.model = UNet(...)
    elif model_type == "new":  # 新增
        self.model = NewModel(...)
```

3. **编写测试**：

```python
class TestNewModel:
    """测试新模型"""

    def test_output_shape(self):
        """测试输出形状"""
        model = NewModel(in_channels=1, out_channels=1)
        x = torch.randn(2, 1, 28, 28)
        t = torch.randint(0, 100, (2,))

        output = model(x, t)

        assert output.shape == x.shape

    def test_gradient_flow(self):
        """测试梯度流"""
        # ...
```

### 4.3 添加新的采样方法

**步骤**：

1. **在 `diffusion.py` 中添加方法**：

```python
@torch.no_grad()
def sample_new_method(
    self,
    batch_size: int,
    device: torch.device,
    **kwargs
) -> torch.Tensor:
    """
    新的采样方法

    来自论文：...

    Args:
        batch_size: 批次大小
        device: 设备
        **kwargs: 额外参数

    Returns:
        生成的图像 [B, C, H, W]
    """
    self.eval()

    # 初始化
    x = torch.randn(batch_size, self.in_channels, self.image_size, self.image_size).to(device)

    # 采样循环
    for t in reversed(range(self.num_timesteps)):
        # 实现细节
        pass

    return x
```

2. **编写测试**：

```python
def test_new_sampling_method(self):
    """测试新的采样方法"""
    model = DiffusionModel(...)

    samples = model.sample_new_method(
        batch_size=4,
        device=torch.device("cpu")
    )

    assert samples.shape == (4, 1, 28, 28)
```

3. **添加示例**：

在 `examples/generate_samples.py` 中添加使用示例。

## 5. 调试技巧

### 5.1 常见问题

**问题 1：损失不下降**

```python
# 检查数据归一化
print(f"Data range: [{images.min():.3f}, {images.max():.3f}]")
# 应该在 [-1, 1] 或 [0, 1] 范围内

# 检查学习率
print(f"Learning rate: {optimizer.param_groups[0]['lr']}")

# 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_norm = {param.grad.norm():.6f}")
```

**问题 2：内存不足**

```python
# 减小批次大小
batch_size = 16  # 而不是 128

# 使用梯度累积
accumulation_steps = 4
for i, batch in enumerate(dataloader):
    loss = model.training_loss(batch)
    loss = loss / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

**问题 3：生成质量差**

```python
# 增加训练时间
num_epochs = 100  # 而不是 50

# 使用更大的模型
hidden_channels = [128, 256, 512]  # 而不是 [64, 128, 256]

# 尝试不同的噪声调度
schedule_type = "cosine"  # 而不是 "linear"
```

### 5.2 调试工具

**打印中间结果**：

```python
def training_loss(self, x_0):
    t = self.scheduler.sample_timestep(batch_size, device)
    noise = torch.randn_like(x_0)
    x_t, noise = self.scheduler.add_noise(x_0, t, noise)
    noise_pred = self.model(x_t, t)

    # 调试打印
    print(f"t: {t}")
    print(f"x_0 range: [{x_0.min():.3f}, {x_0.max():.3f}]")
    print(f"x_t range: [{x_t.min():.3f}, {x_t.max():.3f}]")
    print(f"noise range: [{noise.min():.3f}, {noise.max():.3f}]")
    print(f"noise_pred range: [{noise_pred.min():.3f}, {noise_pred.max():.3f}]")

    loss = F.mse_loss(noise_pred, noise)
    print(f"loss: {loss.item():.6f}")

    return loss
```

**可视化训练过程**：

```python
def visualize_training(model, dataloader, device):
    """可视化训练过程"""
    model.eval()

    # 获取一个批次
    batch = next(iter(dataloader))
    x_0 = batch[0].to(device)

    # 前向扩散
    t = torch.tensor([0, 250, 500, 750, 999])
    noisy_images = []
    for t_val in t:
        x_t, _ = model.scheduler.add_noise(x_0[:1], t_val.unsqueeze(0))
        noisy_images.append(x_t)

    # 可视化
    visualize_diffusion_process(noisy_images, t.tolist())
```

**使用 TensorBoard**：

```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter('runs/diffusion')

for epoch in range(num_epochs):
    avg_loss = trainer.train_epoch(dataloader)

    # 记录损失
    writer.add_scalar('Loss/train', avg_loss, epoch)

    # 记录生成样本
    if epoch % 10 == 0:
        samples = model.sample(batch_size=16, device=device)
        img_grid = make_grid(samples, nrow=4, normalize=True)
        writer.add_image('Generated', img_grid, epoch)

writer.close()
```

### 5.3 性能分析

**使用 cProfile**：

```python
import cProfile

def profile_training():
    """分析训练性能"""
    model = DiffusionModel(...)
    trainer = DiffusionTrainer(model=model)

    cProfile.run('trainer.train_epoch(dataloader)', 'profile_stats')

    # 分析结果
    import pstats
    p = pstats.Stats('profile_stats')
    p.sort_stats('cumulative').print_stats(20)
```

**使用 PyTorch Profiler**：

```python
from torch.profiler import profile, record_function, ProfilerActivity

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    record_shapes=True,
    profile_memory=True
) as prof:
    with record_function("training"):
        loss = model.training_loss(x_0)

print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=10))
```

## 6. 测试指南

### 6.1 编写测试

**测试文件结构**：

```
tests/
├── __init__.py
├── test_scheduler.py
├── test_unet.py
└── test_diffusion.py
```

**测试类结构**：

```python
class TestClassName:
    """测试类名"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.model = SomeModel()

    def test_basic_functionality(self):
        """测试基本功能"""
        result = self.model.method()
        assert result == expected

    def test_edge_cases(self):
        """测试边界情况"""
        # 测试零输入
        # 测试大输入
        # 测试负输入
        pass

    def test_error_handling(self):
        """测试错误处理"""
        with pytest.raises(ValueError):
            self.model.method(invalid_input)
```

### 6.2 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_scheduler.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=html

# 运行并显示输出
pytest tests/ -v -s
```

### 6.3 测试数据

**创建测试数据**：

```python
@pytest.fixture
def sample_images():
    """创建测试图像"""
    return torch.randn(4, 1, 28, 28)

@pytest.fixture
def sample_timesteps():
    """创建测试时间步"""
    return torch.randint(0, 100, (4,))
```

## 7. 文档编写

### 7.1 文档结构

```
docs/
├── 01-RESEARCH.md      # 技术调研
├── 02-ARCHITECTURE.md  # 架构设计
├── 03-IMPLEMENTATION.md # 实现细节
├── 04-TESTING.md        # 测试说明
└── 05-DEVELOPMENT.md    # 开发指南
```

### 7.2 文档更新

**添加新功能时**：
1. 更新 `README.md` 的功能列表
2. 更新 `docs/01-RESEARCH.md` 的技术背景
3. 更新 `docs/02-ARCHITECTURE.md` 的架构图
4. 更新 `docs/03-IMPLEMENTATION.md` 的实现细节
5. 更新 `docs/04-TESTING.md` 的测试用例

### 7.3 文档工具

**生成 API 文档**：

```bash
# 使用 pdoc
pip install pdoc
pdoc src/ -o docs/api

# 使用 sphinx
pip install sphinx
sphinx-quickstart docs/
make html
```

## 8. 发布流程

### 8.1 版本管理

使用语义化版本：

```
MAJOR.MINOR.PATCH

MAJOR：不兼容的 API 更改
MINOR：向后兼容的功能添加
PATCH：向后兼容的 bug 修复
```

### 8.2 发布检查清单

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] 依赖版本已锁定
- [ ] 代码已格式化
- [ ] 类型检查通过

### 8.3 发布步骤

```bash
# 1. 更新版本号
# 在 setup.py 或 pyproject.toml 中

# 2. 更新 CHANGELOG
# 添加新版本的更改说明

# 3. 提交更改
git add .
git commit -m "release: version 1.0.0"

# 4. 创建标签
git tag -a v1.0.0 -m "Version 1.0.0"

# 5. 推送
git push origin master --tags

# 6. 创建 GitHub Release
# 在 GitHub 上创建新的 Release
```

## 9. 协作指南

### 9.1 Pull Request 流程

1. **创建分支**：`feature/xxx` 或 `bugfix/xxx`
2. **开发功能**：编写代码和测试
3. **提交 PR**：描述更改内容
4. **代码审查**：团队成员审查
5. **修改代码**：根据反馈修改
6. **合并 PR**：审查通过后合并
7. **删除分支**：清理分支

### 9.2 代码审查要点

- **功能正确性**：代码是否正确实现功能
- **代码风格**：是否符合项目规范
- **测试覆盖**：是否有足够的测试
- **文档完整**：是否更新了相关文档
- **性能影响**：是否影响性能

### 9.3 沟通规范

- **Issue**：使用 Issue 报告 bug 或提出功能请求
- **PR**：使用 PR 提交代码更改
- **Discussion**：使用 Discussion 讨论技术方案
- **Wiki**：使用 Wiki 记录项目知识

## 10. 常见开发任务

### 10.1 添加新的数据集

```python
def get_new_dataloader(data_dir, batch_size):
    """获取新数据集的数据加载器"""
    transform = transforms.Compose([
        transforms.Resize(32),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    dataset = NewDataset(
        root=data_dir,
        train=True,
        download=True,
        transform=transform
    )

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4
    )
```

### 10.2 调整模型大小

```python
# 小模型（快速实验）
model = SimpleUNet(
    in_channels=1,
    out_channels=1,
    time_emb_dim=64
)

# 中等模型（平衡性能）
model = UNet(
    in_channels=1,
    out_channels=1,
    hidden_channels=[64, 128, 256],
    attention=False
)

# 大模型（最佳质量）
model = UNet(
    in_channels=1,
    out_channels=1,
    hidden_channels=[128, 256, 512],
    attention=True,
    num_res_blocks=3
)
```

### 10.3 优化训练速度

```python
# 使用混合精度训练
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    with autocast():
        loss = model.training_loss(batch)

    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()

# 使用 torch.compile（PyTorch 2.0+）
model = torch.compile(model)

# 使用更高效的注意力实现
# pip install xformers
from xformers.ops import memory_efficient_attention
```

## 11. 故障排除

### 11.1 安装问题

**问题**：PyTorch 安装失败

**解决方案**：
```bash
# 使用官方安装命令
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或使用 conda
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```

### 11.2 CUDA 问题

**问题**：CUDA 不可用

**解决方案**：
```bash
# 检查 CUDA 版本
nvidia-smi

# 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torch; print(torch.version.cuda)"

# 重新安装对应版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 11.3 内存问题

**问题**：GPU 内存不足

**解决方案**：
```python
# 减小批次大小
batch_size = 16

# 使用梯度累积
accumulation_steps = 4

# 使用梯度检查点
from torch.utils.checkpoint import checkpoint

# 使用混合精度训练
from torch.cuda.amp import autocast
```

## 12. 最佳实践总结

### 12.1 代码质量

1. **遵循 PEP 8**：使用 Black 格式化
2. **类型提示**：提高代码可读性
3. **文档字符串**：详细说明功能
4. **单元测试**：确保代码正确性

### 12.2 性能优化

1. **预计算**：避免重复计算
2. **批处理**：充分利用 GPU
3. **混合精度**：减少内存使用
4. **编译优化**：使用 torch.compile

### 12.3 可维护性

1. **模块化设计**：职责清晰
2. **配置管理**：使用配置文件
3. **日志记录**：便于调试
4. **错误处理**：优雅处理异常

### 12.4 协作效率

1. **版本控制**：使用 Git
2. **代码审查**：保证代码质量
3. **文档完整**：降低沟通成本
4. **自动化测试**：减少手动测试
