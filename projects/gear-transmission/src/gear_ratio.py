"""
Module: Gear Ratio Computation
模块: 齿轮比计算

The gear ratio (传动比) is the ratio of the angular velocities of
the input and output shafts. It determines the torque and speed
transmission characteristics.

齿轮比是输入轴和输出轴角速度之比，决定了扭矩和速度的传递特性。

Key formulas:
    - Gear ratio: i = z_driven / z_driver = n_driver / n_driven
      齿轮比 = 从动轮齿数 / 主动轮齿数 = 主动轮转速 / 从动轮转速
    - For reduction: i > 1 (speed decreases, torque increases)
      减速传动: i > 1 (转速降低，扭矩增大)
    - For increase: i < 1 (speed increases, torque decreases)
      增速传动: i < 1 (转速升高，扭矩降低)
"""

from dataclasses import dataclass
from typing import List


@dataclass
class GearPair:
    """
    Represents a pair of meshing gears.

    表示一对啮合齿轮。
    """
    driver: str  # Gear name that provides input (主动轮名称)
    driven: str  # Gear name that receives output (从动轮名称)
    driver_teeth: int  # Number of teeth on driver gear (主动轮齿数)
    driven_teeth: int  # Number of teeth on driven gear (从动轮齿数)
    driver_module: float = 0.0  # Module of driver gear (主动轮模数)
    driven_module: float = 0.0  # Module of driven gear (从动轮模数)

    def __post_init__(self):
        if self.driver_teeth <= 0 or self.driven_teeth <= 0:
            raise ValueError("Number of teeth must be positive")

    @property
    def gear_ratio(self) -> float:
        """
        Gear ratio for this pair.

        i = z_driven / z_driver

        For a single pair:
            - i > 1: reduction (减速)
            - i < 1: increase (增速)
            - i = 1: idler (惰轮)
        """
        return self.driven_teeth / self.driver_teeth

    @property
    def speed_ratio(self) -> float:
        """
        Speed ratio: output speed / input speed.

        n_out / n_in = z_in / z_out = 1 / i
        """
        return self.driver_teeth / self.driven_teeth

    @property
    def torque_ratio(self) -> float:
        """
        Torque ratio: output torque / input torque (ideal, no losses).

        T_out / T_in = i (for reduction, output torque is larger)
        """
        return self.gear_ratio

    @property
    def center_distance(self) -> float:
        """
        Center-to-center distance between the two gears.

        Two meshing gears must have the same module.

        两个啮合齿轮的模数必须相同。

        Formula: a = m * (z1 + z2) / 2
        """
        if self.driver_module != self.driven_module and self.driver_module > 0 and self.driven_module > 0:
            raise ValueError("Meshing gears must have the same module")

        m = self.driver_module if self.driver_module > 0 else self.driven_module
        if m <= 0:
            return 0.0
        return m * (self.driver_teeth + self.driven_teeth) / 2

    def summary(self) -> dict:
        """Get a summary of this gear pair."""
        ratio_type = "减速" if self.gear_ratio > 1 else "增速" if self.gear_ratio < 1 else "等速"
        return {
            "driver": self.driver,
            "driver_teeth": self.driver_teeth,
            "driven": self.driven,
            "driven_teeth": self.driven_teeth,
            "gear_ratio": round(self.gear_ratio, 4),
            "speed_ratio": round(self.speed_ratio, 4),
            "torque_ratio": round(self.torque_ratio, 4),
            "center_distance": round(self.center_distance, 4),
            "type": ratio_type,
        }


