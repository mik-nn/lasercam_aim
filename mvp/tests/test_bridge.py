from unittest.mock import MagicMock, patch

import pytest

from mvp.bridge import FakeLightBurnBridge, LightBurnBridge, get_bridge


def test_lightburn_bridge_init():
    bridge = LightBurnBridge()
    assert bridge.state == "idle"


def test_fake_lightburn_bridge_init():
    bridge = FakeLightBurnBridge()
    assert bridge.state == "idle"


@patch("sys.stdin")
@patch("select.select")
def test_fake_bridge_hotkey_detected(mock_select, mock_stdin):
    bridge = FakeLightBurnBridge()

    # Mock select to return stdin ready
    mock_select.return_value = ([mock_stdin], [], [])
    # Mock stdin to return '1'
    mock_stdin.readline.return_value = "1\n"

    assert bridge.check_for_hotkey() is True


@patch("sys.stdin")
@patch("select.select")
def test_fake_bridge_hotkey_not_detected(mock_select, mock_stdin):
    bridge = FakeLightBurnBridge()

    # Mock select to return nothing
    mock_select.return_value = ([], [], [])

    assert bridge.check_for_hotkey() is False


def test_get_bridge():
    bridge = get_bridge()
    # On linux this should be FakeLightBurnBridge
    assert isinstance(bridge, FakeLightBurnBridge)
