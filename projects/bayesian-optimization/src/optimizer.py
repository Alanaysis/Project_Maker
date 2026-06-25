"""
贝叶斯优化器模块
================

实现贝叶斯优化循环：
- 初始化采样
- 迭代优化
- 结果分析
"""

import numpy as np
from typing import Callable, Optional, Tuple, List, Dict
from .gaussian_process import GaussianProcess
from .acquisition import AcquisitionFunction, ExpectedImprovement, create_acquisition
from .kernels import RBF, Matern


class BayesianOptimizer:
    """
    贝叶斯优化器

    属性：
        objective_function: 目标函数
        bounds: 搜索空间边界
        acquisition: 采集函数
        gp: 高斯过程模型
        n_initial: 初始采样点数
        maximize: 是否最大化目标函数
    """

    def __init__(self,
                 objective_function: Callable,
                 bounds: List[Tuple[float, float]],
                 acquisition: Optional[AcquisitionFunction] = None,
                 kernel: Optional[str] = 'rbf',
                 n_initial: int = 5,
                 maximize: bool = True,
                 random_state: Optional[int] = None):
        """
        初始化贝叶斯优化器

        参数：
            objective_function: 目标函数 f(x) -> float
            bounds: 搜索空间边界 [(low, high), ...]
            acquisition: 采集函数，默认使用 EI
            kernel: 核函数类型 ('rbf' 或 'matern')
            n_initial: 初始采样点数
            maximize: 是否最大化目标函数
            random_state: 随机种子
        """
        self.objective_function = objective_function
        self.bounds = np.array(bounds)
        self.n_initial = n_initial
        self.maximize = maximize

        # 设置随机种子
        if random_state is not None:
            np.random.seed(random_state)

        # 创建核函数
        if kernel == 'rbf':
            self.kernel = RBF(length_scale=1.0, signal_variance=1.0)
        elif kernel == 'matern':
            self.kernel = Matern(length_scale=1.0, signal_variance=1.0, nu=2.5)
        else:
            raise ValueError(f"未知的核函数类型: {kernel}")

        # 创建采集函数
        if acquisition is None:
            self.acquisition = ExpectedImprovement(xi=0.01)
        else:
            self.acquisition = acquisition

        # 创建高斯过程
        self.gp = GaussianProcess(kernel=self.kernel, noise_variance=1e-6)

        # 优化历史
        self.X_history = []
        self.y_history = []
        self.best_x = None
        self.best_y = None

    def _initial_sampling(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        初始采样

        返回：
            X: 初始采样点
            y: 初始采样值
        """
        n_dims = len(self.bounds)

        # 拉丁超立方采样
        X = np.zeros((self.n_initial, n_dims))

        for i in range(n_dims):
            low, high = self.bounds[i]
            # 生成均匀间隔的点
            points = np.linspace(low, high, self.n_initial)
            # 随机打乱
            np.random.shuffle(points)
            X[:, i] = points

        # 评估目标函数
        y = np.array([self.objective_function(x) for x in X])

        # 如果是最小化，取负值
        if not self.maximize:
            y = -y

        return X, y

    def _propose_point(self) -> np.ndarray:
        """
        提议下一个采样点

        返回：
            x_next: 下一个采样点
        """
        n_dims = len(self.bounds)

        # 多次随机重启
        n_restarts = 10
        best_x = None
        best_acquisition = -np.inf

        for _ in range(n_restarts):
            # 随机初始点
            x0 = np.random.uniform(self.bounds[:, 0], self.bounds[:, 1])

            # 使用 L-BFGS-B 优化采集函数
            from scipy.optimize import minimize

            def neg_acquisition(x):
                x = x.reshape(1, -1)
                return -self.acquisition(x, self.gp, self.best_y)[0]

            try:
                result = minimize(neg_acquisition, x0,
                                  bounds=self.bounds,
                                  method='L-BFGS-B')

                if -result.fun > best_acquisition:
                    best_acquisition = -result.fun
                    best_x = result.x
            except:
                continue

        # 如果优化失败，随机采样
        if best_x is None:
            best_x = np.random.uniform(self.bounds[:, 0], self.bounds[:, 1])

        return best_x

    def optimize(self, n_iterations: int = 20,
                 verbose: bool = False) -> Dict:
        """
        运行贝叶斯优化

        参数：
            n_iterations: 迭代次数
            verbose: 是否打印进度

        返回：
            result: 优化结果字典
        """
        # 初始采样
        X_init, y_init = self._initial_sampling()

        self.X_history = list(X_init)
        self.y_history = list(y_init)

        # 更新最优值
        best_idx = np.argmax(y_init)
        self.best_x = X_init[best_idx]
        self.best_y = y_init[best_idx]

        if verbose:
            print(f"初始采样完成，最优值: {self.best_y:.4f}")
            print("-" * 50)

        # 迭代优化
        for i in range(n_iterations):
            # 拟合高斯过程
            X_train = np.array(self.X_history)
            y_train = np.array(self.y_history)
            self.gp.fit(X_train, y_train)

            # 提议下一个点
            x_next = self._propose_point()

            # 评估目标函数
            y_next = self.objective_function(x_next)
            if not self.maximize:
                y_next = -y_next

            # 更新历史
            self.X_history.append(x_next)
            self.y_history.append(y_next)

            # 更新最优值
            if y_next > self.best_y:
                self.best_x = x_next
                self.best_y = y_next

            if verbose:
                print(f"迭代 {i+1}/{n_iterations}: "
                      f"当前值 = {y_next:.4f}, "
                      f"最优值 = {self.best_y:.4f}")

        # 返回结果
        result = {
            'best_x': self.best_x,
            'best_y': self.best_y if self.maximize else -self.best_y,
            'X_history': np.array(self.X_history),
            'y_history': np.array(self.y_history) if self.maximize else -np.array(self.y_history),
            'n_iterations': n_iterations,
            'n_evaluations': len(self.X_history)
        }

        return result

    def get_convergence_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取收敛数据

        返回：
            iterations: 迭代次数
            best_values: 最优值历史
        """
        y_history = np.array(self.y_history)
        if not self.maximize:
            y_history = -y_history

        best_values = np.maximum.accumulate(y_history)
        iterations = np.arange(1, len(best_values) + 1)

        return iterations, best_values

    def plot_convergence(self, save_path: Optional[str] = None):
        """
        绘制收敛曲线

        参数：
            save_path: 保存路径
        """
        import matplotlib.pyplot as plt

        iterations, best_values = self.get_convergence_data()

        plt.figure(figsize=(10, 6))
        plt.plot(iterations, best_values, 'b-', linewidth=2)
        plt.xlabel('迭代次数')
        plt.ylabel('最优值')
        plt.title('贝叶斯优化收敛曲线')
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()

    def plot_objective(self, save_path: Optional[str] = None):
        """
        绘制目标函数和采样点（仅适用于 1D 或 2D）

        参数：
            save_path: 保存路径
        """
        import matplotlib.pyplot as plt

        n_dims = len(self.bounds)

        if n_dims == 1:
            # 1D 可视化
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

            # 生成网格点
            x_grid = np.linspace(self.bounds[0, 0], self.bounds[0, 1], 200).reshape(-1, 1)

            # 预测均值和标准差
            y_mean, y_std = self.gp.predict(x_grid, return_std=True)

            # 目标函数值
            y_true = np.array([self.objective_function(x) for x in x_grid])

            # 绘制目标函数和 GP 预测
            ax1.plot(x_grid, y_true, 'k-', label='目标函数')
            ax1.plot(x_grid, y_mean, 'b-', label='GP 均值')
            ax1.fill_between(x_grid.ravel(),
                             y_mean - 2*y_std,
                             y_mean + 2*y_std,
                             alpha=0.2, label='95% 置信区间')

            # 绘制采样点
            X_train = np.array(self.X_history)
            y_train = np.array(self.y_history)
            ax1.scatter(X_train[:self.n_initial], y_train[:self.n_initial],
                        c='g', marker='o', label='初始点')
            ax1.scatter(X_train[self.n_initial:], y_train[self.n_initial:],
                        c='r', marker='x', label='采样点')

            ax1.set_xlabel('x')
            ax1.set_ylabel('f(x)')
            ax1.set_title('高斯过程拟合')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 绘制采集函数
            acq_values = self.acquisition(x_grid, self.gp, self.best_y)
            ax2.plot(x_grid, acq_values, 'g-', label='采集函数')
            ax2.axvline(x=self.best_x, color='r', linestyle='--', label='当前最优点')
            ax2.set_xlabel('x')
            ax2.set_ylabel('采集函数值')
            ax2.set_title('采集函数')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()

        elif n_dims == 2:
            # 2D 可视化
            fig, ax = plt.subplots(figsize=(10, 8))

            # 生成网格点
            x1 = np.linspace(self.bounds[0, 0], self.bounds[0, 1], 50)
            x2 = np.linspace(self.bounds[1, 0], self.bounds[1, 1], 50)
            X1, X2 = np.meshgrid(x1, x2)
            X_grid = np.column_stack([X1.ravel(), X2.ravel()])

            # 预测值
            y_pred, _ = self.gp.predict(X_grid, return_std=True)
            Y_pred = y_pred.reshape(X1.shape)

            # 绘制等高线
            contour = ax.contourf(X1, X2, Y_pred, levels=20, cmap='viridis', alpha=0.6)
            plt.colorbar(contour)

            # 绘制采样点
            X_train = np.array(self.X_history)
            ax.scatter(X_train[:self.n_initial, 0], X_train[:self.n_initial, 1],
                       c='w', marker='o', edgecolors='k', label='初始点')
            ax.scatter(X_train[self.n_initial:, 0], X_train[self.n_initial:, 1],
                       c='r', marker='x', label='采样点')
            ax.scatter(self.best_x[0], self.best_x[1],
                       c='yellow', marker='*', s=200, label='最优点')

            ax.set_xlabel('x1')
            ax.set_ylabel('x2')
            ax.set_title('贝叶斯优化结果')
            ax.legend()
        else:
            print("无法可视化高维问题")

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.show()
