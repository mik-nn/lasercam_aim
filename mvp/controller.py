import math
import re
import socket
import serial
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
    """A simulated controller that wraps a MotionSimulator."""

    def __init__(self, simulator):
        self._simulator = simulator

    @property
    def position(self) -> tuple[float, float]:
        """Returns camera position (gantry position)."""
        return self._simulator.gantry_x, self._simulator.gantry_y

    @property
    def laser_position(self) -> tuple[float, float]:
        """Returns laser position (camera position + offset)."""
        return (
            self._simulator.gantry_x + self._simulator.laser_offset_x,
            self._simulator.gantry_y + self._simulator.laser_offset_y,
        )

    def move_to(self, x_mm: float, y_mm: float) -> None:
        self._simulator.move_gantry_to(x_mm, y_mm)

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        x, y = self.position
        self.move_to(x + dx_mm, y + dy_mm)

    def release(self) -> None:
        pass


class GRBLController(BaseController):
    """A controller for GRBL-based machines using G-code."""

    _STATUS_RE = re.compile(
        r"<[^|]*[|,]MPos:([-\d.]+),([-\d.]+),([-\d.]+)"
    )

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
        retries: int = 3,
    ):
        self._port_name = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._retries = retries
        self._serial = serial.Serial(port, baudrate, timeout=timeout)
        self._last_position: tuple[float, float] = (0.0, 0.0)
        self._ensure_absolute_mode()

    def _send_command(self, cmd: str) -> str:
        for attempt in range(self._retries):
            try:
                self._serial.write(f"{cmd}\n".encode())
                response = self._serial.readline().decode().strip()
                if response.startswith("error:") or response.startswith("alarm:"):
                    raise RuntimeError(f"GRBL error: {response}")
                return response
            except serial.SerialTimeoutException:
                if attempt == self._retries - 1:
                    raise
        return ""

    def _send_command_wait(self, cmd: str) -> str:
        self._serial.write(f"{cmd}\n".encode())
        while True:
            line = self._serial.readline().decode().strip()
            if line == "ok":
                return line
            if line.startswith("error:") or line.startswith("alarm:"):
                raise RuntimeError(f"GRBL error: {line}")
            if line.startswith("<"):
                continue

    def _ensure_absolute_mode(self) -> None:
        self._send_command_wait("G90")

    @property
    def position(self) -> tuple[float, float]:
        try:
            self._serial.write(b"?\n")
            response = self._serial.readline().decode().strip()
            match = self._STATUS_RE.search(response)
            if match:
                x, y = float(match.group(1)), float(match.group(2))
                self._last_position = (x, y)
                return (x, y)
        except (serial.SerialException, UnicodeDecodeError):
            pass
        return self._last_position

    def move_to(self, x_mm: float, y_mm: float) -> None:
        self._send_command_wait(f"G0 X{x_mm:.3f} Y{y_mm:.3f}")
        self._last_position = (x_mm, y_mm)

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        x, y = self.position
        self.move_to(x + dx_mm, y + dy_mm)

    def release(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()


class RuidaController(BaseController):
    """
    A controller for Ruida-based machines.
    Communicates over UDP on port 50200.

    AICODE-NOTE: Based on MeerK40T's Ruida emulator source analysis.
    Key protocol details:
    - PC -> Controller: Packets include 2-byte checksum + swizzled data
    - Controller -> PC: Responses are swizzled data WITHOUT checksum
    - Magic number 0x88 (default for most Ruida controllers)
    - ACK=0xCC, NAK=0xCF, ENQ=0xCE, ERR=0xCD
    - Coordinates encoded as 5 bytes (7 bits per byte) in micrometers
    """

    ACK = b"\xCC"
    NAK = b"\xCF"
    ENQ = b"\xCE"
    ERR = b"\xCD"

    MOVE_ABS_XY = b"\x88"
    MOVE_REL_XY = b"\x89"
    RAPID_MOVE_XY = b"\xD9\x10"
    GET_SETTING = b"\xDA\x00"
    SET_ABSOLUTE = b"\xE6\x01"
    REF_POINT_2 = b"\xD8\x10"
    START_PROCESS = b"\xD8\x00"

    MEM_CURRENT_X = b"\x04\x21"
    MEM_CURRENT_Y = b"\x04\x31"

    DEFAULT_MAGIC = 0x88

    def __init__(
        self,
        host: str,
        port: int = 50200,
        listen_port: int = 40200,
        timeout: float = 1.0,
        retries: int = 3,
    ):
        self._host = host
        self._port = port
        self._listen_port = listen_port
        self._timeout = timeout
        self._retries = retries
        self._magic = self.DEFAULT_MAGIC
        self._last_position: tuple[float, float] = (0.0, 0.0)
        self._socket = None
        self._connected = False
        self._connect()

    def _swizzle_byte(self, b: int, magic: int) -> int:
        """Swizzle a single byte using MeerK40T's algorithm."""
        b ^= (b >> 7) & 0xFF
        b ^= (b << 7) & 0xFF
        b ^= (b >> 7) & 0xFF
        b ^= magic
        b = (b + 1) & 0xFF
        return b

    def _unswizzle_byte(self, b: int, magic: int) -> int:
        """Unswizzle a single byte using MeerK40T's algorithm."""
        b = (b - 1) & 0xFF
        b ^= magic
        b ^= (b >> 7) & 0xFF
        b ^= (b << 7) & 0xFF
        b ^= (b >> 7) & 0xFF
        return b

    def _swizzle(self, data: bytes) -> bytes:
        return bytes(self._swizzle_byte(b, self._magic) for b in data)

    def _unswizzle(self, data: bytes) -> bytes:
        return bytes(self._unswizzle_byte(b, self._magic) for b in data)

    def _encode32(self, v: int) -> bytes:
        """Encode a 32-bit value as 5 bytes (7 bits per byte)."""
        v = int(v) & 0xFFFFFFFF
        return bytes([
            (v >> 28) & 0x7F,
            (v >> 21) & 0x7F,
            (v >> 14) & 0x7F,
            (v >> 7) & 0x7F,
            v & 0x7F,
        ])

    def _encode14(self, v: int) -> bytes:
        """Encode a 14-bit value as 2 bytes (7 bits per byte)."""
        v = int(v) & 0x3FFF
        return bytes([
            (v >> 7) & 0x7F,
            v & 0x7F,
        ])

    def _decode32(self, data: bytes) -> int:
        """Decode 5 bytes into a 32-bit value."""
        return (
            (data[0] & 0x7F) << 28
            | (data[1] & 0x7F) << 21
            | (data[2] & 0x7F) << 14
            | (data[3] & 0x7F) << 7
            | (data[4] & 0x7F)
        )

    def _encode_abscoord(self, value_um: int) -> bytes:
        return self._encode32(value_um & 0xFFFFFFFF)

    def _encode_relcoord(self, value_um: int) -> bytes:
        value_um = int(value_um) & 0x3FFF
        return self._encode14(value_um)

    def _package(self, data: bytes) -> bytes:
        """Create a complete Ruida packet: checksum + swizzled data.

        AICODE-NOTE: MeerK40T's checksum_write expects:
        [checksum_MSB][checksum_LSB][swizzled_data...]
        Checksum is sum of swizzled bytes (not original bytes).
        """
        swizzled = self._swizzle(data)
        checksum = sum(swizzled) & 0xFFFF
        return bytes([(checksum >> 8) & 0xFF, checksum & 0xFF]) + swizzled

    def _connect(self) -> None:
        """Create UDP socket and perform ENQ handshake."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(self._timeout)
        try:
            self._socket.bind(("", self._listen_port))
        except OSError as e:
            print(f"[RUIDA] Failed to bind to port {self._listen_port}: {e}")
            return

        print(f"[RUIDA] Bound to port {self._listen_port}, sending ENQ to {self._host}:{self._port}")

        enq_packet = self._package(self.ENQ)
        print(f"[RUIDA] ENQ packet: {enq_packet.hex()}")

        for attempt in range(self._retries):
            try:
                self._socket.sendto(enq_packet, (self._host, self._port))
                print(f"[RUIDA] ENQ sent (attempt {attempt + 1})")
                response, addr = self._socket.recvfrom(1024)
                print(f"[RUIDA] Raw response: {response.hex()} ({len(response)} bytes)")

                # AICODE-NOTE: MeerK40T's emulator sends responses WITHOUT checksum.
                # The response is just the swizzled ACK byte (0xC6 for magic 0x88).
                # MeerK40T's own handshake code unswizzles the entire response.
                reply = self._unswizzle(response)
                print(f"[RUIDA] Unswizzled reply: {reply.hex()}")

                if reply == self.ACK:
                    print("[RUIDA] Handshake complete (ACK received)")
                    self._connected = True
                    self._initialize()
                    return
                elif reply == self.NAK:
                    print("[RUIDA] NAK received, retrying...")
                    continue
                elif reply == self.ENQ:
                    print("[RUIDA] ENQ echo, controller is alive")
                    self._connected = True
                    self._initialize()
                    return
                elif reply and len(reply) > 0:
                    print(f"[RUIDA] Controller response {reply.hex()}, accepting connection")
                    self._connected = True
                    self._initialize()
                    return
                else:
                    print(f"[RUIDA] Unexpected reply: {reply.hex()}")
            except (socket.timeout, OSError) as e:
                print(f"[RUIDA] Network error on ENQ attempt {attempt + 1}: {e}")
                if attempt == self._retries - 1:
                    print("[RUIDA] WARNING: Handshake failed, continuing anyway")
                    return

    def _initialize(self) -> None:
        """Send initialization sequence to set up absolute mode and reference point."""
        print("[RUIDA] Initializing controller...")

        # Set absolute coordinate mode
        try:
            self._send_command(self.SET_ABSOLUTE)
            print("[RUIDA] Set absolute mode")
        except Exception as e:
            print(f"[RUIDA] Set absolute mode failed: {e}")

        # Set reference point to machine zero
        try:
            self._send_command(self.REF_POINT_2)
            print("[RUIDA] Set reference point to machine zero")
        except Exception as e:
            print(f"[RUIDA] Set reference point failed: {e}")

    def _send_command(self, data: bytes, expect_reply: bool = False) -> bytes | None:
        """Send a Ruida command and wait for ACK/reply."""
        if not self._connected:
            print("[RUIDA] Not connected, attempting reconnect...")
            self._connect()
            if not self._connected:
                raise ConnectionError("Not connected to Ruida controller")

        packet = self._package(data)
        print(f"[RUIDA] Sending {len(packet)} bytes: {packet.hex()} (cmd: {data.hex()})")

        for attempt in range(self._retries):
            try:
                self._socket.sendto(packet, (self._host, self._port))
                response, addr = self._socket.recvfrom(1024)
                print(f"[RUIDA] Raw response: {response.hex()} ({len(response)} bytes)")

                # AICODE-NOTE: Responses from MeerK40T's emulator don't include checksum.
                # Unswizzle the entire response.
                payload = self._unswizzle(response)
                print(f"[RUIDA] Unswizzled payload: {payload.hex()}")

                if payload == self.ACK:
                    print("[RUIDA] ACK received")
                    if expect_reply:
                        response2, _ = self._socket.recvfrom(1024)
                        payload2 = self._unswizzle(response2)
                        return payload2
                    return None
                elif payload == self.NAK:
                    print("[RUIDA] NAK received, retrying...")
                    continue
                else:
                    return payload
            except (socket.timeout, OSError) as e:
                print(f"[RUIDA] Network error on attempt {attempt + 1}: {e}")
                if attempt == self._retries - 1:
                    raise ConnectionError(f"Failed to communicate with Ruida: {e}")
        return None

    @property
    def position(self) -> tuple[float, float]:
        """Return tracked position based on move commands sent.

        AICODE-NOTE: MeerK40T's Ruida emulator doesn't expose actual position
        via 0xDA 0x00 memory queries. Position is tracked locally.
        """
        return self._last_position

    def _sync_position(self) -> tuple[float, float]:
        """Query controller for position via memory read.

        AICODE-NOTE: MeerK40T's emulator returns static axis range values
        for MEM_CURRENT_X/Y, not actual position. This method is kept for
        compatibility with real Ruida controllers.
        """
        try:
            x_data = self._send_command(self.GET_SETTING + self.MEM_CURRENT_X, expect_reply=True)
            y_data = self._send_command(self.GET_SETTING + self.MEM_CURRENT_Y, expect_reply=True)

            if x_data and len(x_data) >= 9:
                x_um = self._decode32(x_data[4:9])
                self._last_position = (x_um / 1000.0, self._last_position[1])
                print(f"[RUIDA] X synced: {x_um} um = {self._last_position[0]:.1f} mm")

            if y_data and len(y_data) >= 9:
                y_um = self._decode32(y_data[4:9])
                self._last_position = (self._last_position[0], y_um / 1000.0)
                print(f"[RUIDA] Y synced: {y_um} um = {self._last_position[1]:.1f} mm")

            return self._last_position
        except Exception as e:
            print(f"[RUIDA] Position sync error: {e}")
            return self._last_position

    def move_to(self, x_mm: float, y_mm: float) -> None:
        """Move to absolute position in mm using D9 10 (Rapid Move XY)."""
        print(f"[RUIDA] Moving to ({x_mm:.1f}, {y_mm:.1f}) mm")
        x_um = int(x_mm * 1000)
        y_um = int(y_mm * 1000)

        # D9 10 00 [x 5 bytes] [y 5 bytes] - Rapid move XY with Origin option
        cmd = self.RAPID_MOVE_XY + b"\x00" + self._encode_abscoord(x_um) + self._encode_abscoord(y_um)
        try:
            self._send_command(cmd)
        except Exception as e:
            print(f"[RUIDA] Move command failed: {e}")

        self._last_position = (x_mm, y_mm)

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        """Move by relative amount in mm using 89 (Move Relative XY)."""
        print(f"[RUIDA] Moving by ({dx_mm:.1f}, {dy_mm:.1f}) mm")
        dx_um = int(dx_mm * 1000)
        dy_um = int(dy_mm * 1000)
        cmd = self.MOVE_REL_XY + self._encode_relcoord(dx_um) + self._encode_relcoord(dy_um)
        try:
            self._send_command(cmd)
        except Exception as e:
            print(f"[RUIDA] Move command failed: {e}")

        x, y = self._last_position
        self._last_position = (x + dx_mm, y + dy_mm)

    def release(self) -> None:
        """Close the UDP socket."""
        if self._socket:
            self._socket.close()
            self._socket = None
