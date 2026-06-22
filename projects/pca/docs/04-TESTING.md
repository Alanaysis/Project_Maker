# 04 - 测试文档：PCA 主成分分析

## 1. 测试策略

### 1.1 测试目标

- 验证算法正确性
- 确保代码质量
- 覆盖边界情况
- 与参考实现对比

### 1.2 测试方法

1. **单元测试**：测试每个函数/方法的独立功能
2. **集成测试**：测试完整流程的正确性
3. **回归测试**：确保修改不破坏已有功能
4. **边界测试**：测试异常输入和边界条件

### 1.3 测试工具

- pytest：测试框架
- numpy：数值计算和验证

## 2. 测试覆盖

### 2.1 协方差矩阵模块 (test_covariance.py)

#### TestCenterData

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_basic_centering | 基本中心化功能 | 均值正确、中心化后均值为0 |
| test_single_feature | 单特征数据 | 结果与手动计算一致 |
| test_already_centered | 已中心化数据 | 结果不变 |

#### TestCovarianceMatrix

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_known_covariance | 已知协方差 | 形状正确、对称、对角线为正 |
| test_identity_covariance | 标准正态数据 | 协方差接近单位矩阵 |
| test_matches_numpy | 与 numpy 对比 | 结果与 np.cov 一致 |
| test_invalid_input_1d | 1D 输入 | 抛出 ValueError |
| test_invalid_input_single_sample | 单样本 | 抛出 ValueError |

#### TestCovarianceMatrixManual

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_matches_vectorized | 与向量化对比 | 两种实现结果一致 |

### 2.2 特征值分解模块 (test_eigen.py)

#### TestPowerIteration

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_simple_matrix | 对角矩阵 | 最大特征值正确 |
| test_known_symmetric_matrix | 已知对称矩阵 | 特征值正确 |
| test_eigenvector_normalized | 向量归一化 | ||v|| = 1 |
| test_eigenvalue_equation | 特征值方程 | Av = λv |

#### TestDeflation

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_removes_eigenvalue | 压缩效果 | 压缩后特征值为0 |

#### TestQRAlgorithm

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_diagonal_matrix | 对角矩阵 | 特征值正确 |
| test_known_symmetric | 已知对称矩阵 | 特征值正确 |
| test_matches_numpy | 与 numpy 对比 | 结果与 np.linalg.eigh 一致 |
| test_eigenvectors_orthogonal | 特征向量正交 | V^T V = I |

#### TestEigenDecomposition

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_qr_method | QR 方法 | 结果正确 |
| test_power_method | 幂迭代方法 | 结果正确 |
| test_n_components | 指定成分数 | 返回正确数量 |
| test_invalid_input | 非方阵输入 | 抛出 ValueError |
| test_invalid_method | 未知方法 | 抛出 ValueError |

### 2.3 PCA 主类 (test_pca.py)

#### TestPCAFit

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_basic_fit | 基本拟合 | 状态正确 |
| test_components_shape | 主成分形状 | (n_components, n_features) |
| test_explained_variance | 解释方差 | 非负、比例之和为1 |
| test_explained_variance_ratio_by_threshold | 阈值选择 | 累积比例 >= 阈值 |
| test_reproducibility | 可重复性 | 相同输入相同输出 |

#### TestPCATransform

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_fit_transform | 组合方法 | 形状正确 |
| test_transform_new_data | 新数据变换 | 形状正确 |
| test_transform_before_fit_raises | 未拟合调用 | 抛出 RuntimeError |
| test_transform_wrong_features | 特征数不匹配 | 抛出 ValueError |

#### TestPCAInverseTransform

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_inverse_transform | 逆变换 | 形状正确 |
| test_reconstruction_quality | 全维度重建 | 误差接近0 |
| test_reconstruction_error | 重建误差计算 | 全维度误差为0 |

#### TestPCADimensionReduction

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_correlated_data | 相关数据 | 第一主成分解释大部分方差 |
| test_dimension_preserves_structure | 结构保留 | 聚类仍可分离 |

#### TestPCAEdgeCases

| 测试用例 | 测试内容 | 验证方法 |
|----------|----------|----------|
| test_invalid_n_components_int | 无效整数 | 抛出 ValueError |
| test_invalid_n_components_float | 无效浮点数 | 抛出 ValueError |
| test_n_components_exceeds_features | 超过特征数 | 抛出 ValueError |
| test_1d_input_raises | 1D 输入 | 抛出 ValueError |
| test_repr_not_fitted | 未拟合表示 | 包含 "not fitted" |
| test_repr_fitted | 拟合后表示 | 包含正确信息 |

