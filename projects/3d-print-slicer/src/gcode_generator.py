"""
G-code generation module.

G-code is the standardized instruction set for 3D printers. Key G-code commands:

- G0/G1: Linear move (G0 = rapid, G1 = controlled speed)
- G2/G3: Arc move (CW/CCW)
- G28: Home all axes
- G90: Absolute positioning
- G91: Relative positioning
- G92: Set current position
- M104/M109: Set/get extruder temperature
- M140/M190: Set/get bed temperature
- M82: Absolute extrusion mode
- M106: Fan control

Extrusion calculation:
    volume = length * cross_section_area
    extrusion = volume / (filament_diameter^2 * pi / 4)

Where cross_section_area = print_width * layer_height
"""

import numpy as np
from typing import List, Dict, Optional
from .toolpath_planner import ToolpathSegment


class GCodeGenerator:
    """
    Generates G-code from a toolpath.

    The G-code output includes:
    1. Header: Printer info, temperature settings
    2. Per-layer commands: Z moves, temperature checks
    3. Toolpath moves: Extrusion moves with flow control
    4. Footer: Homing, temperature reset, end marker
    """

    def __init__(self,
                 filament_diameter: float = 1.75,
                 nozzle_diameter: float = 0.4,
                 default_speed: float = 60.0,
                 travel_speed: float = 150.0,
                 initial_layer_speed: float = 20.0):
        self.filament_diameter = filament_diameter
        self.nozzle_diameter = nozzle_diameter
        self.default_speed = default_speed
        self.travel_speed = travel_speed
        self.initial_layer_speed = initial_layer_speed

        # Track current printer state
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_e = 0.0
        self.current_temp = 0.0
        self.current_feedrate = 0.0
        self._prev_e = 0.0

        # Printer settings
        self.extruder_temp = 200.0
        self.bed_temp = 60.0
        self.layer_count = 0

    def generate(self, toolpath: List[ToolpathSegment],
                 model_bounds: Dict[str, np.ndarray],
                 settings: Optional[Dict] = None) -> str:
        """
        Generate complete G-code from a toolpath.

        Args:
            toolpath: List of ToolpathSegments
            model_bounds: Dict with 'min' and 'max' numpy arrays
            settings: Optional override settings

        Returns:
            Complete G-code string
        """
        lines = []

        # Add header
        lines.extend(self._generate_header(settings))

        # Process each toolpath segment
        for segment in toolpath:
            lines.extend(self._generate_segment(segment))

        # Add footer
        lines.extend(self._generate_footer())

        return "\n".join(lines)

    def _generate_header(self, settings: Optional[Dict] = None) -> List[str]:
        """Generate G-code header with printer initialization."""
        lines = []
        lines.append("; 3D Print Slicer - Generated G-code")
        lines.append("; https://github.com/3d-print-slicer")
        lines.append(";")
        lines.append(f"; Filament diameter: {self.filament_diameter:.2f} mm")
        lines.append(f"; Nozzle diameter: {self.nozzle_diameter:.2f} mm")
        lines.append(f"; Layer height: {self.layer_height:.3f} mm")
        lines.append(f"; Estimated layers: {self.layer_count}")
        lines.append(";")
        lines.append("; --- Printer Initialization ---")

        # Home the printer
        lines.append("G28 ; Home all axes")
        lines.append("G90 ; Absolute positioning")
        lines.append("M83 ; Relative extrusion")
        lines.append("G92 E0 ; Reset extruder position")

        # Set bed temperature
        lines.append(f"M140 S{self.bed_temp:.1f} ; Set bed temperature")
        lines.append(f"M104 S{self.extruder_temp:.1f} ; Set extruder temperature (non-blocking)")

        # Wait for bed to reach temperature
        lines.append("; Waiting for bed temperature...")
        lines.append(f"M190 S{self.bed_temp:.1f} ; Wait for bed temperature")

        # Wait for extruder to reach temperature
        lines.append("; Waiting for extruder temperature...")
        lines.append(f"M109 S{self.extruder_temp:.1f} ; Wait for extruder temperature")

        # Prime the nozzle
        lines.append("; Prime the nozzle")
        lines.append(f"G1 E2 F100 ; Extrude 2mm to prime")
        lines.append("")

        return lines

    def _generate_segment(self, segment: ToolpathSegment) -> List[str]:
        """Generate G-code for a single toolpath segment."""
        lines = []
        x, y, z = segment.end

        if segment.is_extruding:
            # Calculate extrusion amount
            dx = segment.end[0] - segment.start[0]
            dy = segment.end[1] - segment.start[1]
            dz = segment.end[2] - segment.start[2]
            move_length = np.sqrt(dx**2 + dy**2)

            # Cross-section area of the extrusion
            cross_section_area = self.nozzle_diameter * self.nozzle_diameter

            # Volume of filament to extrude
            volume = move_length * cross_section_area

            # Convert volume to extrusion length
            filament_area = (self.filament_diameter ** 2) * np.pi / 4.0
            e_length = volume / filament_area

            # Update current extrusion position
            e_delta = e_length - (self.current_e - (self._get_prev_e(segment)))
            self.current_e += e_delta

            # Set feed rate
            if self.layer_count == 0 and segment.move_type == "perimeter":
                feedrate = self.initial_layer_speed * 60  # First layer slower
            else:
                feedrate = self.default_speed * 60

            if segment.move_type == "perimeter":
                lines.append(f"; Perimeter move at Z={z:.3f}")
            else:
                lines.append(f"; Infill move at Z={z:.3f}")

            lines.append(f"G1 X{x:.5f} Y{y:.5f} Z{z:.5f} E{self.current_e:.5f} F{feedrate:.1f}")

            self.current_x = x
            self.current_y = y
            self.current_z = z
            self.current_feedrate = feedrate
        else:
            # Travel move (non-extruding)
            # Lift slightly to avoid scraping
            z_lift = z + 0.5
            lines.append(f"G0 X{x:.5f} Y{y:.5f} Z{z_lift:.5f} F{self.travel_speed * 60:.1f}")

            # Move to actual Z height
            if z != self.current_z:
                lines.append(f"G0 X{x:.5f} Y{y:.5f} Z{z:.5f} F{self.travel_speed * 60:.1f}")

            self.current_x = x
            self.current_y = y
            self.current_z = z

        return lines

    def _generate_footer(self) -> List[str]:
        """Generate G-code footer with cleanup commands."""
        lines = []
        lines.append("")
        lines.append("; --- Print Complete ---")
        lines.append("; Total layers: {}".format(self.layer_count))

        # Retract filament
        lines.append("M83 ; Relative extrusion")
        lines.append("G1 E-2 F2400 ; Retract filament")

        # Move nozzle away from print
        lines.append("G0 Z10 F6000 ; Move nozzle up")

        # Turn off heaters
        lines.append("M104 S0 ; Turn off extruder")
        lines.append("M140 S0 ; Turn off bed")

        # Turn on fans
        lines.append("M107 ; Turn off fan")

        # Home and wait
        lines.append("G28 ; Home all axes")
        lines.append("; Print complete. Please remove your print.")

        return lines

    def _get_prev_e(self, segment: ToolpathSegment) -> float:
        """Get the previous extrusion position."""
        if not hasattr(self, '_prev_e') or self._prev_e is None:
            return 0.0
        return self._prev_e

    @property
    def layer_height(self) -> float:
        return self._layer_height if hasattr(self, '_layer_height') else 0.2

    @layer_height.setter
    def layer_height(self, value: float):
        self._layer_height = value

    @property
    def prev_e(self):
        return self._get_prev_e

    @prev_e.setter
    def prev_e(self, value):
        self._prev_e = value


