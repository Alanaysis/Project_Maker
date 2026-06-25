# 05-DEVELOPMENT.md - GAN 开发文档

## 1. 开发环境

### 1.1 系统要求

- Python 3.8+
- PyTorch 1.8+
- CUDA 11.0+ (可选，用于 GPU 加速)

### 1.2 依赖安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install torch torchvision matplotlib numpy pytest
```

### 1.3 IDE 配置

**VS Code**：
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

**PyCharm**：
- 设置 Python 解释器
- 配置 pytest 作为测试运行器
- 启用代码检查

## 2. 项目结构

```
gan/
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档 (本文件)
├── src/                    # 源代码
│   ├── __init__.py         # 包初始化
│   ├── generator.py        # 生成器实现
│   ├── discriminator.py    # 判别器实现
│   ├── gan.py              # GAN 框架
│   └── trainer.py          # 训练器
├── tests/                  # 测试
│   └── test_gan.py         # 测试套件
└── examples/               # 示例
    ├── train_mnist.py      # MNIST 训练示例
    └── simple_example.py   # 简单示例
```

## 3. 开发流程

### 3.1 开发步骤

1. **需求分析**: 理解 GAN 的核心概念和目标
2. **架构设计**: 设计模块结构和接口
3. **代码实现**: 实现各个模块
4. **单元测试**: 编写和运行单元测试
5. **集成测试**: 测试模块交互
6. **文档编写**: 编写使用文档和学习笔记
7. **代码审查**: 检查代码质量
8. **部署发布**: 发布到代码仓库

### 3.2 开发工具

**版本控制**：
```bash
# 初始化 Git 仓库
git init

# 添加文件
git add .

# 提交更改
git commit -m "Initial commit"
```

**代码格式化**：
```bash
# 使用 black 格式化代码
pip install black
black src/ tests/ examples/
```

**代码检查**：
```bash
# 使用 flake8 检查代码
pip install flake8
flake8 src/ tests/ examples/
```

**类型检查**：
```bash
# 使用 mypy 进行类型检查
pip install mypy
mypy src/
```

### 3.3 代码规范

**命名规范**：
- 类名: PascalCase (如 `Generator`, `Discriminator`)
- 函数名: snake_case (如 `train_step`, `generate_samples`)
- 变量名: snake_case (如 `latent_dim`, `img_size`)
- 常量名: UPPER_CASE (如 `DEFAULT_LR`, `DEFAULT_BETA1`)

**文档规范**：
- 每个模块都有模块级 docstring
- 每个类都有类级 docstring
- 每个公共方法都有方法级 docstring
- 使用 Google 风格的 docstring

**代码风格**：
- 使用 4 空格缩进
- 行长度不超过 100 字符
- 使用类型注解
- 遵循 PEP 8 规范

## 4. 模块开发

### 4.1 Generator 开发

**开发步骤**：
1. 定义类接口
2. 实现网络结构
3. 实现前向传播
4. 实现辅助方法
5. 编写测试
6. 优化性能

**关键实现**：
```python
class Generator(nn.Module):
    def __init__(self, latent_dim, img_channels, img_size, hidden_dims):
        super().__init__()
        
        # 参数
        self.latent_dim = latent_dim
        self.img_channels = img_channels
        self.img_size = img_size
        
        # 网络层
        self.fc = nn.Linear(latent_dim, hidden_dims[0] * 7 * 7)
        self.network = nn.Sequential(
            nn.ConvTranspose2d(hidden_dims[0], hidden_dims[1], 4, 2, 1),
            nn.BatchNorm2d(hidden_dims[1]),
            nn.ReLU(True),
            nn.ConvTranspose2d(hidden_dims[1], img_channels, 4, 2, 1),
            nn.Tanh()
        )
    
    def forward(self, z):
        out = self.fc(z)
        out = out.view(-1, self.latent_dim, 7, 7)
        return self.network(out)
