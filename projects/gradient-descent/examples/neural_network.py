"""神经网络训练示例 - 使用不同优化器训练简单神经网络

本示例展示如何使用梯度下降家族的优化器来训练一个简单的神经网络，
用于解决非线性分类问题。
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple, Callable

# 添加项目路径
import sys
sys.path.insert(0, '.')

from src.optimizers import SGD, Momentum, Adam, AdamW, Nadam
from src.schedulers import StepLR, CosineAnnealingLR


class SimpleNeuralNetwork:
    """简单的两层神经网络

    结构: 输入 -> 隐藏层 (ReLU) -> 输出 (Sigmoid)
    """

    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        """初始化神经网络

        Args:
            input_size: 输入特征数量
            hidden_size: 隐藏层神经元数量
            output_size: 输出神经元数量
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # He 初始化
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros(output_size)

        # 缓存
        self.cache = {}

    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU 激活函数"""
        return np.maximum(0, x)

    def relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """ReLU 导数"""
        return (x > 0).astype(float)

    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid 激活函数"""
        x = np.clip(x, -500, 500)
        return 1.0 / (1.0 + np.exp(-x))

    def forward(self, X: np.ndarray) -> np.ndarray:
        """前向传播"""
        self.cache['z1'] = X @ self.W1 + self.b1
        self.cache['a1'] = self.relu(self.cache['z1'])
        self.cache['z2'] = self.cache['a1'] @ self.W2 + self.b2
        self.cache['a2'] = self.sigmoid(self.cache['z2'])
        return self.cache['a2']

    def compute_loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """计算二元交叉熵损失"""
        predictions = self.forward(X)
        predictions = np.clip(predictions, 1e-7, 1 - 1e-7)
        loss = -np.mean(y * np.log(predictions) + (1 - y) * np.log(1 - predictions))
        return loss

    def backward(self, X: np.ndarray, y: np.ndarray) -> Dict[str, np.ndarray]:
        """反向传播"""
        n_samples = X.shape[0]
        predictions = self.cache['a2']

        # 输出层梯度
        dz2 = predictions - y
        dW2 = self.cache['a1'].T @ dz2 / n_samples
        db2 = np.mean(dz2, axis=0)

        # 隐藏层梯度
        da1 = dz2 @ self.W2.T
        dz1 = da1 * self.relu_derivative(self.cache['z1'])
        dW1 = X.T @ dz1 / n_samples
        db1 = np.mean(dz1, axis=0)

        return {
            'W1': dW1,
            'b1': db1,
            'W2': dW2,
            'b2': db2
        }


class MultiOptimizer:
    """多参数优化器包装器

    为每个参数创建独立的优化器实例，避免状态冲突。
    """

    def __init__(self, optimizer_factory: Callable):
        """初始化

        Args:
            optimizer_factory: 创建优化器实例的工厂函数
        """
        self.optimizer_factory = optimizer_factory
        self.optimizers: Dict[str, object] = {}

    def step(self, param_name: str, params: np.ndarray, grads: np.ndarray) -> np.ndarray:
        """执行一步更新

        Args:
            param_name: 参数名称
            params: 当前参数
            grads: 当前梯度

        Returns:
            更新后的参数
        """
        if param_name not in self.optimizers:
            self.optimizers[param_name] = self.optimizer_factory()
        return self.optimizers[param_name].step(params, grads)

    @property
    def learning_rate(self) -> float:
        """获取学习率"""
        return self.optimizer_factory().learning_rate


def generate_spiral_data(n_samples: int = 200, noise: float = 0.1) -> Tuple[np.ndarray, np.ndarray]:
    """生成螺旋数据集"""
    n_per_class = n_samples // 2

    theta = np.linspace(0, 2 * np.pi, n_per_class) + np.random.randn(n_per_class) * noise
    r = np.linspace(0.5, 2, n_per_class)

    x0 = r * np.cos(theta)
    y0 = r * np.sin(theta)

    x1 = r * np.cos(theta + np.pi)
    y1 = r * np.sin(theta + np.pi)

    X = np.vstack([np.column_stack([x0, y0]), np.column_stack([x1, y1])])
    y = np.array([0] * n_per_class + [1] * n_per_class).reshape(-1, 1)

    indices = np.random.permutation(n_samples)
    return X[indices], y[indices]


