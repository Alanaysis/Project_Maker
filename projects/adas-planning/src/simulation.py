"""
Simulation Module
=================

This module provides the main simulation engine that ties together
planning, control, and visualization.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field

from .environment import GridMap, SimulationEnvironment
from .planner import AStarPlanner, DijkstraPlanner, PathPlanner
from .controller import PIDController, StanleyController, MPCController
from .vehicle import BicycleModel, VehicleParameters
from .trajectory import Trajectory, TrajectoryGenerator
from .visualization import Visualizer


@dataclass
class SimulationConfig:
    """Configuration for simulation."""
    map_width: int = 50
    map_height: int = 50
    obstacle_density: float = 0.3
    start: Tuple[int, int] = (2, 2)
    goal: Tuple[int, int] = (47, 47)
    dt: float = 0.1
    max_time: float = 100.0
    target_velocity: float = 5.0
    planner_type: str = "astar"  # "astar", "dijkstra", "rrt"
    controller_type: str = "pid"  # "pid", "stanley", "mpc"
    seed: Optional[int] = None


class SimulationResult:
    """Stores simulation results."""

    def __init__(self):
        self.timestamps: List[float] = []
        self.vehicle_positions: List[np.ndarray] = []
        self.vehicle_headings: List[float] = []
        self.vehicle_speeds: List[float] = []
        self.steering_commands: List[float] = []
        self.acceleration_commands: List[float] = []
        self.tracking_errors: List[float] = []
        self.planned_path: Optional[List[Tuple[int, int]]] = None
        self.trajectory: Optional[Trajectory] = None
        self.success: bool = False
        self.total_time: float = 0.0
        self.path_length: float = 0.0
        self.average_error: float = 0.0
        self.max_error: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for visualization."""
        return {
            'timestamps': self.timestamps,
            'vehicle_positions': self.vehicle_positions,
            'vehicle_headings': self.vehicle_headings,
            'speeds': self.vehicle_speeds,
            'steerings': self.steering_commands,
            'accelerations': self.acceleration_commands,
            'errors': self.tracking_errors,
            'planned_path': self.planned_path,
            'trajectory': self.trajectory,
        }

    def compute_statistics(self) -> None:
        """Compute summary statistics."""
        if self.tracking_errors:
            self.average_error = np.mean(self.tracking_errors)
            self.max_error = np.max(self.tracking_errors)
        if self.timestamps:
            self.total_time = self.timestamps[-1]
        if len(self.vehicle_positions) > 1:
            positions = np.array(self.vehicle_positions)
            diffs = np.diff(positions, axis=0)
            self.path_length = np.sum(np.linalg.norm(diffs, axis=1))


