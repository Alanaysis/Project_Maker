"""Tests for ControllerDesigner."""

import numpy as np
import pytest

from src.transfer_function import TransferFunction
from src.controller_design import ControllerDesigner, PIDParams


class TestControllerDesigner:
    """Test controller design methods."""

    def setup_method(self):
        # Plant: 1/(s+1)
        self.plant = TransferFunction([1], [1, 1])
        self.designer = ControllerDesigner(self.plant)

    def test_pid_ziegler_nichols_step(self):
        # Use a stable second-order plant for Z-N step method
        plant = TransferFunction([1], [1, 3, 2])
        designer = ControllerDesigner(plant)
        params = designer.pid_ziegler_nichols(method="step")
        assert isinstance(params, PIDParams)
        assert params.Kp > 0

    def test_pid_ziegler_nichols_ultimate(self):
        # Use a stable third-order plant for Z-N ultimate method
        plant = TransferFunction([1], [1, 6, 11, 6])
        designer = ControllerDesigner(plant)
        params = designer.pid_ziegler_nichols(method="ultimate")
        assert isinstance(params, PIDParams)
        assert params.Kp > 0

    def test_pid_invalid_method(self):
        with pytest.raises(ValueError):
            self.designer.pid_ziegler_nichols(method="invalid")

    def test_pid_transfer_function(self):
        params = PIDParams(Kp=1.0, Ki=0.5, Kd=0.1, Tf=0.01)
        tf = ControllerDesigner.pid_transfer_function(params)
        assert tf.order == 2  # PID with filter

    def test_design_lead(self):
        # Plant: 1/(s(s+1)) -- needs lead for stability
        plant = TransferFunction([1], [1, 1, 0])
        designer = ControllerDesigner(plant)
        lead = designer.design_lead(phase_boost_deg=45, omega_cross=1.0)
        assert lead.order == 1

    def test_design_lag(self):
        lag = self.designer.design_lag(low_freq_gain_boost=10, omega_cross=1.0)
        assert lag.order == 1

    def test_design_lead_lag(self):
        plant = TransferFunction([1], [1, 1, 0])
        designer = ControllerDesigner(plant)
        lead, lag = designer.design_lead_lag(
            phase_boost_deg=45, omega_cross=1.0, low_freq_boost=10
        )
        assert lead.order == 1
        assert lag.order == 1

    def test_design_from_poles(self):
        # Plant: 1/(s+1)
        # Desired closed-loop poles at s=-3
        controller = self.designer.design_from_poles(desired_poles=[-3])
        assert len(controller.num) > 0

    def test_pid_params_dataclass(self):
        params = PIDParams(Kp=2.0, Ki=1.0, Kd=0.5)
        assert params.Kp == 2.0
        assert params.Ki == 1.0
        assert params.Kd == 0.5
        assert params.Tf == 0.01  # Default