def train_neural_network(
    model: SimpleNeuralNetwork,
    multi_opt: MultiOptimizer,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    n_epochs: int = 100,
    batch_size: int = 32,
    scheduler=None
) -> Dict:
    """训练神经网络

    Args:
        model: 神经网络模型
        multi_opt: 多参数优化器
        X_train: 训练特征
        y_train: 训练标签
        X_val: 验证特征
        y_val: 验证标签
        n_epochs: 训练轮数
        batch_size: 批量大小
        scheduler: 学习率调度器

    Returns:
        训练结果字典
    """
    n_samples = X_train.shape[0]

    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []
    learning_rates = []

    for epoch in range(n_epochs):
        indices = np.random.permutation(n_samples)
        X_shuffled = X_train[indices]
        y_shuffled = y_train[indices]

        # Mini-Batch 训练
        for i in range(0, n_samples, batch_size):
            X_batch = X_shuffled[i:i + batch_size]
            y_batch = y_shuffled[i:i + batch_size]

            model.forward(X_batch)
            gradients = model.backward(X_batch, y_batch)

            # 使用独立优化器更新每个参数
            model.W1 = multi_opt.step('W1', model.W1, gradients['W1'])
            model.b1 = multi_opt.step('b1', model.b1, gradients['b1'])
            model.W2 = multi_opt.step('W2', model.W2, gradients['W2'])
            model.b2 = multi_opt.step('b2', model.b2, gradients['b2'])

        # 更新学习率
        if scheduler:
            scheduler.step()
            learning_rates.append(scheduler.get_lr())
        else:
            learning_rates.append(multi_opt.learning_rate)

        # 计算训练损失和准确率
        train_loss = model.compute_loss(X_train, y_train)
        train_pred = (model.forward(X_train) > 0.5).astype(float)
        train_acc = np.mean(train_pred == y_train)

        # 计算验证损失和准确率
        val_loss = model.compute_loss(X_val, y_val)
        val_pred = (model.forward(X_val) > 0.5).astype(float)
        val_acc = np.mean(val_pred == y_val)

        train_losses.append(train_loss)
        val_losses.append(val_loss)
        train_accs.append(train_acc)
        val_accs.append(val_acc)

        if (epoch + 1) % 20 == 0:
            print(f"Epoch {epoch + 1}/{n_epochs}: "
                  f"Train Loss={train_loss:.4f}, Train Acc={train_acc:.4f}, "
                  f"Val Loss={val_loss:.4f}, Val Acc={val_acc:.4f}")

    return {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'train_accs': train_accs,
        'val_accs': val_accs,
        'learning_rates': learning_rates
    }


def compare_optimizers_neural_network():
    """对比不同优化器在神经网络上的表现"""
    print("=" * 60)
    print("神经网络优化器对比实验")
    print("=" * 60)

    np.random.seed(42)
    X, y = generate_spiral_data(n_samples=400, noise=0.1)

    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    print(f"\n数据集: 训练集 {X_train.shape[0]} 样本, 验证集 {X_val.shape[0]} 样本")
    print(f"特征维度: {X.shape[1]}")

    # 定义优化器配置（每个使用工厂函数，确保独立状态）
    optimizers_config = {
        'SGD': {
            'factory': lambda: SGD(learning_rate=0.1),
            'scheduler_factory': lambda: StepLR(SGD(learning_rate=0.1), step_size=30, gamma=0.5)
        },
        'Momentum': {
            'factory': lambda: Momentum(learning_rate=0.01, momentum=0.9),
            'scheduler_factory': None
        },
        'Adam': {
            'factory': lambda: Adam(learning_rate=0.001),
            'scheduler_factory': None
        },
        'AdamW': {
            'factory': lambda: AdamW(learning_rate=0.001, weight_decay=0.01),
            'scheduler_factory': None
        },
        'Nadam': {
            'factory': lambda: Nadam(learning_rate=0.001),
            'scheduler_factory': lambda: CosineAnnealingLR(Nadam(learning_rate=0.001), T_max=100, eta_min=0.0001)
        },
    }

    # 训练并收集结果
    results = {}
    for name, config in optimizers_config.items():
        print(f"\n训练 {name}...")
        model = SimpleNeuralNetwork(input_size=2, hidden_size=16, output_size=1)
        multi_opt = MultiOptimizer(config['factory'])
        scheduler = config['scheduler_factory']() if config['scheduler_factory'] else None

        result = train_neural_network(
            model, multi_opt,
            X_train, y_train,
            X_val, y_val,
            n_epochs=100,
            batch_size=32,
            scheduler=scheduler
        )
        results[name] = result
        print(f"  最终训练准确率: {result['train_accs'][-1]:.4f}")
        print(f"  最终验证准确率: {result['val_accs'][-1]:.4f}")

    # 绘制结果
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    ax1 = axes[0, 0]
    for name, result in results.items():
        ax1.plot(result['train_losses'], label=name, alpha=0.7)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[0, 1]
    for name, result in results.items():
        ax2.plot(result['val_losses'], label=name, alpha=0.7)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.set_title('Validation Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[1, 0]
    for name, result in results.items():
        ax3.plot(result['train_accs'], label=name, alpha=0.7)
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('Accuracy')
    ax3.set_title('Training Accuracy')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    ax4 = axes[1, 1]
    for name, result in results.items():
        ax4.plot(result['val_accs'], label=name, alpha=0.7)
    ax4.set_xlabel('Epoch')
    ax4.set_ylabel('Accuracy')
    ax4.set_title('Validation Accuracy')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('neural_network_comparison.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存: neural_network_comparison.png")

    return results


if __name__ == '__main__':
    compare_optimizers_neural_network()