class Simulation:
    """
    Main simulation engine.

    Orchestrates planning, control, and visualization.
    """

    def __init__(self, config: SimulationConfig = None):
        """
        Initialize simulation.

        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        self.grid_map: Optional[GridMap] = None
        self.environment: Optional[SimulationEnvironment] = None
        self.planner: Optional[PathPlanner] = None
        self.controller = None
        self.vehicle_model = None
        self.trajectory_generator = None
        self.visualizer = None

    def setup(self) -> None:
        """Setup simulation components."""
        # Create grid map
        self.grid_map = GridMap.random(
            self.config.map_width,
            self.config.map_height,
            self.config.obstacle_density,
            self.config.seed
        )

        # Ensure start and goal are free
        self.grid_map.remove_obstacle(*self.config.start)
        self.grid_map.remove_obstacle(*self.config.goal)

        # Clear area around start and goal
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                sx, sy = self.config.start[0] + dx, self.config.start[1] + dy
                gx, gy = self.config.goal[0] + dx, self.config.goal[1] + dy
                if self.grid_map.in_bounds(sx, sy):
                    self.grid_map.remove_obstacle(sx, sy)
                if self.grid_map.in_bounds(gx, gy):
                    self.grid_map.remove_obstacle(gx, gy)

        # Create environment
        self.environment = SimulationEnvironment(
            grid_map=self.grid_map,
            start=self.config.start,
            goal=self.config.goal,
            dt=self.config.dt
        )

        # Create planner
        if self.config.planner_type == "astar":
            self.planner = AStarPlanner(allow_diagonal=True)
        elif self.config.planner_type == "dijkstra":
            self.planner = DijkstraPlanner(allow_diagonal=True)
        else:
            self.planner = AStarPlanner(allow_diagonal=True)

        # Create controller
        if self.config.controller_type == "pid":
            self.controller = PIDController(
                Kp=1.0, Ki=0.01, Kd=0.5,
                output_limits=(-np.pi / 4, np.pi / 4)
            )
        elif self.config.controller_type == "stanley":
            self.controller = StanleyController(k=1.0)
        else:
            self.controller = PIDController(
                Kp=1.0, Ki=0.01, Kd=0.5,
                output_limits=(-np.pi / 4, np.pi / 4)
            )

        # Create vehicle model
        self.vehicle_model = BicycleModel(VehicleParameters())

        # Create trajectory generator
        self.trajectory_generator = TrajectoryGenerator(ds=0.5)

        # Create visualizer
        self.visualizer = Visualizer()

    def run(self) -> SimulationResult:
        """
        Run the simulation.

        Returns:
            Simulation results
        """
        result = SimulationResult()

        # Plan path
        path = self.planner.plan(
            self.grid_map,
            self.config.start,
            self.config.goal
        )

        if path is None:
            print("No path found!")
            result.success = False
            return result

        result.planned_path = path

        # Generate smooth trajectory
        waypoints = [(float(p[0]), float(p[1])) for p in path]
        trajectory = self.trajectory_generator.generate(
            waypoints,
            target_velocity=self.config.target_velocity
        )
        result.trajectory = trajectory

        # Initialize simulation
        self.environment.reset()
        current_time = 0.0

        # Main simulation loop
        while current_time < self.config.max_time:
            # Get current state
            pos = self.environment.vehicle_position
            heading = self.environment.vehicle_heading
            speed = self.environment.vehicle_speed

            # Compute control
            if isinstance(self.controller, PIDController):
                # Find nearest point on trajectory
                nearest_idx = trajectory.get_nearest_index(pos[0], pos[1])

                # Get cross-track error
                nearest_point = trajectory.get_point(nearest_idx)
                dx = nearest_point.x - pos[0]
                dy = nearest_point.y - pos[1]

                # Compute cross-track error (perpendicular distance)
                path_heading = nearest_point.heading
                cross_track_error = -dx * np.sin(path_heading) + dy * np.cos(path_heading)

                # Compute heading error
                heading_error = path_heading - heading
                heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))

                # Combined error
                error = cross_track_error + 0.5 * heading_error

                # PID control for steering
                steering = self.controller.compute(error, self.config.dt)

                # Simple speed control
                target_speed = trajectory.get_point(
                    min(nearest_idx + 5, len(trajectory) - 1)
                ).velocity
                speed_error = target_speed - speed
                acceleration = 0.5 * speed_error

            elif isinstance(self.controller, StanleyController):
                # Get path points as numpy arrays
                path_points = trajectory.get_positions()

                # Compute steering
                steering = self.controller.compute_steering_angle(
                    pos, heading, path_points, speed
                )

                # Simple speed control
                nearest_idx = trajectory.get_nearest_index(pos[0], pos[1])
                target_speed = trajectory.get_point(
                    min(nearest_idx + 5, len(trajectory) - 1)
                ).velocity
                speed_error = target_speed - speed
                acceleration = 0.5 * speed_error

            else:
                steering = 0.0
                acceleration = 0.0

            # Apply limits
            steering = np.clip(steering, -np.pi / 4, np.pi / 4)
            acceleration = np.clip(acceleration, -3.0, 2.0)

            # Execute step
            self.environment.step(steering, acceleration)

            # Compute tracking error
            nearest_idx = trajectory.get_nearest_index(pos[0], pos[1])
            nearest_point = trajectory.get_point(nearest_idx)
            error = np.sqrt((pos[0] - nearest_point.x) ** 2 +
                            (pos[1] - nearest_point.y) ** 2)

            # Record results
            result.timestamps.append(current_time)
            result.vehicle_positions.append(pos.copy())
            result.vehicle_headings.append(heading)
            result.vehicle_speeds.append(speed)
            result.steering_commands.append(steering)
            result.acceleration_commands.append(acceleration)
            result.tracking_errors.append(error)

            # Check termination
            if self.environment.is_goal_reached(threshold=2.0):
                result.success = True
                break

            if self.environment.is_collision():
                print("Collision detected!")
                result.success = False
                break

            current_time += self.config.dt

        result.compute_statistics()
        return result

    def visualize(self, result: SimulationResult, show: bool = True) -> plt.Figure:
        """
        Visualize simulation results.

        Args:
            result: Simulation results
            show: Whether to show the plot

        Returns:
            Matplotlib figure
        """
        import matplotlib.pyplot as plt

        fig = self.visualizer.plot_simulation_result(
            result.to_dict(),
            grid_map=self.grid_map,
            title=f"ADAS Simulation - {self.config.planner_type.upper()} + {self.config.controller_type.upper()}"
        )

        if show:
            plt.show()

        return fig

    def run_comparison(self, planner_types: List[str] = None,
                       controller_types: List[str] = None) -> Dict[str, SimulationResult]:
        """
        Run comparison of different planning/control combinations.

        Args:
            planner_types: List of planner types to compare
            controller_types: List of controller types to compare

        Returns:
            Dictionary mapping algorithm names to results
        """
        if planner_types is None:
            planner_types = ["astar", "dijkstra"]
        if controller_types is None:
            controller_types = ["pid", "stanley"]

        results = {}

        for planner_type in planner_types:
            for controller_type in controller_types:
                name = f"{planner_type}+{controller_type}"
                print(f"Running {name}...")

                config = SimulationConfig(
                    map_width=self.config.map_width,
                    map_height=self.config.map_height,
                    obstacle_density=self.config.obstacle_density,
                    start=self.config.start,
                    goal=self.config.goal,
                    dt=self.config.dt,
                    max_time=self.config.max_time,
                    target_velocity=self.config.target_velocity,
                    planner_type=planner_type,
                    controller_type=controller_type,
                    seed=self.config.seed
                )

                sim = Simulation(config)
                sim.setup()
                result = sim.run()
                results[name] = result

                print(f"  Success: {result.success}")
                print(f"  Time: {result.total_time:.2f}s")
                print(f"  Avg Error: {result.average_error:.3f}m")

        return results
