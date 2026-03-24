# bridge.py
import platform
import sys


class LightBurnBridge:
    def __init__(self):
        self.state = "idle"

    def check_for_hotkey(self):
        # Placeholder for hotkey detection
        pass


class FakeLightBurnBridge:
    def __init__(self):
        self.state = "idle"
        print("Using FakeLightBurnBridge. Press '1' to simulate Alt+F1.")

    def check_for_hotkey(self):
        """
        Checks for hotkey simulation from stdin.
        Returns True if the hotkey was pressed.
        """
        import select

        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            if "1" in line:
                print("Alt+F1 simulated.")
                return True
        return False


def get_bridge():
    """Factory function to get the correct bridge for the current OS."""
    if platform.system() == "Windows":
        # On Windows, you would try to import win32gui and create a real bridge
        try:
            import win32gui

            # return RealLightBurnBridge()
            print("RealLightBurnBridge not implemented yet, using fake one.")
            return FakeLightBurnBridge()
        except ImportError:
            print("win32gui not found. Using FakeLightBurnBridge.")
            return FakeLightBurnBridge()
    else:
        return FakeLightBurnBridge()
