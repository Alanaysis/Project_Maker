"""
机器学习组合模块

使用机器学习方法学习因子的最优组合权重，能够捕捉因子之间的非线性关系。
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from typing import Optional, List, Dict


class MLCombination:
    """
    机器学习组合器

    使用机器学习模型学习因子与未来收益之间的关系。

    使用示例:
        >>> ml_combiner = MLCombination(model_type="ridge")
        >>> ml_combiner.fit(factor_train, returns_train)
        >>> combined = ml_combiner.predict(factor_test)
    """

    def __init__(self, model_type: str = "ridge", **model_params):
        """
        初始化 ML 组合器

        参数:
            model_type: 模型类型 ("ridge", "lasso", "elastic_net", "gbm", "rf")
            **model_params: 模型参数
        """
        self.model_type = model_type
        self.model = self._create_model(model_type, model_params)
        self.factor_cols = None
        self.is_fitted = False

    def _create_model(self, model_type: str, params: Dict):
        """创建机器学习模型"""
        models = {
            "ridge": Ridge,
            "lasso": Lasso,
            "elastic_net": ElasticNet,
            "gbm": GradientBoostingRegressor,
            "rf": RandomForestRegressor,
        }
        if model_type not in models:
            raise ValueError(f"Unknown model: {model_type}. Choose from {list(models.keys())}")

        # 设置默认参数
        defaults = {
            "ridge": {"alpha": 1.0},
            "lasso": {"alpha": 0.01},
            "elastic_net": {"alpha": 0.01, "l1_ratio": 0.5},
            "gbm": {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.1},
            "rf": {"n_estimators": 100, "max_depth": 5},
        }

        final_params = {**defaults.get(model_type, {}), **params}
        return models[model_type](**final_params)

    def fit(self, factors: pd.DataFrame, forward_returns: pd.Series,
            factor_cols: Optional[List[str]] = None) -> "MLCombination":
        """
        训练模型

        参数:
            factors: 因子 DataFrame
            forward_returns: 未来收益率序列
            factor_cols: 要使用的因子列名

        返回:
            self (支持链式调用)
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()
        self.factor_cols = factor_cols

        # 准备数据
        data = factors[factor_cols].copy()
        data["target"] = forward_returns
        data = data.dropna()

        X = data[factor_cols].values
        y = data["target"].values

        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, factors: pd.DataFrame) -> pd.Series:
        """
        预测组合因子值

        参数:
            factors: 因子 DataFrame

        返回:
            组合因子值序列
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X = factors[self.factor_cols].fillna(0).values
        predictions = self.model.predict(X)
        return pd.Series(predictions, index=factors.index)

    def get_feature_importance(self) -> pd.Series:
        """
        获取特征重要性 (因子权重)

        返回:
            各因子的重要性分数
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        if hasattr(self.model, "coef_"):
            # 线性模型
            importance = np.abs(self.model.coef_)
        elif hasattr(self.model, "feature_importances_"):
            # 树模型
            importance = self.model.feature_importances_
        else:
            return pd.Series()

        return pd.Series(importance, index=self.factor_cols).sort_values(ascending=False)

    @staticmethod
    def rolling_train_predict(factors: pd.DataFrame,
                               forward_returns: pd.Series,
                               train_window: int = 252,
                               model_type: str = "ridge",
                               factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        滚动训练预测: 使用滚动窗口训练模型并预测

        原理: 因子与收益的关系可能随时间变化，滚动训练能适应这种变化。

        参数:
            factors: 因子 DataFrame
            forward_returns: 未来收益率序列
            train_window: 训练窗口大小 (交易日数)
            model_type: 模型类型
            factor_cols: 因子列名

        返回:
            组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        result = pd.Series(np.nan, index=factors.index)

        for i in range(train_window, len(factors)):
            # 训练数据
            train_factors = factors.iloc[i - train_window:i]
            train_returns = forward_returns.iloc[i - train_window:i]

            # 训练模型
            combiner = MLCombination(model_type=model_type)
            combiner.fit(train_factors, train_returns, factor_cols)

            # 预测
            result.iloc[i] = combiner.predict(factors.iloc[[i]]).iloc[0]

        return result

    @staticmethod
    def cross_validate(factors: pd.DataFrame,
                        forward_returns: pd.Series,
                        n_splits: int = 5,
                        model_type: str = "ridge",
                        factor_cols: Optional[List[str]] = None) -> Dict[str, float]:
        """
        交叉验证: 评估 ML 组合的样本外表现

        参数:
            factors: 因子 DataFrame
            forward_returns: 未来收益率序列
            n_splits: 交叉验证折数
            model_type: 模型类型
            factor_cols: 因子列名

        返回:
            包含 CV 指标的字典
        """
        from scipy import stats

        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        data = factors[factor_cols].copy()
        data["target"] = forward_returns
        data = data.dropna()

        n = len(data)
        fold_size = n // n_splits
        ics = []

        for fold in range(n_splits):
            test_start = fold * fold_size
            test_end = min((fold + 1) * fold_size, n)

            test_data = data.iloc[test_start:test_end]
            train_data = pd.concat([data.iloc[:test_start], data.iloc[test_end:]])

            if len(train_data) < 50:
                continue

            combiner = MLCombination(model_type=model_type)
            combiner.fit(train_data[factor_cols], train_data["target"])

            predictions = combiner.predict(test_data[factor_cols])
            corr, _ = stats.spearmanr(predictions, test_data["target"])
            ics.append(corr)

        if not ics:
            return {"cv_ic_mean": np.nan, "cv_ic_std": np.nan, "cv_ir": np.nan}

        ic_arr = np.array(ics)
        return {
            "cv_ic_mean": np.mean(ic_arr),
            "cv_ic_std": np.std(ic_arr),
            "cv_ir": np.mean(ic_arr) / np.std(ic_arr) if np.std(ic_arr) > 0 else 0,
            "cv_ic_positive_rate": (ic_arr > 0).mean(),
            "n_folds": len(ics),
        }
