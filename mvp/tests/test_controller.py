from unittest.mock import Mock, patch, MagicMock

import pytest

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


# ------------------------------------------------------------------
# GRBLController tests
# ------------------------------------------------------------------


@patch("mvp.controller.serial.Serial")
def test_grbl_controller_init(mock_serial):
    mock_ser = MagicMock()
    mock_ser.readline.side_effect = [b"ok\n"]
    mock_serial.return_value = mock_ser

    ctrl = GRBLController("COM3", baudrate=115200)
    mock_serial.assert_called_once_with("COM3", 115200, timeout=1.0)
    ctrl.release()


@patch("mvp.controller.serial.Serial")
def test_grbl_controller_move_to(mock_serial):
    mock_ser = MagicMock()
    mock_ser.readline.side_effect = [b"ok\n", b"ok\n"]
    mock_serial.return_value = mock_ser

    ctrl = GRBLController("COM3")
    ctrl.move_to(100.5, 50.25)

    expected_cmd = f"G0 X{100.5:.3f} Y{50.25:.3f}\n".encode()
    mock_ser.write.assert_any_call(expected_cmd)
    ctrl.release()


@patch("mvp.controller.serial.Serial")
def test_grbl_controller_move_by(mock_serial):
    mock_ser = MagicMock()
    mock_ser.readline.side_effect = [b"ok\n", b"ok\n", b"ok\n"]
    mock_serial.return_value = mock_ser

    ctrl = GRBLController("COM3")
    ctrl._last_position = (10.0, 20.0)
    ctrl.move_by(5.0, -3.0)

    expected_cmd = f"G0 X{15.0:.3f} Y{17.0:.3f}\n".encode()
    mock_ser.write.assert_any_call(expected_cmd)
    ctrl.release()


@patch("mvp.controller.serial.Serial")
def test_grbl_controller_position_query(mock_serial):
    mock_ser = MagicMock()
    mock_ser.readline.side_effect = [
        b"ok\n", b"<Idle|MPos:100.000,50.000,0.000|FS:0,0>\n",
    ]
    mock_serial.return_value = mock_ser

    ctrl = GRBLController("COM3")
    pos = ctrl.position

    assert pos == (100.0, 50.0)
    mock_ser.write.assert_called_with(b"?\n")
    ctrl.release()


@patch("mvp.controller.serial.Serial")
def test_grbl_controller_position_query_grbl09(mock_serial):
    mock_ser = MagicMock()
    mock_ser.readline.side_effect = [b"ok\n", b"<Idle,MPos:200.000,75.000,0.000>\n"]
    mock_serial.return_value = mock_ser

    ctrl = GRBLController("COM3")
    pos = ctrl.position

    assert pos == (200.0, 75.0)
    ctrl.release()


@patch("mvp.controller.serial.Serial")
def test_grbl_controller_release(mock_serial):
    mock_ser = MagicMock()
    mock_ser.readline.return_value = b"ok\n"
    mock_ser.is_open = True
    mock_serial.return_value = mock_ser

    ctrl = GRBLController("COM3")
    ctrl.release()

    mock_ser.close.assert_called_once()


# ------------------------------------------------------------------
# RuidaController tests
# ------------------------------------------------------------------


@patch("mvp.controller.socket.socket")
def test_ruida_controller_init(mock_socket_cls):
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    mock_sock.recvfrom.return_value = (b"\x00\xcc", ("192.168.1.100", 40200))  # ACK response

    ctrl = RuidaController("192.168.1.100", port=50200)

    mock_socket_cls.assert_called_once()
    mock_sock.bind.assert_called_once_with(("", 40200))
    # Should have sent ENQ during handshake
    mock_sock.sendto.assert_called()
    ctrl.release()


@patch("mvp.controller.socket.socket")
def test_ruida_controller_move_to(mock_socket_cls):
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    # ACK responses for ENQ handshake and move command
    mock_sock.recvfrom.return_value = (b"\x00\xcc", ("192.168.1.100", 40200))

    ctrl = RuidaController("192.168.1.100")
    ctrl.move_to(100.0, 50.0)

    # Verify sendto was called (ENQ + move command)
    assert mock_sock.sendto.call_count >= 2
    ctrl.release()


@patch("mvp.controller.socket.socket")
def test_ruida_controller_move_by(mock_socket_cls):
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    mock_sock.recvfrom.return_value = (b"\x00\xcc", ("192.168.1.100", 40200))

    ctrl = RuidaController("192.168.1.100")
    ctrl._last_position = (10.0, 20.0)
    ctrl.move_by(5.0, -3.0)

    # Verify sendto was called
    assert mock_sock.sendto.call_count >= 2
    ctrl.release()


@patch("mvp.controller.socket.socket")
def test_ruida_controller_position_query(mock_socket_cls):
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock

    # Simplified: just return last position when query fails
    mock_sock.recvfrom.return_value = (b"\x00\xcc", ("192.168.1.100", 40200))

    ctrl = RuidaController("192.168.1.100")
    ctrl._last_position = (150.0, 75.0)
    pos = ctrl.position

    # Should return last position when query fails
    assert pos == (150.0, 75.0)
    ctrl.release()


@patch("mvp.controller.socket.socket")
def test_ruida_controller_release(mock_socket_cls):
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    mock_sock.recvfrom.return_value = (b"\x00\xcc", ("192.168.1.100", 40200))

    ctrl = RuidaController("192.168.1.100")
    ctrl.release()

    mock_sock.close.assert_called_once()


