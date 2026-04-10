# bridge.py
"""
LightBurn Bridge — sends Alt+1 and Alt+2 hotkeys to LightBurn.

On Windows, uses pyautogui to send keystrokes to the LightBurn window.
For development without LightBurn, a fake bridge simulates the same interface.

AICODE-NOTE: This module is the bridge between LaserCam and LightBurn's
Print&Cut workflow. Alt+1 registers M1, Alt+2 registers M2.
"""
import platform
import time


class LightBurnBridge:
    """Base interface for LightBurn hotkey injection."""

    def __init__(self):
        self.state = "idle"

    def send_alt_1(self) -> bool:
        """Send Alt+1 to LightBurn to register M1. Returns True on success."""
        raise NotImplementedError

    def send_alt_2(self) -> bool:
        """Send Alt+2 to LightBurn to register M2. Returns True on success."""
        raise NotImplementedError

    def focus_lightburn(self) -> bool:
        """Bring the LightBurn window to the foreground."""
        raise NotImplementedError


class RealLightBurnBridge(LightBurnBridge):
    """
    WinAPI-based hotkey injection into LightBurn.

    Uses win32gui to find the LightBurn window and pyautogui
    to send Alt+1 / Alt+2 keystrokes.
    """

    _WINDOW_TITLES = ["LightBurn", "LightBurn "]

    def __init__(self):
        super().__init__()
        import win32gui
        import win32con

        self._win32gui = win32gui
        self._win32con = win32con
        self._hwnd = None
        self._find_window()

    def _find_window(self) -> bool:
        """Find the LightBurn window by title."""
        for title in self._WINDOW_TITLES:
            hwnd = self._win32gui.FindWindow(None, title)
            if hwnd:
                self._hwnd = hwnd
                return True
        # Try partial match via EnumWindows

        def enum_callback(hwnd, _):
            try:
                wtitle = self._win32gui.GetWindowText(hwnd)
                if "LightBurn" in wtitle and self._win32gui.IsWindowVisible(hwnd):
                    self._hwnd = hwnd
                    return False
            except Exception:
                pass
            return True
        self._win32gui.EnumWindows(enum_callback, None)
        return self._hwnd is not None

    def focus_lightburn(self) -> bool:
        """Bring the LightBurn window to the foreground."""
        if self._hwnd is None:
            self._find_window()
        if self._hwnd is None:
            print("LightBurnBridge: LightBurn window not found")
            return False
        try:
            # Try to restore if minimized
            if self._win32gui.IsIconic(self._hwnd):
                self._win32gui.ShowWindow(self._hwnd, self._win32con.SW_RESTORE)
            # Set foreground window
            self._win32gui.SetForegroundWindow(self._hwnd)
            # Small delay to ensure window is focused
            time.sleep(0.3)
            return True
        except Exception as e:
            print(f"LightBurnBridge: Failed to focus LightBurn: {e}")
            return False

    def _send_hotkey(self, modifiers: list, key: str) -> None:
        """Send a hotkey combination using pyautogui."""
        import pyautogui

        # pyautogui.hotkey sends keys sequentially with proper timing
        pyautogui.hotkey(*modifiers, key, interval=0.15)

    def send_alt_1(self) -> bool:
        """Send Alt+1 to LightBurn to register M1."""
        if not self.focus_lightburn():
            return False
        self._send_hotkey(["alt"], "1")
        self.state = "m1_registered"
        print("LightBurnBridge: Sent Alt+1 to LightBurn (register M1)")
        return True

    def send_alt_2(self) -> bool:
        """Send Alt+2 to LightBurn to register M2."""
        if not self.focus_lightburn():
            return False
        self._send_hotkey(["alt"], "2")
        self.state = "m2_registered"
        print("LightBurnBridge: Sent Alt+2 to LightBurn (register M2)")
        return True


class FakeLightBurnBridge(LightBurnBridge):
    """
    Fake bridge for development without LightBurn.
    Simulates Alt+1 / Alt+2 via method calls.
    """

    def __init__(self):
        super().__init__()
        print("Using FakeLightBurnBridge. Call send_alt_1() / send_alt_2() directly.")

    def focus_lightburn(self) -> bool:
        print("FakeLightBurnBridge: LightBurn focus simulated")
        return True

    def send_alt_1(self) -> bool:
        print("FakeLightBurnBridge: Alt+1 simulated (register M1)")
        self.state = "m1_registered"
        return True

    def send_alt_2(self) -> bool:
        print("FakeLightBurnBridge: Alt+2 simulated (register M2)")
        self.state = "m2_registered"
        return True


def get_bridge():
    """Factory function to get the correct bridge for the current OS."""
    if platform.system() == "Windows":
        try:
            return RealLightBurnBridge()
        except ImportError:
            print("win32gui not found. Using FakeLightBurnBridge.")
            return FakeLightBurnBridge()
    else:
        print(f"Non-Windows platform ({platform.system()}). Using FakeLightBurnBridge.")
        return FakeLightBurnBridge()
