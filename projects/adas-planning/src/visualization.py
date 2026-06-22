"""
Visualization Module
====================

This module provides visualization tools for the ADAS planning system:
- Grid map visualization
- Path planning visualization
- Vehicle trajectory visualization
- Simulation animation
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
from matplotlib.collections import LineCollection
from typing import List, Tuple, Optional, Dict
import matplotlib.animation as animation

from .environment import GridMap, CellType
from .trajectory import Trajectory


class Visualizer:
    """
    Main visualization class for ADAS planning system.

    Provides methods to visualize:
    - Grid maps with obstacles
    - Planned paths
    - Vehicle trajectories
    - Simulation results
    """

    def __init__(self, figsize: Tuple[int, int] = (10, 10)):
        """
        Initialize visualizer.

        Args:
            figsize: Figure size (width, height)
        """
        self.figsize = figsize
        self.fig = None
        self.ax = None

    def setup_figure(self, title: str = "ADAS Planning Visualization") -> Tuple[plt.Figure, plt.Axes]:
        """Setup matplotlib figure."""
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        self.ax.set_title(title, fontsize=14)
        self.ax.set_xlabel("X Position (m)")
        self.ax.set_ylabel("Y Position (m)")
        self.ax.set_aspect('equal')
        return self.fig, self.ax

    def plot_grid_map(self, grid_map: GridMap, ax: plt.Axes = None,
                      show_grid: bool = True, alpha: float = 0.8) -> plt.Axes:
        """
        Plot grid map.

        Args:
            grid_map: Grid map to plot
            ax: Matplotlib axes (creates new if None)
            show_grid: Whether to show grid lines
            alpha: Transparency

        Returns:
            Matplotlib axes
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        # Create colored grid
        grid_data = grid_map.grid.T  # Transpose for correct orientation

        # Plot obstacles
        obstacle_mask = grid_data == CellType.OBSTACLE.value
        ax.imshow(obstacle_mask.T, origin='lower', cmap='binary',
                  extent=[0, grid_map.width, 0, grid_map.height],
                  alpha=alpha, aspect='equal')

        # Add grid lines
        if show_grid:
            ax.grid(True, linewidth=0.5, alpha=0.3)
            ax.set_xticks(np.arange(0, grid_map.width + 1, 1), minor=True)
            ax.set_yticks(np.arange(0, grid_map.height + 1, 1), minor=True)

        ax.set_xlim(0, grid_map.width)
        ax.set_ylim(0, grid_map.height)

        return ax

    def plot_path(self, path: List[Tuple[int, int]], ax: plt.Axes = None,
                  color: str = 'blue', linewidth: float = 2.0,
                  label: str = 'Path', show_points: bool = True) -> plt.Axes:
        """
        Plot planned path.

        Args:
            path: List of (x, y) positions
            ax: Matplotlib axes
            color: Path color
            linewidth: Line width
            label: Legend label
            show_points: Whether to show path points

        Returns:
            Matplotlib axes
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        if not path:
            return ax

        # Convert to numpy array
        path_array = np.array(path)
        x = path_array[:, 0]
        y = path_array[:, 1]

        # Plot path line
        ax.plot(x, y, color=color, linewidth=linewidth, label=label, zorder=3)

        # Plot path points
        if show_points:
            ax.scatter(x[1:-1], y[1:-1], color=color, s=20, zorder=4)

        return ax

    def plot_trajectory(self, trajectory: Trajectory, ax: plt.Axes = None,
                        color: str = 'green', show_velocity: bool = True,
                        show_heading: bool = False) -> plt.Axes:
        """
        Plot trajectory with optional velocity coloring.

        Args:
            trajectory: Trajectory to plot
            ax: Matplotlib axes
            color: Base color
            show_velocity: Whether to color by velocity
            show_heading: Whether to show heading arrows

        Returns:
            Matplotlib axes
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        positions = trajectory.get_positions()

        if show_velocity and len(trajectory.points) > 0:
            # Color by velocity
            velocities = trajectory.get_velocities()
            points = positions.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)

            norm = plt.Normalize(velocities.min(), velocities.max())
            lc = LineCollection(segments, cmap='viridis', norm=norm, linewidth=2)
            lc.set_array(velocities[:-1])
            ax.add_collection(lc)

            # Add colorbar
            cbar = plt.colorbar(lc, ax=ax)
            cbar.set_label('Velocity (m/s)')
        else:
            ax.plot(positions[:, 0], positions[:, 1], color=color, linewidth=2)

        if show_heading:
            # Plot heading arrows
            for i in range(0, len(trajectory.points), max(1, len(trajectory.points) // 20)):
                p = trajectory.points[i]
                dx = 0.5 * np.cos(p.heading)
                dy = 0.5 * np.sin(p.heading)
                ax.arrow(p.x, p.y, dx, dy,
                         head_width=0.2, head_length=0.1, fc=color, ec=color)

        return ax

    def plot_vehicle(self, x: float, y: float, heading: float,
                     ax: plt.Axes = None, color: str = 'red',
                     length: float = 2.0, width: float = 1.0) -> plt.Axes:
        """
        Plot vehicle rectangle.

        Args:
            x: Vehicle x position
            y: Vehicle y position
            heading: Vehicle heading (radians)
            ax: Matplotlib axes
            color: Vehicle color
            length: Vehicle length
            width: Vehicle width

        Returns:
            Matplotlib axes
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        # Vehicle corners in local frame
        corners = np.array([
            [-length / 2, -width / 2],
            [length / 2, -width / 2],
            [length / 2, width / 2],
            [-length / 2, width / 2],
        ])

        # Rotation matrix
        R = np.array([
            [np.cos(heading), -np.sin(heading)],
            [np.sin(heading), np.cos(heading)]
        ])

        # Transform to global frame
        global_corners = (R @ corners.T).T + np.array([x, y])

        # Plot vehicle
        vehicle_patch = patches.Polygon(global_corners, closed=True,
                                        facecolor=color, edgecolor='black',
                                        alpha=0.7, zorder=5)
        ax.add_patch(vehicle_patch)

        # Plot heading indicator
        dx = length * 0.6 * np.cos(heading)
        dy = length * 0.6 * np.sin(heading)
        ax.arrow(x, y, dx, dy, head_width=0.3, head_length=0.2,
                 fc='yellow', ec='black', zorder=6)

        return ax

    def plot_simulation_result(self, result: Dict, grid_map: GridMap = None,
                               title: str = "Simulation Result") -> plt.Figure:
        """
        Plot complete simulation result.

        Args:
            result: Dictionary containing simulation data
            grid_map: Optional grid map
            title: Plot title

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        fig.suptitle(title, fontsize=14)

        # Plot 1: Path and trajectory
        ax1 = axes[0, 0]
        if grid_map:
            self.plot_grid_map(grid_map, ax=ax1, show_grid=False)

        if 'planned_path' in result:
            self.plot_path(result['planned_path'], ax=ax1, color='blue',
                          label='Planned Path')

        if 'trajectory' in result:
            self.plot_trajectory(result['trajectory'], ax=ax1, show_velocity=True)

        if 'vehicle_positions' in result:
            positions = np.array(result['vehicle_positions'])
            ax1.plot(positions[:, 0], positions[:, 1], 'r-', linewidth=1,
                    label='Actual Path', alpha=0.7)

        ax1.legend()
        ax1.set_title('Path and Trajectory')
        ax1.set_aspect('equal')

        # Plot 2: Velocity profile
        ax2 = axes[0, 1]
        if 'timestamps' in result and 'speeds' in result:
            ax2.plot(result['timestamps'], result['speeds'], 'b-', linewidth=2)
            ax2.set_xlabel('Time (s)')
            ax2.set_ylabel('Speed (m/s)')
            ax2.set_title('Velocity Profile')
            ax2.grid(True)

        # Plot 3: Tracking errors
        ax3 = axes[1, 0]
        if 'timestamps' in result and 'errors' in result:
            ax3.plot(result['timestamps'], result['errors'], 'r-', linewidth=2)
            ax3.set_xlabel('Time (s)')
            ax3.set_ylabel('Tracking Error (m)')
            ax3.set_title('Tracking Error')
            ax3.grid(True)

        # Plot 4: Steering angle
        ax4 = axes[1, 1]
        if 'timestamps' in result and 'steerings' in result:
            ax4.plot(result['timestamps'], np.degrees(result['steerings']),
                    'g-', linewidth=2)
            ax4.set_xlabel('Time (s)')
            ax4.set_ylabel('Steering Angle (deg)')
            ax4.set_title('Steering Command')
            ax4.grid(True)

        plt.tight_layout()
        return fig

    def animate_simulation(self, frames: List[Dict], grid_map: GridMap = None,
                           interval: int = 50, save_path: str = None) -> animation.FuncAnimation:
        """
        Create animation of simulation.

        Args:
            frames: List of frame data dictionaries
            grid_map: Grid map
            interval: Frame interval in milliseconds
            save_path: Path to save animation

        Returns:
            Animation object
        """
        fig, ax = plt.subplots(figsize=self.figsize)

        if grid_map:
            self.plot_grid_map(grid_map, ax=ax, show_grid=False)

        # Initialize plot elements
        path_line, = ax.plot([], [], 'b-', linewidth=2, label='Planned Path')
        vehicle_patch = patches.Polygon([[0, 0]], closed=True,
                                        facecolor='red', edgecolor='black',
                                        alpha=0.7, zorder=5)
        ax.add_patch(vehicle_patch)
        trajectory_line, = ax.plot([], [], 'g-', linewidth=1, alpha=0.5, label='Trajectory')

        ax.legend()
        ax.set_title('ADAS Simulation')

        def init():
            path_line.set_data([], [])
            trajectory_line.set_data([], [])
            return path_line, vehicle_patch, trajectory_line

        def update(frame):
            data = frames[frame]

            # Update path
            if 'planned_path' in data:
                path = np.array(data['planned_path'])
                path_line.set_data(path[:, 0], path[:, 1])

            # Update vehicle
            if 'vehicle_position' in data and 'vehicle_heading' in data:
                x, y = data['vehicle_position']
                heading = data['vehicle_heading']
                length, width = 2.0, 1.0

                corners = np.array([
                    [-length / 2, -width / 2],
                    [length / 2, -width / 2],
                    [length / 2, width / 2],
                    [-length / 2, width / 2],
                ])

                R = np.array([
                    [np.cos(heading), -np.sin(heading)],
                    [np.sin(heading), np.cos(heading)]
                ])

                global_corners = (R @ corners.T).T + np.array([x, y])
                vehicle_patch.set_xy(global_corners)

            # Update trajectory
            if 'trajectory' in data:
                traj = np.array(data['trajectory'])
                trajectory_line.set_data(traj[:, 0], traj[:, 1])

            return path_line, vehicle_patch, trajectory_line

        anim = animation.FuncAnimation(fig, update, frames=len(frames),
                                        init_func=init, blit=True, interval=interval)

        if save_path:
            anim.save(save_path, writer='pillow', fps=1000 // interval)

        return anim

    def plot_comparison(self, results: Dict[str, Dict],
                        title: str = "Algorithm Comparison") -> plt.Figure:
        """
        Plot comparison of different algorithms.

        Args:
            results: Dictionary mapping algorithm names to results
            title: Plot title

        Returns:
            Matplotlib figure
        """
        n_algorithms = len(results)
        fig, axes = plt.subplots(2, n_algorithms, figsize=(6 * n_algorithms, 10))
        fig.suptitle(title, fontsize=14)

        if n_algorithms == 1:
            axes = axes.reshape(-1, 1)

        for idx, (name, data) in enumerate(results.items()):
            # Top row: paths
            ax1 = axes[0, idx]
            if 'planned_path' in data:
                path = np.array(data['planned_path'])
                ax1.plot(path[:, 0], path[:, 1], 'b-', linewidth=2)
            if 'vehicle_positions' in data:
                positions = np.array(data['vehicle_positions'])
                ax1.plot(positions[:, 0], positions[:, 1], 'r-', linewidth=1, alpha=0.7)
            ax1.set_title(f'{name}\nPath')
            ax1.set_aspect('equal')
            ax1.grid(True)

            # Bottom row: errors
            ax2 = axes[1, idx]
            if 'timestamps' in data and 'errors' in data:
                ax2.plot(data['timestamps'], data['errors'], 'r-', linewidth=2)
            ax2.set_title(f'{name}\nTracking Error')
            ax2.set_xlabel('Time (s)')
            ax2.set_ylabel('Error (m)')
            ax2.grid(True)

        plt.tight_layout()
        return fig

    def show(self):
        """Display the plot."""
        plt.show()

    def save(self, filename: str, dpi: int = 150):
        """Save current figure."""
        if self.fig:
            self.fig.savefig(filename, dpi=dpi, bbox_inches='tight')
