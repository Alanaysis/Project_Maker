"""
Tests for spur gear geometry and calculations.
测试直齿轮几何与计算。
"""

import pytest
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.spur_gear import SpurGear
from src.gear_ratio import GearRatioCalculator, GearPair
from src.transmission import TransmissionCalculator
from src.efficiency import EfficiencyAnalyzer
from src.contact_ratio import ContactRatioCalculator
from src.gear_train import SimpleGearTrain, CompoundGearTrain, PlanetaryGearTrain


class TestSpurGear:
    """Test cases for SpurGear class."""

    def test_create_gear(self):
        """Test basic gear creation."""
        gear = SpurGear(module=2.0, num_teeth=20, name="test_gear")
        assert gear.module == 2.0
        assert gear.num_teeth == 20
        assert gear.name == "test_gear"
        assert gear.pressure_angle_deg == 20.0

    def test_pitch_diameter(self):
        """Test pitch diameter calculation: d = m * z."""
        gear = SpurGear(module=2.0, num_teeth=20)
        assert gear.pitch_diameter == 40.0

        gear2 = SpurGear(module=3.0, num_teeth=30)
        assert gear2.pitch_diameter == 90.0

    def test_base_circle_diameter(self):
        """Test base circle diameter: db = d * cos(phi)."""
        gear = SpurGear(module=2.0, num_teeth=20, pressure_angle_deg=20)
        expected = 40.0 * math.cos(math.radians(20))
        assert abs(gear.base_circle_diameter - expected) < 0.0001

    def test_addendum(self):
        """Test addendum calculation: a = ha* * m."""
        gear = SpurGear(module=2.0, num_teeth=20)
        assert gear.addendum == 2.0  # ha* = 1.0, so a = 1.0 * 2.0

    def test_dedendum(self):
        """Test dedendum calculation: b = (ha* + c*) * m."""
        gear = SpurGear(module=2.0, num_teeth=20)
        expected = (1.0 + 1.25) * 2.0  # = 4.5
        assert gear.dedendum == expected

    def test_outside_diameter(self):
        """Test outside diameter: do = d + 2*m."""
        gear = SpurGear(module=2.0, num_teeth=20)
        assert gear.outside_diameter == 44.0  # 40 + 2*2

    def test_root_diameter(self):
        """Test root diameter: df = d - 2*(ha*+c*)*m = d - 4.5*m."""
        gear = SpurGear(module=2.0, num_teeth=20)
        assert gear.root_diameter == 31.0  # 40 - 2*(1.0+1.25)*2 = 40 - 9 = 31

    def test_circular_pitch(self):
        """Test circular pitch: p = pi * m."""
        gear = SpurGear(module=2.0, num_teeth=20)
        assert abs(gear.circular_pitch - math.pi * 2.0) < 0.0001

    def test_tooth_thickness(self):
        """Test tooth thickness: s = pi * m / 2."""
        gear = SpurGear(module=2.0, num_teeth=20)
        assert abs(gear.tooth_thickness - math.pi * 2.0 / 2) < 0.0001

    def test_undercut_warning(self):
        """Test undercutting detection."""
        # 20 teeth with 20 deg pressure angle - should be OK
        gear_ok = SpurGear(module=2.0, num_teeth=20, pressure_angle_deg=20)
        assert not gear_ok.undercut_warning

        # 15 teeth with 20 deg pressure angle - should warn
        gear_warn = SpurGear(module=2.0, num_teeth=15, pressure_angle_deg=20)
        assert gear_warn.undercut_warning

    def test_pressure_angle_conversion(self):
        """Test pressure angle to radians conversion."""
        gear = SpurGear(module=2.0, num_teeth=20, pressure_angle_deg=14.5)
        assert abs(gear.pressure_angle_rad - math.radians(14.5)) < 0.0001

    def test_invalid_module(self):
        """Test that negative module raises error."""
        with pytest.raises(ValueError):
            SpurGear(module=-1.0, num_teeth=20)

    def test_invalid_teeth(self):
        """Test that negative teeth raises error."""
        with pytest.raises(ValueError):
            SpurGear(module=2.0, num_teeth=-10)

    def test_geometry_summary(self):
        """Test geometry summary output."""
        gear = SpurGear(module=2.0, num_teeth=20, name="test")
        summary = gear.get_geometry_summary()
        assert summary["name"] == "test"
        assert summary["module (m)"] == 2.0
        assert summary["num_teeth (z)"] == 20

    def test_mass_calculation(self):
        """Test mass estimation."""
        gear = SpurGear(module=2.0, num_teeth=20, face_width=10.0)
        assert gear.mass > 0

    def test_standard_min_teeth(self):
        """Test minimum teeth for no undercutting."""
        # z_min = 2/sin²(20°) ≈ 17.09, ceil = 18
        gear_20deg = SpurGear(module=2.0, num_teeth=20, pressure_angle_deg=20)
        assert gear_20deg.standard_min_teeth == 18

        # z_min = 2/sin²(25°) ≈ 11.79, ceil = 12
        gear_25deg = SpurGear(module=2.0, num_teeth=20, pressure_angle_deg=25)
        assert gear_25deg.standard_min_teeth == 12