def estimate_print_time(toolpath: List[ToolpathSegment],
                        travel_speed: float = 150.0,
                        print_speed: float = 60.0) -> Dict[str, float]:
    """
    Estimate print time from a toolpath.

    Args:
        toolpath: List of ToolpathSegments
        travel_speed: Speed for non-extruding moves (mm/s)
        print_speed: Speed for extruding moves (mm/s)

    Returns:
        Dict with 'total_time', 'print_time', 'travel_time' in seconds
    """
    total_time = 0.0
    print_time = 0.0
    travel_time = 0.0

    for segment in toolpath:
        length = segment.length()
        if segment.is_extruding:
            time = length / print_speed
            print_time += time
        else:
            time = length / travel_speed
            travel_time += time

        total_time += time

    return {
        'total_time': total_time,
        'print_time': print_time,
        'travel_time': travel_time,
        'total_distance': sum(s.length() for s in toolpath),
        'extrusion_distance': sum(s.length() for s in toolpath if s.is_extruding),
    }


def estimate_material_usage(toolpath: List[ToolpathSegment],
                            filament_diameter: float = 1.75,
                            nozzle_diameter: float = 0.4) -> Dict[str, float]:
    """
    Estimate material usage from a toolpath.

    Args:
        toolpath: List of ToolpathSegments
        filament_diameter: Filament diameter (mm)
        nozzle_diameter: Nozzle diameter (mm)

    Returns:
        Dict with 'volume_mm3', 'mass_g' (assuming PLA density = 1.24 g/cm3)
    """
    # Total extrusion length
    extrusion_length = sum(s.length() for s in toolpath if s.is_extruding)

    # Cross-section area of the extrusion
    cross_section_area = nozzle_diameter * nozzle_diameter

    # Volume
    volume_mm3 = extrusion_length * cross_section_area
    volume_cm3 = volume_mm3 / 1000.0

    # Mass (PLA density ~ 1.24 g/cm3)
    mass_g = volume_cm3 * 1.24

    return {
        'extrusion_length_mm': extrusion_length,
        'volume_mm3': volume_mm3,
        'volume_cm3': volume_cm3,
        'mass_g': mass_g,
        'filament_length_mm': extrusion_length * (nozzle_diameter ** 2) / (filament_diameter ** 2),
    }
