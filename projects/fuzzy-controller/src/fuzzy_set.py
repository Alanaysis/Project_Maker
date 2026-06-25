"""
模糊集合模块

实现模糊集合和各种隶属函数：
- 三角形隶属函数 (Triangular)
- 梯形隶属函数 (Trapezoidal)
- 高斯隶属函数 (Gaussian)
- 钟形隶属函数 (Bell-shaped)
"""

import numpy as np
from typing import Union, List, Tuple


class MembershipFunction:
    """
    隶属函数基类

    隶属函数将输入值映射到 [0, 1] 的隶属度
    """

    def __init__(self, name: str):
        """
        初始化隶属函数

        参数:
            name: 隶属函数名称
        """
        self.name = name

    def __call__(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        计算隶属度

        参数:
            x: 输入值或数组

        返回:
            隶属度 (0-1)
        """
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"


class TriangularMF(MembershipFunction):
    """
    三角形隶属函数

    参数:
        a: 左端点
        b: 峰值点
        c: 右端点

    数学公式:
        μ(x) = max(0, min((x-a)/(b-a), (c-x)/(c-b)))
    """

    def __init__(self, name: str, a: float, b: float, c: float):
        super().__init__(name)
        self.a = a
        self.b = b
        self.c = c

    def __call__(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=float)
        result = np.zeros_like(x)

        # 处理退化情况：a=b（左端点=峰值点）
        if self.a == self.b:
            # 此时只有下降段
            mask = (x >= self.a) & (x <= self.c)
            if self.c != self.b:
                result[mask] = (self.c - x[mask]) / (self.c - self.b)
            else:
                # a=b=c，脉冲函数
                result[x == self.a] = 1.0
        elif self.b == self.c:
            # 此时只有上升段
            mask = (x >= self.a) & (x <= self.b)
            result[mask] = (x[mask] - self.a) / (self.b - self.a)
        else:
            # 标准三角形：上升段 + 下降段
            mask1 = (x >= self.a) & (x <= self.b)
            result[mask1] = (x[mask1] - self.a) / (self.b - self.a)

            mask2 = (x > self.b) & (x <= self.c)
            result[mask2] = (self.c - x[mask2]) / (self.c - self.b)

        # 如果输入是标量，返回标量
        if result.ndim == 0:
            return float(result)
        return result


class TrapezoidalMF(MembershipFunction):
    """
    梯形隶属函数

    参数:
        a: 左端点
        b: 左肩点
        c: 右肩点
        d: 右端点

    数学公式:
        μ(x) = max(0, min((x-a)/(b-a), 1, (d-x)/(d-c)))
    """

    def __init__(self, name: str, a: float, b: float, c: float, d: float):
        super().__init__(name)
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def __call__(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=float)
        result = np.zeros_like(x)

        # 上升段：a 到 b（不包含 b，因为平台段会处理 b）
        if self.b != self.a:
            mask1 = (x >= self.a) & (x < self.b)
            result[mask1] = (x[mask1] - self.a) / (self.b - self.a)

        # 平台段：b 到 c
        mask2 = (x >= self.b) & (x <= self.c)
        result[mask2] = 1.0

        # 下降段：c 到 d（不包含 c，因为平台段已处理 c）
        if self.d != self.c:
            mask3 = (x > self.c) & (x <= self.d)
            result[mask3] = (self.d - x[mask3]) / (self.d - self.c)

        # 如果输入是标量，返回标量
        if result.ndim == 0:
            return float(result)
        return result


class GaussianMF(MembershipFunction):
    """
    高斯隶属函数

    参数:
        mean: 均值
        sigma: 标准差

    数学公式:
        μ(x) = exp(-(x - mean)^2 / (2 * sigma^2))
    """

    def __init__(self, name: str, mean: float, sigma: float):
        super().__init__(name)
        self.mean = mean
        self.sigma = sigma

    def __call__(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=float)
        result = np.exp(-((x - self.mean) ** 2) / (2 * self.sigma ** 2))

        # 如果输入是标量，返回标量
        if result.ndim == 0:
            return float(result)
        return result


class BellShapedMF(MembershipFunction):
    """
    钟形隶属函数 (广义钟形函数)

    参数:
        a: 宽度参数
        b: 斜率参数
        c: 中心点

    数学公式:
        μ(x) = 1 / (1 + |(x - c) / a|^(2b))
    """

    def __init__(self, name: str, a: float, b: float, c: float):
        super().__init__(name)
        self.a = a
        self.b = b
        self.c = c

    def __call__(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=float)
        result = 1.0 / (1.0 + np.abs((x - self.c) / self.a) ** (2 * self.b))

        # 如果输入是标量，返回标量
        if result.ndim == 0:
            return float(result)
        return result


class FuzzySet:
    """
    模糊集合类

    表示一个模糊集合，包含隶属函数和相关操作

    属性:
        name: 模糊集合名称
        mf: 隶属函数
        universe: 论域范围 (min, max)
    """

    def __init__(self, name: str, mf: MembershipFunction, universe: Tuple[float, float] = None):
        """
        初始化模糊集合

        参数:
            name: 模糊集合名称
            mf: 隶属函数
            universe: 论域范围 (min, max)
        """
        self.name = name
        self.mf = mf
        self.universe = universe

    def membership(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        计算隶属度

        参数:
            x: 输入值或数组

        返回:
            隶属度
        """
        return self.mf(x)

    def complement(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        计算模糊集合的补集 (NOT 操作)

        参数:
            x: 输入值或数组

        返回:
            补集的隶属度
        """
        return 1.0 - self.mf(x)

    def intersect(self, other: 'FuzzySet', x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        计算两个模糊集合的交集 (AND 操作)

        参数:
            other: 另一个模糊集合
            x: 输入值或数组

        返回:
            交集的隶属度 (取最小值)
        """
        return np.minimum(self.mf(x), other.mf(x))

    def union(self, other: 'FuzzySet', x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        计算两个模糊集合的并集 (OR 操作)

        参数:
            other: 另一个模糊集合
            x: 输入值或数组

        返回:
            并集的隶属度 (取最大值)
        """
        return np.maximum(self.mf(x), other.mf(x))

    def alpha_cut(self, x: Union[float, np.ndarray], alpha: float) -> np.ndarray:
        """
        α-截集

        参数:
            x: 输入值数组
            alpha: 阈值 (0-1)

        返回:
            满足隶属度 >= alpha 的元素
        """
        x = np.asarray(x, dtype=float)
        membership_values = self.mf(x)
        return x[membership_values >= alpha]

    def plot(self, x_range: Tuple[float, float] = None, num_points: int = 100):
        """
        绘制隶属函数 (需要 matplotlib)

        参数:
            x_range: x轴范围
            num_points: 采样点数
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("需要安装 matplotlib 来绘图")
            return

        if x_range is None:
            if self.universe is not None:
                x_range = self.universe
            else:
                raise ValueError("需要指定 x_range 或 universe")

        x = np.linspace(x_range[0], x_range[1], num_points)
        y = self.mf(x)

        plt.figure(figsize=(8, 4))
        plt.plot(x, y, 'b-', linewidth=2)
        plt.fill_between(x, y, alpha=0.3)
        plt.xlabel('x')
        plt.ylabel('隶属度')
        plt.title(f'模糊集合: {self.name}')
        plt.grid(True, alpha=0.3)
        plt.ylim(-0.05, 1.05)
        plt.show()

    def __repr__(self):
        return f"FuzzySet(name='{self.name}', mf={self.mf})"


# 工厂函数：创建常见的模糊集合
def create_triangular_set(name: str, a: float, b: float, c: float, universe: Tuple[float, float] = None) -> FuzzySet:
    """创建三角形模糊集合"""
    mf = TriangularMF(name, a, b, c)
    return FuzzySet(name, mf, universe)


def create_trapezoidal_set(name: str, a: float, b: float, c: float, d: float, universe: Tuple[float, float] = None) -> FuzzySet:
    """创建梯形模糊集合"""
    mf = TrapezoidalMF(name, a, b, c, d)
    return FuzzySet(name, mf, universe)


def create_gaussian_set(name: str, mean: float, sigma: float, universe: Tuple[float, float] = None) -> FuzzySet:
    """创建高斯模糊集合"""
    mf = GaussianMF(name, mean, sigma)
    return FuzzySet(name, mf, universe)