class TestGearRatio:
    """Test cases for GearRatioCalculator."""

    def test_single_pair_ratio(self):
        """Test single pair gear ratio."""
        ratio = GearRatioCalculator.calculate_single_pair(20, 40)
        assert ratio == 2.0

    def test_gear_pair_class(self):
        """Test GearPair dataclass."""
        pair = GearPair(driver="G1", driven="G2", driver_teeth=20, driven_teeth=40,
                        driver_module=2.0, driven_module=2.0)
        assert pair.gear_ratio == 2.0
        assert pair.speed_ratio == 0.5
        assert pair.torque_ratio == 2.0
        assert pair.center_distance == 60.0

    def test_simple_train_ratio(self):
        """Test simple gear train ratio."""
        # z1=20 -> z2=40 -> z3=30 -> z4=60
        gears = [(20, 40), (40, 30), (30, 60)]
        ratio = GearRatioCalculator.calculate_simple_train([(20,), (40,), (30,), (60,)])
        assert abs(ratio - 60.0 / 20.0) < 0.0001

    def test_compound_train_ratio(self):
        """Test compound gear train ratio."""
        stages = [(15, 45), (18, 36), (20, 40)]
        ratio = GearRatioCalculator.calculate_compound_train(stages)
        expected = (45/15) * (36/18) * (40/20)
        assert abs(ratio - expected) < 0.0001

    def test_direction_changes(self):
        """Test direction change calculation."""
        assert GearRatioCalculator.calculate_direction_changes(1) == "反向 (opposite direction)"
        assert GearRatioCalculator.calculate_direction_changes(2) == "同向 (same direction)"
        assert GearRatioCalculator.calculate_direction_changes(3) == "反向 (opposite direction)"

    def test_analyze_ratio(self):
        """Test ratio analysis."""
        result = GearRatioCalculator.analyze_ratio(2.0)
        assert result["type"] == "减速传动 (Reduction)"
        assert result["ratio"] == 2.0
        assert result["speed_multiplier"] == 0.5
        assert result["torque_multiplier"] == 2.0

        result2 = GearRatioCalculator.analyze_ratio(0.5)
        assert result2["type"] == "增速传动 (Increase)"

    def test_invalid_input(self):
        """Test invalid inputs raise errors."""
        with pytest.raises(ValueError):
            GearRatioCalculator.calculate_single_pair(0, 20)
        with pytest.raises(ValueError):
            GearRatioCalculator.calculate_single_pair(20, -10)


class TestTransmission:
    """Test cases for TransmissionCalculator."""

    def test_gear_pair_transmission(self):
        """Test single gear pair transmission."""
        driver = SpurGear(module=2.0, num_teeth=20, name="driver")
        driven = SpurGear(module=2.0, num_teeth=40, name="driven")

        calc = TransmissionCalculator("spur")
        result = calc.calculate_gear_pair(
            driver=driver, driven=driven,
            input_speed_rpm=1500, input_torque_nm=10
        )

        assert result.overall_ratio == 2.0
        assert abs(result.output_speed_rpm - 750) < 0.1
        assert result.output_torque_nm == 19.6  # 10 * 2.0 * 0.98
        assert result.efficiency == 0.98

    def test_gear_train_transmission(self):
        """Test gear train transmission."""
        gears = [
            SpurGear(module=2, num_teeth=15, name="G1"),
            SpurGear(module=2, num_teeth=45, name="G2"),
            SpurGear(module=2, num_teeth=20, name="G3"),
            SpurGear(module=2, num_teeth=40, name="G4"),
        ]

        calc = TransmissionCalculator("spur")
        result = calc.calculate_gear_train(
            gears=gears, input_speed_rpm=3000, input_torque_nm=5
        )

        # Simple train: ratio = product of all stages = (45/15)*(20/45)*(40/20) = 40/15
        expected_ratio = 40.0 / 15.0
        assert abs(result.overall_ratio - expected_ratio) < 0.0001
        assert result.output_speed_rpm < 3000
        assert result.output_torque_nm > 5

    def test_power_calculation(self):
        """Test power-torque-speed conversion."""
        # P = T * omega = T * 2*pi*n/60
        torque = 10  # N·m
        speed = 1000  # RPM
        power = TransmissionCalculator.torque_to_power(torque, speed)
        omega = 2 * math.pi * speed / 60
        assert abs(power - torque * omega) < 0.01

    def test_power_to_torque(self):
        """Test power to torque conversion."""
        power = 1000  # W
        speed = 1000  # RPM
        torque = TransmissionCalculator.power_to_torque(power, speed)
        omega = 2 * math.pi * speed / 60
        assert abs(torque - power / omega) < 0.001

    def test_stage_by_stage(self):
        """Test stage-by-stage analysis."""
        gears = [
            SpurGear(module=2, num_teeth=20, name="G1"),
            SpurGear(module=2, num_teeth=40, name="G2"),
            SpurGear(module=2, num_teeth=30, name="G3"),
        ]

        calc = TransmissionCalculator("spur")
        stages = calc.calculate_stage_by_stage(gears, 1500, 10)

        assert len(stages) == 2
        assert stages[0]["stage_ratio"] == 2.0  # 40/20
        assert stages[1]["stage_ratio"] == 0.75  # 30/40