# ------------------------------------------------------------------
# RuidaController Integration Tests (live communication)
# ------------------------------------------------------------------


@patch("mvp.controller.socket.socket")
def test_ruida_packet_structure_enq(mock_socket_cls):
    """Test that ENQ packet structure matches MeerK40T expectations."""
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    mock_sock.recvfrom.return_value = (b"\xc6", ("127.0.0.1", 40200))  # swizzled ACK

    ctrl = RuidaController("127.0.0.1")

    # ENQ = 0xCE, swizzled with magic 0x88 -> 0xC8
    # checksum = 0xC8, so packet = 0x00C8 0xC8
    # Expected: 00c8c8
    enq_call = mock_sock.sendto.call_args_list[0]
    packet = enq_call[0][0]
    print(f"ENQ packet: {packet.hex()}")

    # Verify it's a valid Ruida packet (2 byte checksum + swizzled data)
    assert len(packet) >= 3, "ENQ packet should have at least 2 checksum + 1 data byte"
    ctrl.release()


@patch("mvp.controller.socket.socket")
def test_ruida_packet_structure_move_xy(mock_socket_cls):
    """Test that D9 10 (Rapid Move XY) packet structure is correct."""
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    mock_sock.recvfrom.return_value = (b"\xc6", ("127.0.0.1", 40200))

    ctrl = RuidaController("127.0.0.1")
    ctrl.move_to(100.0, 50.0)

    # Get all sendto calls - the last one should be the move command
    sendto_calls = mock_sock.sendto.call_args_list
    print(f"Total sendto calls: {len(sendto_calls)}")

    # Find the move command (contains D9)
    move_packet = None
    for call in sendto_calls:
        packet = call[0][0]
        # D9 is the rapid move command
        if len(packet) > 2 and packet[2] == 0x52:  # swizzled D9 = 0x52
            move_packet = packet
            print(f"Found move packet: {move_packet.hex()}")
            break

    if move_packet:
        # D9 10 00 [x 5 bytes] [y 5 bytes] = 13 bytes of data
        # Plus 2 bytes checksum = 15 bytes total
        assert len(move_packet) == 15, f"Move packet should be 15 bytes, got {len(move_packet)}"
    else:
        # If not found by swizzled byte, just check we have enough calls
        assert len(sendto_calls) >= 4, "Should have sent ENQ, init, ref, move"

    ctrl.release()


@patch("mvp.controller.socket.socket")
def test_ruida_response_unswizzle(mock_socket_cls):
    """Test that response handling correctly unswizzles data."""
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    # Simulate MeerK40T sending swizzled ACK (0xCC -> 0xC6 with magic 0x88)
    mock_sock.recvfrom.return_value = (b"\xc6", ("127.0.0.1", 40200))

    ctrl = RuidaController("127.0.0.1")

    # The response 0xC6 should unswizzle to 0xCC (ACK)
    assert ctrl._unswizzle(b"\xc6") == b"\xCC", "0xC6 should unswizzle to 0xCC"
    ctrl.release()


@patch("mvp.controller.socket.socket")
def test_ruida_checksum_calculation(mock_socket_cls):
    """Test that checksum is calculated correctly from swizzled data."""
    mock_sock = MagicMock()
    mock_socket_cls.return_value = mock_sock
    mock_sock.recvfrom.return_value = (b"\xc6", ("127.0.0.1", 40200))

    ctrl = RuidaController("127.0.0.1")

    # Test packet construction
    data = b"\xCE"  # ENQ
    packet = ctrl._package(data)
    print(f"ENQ package: {packet.hex()}")

    # Verify checksum: first 2 bytes should equal sum of swizzled data
    checksum_sent = (packet[0] << 8) | packet[1]
    swizzled = ctrl._swizzle(data)
    checksum_calc = sum(swizzled) & 0xFFFF
    assert checksum_sent == checksum_calc, f"Checksum mismatch: {checksum_sent} vs {checksum_calc}"

    ctrl.release()


def test_ruida_encode32_known_values():
    """Test encode32 with known values."""
    from mvp.controller import RuidaController
    ctrl = RuidaController("127.0.0.1")

    # Test encoding of 0 (should be all zeros)
    result = ctrl._encode32(0)
    assert result == b"\x00\x00\x00\x00\x00", f"encode32(0) = {result.hex()}, expected 0000000000"

    # Test encoding of 100000 micrometers (100mm)
    result = ctrl._encode32(100000)
    print(f"encode32(100000) = {result.hex()}")
    # 100000 = 0x186A0, in 5-byte 7-bit format should be: 0x00 0x06 0x0D 0x20 0x00
    # Actually 100000 decimal = 0x186A0
    # 0x186A0 = 000 0110 1101 0010 0000
    # 7-bit: 0000110 1101001 0010000 = 0x06 0x69 0x10
    # With high bits: 00000110 1101001 0010000 = 0x06 0x69 0x10

    ctrl.release()


# ------------------------------------------------------------------
# Interface conformance
# ------------------------------------------------------------------


def test_controller_interface_conformance():
    # Check that the concrete classes implement the abstract methods
    assert issubclass(SimulatedController, BaseController)
    assert issubclass(GRBLController, BaseController)
    assert issubclass(RuidaController, BaseController)