## 3. 测试用例详情

### 3.1 关键测试用例

#### 测试与 NumPy 结果一致性

```python
def test_matches_numpy(self):
    """验证我们的实现与 NumPy 结果一致。"""
    np.random.seed(42)
    X = np.random.randn(50, 4)
    X_centered, _ = center_data(X)

    cov_ours = compute_covariance_matrix(X_centered)
    cov_numpy = np.cov(X_centered, rowvar=False)

    np.testing.assert_array_almost_equal(cov_ours, cov_numpy)
```

#### 测试全维度重建无损

```python
def test_reconstruction_quality(self):
    """全维度 PCA 应无损重建。"""
    X = np.random.randn(50, 3)
    pca = PCA(n_components=3)
    X_reduced = pca.fit_transform(X)
    X_reconstructed = pca.inverse_transform(X_reduced)

    np.testing.assert_array_almost_equal(X, X_reconstructed, decimal=10)
```

#### 测试特征向量正交性

```python
def test_eigenvectors_orthogonal(self):
    """特征向量应正交。"""
    A = np.random.randn(3, 3)
    A = A + A.T

    _, eigenvectors = qr_algorithm(A)

    orthogonality = eigenvectors.T @ eigenvectors
    np.testing.assert_array_almost_equal(orthogonality, np.eye(3))
```

### 3.2 边界测试用例

#### 测试无效输入

```python
def test_invalid_input_1d(self):
    """1D 输入应抛出异常。"""
    X = np.array([1, 2, 3], dtype=np.float64)
    with pytest.raises(ValueError, match="2D"):
        compute_covariance_matrix(X)
```

#### 测试状态检查

```python
def test_transform_before_fit_raises(self):
    """未拟合时调用 transform 应抛出异常。"""
    pca = PCA(n_components=2)
    X = np.random.randn(10, 3)
    with pytest.raises(RuntimeError, match="尚未拟合"):
        pca.transform(X)
```

## 4. 测试数据

### 4.1 测试数据生成

使用 numpy 随机数生成器，设置固定种子确保可重复性：

```python
np.random.seed(42)
X = np.random.randn(100, 5)
```

### 4.2 特殊测试数据

- 对角矩阵：特征值已知
- 单位矩阵：特征值全为1
- 秩1矩阵：只有一个非零特征值
- 相关数据：测试降维效果

## 5. 运行测试

### 5.1 运行所有测试

```bash
cd projects/pca
python -m pytest tests/ -v
```

### 5.2 运行特定模块

```bash
python -m pytest tests/test_covariance.py -v
python -m pytest tests/test_eigen.py -v
python -m pytest tests/test_pca.py -v
```

### 5.3 运行特定测试

```bash
python -m pytest tests/test_pca.py::TestPCAFit::test_basic_fit -v
```

### 5.4 查看覆盖率

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## 6. 测试结果

### 6.1 预期结果

所有测试应通过，无失败或错误。

### 6.2 数值精度

- 浮点比较使用 `decimal=6` 或 `decimal=10`
- 使用 `np.testing.assert_almost_equal` 或 `np.testing.assert_array_almost_equal`

### 6.3 测试报告示例

```
tests/test_covariance.py::TestCenterData::test_basic_centering PASSED
tests/test_covariance.py::TestCovarianceMatrix::test_known_covariance PASSED
tests/test_eigen.py::TestQRAlgorithm::test_matches_numpy PASSED
tests/test_pca.py::TestPCAFit::test_basic_fit PASSED
...

========================= 35 passed in 0.52s =========================
```

## 7. 持续集成

### 7.1 自动化测试

建议在以下情况运行测试：
- 代码提交前
- 代码修改后
- 定期回归测试

### 7.2 测试覆盖率目标

- 语句覆盖率：> 90%
- 分支覆盖率：> 80%
- 函数覆盖率：100%

## 8. 测试总结

### 8.1 测试统计

| 模块 | 测试类数 | 测试用例数 |
|------|----------|------------|
| covariance | 3 | 8 |
| eigen | 4 | 11 |
| pca | 5 | 16 |
| 总计 | 12 | 35 |

### 8.2 测试质量评估

- 功能覆盖：覆盖所有主要功能
- 边界覆盖：覆盖主要边界情况
- 错误处理：验证异常情况
- 数值精度：与参考实现对比
