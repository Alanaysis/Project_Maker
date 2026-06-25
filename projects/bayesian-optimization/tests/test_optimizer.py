"""
贝叶斯优化器测试
"""

import numpy as np
import pytest
from src.optimizer import BayesianOptimizer


class TestBayesianOptimizer:
    """贝叶斯优化器测试类"""

    def setup_method(self):
        """测试前准备"""
        np.random.seed(42)

    def test_initialization(self):
        """测试初始化"""
        def objective(x):
            return -np.sum(x**2)

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5)],
            n_initial=5,
            random_state=42
        )

        assert optimizer.n_initial == 5
        assert len(optimizer.bounds) == 1

    def test_initial_sampling(self):
        """测试初始采样"""
        def objective(x):
            return -np.sum(x**2)

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5)],
            n_initial=5,
            random_state=42
        )

        X, y = optimizer._initial_sampling()

        assert X.shape == (5, 1)
        assert y.shape == (5,)
        assert np.all(X >= -5)
        assert np.all(X <= 5)

    def test_optimize_1d(self):
        """测试 1D 优化"""
        def objective(x):
            return -x[0]**2

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5)],
            n_initial=5,
            maximize=True,
            random_state=42
        )

        result = optimizer.optimize(n_iterations=10, verbose=False)

        assert 'best_x' in result
        assert 'best_y' in result
        assert 'X_history' in result
        assert 'y_history' in result

        # 最优值应该接近 0
        assert result['best_y'] < 0.1

    def test_optimize_2d(self):
        """测试 2D 优化"""
        def objective(x):
            return -(x[0]**2 + x[1]**2)

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5), (-5, 5)],
            n_initial=10,
            maximize=True,
            random_state=42
        )

        result = optimizer.optimize(n_iterations=15, verbose=False)

        assert result['best_x'].shape == (2,)
        assert result['best_y'] < 1.0

    def test_minimize(self):
        """测试最小化"""
        def objective(x):
            return x[0]**2

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5)],
            n_initial=5,
            maximize=False,
            random_state=42
        )

        result = optimizer.optimize(n_iterations=10, verbose=False)

        assert result['best_y'] < 0.1

    def test_convergence_data(self):
        """测试收敛数据"""
        def objective(x):
            return -x[0]**2

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5)],
            n_initial=5,
            random_state=42
        )

        optimizer.optimize(n_iterations=10, verbose=False)
        iterations, best_values = optimizer.get_convergence_data()

        assert len(iterations) == len(best_values)
        assert len(iterations) == 15  # 5 initial + 10 iterations

    def test_different_kernels(self):
        """测试不同核函数"""
        def objective(x):
            return -x[0]**2

        for kernel in ['rbf', 'matern']:
            optimizer = BayesianOptimizer(
                objective_function=objective,
                bounds=[(-5, 5)],
                n_initial=5,
                kernel=kernel,
                random_state=42
            )

            result = optimizer.optimize(n_iterations=5, verbose=False)
            assert result['best_y'] < 1.0

    def test_invalid_kernel(self):
        """测试无效核函数"""
        def objective(x):
            return -x[0]**2

        with pytest.raises(ValueError):
            BayesianOptimizer(
                objective_function=objective,
                bounds=[(-5, 5)],
                kernel='invalid'
            )

    def test_custom_acquisition(self):
        """测试自定义采集函数"""
        from src.acquisition import UpperConfidenceBound

        def objective(x):
            return -x[0]**2

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5)],
            n_initial=5,
            acquisition=UpperConfidenceBound(kappa=2.0),
            random_state=42
        )

        result = optimizer.optimize(n_iterations=5, verbose=False)
        assert result['best_y'] < 1.0

    def test_verbose_output(self, capsys):
        """测试详细输出"""
        def objective(x):
            return -x[0]**2

        optimizer = BayesianOptimizer(
            objective_function=objective,
            bounds=[(-5, 5)],
            n_initial=3,
            random_state=42
        )

        optimizer.optimize(n_iterations=2, verbose=True)
        captured = capsys.readouterr()

        assert '初始采样完成' in captured.out
        assert '迭代' in captured.out


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
