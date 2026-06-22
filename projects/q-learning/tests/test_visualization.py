"""Tests for visualization utilities."""

import pytest
import numpy as np

from src.visualization import (
    visualize_training,
    visualize_policy,
    visualize_q_values,
    visualize_episode_path,
    _moving_average,
    _ascii_plot,
)


class TestVisualizeTraining:
    """Tests for visualize_training function."""

    def test_basic_output(self):
        rewards = [1.0, 2.0, 3.0, 4.0, 5.0]
        steps = [10, 8, 6, 4, 2]
        result = visualize_training(rewards, steps, window=3)

        assert "TRAINING PROGRESS" in result
        assert "Total Episodes: 5" in result

    def test_with_large_dataset(self):
        rewards = [float(i) for i in range(100)]
        steps = [100 - i for i in range(100)]
        result = visualize_training(rewards, steps, window=10)

        assert "TRAINING PROGRESS" in result
        assert "Total Episodes: 100" in result

    def test_empty_data(self):
        rewards = [1.0]
        steps = [10]
        result = visualize_training(rewards, steps)
        assert "Total Episodes: 1" in result


class TestVisualizePolicy:
    """Tests for visualize_policy function."""

    def test_basic_output(self):
        grid = np.zeros((3, 3), dtype=np.int32)
        grid[0, 2] = 2  # Goal
        policy = np.array([
            [1, 1, 0],
            [2, 2, 0],
            [2, 2, 0],
        ])

        result = visualize_policy(grid, policy, (0, 0), (0, 2))
        assert "S" in result
        assert "G" in result

    def test_with_walls(self):
        grid = np.zeros((3, 3), dtype=np.int32)
        grid[1, 1] = 1  # Wall
        grid[0, 2] = 2  # Goal
        policy = np.array([
            [1, 1, 0],
            [2, 0, 0],
            [2, 2, 0],
        ])

        result = visualize_policy(grid, policy, (0, 0), (0, 2))
        assert "#" in result

    def test_with_traps(self):
        grid = np.zeros((3, 3), dtype=np.int32)
        grid[2, 2] = 3  # Trap
        grid[0, 2] = 2  # Goal
        policy = np.array([
            [1, 1, 0],
            [2, 2, 0],
            [2, 2, 0],
        ])

        result = visualize_policy(grid, policy, (0, 0), (0, 2))
        assert "X" in result


class TestVisualizeQValues:
    """Tests for visualize_q_values function."""

    def test_basic_output(self):
        grid = np.zeros((3, 3), dtype=np.int32)
        grid[0, 2] = 2  # Goal
        value_map = np.array([
            [1.0, 2.0, 100.0],
            [0.5, 1.5, 50.0],
            [0.1, 0.8, 25.0],
        ])

        result = visualize_q_values(grid, value_map, (0, 0), (0, 2))
        assert "Q-Value Map" in result
        assert "Q-value range" in result


class TestVisualizeEpisodePath:
    """Tests for visualize_episode_path function."""

    def test_basic_output(self):
        grid = np.zeros((3, 3), dtype=np.int32)
        grid[0, 2] = 2  # Goal
        path = [(0, 0), (0, 1), (0, 2)]

        result = visualize_episode_path(grid, path, (0, 0), (0, 2))
        assert "Path length: 3" in result
        assert "*" in result


class TestMovingAverage:
    """Tests for _moving_average function."""

    def test_basic(self):
        data = [1, 2, 3, 4, 5]
        result = _moving_average(data, 3)
        assert len(result) == 3
        assert result[0] == pytest.approx(2.0)
        assert result[1] == pytest.approx(3.0)
        assert result[2] == pytest.approx(4.0)

    def test_window_larger_than_data(self):
        data = [1, 2, 3]
        result = _moving_average(data, 10)
        assert len(result) == 1
        assert result[0] == pytest.approx(2.0)


class TestAsciiPlot:
    """Tests for _ascii_plot function."""

    def test_basic(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _ascii_plot(data, width=5, height=5)
        assert "max:" in result
        assert "min:" in result

    def test_single_value(self):
        data = [5.0]
        result = _ascii_plot(data, width=5, height=5)
        assert "max:" in result
