"""Tests for visualization module."""

import pytest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

from src.position_analysis import FourBarParams
from src.visualization import (
    plot_linkage,
    plot_coupler_curve,
    plot_transmission_angle,
    plot_phase_diagram,
    plot_acceleration_phase,
    create_full_analysis_figure,
)


class TestVisualization:
    """Test visualization functions."""

    @pytest.fixture
    def params(self):
        """Create a standard crank-rocker mechanism for testing."""
        return FourBarParams(a1=4.0, a2=1.5, a3=4.5, a4=3.5)

    def test_plot_linkage(self, params):
        """Linkage plot should create a valid figure."""
        fig, ax = plt.subplots()
        result_ax = plot_linkage(params, np.pi/4, ax=ax)
        assert result_ax is ax
        lines = result_ax.get_lines()
        assert len(lines) > 0
        plt.close(fig)

    def test_plot_coupler_curve(self, params):
        """Coupler curve plot should create a valid figure."""
        fig, ax = plt.subplots()
        result_ax = plot_coupler_curve(params, num_points=360, ax=ax)
        assert result_ax is ax
        lines = result_ax.get_lines()
        assert len(lines) > 0
        plt.close(fig)

    def test_plot_transmission_angle(self, params):
        """Transmission angle plot should create a valid figure."""
        fig, ax = plt.subplots()
        result_ax = plot_transmission_angle(params, num_points=360, ax=ax)
        assert result_ax is ax
        lines = result_ax.get_lines()
        assert len(lines) > 0
        plt.close(fig)

    def test_plot_phase_diagram(self, params):
        """Phase diagram should create valid figures."""
        fig, axes = plt.subplots(1, 2)
        ax1, ax2 = axes[0], axes[1]
        result_ax1, result_ax2 = plot_phase_diagram(params, omega2=1.0, ax1=ax1, ax2=ax2)
        assert result_ax1 is ax1
        assert result_ax2 is ax2
        plt.close(fig)

    def test_plot_acceleration_phase(self, params):
        """Acceleration phase plot should create a valid figure."""
        fig, ax = plt.subplots()
        result_ax = plot_acceleration_phase(params, omega2=1.0, ax=ax)
        assert result_ax is ax
        lines = result_ax.get_lines()
        assert len(lines) > 0
        plt.close(fig)

    def test_create_full_analysis_figure(self, params):
        """Full analysis figure should create a valid figure."""
        fig = create_full_analysis_figure(params)
        assert fig is not None
        assert len(fig.axes) == 5  # Should have 5 subplots
        plt.close(fig)

    def test_plot_coupler_curve_creates_new_axes(self, params):
        """Coupler curve should create new axes if none provided."""
        ax = plot_coupler_curve(params, num_points=180)
        assert ax is not None
        plt.close(ax.figure)