```

**注意事项**：
- 使用 BatchNorm 稳定训练
- 使用 Tanh 作为输出激活函数
- 正确初始化权重

### 4.2 Discriminator 开发

**开发步骤**：
1. 定义类接口
2. 实现卷积网络
3. 实现分类层
4. 实现辅助方法
5. 编写测试
6. 优化性能

**关键实现**：
```python
class Discriminator(nn.Module):
    def __init__(self, img_channels, img_size, hidden_dims):
        super().__init__()
        
        # 参数
        self.img_channels = img_channels
        self.img_size = img_size
        
        # 网络层
        self.network = nn.Sequential(
            nn.Conv2d(img_channels, hidden_dims[0], 4, 2, 1),
            nn.LeakyReLU(0.2, True),
            nn.Dropout2d(0.25),
            nn.Conv2d(hidden_dims[0], hidden_dims[1], 4, 2, 1),
            nn.LeakyReLU(0.2, True),
            nn.Dropout2d(0.25),
        )
        
        # 分类层
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dims[1] * 7 * 7, 1),
            nn.Sigmoid()
        )
    
    def forward(self, img):
        features = self.network(img)
        features = features.view(features.size(0), -1)
        return self.classifier(features)
```

**注意事项**：
- 使用 LeakyReLU 防止梯度消失
- 使用 Dropout 防止过拟合
- 使用 Sigmoid 作为输出激活函数

### 4.3 GAN 框架开发

**开发步骤**：
1. 定义类接口
2. 整合生成器和判别器
3. 实现训练逻辑
4. 实现统计功能
5. 编写测试
6. 优化性能

**关键实现**：
```python
class GAN(nn.Module):
    def __init__(self, latent_dim, img_channels, img_size, lr, beta1, beta2):
        super().__init__()
        
        # 创建生成器和判别器
        self.generator = Generator(latent_dim, img_channels, img_size)
        self.discriminator = Discriminator(img_channels, img_size)
        
        # 损失函数
        self.adversarial_loss = nn.BCELoss()
        
        # 优化器
        self.optimizer_G = Adam(self.generator.parameters(), lr=lr, betas=(beta1, beta2))
        self.optimizer_D = Adam(self.discriminator.parameters(), lr=lr, betas=(beta1, beta2))
    
    def train_discriminator(self, real_images, batch_size):
        # 训练判别器逻辑
        ...
    
    def train_generator(self, batch_size, device):
        # 训练生成器逻辑
        ...
    
    def train_step(self, real_images):
        # 一步训练逻辑
        ...
```

**注意事项**：
- 为生成器和判别器使用独立的优化器
- 使用 detach() 防止梯度错误传播
- 正确记录训练统计

### 4.4 Trainer 开发

**开发步骤**：
1. 定义类接口
2. 实现训练循环
3. 实现检查点管理
4. 实现回调机制
5. 编写测试
6. 优化性能

**关键实现**：
```python
class GANTrainer:
    def __init__(self, gan, device, label_smoothing, noisy_labels, n_critic):
        self.gan = gan
        self.device = device
        self.label_smoothing = label_smoothing
        self.noisy_labels = noisy_labels
        self.n_critic = n_critic
    
    def train_epoch(self, dataloader, epoch):
        # 训练一个 epoch
        ...
    
    def train(self, dataloader, n_epochs, ...):
        # 完整训练
        ...
    
    def save_checkpoint(self, save_dir, epoch):
        # 保存检查点
        ...
    
    def load_checkpoint(self, checkpoint_path):
        # 加载检查点
        ...
```

**注意事项**：
- 支持标签平滑和噪声标签
- 支持检查点保存和加载
- 支持回调函数

## 5. 测试开发

### 5.1 测试策略

**单元测试**：
- 测试单个函数或方法
- 隔离测试，不依赖外部
- 快速执行

**集成测试**：
- 测试组件交互
- 测试完整流程
- 可能依赖外部资源

**性能测试**：
- 测试执行时间
- 测试内存占用
- 测试吞吐量

### 5.2 测试开发步骤

1. 编写测试用例
2. 运行测试
3. 修复失败的测试
4. 检查测试覆盖率
5. 优化测试性能

### 5.3 测试示例

```python
class TestGenerator:
    def setup_method(self):
        """测试前准备"""
        self.generator = Generator(latent_dim=100, img_channels=1, img_size=28)
    
    def test_forward(self):
        """测试前向传播"""
        z = torch.randn(4, 100)
        output = self.generator(z)
        assert output.shape == (4, 1, 28, 28)
    
    def test_gradient_flow(self):
        """测试梯度流动"""
        z = torch.randn(4, 100, requires_grad=True)
        output = self.generator(z)
        loss = output.mean()
        loss.backward()
        assert z.grad is not None