class TestEfficiency:
    """Test cases for EfficiencyAnalyzer."""

    def test_mesh_efficiency(self):
        """Test mesh efficiency for different gear types."""
        analyzer = EfficiencyAnalyzer()

        spur_eff = analyzer.analyze_mesh_efficiency("spur", pitch_line_velocity=5.0)
        assert 0.95 < spur_eff < 1.0

        helical_eff = analyzer.analyze_mesh_efficiency("helical", pitch_line_velocity=5.0)
        assert helical_eff > spur_eff  # Helical is more efficient

    def test_worm_gear_efficiency(self):
        """Test worm gear efficiency calculation."""
        analyzer = EfficiencyAnalyzer()

        # High lead angle = higher efficiency
        eff_high = analyzer.calculate_worm_gear_efficiency(
            lead_angle_deg=25, lubrication="good_lubrication"
        )
        eff_low = analyzer.calculate_worm_gear_efficiency(
            lead_angle_deg=5, lubrication="good_lubrication"
        )
        assert eff_high > eff_low

    def test_gear_train_efficiency(self):
        """Test gear train efficiency analysis."""
        analyzer = EfficiencyAnalyzer()
        gears = [
            SpurGear(module=2, num_teeth=20, name="G1"),
            SpurGear(module=2, num_teeth=40, name="G2"),
        ]

        result = analyzer.analyze_gear_train_efficiency(
            gears=gears, input_power_w=1000, gear_type="spur"
        )

        assert result.overall_efficiency < 1.0
        assert result.overall_efficiency > 0
        assert result.total_loss_w > 0
        assert result.output_power_w < result.input_power_w

    def test_efficiency_report(self):
        """Test efficiency report formatting."""
        analyzer = EfficiencyAnalyzer()
        gears = [
            SpurGear(module=2, num_teeth=20, name="G1"),
            SpurGear(module=2, num_teeth=40, name="G2"),
        ]
        result = analyzer.analyze_gear_train_efficiency(
            gears=gears, input_power_w=1000, gear_type="spur"
        )

        report = EfficiencyAnalyzer.print_efficiency_report(result)
        assert "Input Power" in report
        assert "Output Power" in report
        assert "Overall Efficiency" in report


class TestContactRatio:
    """Test cases for ContactRatioCalculator."""

    def test_basic_contact_ratio(self):
        """Test basic contact ratio calculation."""
        g1 = SpurGear(module=2, num_teeth=20, name="G1")
        g2 = SpurGear(module=2, num_teeth=40, name="G2")

        result = ContactRatioCalculator.calculate(g1, g2)
        assert result.contact_ratio > 0
        assert result.is_adequate  # Should meet minimum for general use

    def test_contact_ratio_quality(self):
        """Test contact ratio quality analysis."""
        quality = ContactRatioCalculator.analyze_contact_quality(0.9)
        assert quality["quality"] == "poor"

        quality = ContactRatioCalculator.analyze_contact_quality(1.4)
        assert quality["quality"] == "good"

        quality = ContactRatioCalculator.analyze_contact_quality(1.8)
        assert quality["quality"] == "excellent"

    def test_gear_pairing_requirements(self):
        """Test that meshing gears must have same module and pressure angle."""
        g1 = SpurGear(module=2, num_teeth=20, name="G1")
        g2 = SpurGear(module=3, num_teeth=30, name="G2")

        with pytest.raises(ValueError):
            ContactRatioCalculator.calculate(g1, g2)

        g3 = SpurGear(module=2, num_teeth=20, name="G3", pressure_angle_deg=14.5)
        with pytest.raises(ValueError):
            ContactRatioCalculator.calculate(g1, g3)

    def test_contact_ratio_summary(self):
        """Test contact ratio summary output."""
        g1 = SpurGear(module=2, num_teeth=20, name="G1")
        g2 = SpurGear(module=2, num_teeth=40, name="G2")
        result = ContactRatioCalculator.calculate(g1, g2)
        summary = result.summary()
        assert "contact_ratio" in summary
        assert "is_adequate" in summary

    def test_find_gear_pairs(self):
        """Test finding gear pairs for target ratio."""
        pairs = ContactRatioCalculator.find_gear_pairs_for_ratio(2.0, min_contact=1.2)
        assert len(pairs) > 0
        for pair in pairs:
            assert abs(pair["actual_ratio"] - 2.0) < 0.1


