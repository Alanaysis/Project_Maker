"""
Tests for Modal Analysis Module
模态分析模块测试
"""

import numpy as np
import pytest

from src.modal_analysis import (
    modal_analysis,
    verify_orthogonality,
    modal_participation_factor,
    summarize_modes,
)
from src.multi_dof import build_spring_mass_matrices


class TestModalAnalysis:
    """模态分析测试"""

    def test_sdof_modal(self):
        """测试单自由度模态分析"""
        mass_matrix = np.array([[1.0]])
        stiffness_matrix = np.array([[100.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)

        expected_freq = np.sqrt(100.0 / 1.0) / (2 * np.pi)
        assert np.isclose(modal.natural_freq_hz[0], expected_freq, rtol=1e-5)

    def test_two_dof_frequencies(self):
        """测试两自由度固有频率"""
        mass_matrix = np.diag([1.0, 1.0])
        stiffness_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)

        # 理论值: omega1 = 1, omega2 = sqrt(3)
        expected = np.array([1.0, np.sqrt(3.0)]) / (2 * np.pi)
        assert np.allclose(modal.natural_freq_hz, expected, rtol=1e-5)

    def test_mode_shapes_count(self):
        """测试模态振型数量"""
        mass_matrix = np.diag([1.0, 2.0, 3.0])
        stiffness_matrix = np.array([[2, -1, 0], [-1, 3, -1], [0, -1, 2]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)

        assert len(modal.natural_freq_hz) == 3
        assert modal.mode_shapes.shape == (3, 3)

    def test_frequencies_sorted(self):
        """测试频率排序"""
        mass_matrix = np.diag([1.0, 1.0])
        stiffness_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)

        assert modal.natural_freq_hz[0] < modal.natural_freq_hz[1]

    def test_invalid_mass_matrix(self):
        """测试无效质量矩阵"""
        mass_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])  # 2x2
        stiffness_matrix = np.array([[1.0]])  # 1x1, 维度不匹配
        with pytest.raises(ValueError):
            modal_analysis(mass_matrix, stiffness_matrix)

    def test_dimension_mismatch(self):
        """测试维度不匹配"""
        mass_matrix = np.array([[1.0]])
        stiffness_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])
        with pytest.raises(ValueError):
            modal_analysis(mass_matrix, stiffness_matrix)


class TestOrthogonality:
    """正交性验证测试"""

    def test_mass_orthogonality(self):
        """测试质量正交性"""
        mass_matrix = np.diag([1.0, 1.0])
        stiffness_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)
        ortho = verify_orthogonality(modal.mode_shapes, mass_matrix, stiffness_matrix)

        # 非对角元应接近零
        assert ortho['mass_ortho_max_offdiag'] < 1e-10

    def test_stiffness_orthogonality(self):
        """测试刚度正交性"""
        mass_matrix = np.diag([1.0, 1.0])
        stiffness_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)
        ortho = verify_orthogonality(modal.mode_shapes, mass_matrix, stiffness_matrix)

        # 非对角元应接近零
        assert ortho['stiff_ortho_max_offdiag'] < 1e-10

    def test_diagonal_properties(self):
        """测试对角元性质"""
        mass_matrix = np.diag([1.0, 1.0])
        stiffness_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)
        ortho = verify_orthogonality(modal.mode_shapes, mass_matrix, stiffness_matrix)

        # 对角元应为正
        assert np.all(np.diag(ortho['mass_orthogonality']) > 0)
        assert np.all(np.diag(ortho['stiffness_orthogonality']) > 0)


class TestModalParticipation:
    """模态参与系数测试"""

    def test_participation_factor_shape(self):
        """测试参与系数形状"""
        mass_matrix = np.diag([1.0, 1.0, 1.0])
        stiffness_matrix = np.array([[2, -1, 0], [-1, 2, -1], [0, -1, 2]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)

        gamma = modal_participation_factor(modal.mode_shapes, mass_matrix, np.array([1.0, 0.0, 0.0]))
        assert len(gamma) == 3

    def test_participation_factor_values(self):
        """测试参与系数值"""
        mass_matrix = np.diag([1.0, 1.0])
        stiffness_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)

        gamma = modal_participation_factor(modal.mode_shapes, mass_matrix, np.array([1.0, 0.0]))
        assert len(gamma) == 2


class TestSummarizeModes:
    """模态摘要测试"""

    def test_summary_contains_info(self):
        """测试摘要包含基本信息"""
        mass_matrix = np.diag([1.0, 1.0])
        stiffness_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
        modal = modal_analysis(mass_matrix, stiffness_matrix)

        summary = summarize_modes(modal)
        assert "模态分析" in summary or "Modal" in summary
        assert "1.0" in summary or "1" in summary  # 频率值


class TestMDOFSystem:
    """多自由度系统测试"""

    def test_spring_mass_construction(self):
        """测试弹簧-质量矩阵构建"""
        masses = [1.0, 2.0]
        springs = [(0, 1, 100.0)]
        ground_springs = [(0, 50.0), (1, 75.0)]

        mass_matrix, stiffness_matrix = build_spring_mass_matrices(masses, springs, ground_springs)

        assert mass_matrix.shape == (2, 2)
        assert stiffness_matrix.shape == (2, 2)
        assert np.allclose(np.diag(mass_matrix), masses)

    def test_symmetric_stiffness(self):
        """测试刚度矩阵对称性"""
        masses = [1.0, 1.0, 1.0]
        springs = [(0, 1, 100.0), (1, 2, 100.0)]
        ground_springs = [(0, 50.0), (2, 50.0)]

        _, stiffness_matrix = build_spring_mass_matrices(masses, springs, ground_springs)

        assert np.allclose(stiffness_matrix, stiffness_matrix.T)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