```

### 5.4 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html tests/

# 查看覆盖率
open htmlcov/index.html
```

## 6. 文档开发

### 6.1 文档类型

**README.md**：
- 项目介绍
- 安装说明
- 使用示例
- API 文档

**LEARNING_NOTES.md**：
- 学习路径
- 关键概念
- 学习心得

**docs/ 目录**：
- 01-RESEARCH.md: 调研文档
- 02-DESIGN.md: 设计文档
- 03-IMPLEMENTATION.md: 实现文档
- 04-TESTING.md: 测试文档
- 05-DEVELOPMENT.md: 开发文档

### 6.2 文档编写步骤

1. 编写 README.md
2. 编写 LEARNING_NOTES.md
3. 编写 docs/ 目录下的文档
4. 检查文档完整性
5. 优化文档质量

### 6.3 文档规范

**Markdown 规范**：
- 使用标准 Markdown 语法
- 使用清晰的标题层级
- 使用代码块显示代码
- 使用表格显示数据

**文档结构**：
- 使用清晰的目录结构
- 使用一致的命名规范
- 使用适当的链接

## 7. 部署开发

### 7.1 部署步骤

1. 准备部署环境
2. 打包项目
3. 上传到代码仓库
4. 配置 CI/CD
5. 监控部署状态

### 7.2 部署工具

**代码仓库**：
- GitHub
- GitLab
- Bitbucket

**CI/CD**：
- GitHub Actions
- GitLab CI
- Jenkins

**包管理**：
- pip
- conda

### 7.3 部署配置

**GitHub Actions 配置**：
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install dependencies
      run: |
        pip install torch torchvision pytest
    
    - name: Run tests
      run: |
        pytest tests/ -v
```

## 8. 性能优化

### 8.1 代码优化

**使用 inplace 操作**：
```python
# 不推荐
x = x + 1
x = torch.relu(x)

# 推荐
x += 1
x = torch.relu(x, inplace=True)
```

**使用 detach()**：
```python
# 不推荐
fake_output = self.discriminator(fake_images)

# 推荐
fake_output = self.discriminator(fake_images.detach())
```

**使用 no_grad()**：
```python
# 不推荐
z = torch.randn(4, 100)
output = self.generator(z)

# 推荐
with torch.no_grad():
    z = torch.randn(4, 100)
    output = self.generator(z)
```

### 8.2 训练优化

**使用 GPU**：
```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
gan = gan.to(device)
```

**使用 DataLoader**：
```python
dataloader = DataLoader(
    dataset,
    batch_size=64,
    shuffle=True,
    num_workers=4,
    pin_memory=True
)
```

**使用混合精度训练**：
```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

with autocast():
    output = model(input)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 8.3 内存优化

**及时释放不需要的张量**：
```python
del z, fake_images
torch.cuda.empty_cache()
```

**使用梯度累积**：
```python
optimizer.zero_grad()

for i in range(accumulation_steps):
    output = model(input)
    loss = criterion(output, target) / accumulation_steps
    loss.backward()

optimizer.step()
```

## 9. 调试技巧

### 9.1 常见问题

**维度不匹配**：
```python
# 检查张量形状
print(f"z shape: {z.shape}")
print(f"output shape: {output.shape}")
```

**梯度消失**：
```python
# 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad norm = {param.grad.norm()}")
```

**数值不稳定**：
```python
# 使用 clamp 防止 log(0)
output = torch.clamp(output, 1e-7, 1 - 1e-7)
loss = -torch.log(output)
```

### 9.2 调试工具

**打印调试**：
```python
print(f"batch_size: {batch_size}")
print(f"d_loss: {d_loss.item()}")
print(f"g_loss: {g_loss.item()}")
```

**可视化调试**：
```python
import matplotlib.pyplot as plt

# 可视化生成图像
images = gan.generate_samples(n_samples=16)
fig, axes = plt.subplots(4, 4, figsize=(8, 8))
for i in range(4):
    for j in range(4):
        axes[i][j].imshow(images[i*4+j].squeeze(), cmap="gray")
        axes[i][j].axis("off")
plt.show()
```

