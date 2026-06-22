"""
Visualization module for SLAM system.
Handles 3D visualization of map and trajectory.
"""

import numpy as np
from typing import List, Optional, Tuple
import os

try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class Visualizer:
    """3D visualization for SLAM map and trajectory."""

    def __init__(self, use_open3d: bool = True):
        """
        Initialize visualizer.

        Args:
            use_open3d: Whether to use Open3D (falls back to matplotlib)
        """
        self.use_open3d = use_open3d and HAS_OPEN3D
        self.vis = None
        self.point_cloud = None
        self.trajectory_lines = None

    def create_point_cloud(
        self,
        points: np.ndarray,
        colors: Optional[np.ndarray] = None
    ) -> 'o3d.geometry.PointCloud':
        """
        Create Open3D point cloud.

        Args:
            points: 3D points (N, 3)
            colors: Optional RGB colors (N, 3), range [0, 1]

        Returns:
            Open3D point cloud
        """
        if not self.use_open3d:
            raise RuntimeError("Open3D not available")

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        if colors is not None:
            pcd.colors = o3d.utility.Vector3dVector(colors)

        return pcd

    def create_trajectory_line(
        self,
        positions: np.ndarray,
        color: Tuple[float, float, float] = (1, 0, 0)
    ) -> 'o3d.geometry.LineSet':
        """
        Create trajectory line set.

        Args:
            positions: Camera positions (N, 3)
            color: Line color (R, G, B)

        Returns:
            Open3D line set
        """
        if not self.use_open3d:
            raise RuntimeError("Open3D not available")

        if len(positions) < 2:
            return None

        # Create line set
        lines = [[i, i + 1] for i in range(len(positions) - 1)]
        colors = [color for _ in lines]

        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(positions)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        line_set.colors = o3d.utility.Vector3dVector(colors)

        return line_set

    def create_camera_frustum(
        self,
        pose: np.ndarray,
        scale: float = 0.1,
        color: Tuple[float, float, float] = (0, 1, 0)
    ) -> 'o3d.geometry.LineSet':
        """
        Create camera frustum visualization.

        Args:
            pose: 4x4 transformation matrix
            scale: Frustum scale
            color: Frustum color

        Returns:
            Open3D line set
        """
        if not self.use_open3d:
            raise RuntimeError("Open3D not available")

        # Camera frustum points (in camera frame)
        frustum_points = np.array([
            [0, 0, 0],  # Camera center
            [-scale, -scale * 0.75, scale * 1.5],  # Top-left
            [scale, -scale * 0.75, scale * 1.5],   # Top-right
            [scale, scale * 0.75, scale * 1.5],    # Bottom-right
            [-scale, scale * 0.75, scale * 1.5],   # Bottom-left
        ])

        # Transform to world frame
        R = pose[:3, :3]
        t = pose[:3, 3]
        frustum_points = (R @ frustum_points.T).T + t

        # Create lines
        lines = [
            [0, 1], [0, 2], [0, 3], [0, 4],  # Center to corners
            [1, 2], [2, 3], [3, 4], [4, 1]   # Rectangle
        ]
        colors = [color for _ in lines]

        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(frustum_points)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        line_set.colors = o3d.utility.Vector3dVector(colors)

        return line_set

    def visualize_map(
        self,
        points: np.ndarray,
        colors: Optional[np.ndarray] = None,
        trajectory: Optional[np.ndarray] = None,
        camera_poses: Optional[List[np.ndarray]] = None,
        show_cameras: bool = True,
        save_path: Optional[str] = None
    ):
        """
        Visualize the SLAM map.

        Args:
            points: Map points (N, 3)
            colors: Point colors (N, 3)
            trajectory: Camera trajectory (N, 3)
            camera_poses: List of 4x4 camera poses
            show_cameras: Whether to show camera frustums
            save_path: Path to save visualization
        """
        if self.use_open3d:
            self._visualize_open3d(
                points, colors, trajectory, camera_poses, show_cameras, save_path
            )
        else:
            self._visualize_matplotlib(
                points, colors, trajectory, camera_poses
            )

    def _visualize_open3d(
        self,
        points: np.ndarray,
        colors: Optional[np.ndarray],
        trajectory: Optional[np.ndarray],
        camera_poses: Optional[List[np.ndarray]],
        show_cameras: bool,
        save_path: Optional[str]
    ):
        """Visualize using Open3D."""
        geometries = []

        # Add point cloud
        if len(points) > 0:
            pcd = self.create_point_cloud(points, colors)
            geometries.append(pcd)

        # Add trajectory
        if trajectory is not None and len(trajectory) > 1:
            traj_line = self.create_trajectory_line(trajectory)
            if traj_line:
                geometries.append(traj_line)

        # Add camera frustums
        if show_cameras and camera_poses:
            for i, pose in enumerate(camera_poses):
                frustum = self.create_camera_frustum(pose, scale=0.05)
                if frustum:
                    geometries.append(frustum)

        # Visualize
        if geometries:
            if save_path:
                # Save to file
                o3d.visualization.draw_geometries(
                    geometries,
                    window_name="SLAM Map",
                    width=1280,
                    height=720
                )
            else:
                o3d.visualization.draw_geometries(
                    geometries,
                    window_name="SLAM Map",
                    width=1280,
                    height=720
                )

    def _visualize_matplotlib(
        self,
        points: np.ndarray,
        colors: Optional[np.ndarray],
        trajectory: Optional[np.ndarray],
        camera_poses: Optional[List[np.ndarray]]
    ):
        """Visualize using matplotlib."""
        if not HAS_MATPLOTLIB:
            print("Warning: Neither Open3D nor matplotlib available for visualization")
            return

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Plot points
        if len(points) > 0:
            if colors is not None:
                ax.scatter(
                    points[:, 0], points[:, 1], points[:, 2],
                    c=colors, s=1, alpha=0.5
                )
            else:
                ax.scatter(
                    points[:, 0], points[:, 1], points[:, 2],
                    c='b', s=1, alpha=0.5
                )

        # Plot trajectory
        if trajectory is not None and len(trajectory) > 1:
            ax.plot(
                trajectory[:, 0], trajectory[:, 1], trajectory[:, 2],
                'r-', linewidth=2, label='Trajectory'
            )

        # Plot camera positions
        if camera_poses:
            positions = np.array([pose[:3, 3] for pose in camera_poses])
            ax.scatter(
                positions[:, 0], positions[:, 1], positions[:, 2],
                c='g', s=50, marker='^', label='Cameras'
            )

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('SLAM Map')
        ax.legend()

        plt.show()

    def save_point_cloud(
        self,
        points: np.ndarray,
        colors: Optional[np.ndarray],
        filepath: str
    ):
        """
        Save point cloud to file.

        Args:
            points: 3D points (N, 3)
            colors: Point colors (N, 3)
            filepath: Output file path (ply, pcd, or xyz)
        """
        if not self.use_open3d:
            print("Warning: Open3D required to save point clouds")
            return

        pcd = self.create_point_cloud(points, colors)

        # Create directory if needed
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Save
        o3d.io.write_point_cloud(filepath, pcd)
        print(f"Saved point cloud to {filepath}")

    def create_animated_visualization(
        self,
        frames_data: List[Tuple[np.ndarray, np.ndarray, np.ndarray]],
        output_path: str
    ):
        """
        Create animated visualization of SLAM process.

        Args:
            frames_data: List of (points, colors, camera_position)
            output_path: Output video path
        """
        if not HAS_MATPLOTLIB:
            print("Warning: matplotlib required for animated visualization")
            return

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Set axis limits
        all_points = np.vstack([fd[0] for fd in frames_data if len(fd[0]) > 0])
        if len(all_points) > 0:
            ax.set_xlim([all_points[:, 0].min(), all_points[:, 0].max()])
            ax.set_ylim([all_points[:, 1].min(), all_points[:, 1].max()])
            ax.set_zlim([all_points[:, 2].min(), all_points[:, 2].max()])

        def update(frame_idx):
            ax.clear()
            points, colors, cam_pos = frames_data[frame_idx]

            if len(points) > 0:
                ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                          c='b', s=1, alpha=0.5)

            ax.scatter(*cam_pos, c='r', s=100, marker='^')
            ax.set_title(f'Frame {frame_idx}')

        # Create animation
        from matplotlib.animation import FuncAnimation
        anim = FuncAnimation(fig, update, frames=len(frames_data), interval=100)

        # Save
        anim.save(output_path, writer='ffmpeg', fps=10)
        print(f"Saved animation to {output_path}")
