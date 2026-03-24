import pytest
from unittest.mock import Mock
from mvp.controller import (
    SimulatedController,
    GRBLController,
    RuidaController,
    BaseController,
)


def test_simulated_controller_move_to():
    simulator = Mock()
    controller = SimulatedController(simulator)
    controller.move_to(10, 20)
    simulator.move_gantry_to.assert_called_once_with(10, 20)


def test_simulated_controller_move_by():
    simulator = Mock()
    simulator.gantry_x = 5
    simulator.gantry_y = 8
    controller = SimulatedController(simulator)
    controller.move_by(2, 3)
    simulator.move_gantry_to.assert_called_once_with(7, 11)


def test_simulated_controller_move_in_direction():
    simulator = Mock()
    simulator.gantry_x = 0
    simulator.gantry_y = 0
    controller = SimulatedController(simulator)
    controller.move_in_direction(90, 10)
    # 90 degrees is positive y direction
    simulator.move_gantry_to.assert_called_once_with(
        pytest.approx(0, abs=1e-6), pytest.approx(10, abs=1e-6)
    )


def test_grbl_controller_init():
    with pytest.raises(NotImplementedError):
        GRBLController("COM3")


def test_ruida_controller_init():
    with pytest.raises(NotImplementedError):
        RuidaController("192.168.1.100")


def test_controller_interface_conformance():
    # Check that the concrete classes implement the abstract methods
    assert issubclass(SimulatedController, BaseController)
    assert issubclass(GRBLController, BaseController)
    assert issubclass(RuidaController, BaseController)
