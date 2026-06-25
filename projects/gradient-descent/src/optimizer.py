"""优化工具函数 - 统一的优化流程"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
from .optimizers.base import BaseOptimizer


def optimize(
    func,
    optimizer: BaseOptimizer,
    x_init: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-6,
    verbose: bool = False,
    record_interval: int = 1
) -> Dict[str, Any]:
    """统一优化接口

    Args:
        func: 测试函数
        optimizer: 优化器实例
        x_init: 初始点
        max_iter: 最大迭代次数
        tol: 收敛容差
        verbose: 是否打印详细信息
        record_interval: 记录间隔

    Returns:
        优化结果字典
    """
    x = x_init.copy().astype(float)
    trajectory = [x.copy()]
    values = [func(x)]
    grad_norms = []
    learning_rates = []

    for i in range(max_iter):
        # 计算梯度
        grad = func.gradient(x)
        grad_norm = np.linalg.norm(grad)
        grad_norms.append(grad_norm)
        learning_rates.append(optimizer.learning_rate)

        # 检查收敛
        if grad_norm < tol:
            if verbose:
                print(f"Converged at iteration {i}, gradient norm: {grad_norm:.6e}")
            break

        # 更新参数
        x = optimizer.step(x, grad)

        # 记录轨迹
        if (i + 1) % record_interval == 0:
            trajectory.append(x.copy())
            values.append(func(x))

        # 打印进度
        if verbose and (i + 1) % 100 == 0:
            print(f"Iteration {i+1}: f(x) = {func(x):.6e}, |grad| = {grad_norm:.6e}")

    # 确保记录最终结果
    if len(trajectory) == 0 or not np.array_equal(trajectory[-1], x):
        trajectory.append(x.copy())
        values.append(func(x))

    return {
        'x': x,
        'fun': func(x),
        'niter': i + 1,
        'trajectory': np.array(trajectory),
        'values': np.array(values),
        'grad_norms': np.array(grad_norms),
        'learning_rates': np.array(learning_rates),
        'success': grad_norm < tol,
        'message': 'Converged' if grad_norm < tol else 'Maximum iterations reached'
    }


def compare_optimizers(
    func,
    optimizers: Dict[str, BaseOptimizer],
    x_init: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-6,
    verbose: bool = False
) -> Dict[str, Dict[str, Any]]:
    """对比多个优化器

    Args:
        func: 测试函数
        optimizers: 优化器字典 {name: optimizer}
        x_init: 初始点
        max_iter: 最大迭代次数
        tol: 收敛容差
        verbose: 是否打印详细信息

    Returns:
        对比结果字典
    """
    results = {}

    for name, optimizer in optimizers.items():
        if verbose:
            print(f"\nRunning {name}...")

        # 重置优化器状态
        optimizer.reset()

        # 运行优化
        result = optimize(
            func, optimizer, x_init, max_iter, tol, verbose
        )

        results[name] = result

        if verbose:
            print(f"{name}: {result['niter']} iterations, "
                  f"f(x) = {result['fun']:.6e}, "
                  f"|grad| = {result['grad_norms'][-1]:.6e}")

    return results


def grid_search(
    func,
    optimizer_class,
    x_init: np.ndarray,
    param_grid: Dict[str, list],
    max_iter: int = 1000,
    tol: float = 1e-6
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """网格搜索最优超参数

    Args:
        func: 测试函数
        optimizer_class: 优化器类
        x_init: 初始点
        param_grid: 参数网格 {param_name: [values]}
        max_iter: 最大迭代次数
        tol: 收敛容差

    Returns:
        (最优参数, 所有结果)
    """
    from itertools import product

    # 生成所有参数组合
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    param_combinations = list(product(*param_values))

    best_result = None
    best_params = None
    all_results = {}

    for combo in param_combinations:
        # 创建参数字典
        params = dict(zip(param_names, combo))
        params_key = str(params)

        # 创建优化器
        optimizer = optimizer_class(**params)

        # 运行优化
        result = optimize(func, optimizer, x_init.copy(), max_iter, tol)

        # 记录结果
        all_results[params_key] = {
            'params': params,
            'result': result
        }

        # 更新最优结果
        if best_result is None or result['fun'] < best_result['fun']:
            best_result = result
            best_params = params

    return best_params, all_results
