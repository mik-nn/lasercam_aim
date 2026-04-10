from mvp.bridge import FakeLightBurnBridge, LightBurnBridge, get_bridge


def test_lightburn_bridge_init():
    bridge = LightBurnBridge()
    assert bridge.state == "idle"


def test_fake_lightburn_bridge_init():
    bridge = FakeLightBurnBridge()
    assert bridge.state == "idle"


def test_fake_bridge_send_alt_1():
    bridge = FakeLightBurnBridge()
    assert bridge.send_alt_1() is True
    assert bridge.state == "m1_registered"


def test_fake_bridge_send_alt_2():
    bridge = FakeLightBurnBridge()
    assert bridge.send_alt_2() is True
    assert bridge.state == "m2_registered"


def test_fake_bridge_focus():
    bridge = FakeLightBurnBridge()
    assert bridge.focus_lightburn() is True


def test_get_bridge():
    bridge = get_bridge()
    # On Windows with win32gui, this returns RealLightBurnBridge
    # On other platforms or without win32gui, returns FakeLightBurnBridge
    assert isinstance(bridge, LightBurnBridge)
