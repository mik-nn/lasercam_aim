import math
from abc import ABC, abstractmethod


class BaseController(ABC):
    @property
    @abstractmethod
    def position(self) -> tuple[float, float]:
        """Returns the current (x_mm, y_mm) position of the controller."""
        ...

    @abstractmethod
    def move_to(self, x_mm: float, y_mm: float) -> None:
        """Moves to an absolute position."""
        ...

    @abstractmethod
    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        """Moves by a relative amount."""
        ...

    def move_in_direction(self, angle_deg: float, distance_mm: float) -> None:
        """Moves in a specific direction by a certain distance."""
        dx = distance_mm * math.cos(math.radians(angle_deg))
        dy = distance_mm * math.sin(math.radians(angle_deg))
        self.move_by(dx, dy)

    @abstractmethod
    def release(self) -> None:
        """Releases any resources held by the controller."""
        ...


class SimulatedController(BaseController):
    """
    A simulated controller that wraps a MotionSimulator.
    This is for testing and simulation purposes.
    """

    def __init__(self, simulator):
        self._simulator = simulator

    @property
    def position(self) -> tuple[float, float]:
        return self._simulator.gantry_x, self._simulator.gantry_y

    def move_to(self, x_mm: float, y_mm: float) -> None:
        self._simulator.move_gantry_to(x_mm, y_mm)

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        x, y = self.position
        self.move_to(x + dx_mm, y + dy_mm)

    def release(self) -> None:
        pass  # Nothing to release


class GRBLController(BaseController):
    """
    A controller for GRBL-based machines.
    Communicates over a serial port.
    """

    def __init__(self, port, baudrate=115200):
        # Implementation will be added later
        raise NotImplementedError("GRBLController is not yet implemented.")

    @property
    def position(self) -> tuple[float, float]:
        raise NotImplementedError("GRBLController is not yet implemented.")

    def move_to(self, x_mm: float, y_mm: float) -> None:
        raise NotImplementedError("GRBLController is not yet implemented.")

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        raise NotImplementedError("GRBLController is not yet implemented.")

    def release(self) -> None:
        raise NotImplementedError("GRBLController is not yet implemented.")


class RuidaController(BaseController):
    """
    A controller for Ruida-based machines.
    Communicates over UDP.
    """

    def __init__(self, host, port=50200):
        # Implementation will be added later
        raise NotImplementedError("RuidaController is not yet implemented.")

    @property
    def position(self) -> tuple[float, float]:
        raise NotImplementedError("RuidaController is not yet implemented.")

    def move_to(self, x_mm: float, y_mm: float) -> None:
        raise NotImplementedError("RuidaController is not yet implemented.")

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        raise NotImplementedError("RuidaController is not yet implemented.")

    def release(self) -> None:
        raise NotImplementedError("RuidaController is not yet implemented.")
