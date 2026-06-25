"""
因子组合模块测试
"""

import numpy as np
import pandas as pd
import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.combination.equal_weight import EqualWeightCombination
from src.combination.ic_weight import ICWeightCombination
from src.combination.ml_combination import MLCombination


@pytest.fixture
def sample_factors():
    """生成测试用因子数据"""
    np.random.seed(42)
    n = 200
    factors = pd.DataFrame({
        "momentum": np.random.randn(n),
        "volatility": np.random.randn(n),
        "value": np.random.randn(n),
    })
    returns = pd.Series(np.random.randn(n) * 0.02, index=range(n))
    return factors, returns


class TestEqualWeightCombination:
    """等权组合测试"""

    def test_combine(self, sample_factors):
        """测试等权组合"""
        factors, _ = sample_factors
        result = EqualWeightCombination.combine(factors)
        assert len(result) == len(factors)

    def test_rank_equal_weight(self, sample_factors):
        """测试排名等权组合"""
        factors, _ = sample_factors
        result = EqualWeightCombination.rank_equal_weight(factors)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 1).all()

    def test_sign_adjusted_combine(self, sample_factors):
        """测试符号调整组合"""
        factors, _ = sample_factors
        signs = pd.Series({"momentum": 1, "volatility": -1, "value": 1})
        result = EqualWeightCombination.sign_adjusted_combine(factors, signs)
        assert len(result) == len(factors)


class TestICWeightCombination:
    """IC 加权组合测试"""

    def test_combine(self, sample_factors):
        """测试 IC 加权组合"""
        factors, _ = sample_factors
        ic_values = pd.Series({
            "momentum": 0.05,
            "volatility": -0.03,
            "value": 0.04,
        })
        result = ICWeightCombination.combine(factors, ic_values)
        assert len(result) == len(factors)


class TestMLCombination:
    """ML 组合测试"""

    def test_ridge_combination(self, sample_factors):
        """测试 Ridge 回归组合"""
        factors, returns = sample_factors
        combiner = MLCombination(model_type="ridge")
        combiner.fit(factors, returns)
        predictions = combiner.predict(factors)
        assert len(predictions) == len(factors)

    def test_feature_importance(self, sample_factors):
        """测试特征重要性"""
        factors, returns = sample_factors
        combiner = MLCombination(model_type="ridge")
        combiner.fit(factors, returns)
        importance = combiner.get_feature_importance()
        assert len(importance) == 3
        assert (importance >= 0).all()

    def test_cross_validate(self, sample_factors):
        """测试交叉验证"""
        factors, returns = sample_factors
        results = MLCombination.cross_validate(
            factors, returns, n_splits=3, model_type="ridge"
        )
        assert "cv_ic_mean" in results
        assert "cv_ir" in results
        assert results["n_folds"] == 3

    def test_gbm_combination(self, sample_factors):
        """测试 GBM 组合"""
        factors, returns = sample_factors
        combiner = MLCombination(model_type="gbm", n_estimators=10)
        combiner.fit(factors, returns)
        predictions = combiner.predict(factors)
        assert len(predictions) == len(factors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