class TestGearTrains:
    """Test cases for gear train classes."""

    def test_simple_gear_train(self):
        """Test simple gear train."""
        train = SimpleGearTrain()
        train.add_gear(SpurGear(module=2, num_teeth=20, name="G1"))
        train.add_gear(SpurGear(module=2, num_teeth=40, name="G2"))
        train.add_gear(SpurGear(module=2, num_teeth=30, name="G3"))

        # Simple train: (40/20)*(30/40) = 30/20 = 1.5
        assert train.overall_ratio == 30.0 / 20.0
        assert train.num_meshes == 2
        assert "同向" in train.output_direction  # 2 meshes = even = same direction

    def test_simple_gear_transmission(self):
        """Test simple gear train transmission."""
        train = SimpleGearTrain()
        train.add_gear(SpurGear(module=2, num_teeth=20, name="G1"))
        train.add_gear(SpurGear(module=2, num_teeth=40, name="G2"))

        result = train.calculate_transmission(1500, 10)
        assert result.overall_ratio == 2.0
        assert result.output_speed_rpm == 750

    def test_compound_gear_train(self):
        """Test compound gear train."""
        train = CompoundGearTrain()
        train.add_stage(15, 45, 2.0)
        train.add_stage(18, 36, 2.0)
        train.add_stage(20, 40, 2.0)

        assert train.overall_ratio == (45/15) * (36/18) * (40/20)
        assert train.num_stages == 3

    def test_compound_gear_transmission(self):
        """Test compound gear train transmission."""
        train = CompoundGearTrain()
        train.add_stage(20, 40, 2.0)
        train.add_stage(20, 40, 2.0)

        result = train.calculate_transmission(3000, 5)
        assert result.overall_ratio == 4.0  # (40/20)*(40/20)
        assert abs(result.output_speed_rpm - 750) < 0.1

    def test_planary_gear_train(self):
        """Test planetary gear train."""
        # Sun=20, Planet=18, Ring=56 (56 = 20 + 2*18)
        # (20+56) % 3 != 0, so use num_planets=4 (76 % 4 = 0)
        planetary = PlanetaryGearTrain(
            sun_teeth=20, planet_teeth=18, ring_teeth=56, num_planets=4
        )

        assert planetary.ring_teeth == 56
        speeds = planetary.solve_speed("ring", 1000, "sun")
        assert speeds["ring"] == 0
        assert speeds["sun"] == 1000

    def test_planary_invalid(self):
        """Test invalid planetary gear parameters."""
        with pytest.raises(ValueError):
            PlanetaryGearTrain(
                sun_teeth=20, planet_teeth=18, ring_teeth=50, num_planets=3
            )

    def test_planary_modes(self):
        """Test planetary gear modes."""
        planetary = PlanetaryGearTrain(
            sun_teeth=20, planet_teeth=18, ring_teeth=56, num_planets=4
        )
        modes = planetary.get_modes()
        assert len(modes) > 0

    def test_gear_train_summaries(self):
        """Test summary methods."""
        # Simple train
        simple = SimpleGearTrain()
        simple.add_gear(SpurGear(module=2, num_teeth=20, name="G1"))
        simple.add_gear(SpurGear(module=2, num_teeth=40, name="G2"))
        summary = simple.summary()
        assert summary["type"] == "Simple Gear Train (简单齿轮系)"

        # Compound train
        compound = CompoundGearTrain()
        compound.add_stage(20, 40, 2.0)
        summary = compound.summary()
        assert summary["type"] == "Compound Gear Train (复合齿轮系)"

        # Planetary
        planetary = PlanetaryGearTrain(
            sun_teeth=20, planet_teeth=18, ring_teeth=56, num_planets=4
        )
        summary = planetary.summary()
        assert summary["type"] == "Planetary Gear Train (行星齿轮系)"