class GearRatioCalculator:
    """
    Calculator for gear ratios in various gear train configurations.

    用于各种齿轮系配置的齿轮比计算器。

    Key principles:
        1. For a gear train, the total ratio is the product of individual ratios.
           对于齿轮系，总传动比是各级传动比的乘积。

        2. Idler gears (惰轮) do not affect the overall ratio, only the direction.
           惰轮不影响总传动比，只影响转向。

        3. All meshing gears in a simple train must have the same module.
           简单齿轮系中所有啮合齿轮必须具有相同的模数。
    """

    @staticmethod
    def calculate_single_pair(driver_teeth: int, driven_teeth: int) -> float:
        """
        Calculate gear ratio for a single gear pair.

        计算单级齿轮副的传动比。

        i = z_driven / z_driver
        """
        if driver_teeth <= 0 or driven_teeth <= 0:
            raise ValueError("Number of teeth must be positive")
        return driven_teeth / driver_teeth

    @staticmethod
    def calculate_simple_train( gears: List[tuple]) -> float:
        """
        Calculate gear ratio for a simple gear train.

        计算简单齿轮系的传动比。

        In a simple train, all gears share a common axis arrangement:
        在简单齿轮系中，所有齿轮沿轴线排列：

            Driver -> Idler1 -> Idler2 -> ... -> Driven

        Total ratio = product of all individual stage ratios
        总传动比 = 所有各级传动比的乘积

        For a simple train:
            i_total = (z2/z1) * (z4/z3) * ... = (driven_teeth / driver_teeth) * (product of idler ratios)

        Note: Idlers cancel out in simple train:
        注意：在简单齿轮系中，惰轮的传动比会相互抵消：
            i_total = (-1)^n * (z_driven / z_driver)
        where n is the number of gear meshes.
        其中 n 是啮合次数。
        """
        if len(gears) < 2:
            raise ValueError("At least 2 gears needed")

        total_ratio = 1.0
        for i in range(len(gears) - 1):
            z_driver = gears[i][0]  # teeth of driver gear
            z_driven = gears[i + 1][0]  # teeth of driven gear
            if z_driver <= 0 or z_driven <= 0:
                raise ValueError("Number of teeth must be positive")
            total_ratio *= z_driven / z_driver

        return total_ratio

    @staticmethod
    def calculate_compound_train(stages: List[tuple]) -> float:
        """
        Calculate gear ratio for a compound gear train.

        计算复合齿轮系的传动比。

        In a compound train, multiple gears share shafts:
        在复合齿轮系中，多个齿轮共享轴：

            Stage 1: z1 (driver) -> z2 (driven, on same shaft as z3)
            Stage 2: z3 (driver) -> z4 (driven, on same shaft as z5)
            Stage 3: z5 (driver) -> z6 (driven)

        Total ratio = (z2/z1) * (z4/z3) * (z6/z5) * ...
        """
        total_ratio = 1.0
        for stage in stages:
            if len(stage) != 2:
                raise ValueError("Each stage must have (driver_teeth, driven_teeth)")
            z_driver, z_driven = stage
            if z_driver <= 0 or z_driven <= 0:
                raise ValueError("Number of teeth must be positive")
            total_ratio *= z_driven / z_driver
        return total_ratio

    @staticmethod
    def calculate_direction_changes(num_meshes: int) -> str:
        """
        Calculate the output direction relative to input.

        计算输出方向相对于输入方向的变化。

        Each mesh reverses direction:
        每次啮合都会反转方向：

            Even number of meshes: same direction (同向)
            Odd number of meshes: opposite direction (反向)
        """
        if num_meshes % 2 == 0:
            return "同向 (same direction)"
        else:
            return "反向 (opposite direction)"

    @staticmethod
    def find_optimal_ratios(target_ratio: float, max_stages: int = 4) -> List[List[tuple]]:
        """
        Find integer tooth count combinations that approximate a target ratio.

        找到逼近目标传动比的整数齿数组合。

        This is useful for practical gear design where we need integer
        tooth counts with standard modules.

        这对于需要整数齿数的实际齿轮设计很有用。
        """
        results = []

        def search(current_stages, current_ratio, remaining):
            if remaining == 0:
                if abs(current_ratio - target_ratio) < 0.01:
                    results.append(list(current_stages))
                return

            # Try tooth counts from 10 to 100
            for z_driver in range(10, 61):
                for z_driven in range(10, 61):
                    if z_driver == z_driven:
                        continue
                    stage_ratio = z_driven / z_driver
                    new_ratio = current_ratio * stage_ratio
                    if new_ratio > target_ratio * 2 or new_ratio < target_ratio / 2:
                        continue
                    current_stages.append((z_driver, z_driven))
                    search(current_stages, new_ratio, remaining - 1)
                    current_stages.pop()

        search([], 1.0, min(max_stages, 3))
        return results[:10]  # Return top 10 results

    @staticmethod
    def analyze_ratio(ratio: float) -> dict:
        """
        Analyze and describe a gear ratio.

        分析和描述一个齿轮比。
        """
        if ratio > 1:
            type_desc = "减速传动 (Reduction)"
            behavior = f"转速降至 {1/ratio:.3f}，扭矩增大 {ratio:.3f} 倍"
        elif ratio < 1:
            type_desc = "增速传动 (Increase)"
            behavior = f"转速增至 {ratio:.3f} 倍，扭矩降至 {1/ratio:.3f}"
        else:
            type_desc = "等速传动 (Direct Drive)"
            behavior = "转速和扭矩不变"

        return {
            "ratio": ratio,
            "type": type_desc,
            "behavior": behavior,
            "speed_multiplier": round(1 / ratio, 4),
            "torque_multiplier": round(ratio, 4),
        }