**使用 TensorBoard**：
```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter()

for epoch in range(n_epochs):
    # 训练
    ...
    
    # 记录损失
    writer.add_scalar("Loss/D", d_loss, epoch)
    writer.add_scalar("Loss/G", g_loss, epoch)
    
    # 记录图像
    images = gan.generate_samples(n_samples=16)
    writer.add_images("Generated", images, epoch)

writer.close()
```

### 9.3 调试策略

**从小规模开始**：
- 使用小数据集
- 使用小网络
- 使用少的训练轮数

**逐步验证**：
- 先验证生成器
- 再验证判别器
- 最后验证 GAN

**监控指标**：
- 监控损失变化
- 监控准确率变化
- 监控生成图像质量

## 10. 版本管理

### 10.1 版本号规范

使用语义化版本号：
- 主版本号: 不兼容的 API 修改
- 次版本号: 向下兼容的功能性新增
- 修订号: 向下兼容的问题修正

**示例**：
- 1.0.0: 初始版本
- 1.1.0: 添加新功能
- 1.1.1: 修复 bug

### 10.2 Git 工作流

**分支策略**：
- main: 主分支，保持稳定
- develop: 开发分支
- feature/*: 功能分支
- hotfix/*: 紧急修复分支

**提交规范**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**示例**：
```
feat(generator): add batch normalization

- Add BatchNorm2d after each ConvTranspose2d layer
- Improve training stability

Closes #123
```

### 10.3 发布流程

1. 创建发布分支
2. 更新版本号
3. 更新 CHANGELOG
4. 运行测试
5. 合并到 main
6. 创建标签
7. 发布到 PyPI (可选)

## 11. 持续改进

### 11.1 代码审查

**审查内容**：
- 代码质量
- 测试覆盖
- 文档完整性
- 性能影响

**审查流程**：
1. 提交 Pull Request
2. 自动化测试
3. 人工审查
4. 合并代码

### 11.2 重构

**重构时机**：
- 代码重复
- 函数过长
- 类过大
- 性能问题

**重构步骤**：
1. 识别问题
2. 设计重构方案
3. 执行重构
4. 运行测试
5. 验证功能

### 11.3 技术债务

**识别技术债务**：
- TODO 注释
- 临时解决方案
- 重复代码
- 过时依赖

**处理技术债务**：
1. 记录技术债务
2. 评估优先级
3. 制定计划
4. 逐步解决

## 12. 最佳实践

### 12.1 代码质量

**SOLID 原则**：
- 单一职责原则
- 开闭原则
- 里氏替换原则
- 接口隔离原则
- 依赖倒置原则

**DRY 原则**：
- Don't Repeat Yourself
- 提取公共代码
- 使用函数和类

**KISS 原则**：
- Keep It Simple, Stupid
- 避免过度设计
- 保持代码简洁

### 12.2 测试质量

**FIRST 原则**：
- Fast: 测试执行快速
- Independent: 测试相互独立
- Repeatable: 测试可重复
- Self-Validating: 测试自动验证
- Timely: 测试及时编写

**AAA 模式**：
- Arrange: 准备测试数据
- Act: 执行被测试操作
- Assert: 验证结果

### 12.3 文档质量

**文档原则**：
- 完整性: 覆盖所有功能
- 准确性: 信息准确无误
- 及时性: 及时更新
- 可读性: 易于理解

**文档工具**：
- Markdown: 文档格式
- Sphinx: 文档生成
- Read the Docs: 文档托管

## 13. 总结

### 13.1 开发流程

1. **需求分析**: 理解目标和需求
2. **架构设计**: 设计模块结构
3. **代码实现**: 实现功能
4. **测试验证**: 验证正确性
5. **文档编写**: 编写文档
6. **部署发布**: 发布项目

### 13.2 开发工具

- **IDE**: VS Code, PyCharm
- **版本控制**: Git
- **测试**: pytest
- **CI/CD**: GitHub Actions
- **文档**: Markdown, Sphinx

### 13.3 开发经验

1. **从小规模开始**: 先实现核心功能
2. **持续测试**: 及时发现和修复问题
3. **代码审查**: 保证代码质量
4. **文档驱动**: 文档和代码同步更新
5. **持续改进**: 不断优化和重构

### 13.4 未来计划

1. **功能扩展**: 添加更多 GAN 变体
2. **性能优化**: 提高训练和生成速度
3. **文档完善**: 补充更多示例和教程
4. **社区建设**: 建立用户社区
