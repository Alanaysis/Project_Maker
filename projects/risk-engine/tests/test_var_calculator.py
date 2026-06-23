"""测试 VaR 计算模块"""

import pytest
import numpy as np
from src.var_calculator import VaRCalculator, VaRMethod, VaRResult


@pytest.fixture
def sample_returns():
    """示例收益率数据"""
    np.random.seed(42)
    return np.random.normal(0.001, 0.02, 252)  # 一年的日收益率


@pytest.fixture
def calculator():
    """VaR 计算器"""
    return VaRCalculator(portfolio_value=1000000)


class TestVaRCalculator:
    """VaRCalculator 类测试"""

    def test_historical_var(self, calculator, sample_returns):
        """测试历史模拟法 VaR"""
        result = calculator.calculate(sample_returns, VaRMethod.HISTORICAL, 0.95)

        assert isinstance(result, VaRResult)
        assert result.method == "historical"
        assert result.confidence_level == 0.95
        assert result.var < 0  # VaR 应该是负数（损失）
        assert result.cvar <= result.var  # CVaR 应该小于等于 VaR
        assert result.portfolio_value == 1000000
        assert result.var_amount > 0

    def test_parametric_var(self, calculator, sample_returns):
        """测试参数法 VaR"""
        result = calculator.calculate(sample_returns, VaRMethod.PARAMETRIC, 0.95)

        assert isinstance(result, VaRResult)
        assert result.method == "parametric"
        assert result.confidence_level == 0.95
        assert result.var < 0

    def test_monte_carlo_var(self, calculator, sample_returns):
        """测试蒙特卡洛模拟法 VaR"""
        result = calculator.calculate(
            sample_returns, VaRMethod.MONTE_CARLO, 0.95, num_simulations=5000
        )

        assert isinstance(result, VaRResult)
        assert result.method == "monte_carlo"
        assert result.confidence_level == 0.95
        assert result.var < 0

    def test_var_at_different_confidence_levels(self, calculator, sample_returns):
        """测试不同置信水平的 VaR"""
        result_90 = calculator.calculate(sample_returns, VaRMethod.HISTORICAL, 0.90)
        result_95 = calculator.calculate(sample_returns, VaRMethod.HISTORICAL, 0.95)
        result_99 = calculator.calculate(sample_returns, VaRMethod.HISTORICAL, 0.99)

        # 更高的置信水平应该有更大的 VaR（更负）
        assert result_90.var > result_95.var > result_99.var

    def test_var_amount_calculation(self, calculator, sample_returns):
        """测试 VaR 金额计算"""
        result = calculator.calculate(sample_returns, VaRMethod.HISTORICAL, 0.95)

        expected_amount = 1000000 * abs(result.var)
        assert result.var_amount == pytest.approx(expected_amount)

    def test_cvar_calculation(self, calculator, sample_returns):
        """测试 CVaR 计算"""
        result = calculator.calculate(sample_returns, VaRMethod.HISTORICAL, 0.95)

        # CVaR 应该大于等于 VaR（绝对值）
        assert abs(result.cvar) >= abs(result.var)

    def test_calculate_multiple_confidence_levels(self, calculator, sample_returns):
        """测试计算多个置信水平"""
        results = calculator.calculate_multiple_confidence_levels(
            sample_returns,
            VaRMethod.HISTORICAL,
            [0.90, 0.95, 0.99]
        )

        assert len(results) == 3
        assert results[0].confidence_level == 0.90
        assert results[1].confidence_level == 0.95
        assert results[2].confidence_level == 0.99

    def test_compare_methods(self, calculator, sample_returns):
        """测试比较不同方法"""
        results = calculator.compare_methods(sample_returns, 0.95)

        assert len(results) == 3
        assert "historical" in results
        assert "parametric" in results
        assert "monte_carlo" in results

    def test_empty_returns(self, calculator):
        """测试空收益率数据"""
        with pytest.raises(ValueError, match="Returns array is empty"):
            calculator.calculate(np.array([]), VaRMethod.HISTORICAL, 0.95)

    def test_result_to_dict(self, calculator, sample_returns):
        """测试结果转换为字典"""
        result = calculator.calculate(sample_returns, VaRMethod.HISTORICAL, 0.95)
        data = result.to_dict()

        assert "method" in data
        assert "confidence_level" in data
        assert "var" in data
        assert "cvar" in data
        assert "portfolio_value" in data
        assert "var_amount" in data
        assert "cvar_amount" in data


class TestVaRResult:
    """VaRResult 类测试"""

    def test_var_result_creation(self):
        """测试 VaR 结果创建"""
        result = VaRResult(
            method="historical",
            confidence_level=0.95,
            var=-0.025,
            cvar=-0.035,
            portfolio_value=1000000,
            var_amount=25000,
            cvar_amount=35000
        )

        assert result.method == "historical"
        assert result.confidence_level == 0.95
        assert result.var == -0.025
        assert result.cvar == -0.035
        assert result.portfolio_value == 1000000
        assert result.var_amount == 25000
        assert result.cvar_amount == 35000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
