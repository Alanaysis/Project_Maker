"""Visualization Module for Cam Mechanism Analysis.

This module provides plotting functions for visualizing cam profiles,
motion diagrams, pressure angles, curvature analysis, and dynamic behavior.

凸轮机构分析可视化模块
提供凸轮轮廓、运动图、压力角、曲率分析和动力学行为的可视化工具
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, FancyArrowPatch
from typing import Optional, Tuple, List
from .cam_profile import CamGeometry, FollowerType, FollowerMotion
from .motion_laws import MotionLaw, MotionLawCalculator
from .pressure_angle import PressureAngleAnalyzer
from .dynamic_analysis import DynamicAnalyzer, SystemParameters
from .contact_stress import ContactStressAnalyzer


class CamVisualizer:
    """Provides visualization tools for cam mechanism analysis.
    
    凸轮机构分析可视化工具
    """

    # Color scheme
    COLORS = {
        'profile': '#2196F3',
        'base_circle': '#9E9E9E',
        'pitch_curve': '#4CAF50',
        'pressure_angle': '#FF5722',
        'curvature': '#9C27B0',
        'motion': '#00BCD4',
        'dwell': '#FFC107',
        'rise': '#4CAF50',
        'return': '#F44336',
        'grid': '#EEEEEE'
    }

    @staticmethod
    def plot_cam_profile(
        geometry: CamGeometry,
        show_base_circle: bool = True,
        show_pressure_angle: bool = False,
        show_curvature: bool = False,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        figure_size: Tuple[int, int] = (10, 8)
    ) -> plt.Figure:
        """Plot the cam profile with optional overlays.
        
        绘制凸轮轮廓及可选叠加层
        
        Args:
            geometry: Cam geometry from profile generation
            show_base_circle: Whether to show the base circle
            show_pressure_angle: Whether to highlight max pressure angle points
            show_curvature: Whether to show curvature radius color mapping
            title: Custom title
            save_path: Path to save the figure
            figure_size: Figure size in inches
            
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(1, 1, figsize=figure_size)
        fig.suptitle(title or 'Cam Profile / 凸轮轮廓', fontsize=14)

        # Plot base circle
        if show_base_circle:
            base_circle = Circle(
                (0, 0), geometry.base_radius,
                fill=False, edgecolor=CamVisualizer.COLORS['base_circle'],
                linewidth=1.5, linestyle='--', label='Base Circle / 基圆'
            )
            ax.add_patch(base_circle)

        # Plot cam profile
        ax.plot(geometry.profile_x, geometry.profile_y,
                color=CamVisualizer.COLORS['profile'],
                linewidth=2.5, label='Cam Profile / 凸轮轮廓')

        # Show curvature analysis if requested
        if show_curvature:
            from .cam_profile import CamProfileGenerator
            generator = CamProfileGenerator(geometry.base_radius, geometry.roller_radius)
            curvature_radius, cx, cy = generator.calculate_curvature(geometry)
            
            # Color map by curvature radius
            norm = plt.Normalize(curvature_radius.min(), curvature_radius.max())
            scatter = ax.scatter(geometry.profile_x, geometry.profile_y,
                                c=curvature_radius, cmap='viridis', s=20, norm=norm,
                                label='Curvature / 曲率')
            plt.colorbar(scatter, ax=ax, label='Radius / 半径 [mm]')

        # Show pressure angle at critical points
        if show_pressure_angle:
            analyzer = PressureAngleAnalyzer()
            angles, pa = analyzer.calculate_pressure_angle_analytical(
                geometry.follower_motion, geometry.base_radius,
                geometry.lift, 90, 90, 1.0, geometry.offset
            )
            
            # Find max pressure angle points
            max_indices = np.where(np.abs(pa) > np.max(np.abs(pa)) * 0.8)[0]
            if len(max_indices) > 0:
                ax.scatter(geometry.profile_x[max_indices[0]],
                          geometry.profile_y[max_indices[0]],
                          color=CamVisualizer.COLORS['pressure_angle'],
                          s=100, marker='*', label=f'Max PA / 最大压力角')

        # Add center point
        ax.plot(0, 0, 'ko', markersize=6, label='Cam Center / 凸轮中心')

        # Add roller circle for roller follower
        if geometry.follower_type == FollowerType.ROLLER and geometry.roller_radius > 0:
            roller = Circle(
                (0, geometry.base_radius + geometry.lift),
                geometry.roller_radius,
                fill=False, edgecolor=CamVisualizer.COLORS['pitch_curve'],
                linewidth=1.5, linestyle=':', label='Roller / 滚子'
            )
            ax.add_patch(roller)

        ax.set_aspect('equal')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X [mm]', fontsize=11)
        ax.set_ylabel('Y [mm]', fontsize=11)

        # Set limits
        max_dim = max(np.max(np.abs(geometry.profile_x)),
                      np.max(np.abs(geometry.profile_y))) * 1.2
        ax.set_xlim(-max_dim, max_dim)
        ax.set_ylim(-max_dim, max_dim)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Figure saved to: {save_path}")

        return fig

    @staticmethod
    def plot_motion_diagram(
        laws: List[Tuple[MotionLaw, str]],
        lift: float = 20.0,
        angle: float = 180.0,
        omega: float = 1.0,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        figure_size: Tuple[int, int] = (14, 10)
    ) -> plt.Figure:
        """Plot motion diagrams comparing different motion laws.
        
        绘制运动规律对比图
        
        Shows displacement, velocity, acceleration, and jerk diagrams.
        
        Args:
            laws: List of (MotionLaw, label) tuples
            lift: Total lift in mm
            angle: Total angle in degrees
            omega: Angular velocity in rad/s
            title: Custom title
            save_path: Path to save the figure
            figure_size: Figure size in inches
            
        Returns:
            matplotlib Figure object
        """
        fig, axes = plt.subplots(4, 1, figsize=figure_size, sharex=True)
        fig.suptitle(title or 'Motion Law Comparison / 运动规律对比', fontsize=14)

        calc = MotionLawCalculator(lift, omega)
        n_points = 360
        angles = np.linspace(0, angle, n_points)

        colors = ['#2196F3', '#4CAF50', '#FF5722', '#9C27B0', '#FFC107',
                  '#00BCD4', '#795548', '#607D8B', '#E91E63']

        for law, label in laws:
            s_vals, v_vals, a_vals, j_vals = [], [], [], []
            for theta in angles:
                result = calc.calculate(law, angle, theta)
                s_vals.append(result.displacement)
                v_vals.append(result.velocity)
                a_vals.append(result.acceleration)
                j_vals.append(result.jerk)

            s_vals = np.array(s_vals)
            v_vals = np.array(v_vals)
            a_vals = np.array(a_vals)
            j_vals = np.array(j_vals)

            color = colors[laws.index((law, label)) % len(colors)]

            axes[0].plot(angles, s_vals, color=color, linewidth=1.5,
                        alpha=0.8, label=label)
            axes[1].plot(angles, v_vals, color=color, linewidth=1.5,
                        alpha=0.8, linestyle='--')
            axes[2].plot(angles, a_vals, color=color, linewidth=1.5,
                        alpha=0.8, linestyle='--')
            axes[3].plot(angles, j_vals, color=color, linewidth=1.5,
                        alpha=0.8, linestyle='--')

        # Configure axes
        axes[0].set_ylabel('Displacement\n位移 [mm]', fontsize=10)
        axes[1].set_ylabel('Velocity\n速度 [mm/s]', fontsize=10)
        axes[2].set_ylabel('Acceleration\n加速度 [mm/s²]', fontsize=10)
        axes[3].set_ylabel('Jerk\n跃度 [mm/s³]', fontsize=10)
        axes[3].set_xlabel('Cam Angle / 凸轮转角 [degrees]', fontsize=10)

        axes[0].legend(loc='upper right', fontsize=8)
        for ax in axes:
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='k', linewidth=0.3)

        # Mark rise/dwell regions
        for ax in axes:
            ax.axvspan(0, angle, alpha=0.05, color='green', label='Rise')
            ax.axvspan(angle, angle + 30, alpha=0.05, color='yellow')
            ax.axvspan(angle + 30, angle + 30 + angle, alpha=0.05, color='red')
            ax.axvspan(angle + 30 + angle, 2*angle + 30, alpha=0.05, color='yellow')

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Figure saved to: {save_path}")

        return fig

    @staticmethod
    def plot_pressure_angle_analysis(
        angles: np.ndarray,
        pressure_angles: np.ndarray,
        max_allowed: float = 30.0,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        figure_size: Tuple[int, int] = (12, 6)
    ) -> plt.Figure:
        """Plot pressure angle analysis.
        
        绘制压力角分析图
        
        Args:
            angles: Cam rotation angles
            pressure_angles: Calculated pressure angles
            max_allowed: Maximum allowable pressure angle
            title: Custom title
            save_path: Path to save the figure
            figure_size: Figure size in inches
            
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(1, 1, figsize=figure_size)
        fig.suptitle(title or 'Pressure Angle Analysis / 压力角分析', fontsize=14)

        ax.plot(angles, pressure_angles, 'b-', linewidth=2, label='Pressure Angle / 压力角')
        ax.axhline(y=max_allowed, color='r', linestyle='--', linewidth=1.5,
                   label=f'Max Allowable / 最大允许 ({max_allowed}°)')
        ax.axhline(y=-max_allowed, color='r', linestyle='--', linewidth=1.5)
        ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)

        # Highlight violations
        violation_mask = np.abs(pressure_angles) > max_allowed
        if np.any(violation_mask):
            ax.scatter(angles[violation_mask], pressure_angles[violation_mask],
                      color='red', s=50, marker='x', label='Violation / 超限', zorder=5)

        ax.fill_between(angles, -max_allowed, max_allowed, alpha=0.1, color='green',
                        label='Acceptable Region / 安全区域')

        ax.set_xlabel('Cam Angle / 凸轮转角 [degrees]', fontsize=11)
        ax.set_ylabel('Pressure Angle / 压力角 [degrees]', fontsize=11)
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Figure saved to: {save_path}")

        return fig

    @staticmethod
    def plot_dynamic_analysis(
        angles: np.ndarray,
        inertia_force: np.ndarray,
        spring_force: np.ndarray,
        total_force: np.ndarray,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        figure_size: Tuple[int, int] = (14, 8)
    ) -> plt.Figure:
        """Plot dynamic force analysis.
        
        绘制动力学分析图
        
        Args:
            angles: Cam rotation angles
            inertia_force: Inertia force at each angle
            spring_force: Spring force at each angle
            total_force: Total contact force at each angle
            title: Custom title
            save_path: Path to save the figure
            figure_size: Figure size in inches
            
        Returns:
            matplotlib Figure object
        """
        fig, axes = plt.subplots(2, 1, figsize=figure_size, sharex=True)
        fig.suptitle(title or 'Dynamic Force Analysis / 动力学分析', fontsize=14)

        # Force plot
        axes[0].plot(angles, inertia_force, 'r-', linewidth=2, label='Inertia Force / 惯性力')
        axes[0].plot(angles, spring_force, 'b-', linewidth=2, label='Spring Force / 弹簧力')
        axes[0].plot(angles, total_force, 'g-', linewidth=2, label='Total Force / 总力')
        axes[0].axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        axes[0].fill_between(angles, 0, total_force, alpha=0.1, color='green')
        axes[0].set_ylabel('Force / 力 [N]', fontsize=11)
        axes[0].legend(loc='upper right', fontsize=9)
        axes[0].grid(True, alpha=0.3)

        # Contact status
        has_loss = np.any(total_force <= 0)
        if has_loss:
            loss_mask = total_force <= 0
            axes[1].fill_between(angles[loss_mask], 0, 1, alpha=0.3, color='red',
                                label='Contact Loss / 脱离接触')

        axes[1].axhline(y=0.5, color='k', linewidth=0.5, alpha=0.3)
        axes[1].set_ylabel('Contact Status / 接触状态', fontsize=11)
        axes[1].set_xlabel('Cam Angle / 凸轮转角 [degrees]', fontsize=11)
        axes[1].set_ylim(-0.1, 1.1)
        axes[1].grid(True, alpha=0.3)

        if has_loss:
            axes[1].legend(loc='upper right', fontsize=9)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Figure saved to: {save_path}")

        return fig

    @staticmethod
    def plot_curvature_analysis(
        geometry: CamGeometry,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """Plot curvature radius analysis.
        
        绘制曲率半径分析图
        
        Args:
            geometry: Cam geometry
            save_path: Path to save the figure
            
        Returns:
            matplotlib Figure object
        """
        from .cam_profile import CamProfileGenerator
        generator = CamProfileGenerator(geometry.base_radius, geometry.roller_radius)
        curvature_radius, cx, cy = generator.calculate_curvature(geometry)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Curvature Analysis / 曲率分析', fontsize=14)

        # Profile with curvature color mapping
        norm = plt.Normalize(curvature_radius.min(), curvature_radius.max())
        scatter = ax1.scatter(geometry.profile_x, geometry.profile_y,
                             c=curvature_radius, cmap='viridis', s=30, norm=norm)
        ax1.plot(geometry.profile_x, geometry.profile_y, 'k-', linewidth=1)
        plt.colorbar(scatter, ax=ax1, label='Curvature Radius / 曲率半径 [mm]')
        ax1.set_aspect('equal')
        ax1.set_xlabel('X [mm]')
        ax1.set_ylabel('Y [mm]')
        ax1.set_title('Cam Profile with Curvature / 带曲率的凸轮轮廓')
        ax1.grid(True, alpha=0.3)

        # Curvature radius vs angle
        angles = np.linspace(0, geometry.total_angle, len(curvature_radius))
        ax2.plot(angles, curvature_radius, 'b-', linewidth=2, label='Curvature Radius / 曲率半径')
        if geometry.roller_radius > 0:
            ax2.axhline(y=geometry.roller_radius, color='r', linestyle='--',
                       linewidth=1.5, label=f'Roller Radius / 滚子半径 ({geometry.roller_radius}mm)')
        ax2.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax2.set_xlabel('Cam Angle / 凸轮转角 [degrees]')
        ax2.set_ylabel('Curvature Radius / 曲率半径 [mm]')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)

        # Check undercutting
        min_curv = np.min(curvature_radius)
        if min_curv < geometry.roller_radius:
            ax2.text(0.02, 0.95, f'UNDERCUT RISK!\n最小曲率: {min_curv:.2f}mm < {geometry.roller_radius}mm',
                    transform=ax2.transAxes, fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7),
                    color='red')

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Figure saved to: {save_path}")

        return fig

    @staticmethod
    def create_comprehensive_report(
        geometry: CamGeometry,
        angles: np.ndarray,
        pressure_angles: np.ndarray,
        dynamic_result,
        save_dir: str = '.'
    ) -> str:
        """Create a comprehensive visualization report.
        
        创建综合可视化报告
        
        Args:
            geometry: Cam geometry
            angles: Cam angles
            pressure_angles: Pressure angles
            dynamic_result: Dynamic analysis result
            save_dir: Directory to save figures
            
        Returns:
            Path to the report file
        """
        import os
        
        # Generate all figures
        CamVisualizer.plot_cam_profile(
            geometry,
            save_path=os.path.join(save_dir, 'cam_profile.png'),
            title='Cam Profile / 凸轮轮廓'
        )
        
        CamVisualizer.plot_pressure_angle_analysis(
            angles, pressure_angles,
            save_path=os.path.join(save_dir, 'pressure_angle.png'),
            title='Pressure Angle / 压力角'
        )
        
        CamVisualizer.plot_dynamic_analysis(
            angles,
            dynamic_result.inertia_force,
            dynamic_result.spring_force,
            dynamic_result.total_force,
            save_path=os.path.join(save_dir, 'dynamic_analysis.png'),
            title='Dynamic Analysis / 动力学分析'
        )

        # Write summary report
        report_path = os.path.join(save_dir, 'analysis_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Cam Mechanism Analysis Report / 凸轮机构分析报告\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("1. Cam Geometry / 凸轮几何参数:\n")
            f.write(f"   Base Radius / 基圆半径: {geometry.base_radius} mm\n")
            f.write(f"   Lift / 升程: {geometry.lift} mm\n")
            f.write(f"   Total Angle / 总转角: {geometry.total_angle} degrees\n")
            f.write(f"   Follower Type / 从动件类型: {geometry.follower_type.value}\n")
            f.write(f"   Follower Motion / 运动方式: {geometry.follower_motion.value}\n")
            if geometry.roller_radius > 0:
                f.write(f"   Roller Radius / 滚子半径: {geometry.roller_radius} mm\n")
            if geometry.offset != 0:
                f.write(f"   Offset / 偏置距: {geometry.offset} mm\n")
            f.write("\n")
            
            f.write("2. Pressure Angle Analysis / 压力角分析:\n")
            f.write(f"   Max Pressure Angle / 最大压力角: {np.max(np.abs(pressure_angles)):.2f} degrees\n")
            f.write(f"   Mean Pressure Angle / 平均压力角: {np.mean(np.abs(pressure_angles)):.2f} degrees\n")
            f.write(f"   Acceptable (<=30 deg): {np.max(np.abs(pressure_angles)) <= 30}\n")
            f.write("\n")
            
            f.write("3. Dynamic Analysis / 动力学分析:\n")
            f.write(f"   Max Inertia Force / 最大惯性力: {np.max(np.abs(dynamic_result.inertia_force)):.2f} N\n")
            f.write(f"   Natural Frequency / 固有频率: {dynamic_result.natural_frequency:.2f} Hz\n")
            f.write(f"   Max Dynamic Factor / 最大动态放大系数: {dynamic_result.max_dynamic_factor:.2f}\n")
            f.write("\n")
            
            f.write("4. Curvature Analysis / 曲率分析:\n")
            from .cam_profile import CamProfileGenerator
            generator = CamProfileGenerator(geometry.base_radius, geometry.roller_radius)
            curvature_radius, _, _ = generator.calculate_curvature(geometry)
            f.write(f"   Min Curvature Radius / 最小曲率半径: {np.min(curvature_radius):.2f} mm\n")
            f.write(f"   Roller Radius / 滚子半径: {geometry.roller_radius} mm\n")
            f.write(f"   Undercutting Risk / 失真风险: {np.min(curvature_radius) < geometry.roller_radius}\n")
            f.write("\n")
            
            f.write("=" * 60 + "\n")
            f.write("End of Report / 报告结束\n")
            f.write("=" * 60 + "\n")

        print(f"Report saved to: {report_path}")
        return report_path
