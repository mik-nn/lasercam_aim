"""
Test Ruida controller communication with MeerK40T.
"""
import sys
import socket
sys.path.insert(0, '.')

from mvp.controller import RuidaController

print("=== Ruida Controller Test ===")

# Create controller
try:
    ctrl = RuidaController(
        host="127.0.0.1",
        port=50200,
        listen_port=40200,
        timeout=2.0,
        retries=3,
    )
    print("Controller created successfully")
except Exception as e:
    print(f"Failed to create controller: {e}")
    sys.exit(1)

# Test move commands
print("\n=== Move Commands Test ===")
print("Moving to (10, 10) mm...")
ctrl.move_to(10.0, 10.0)
print(f"Position after move_to(10, 10): {ctrl.position}")

print("\nMoving by (5, -3) mm...")
ctrl.move_by(5.0, -3.0)
print(f"Position after move_by(5, -3): {ctrl.position}")

print("\nMoving to (0, 0) mm...")
ctrl.move_to(0.0, 0.0)
print(f"Position after move_to(0, 0): {ctrl.position}")

# Test position query
print("\n=== Position Query Test ===")
print("Querying position from controller...")
try:
    pos = ctrl._sync_position()
    print(f"Queried position: {pos}")
except Exception as e:
    print(f"Position query failed: {e}")

# Cleanup
ctrl.release()
print("\n=== Test Complete ===")
