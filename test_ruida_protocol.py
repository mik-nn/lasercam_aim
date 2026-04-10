"""
Test Ruida protocol implementation against MeerK40T's source code.
"""
import sys
sys.path.insert(0, '.')

from mvp.controller import RuidaController

# Test swizzle/unswizzle round-trip
print("=== Swizzle/Unswizzle Test ===")
magic = 0x88

# Test individual bytes
test_bytes = [0x00, 0x01, 0x88, 0x89, 0xCC, 0xCE, 0xFF]
for b in test_bytes:
    swizzled = RuidaController._swizzle_byte(None, b, magic)
    unswizzled = RuidaController._unswizzle_byte(None, swizzled, magic)
    print(f"  0x{b:02X} -> swizzle -> 0x{swizzled:02X} -> unswizzle -> 0x{unswizzled:02X} {'OK' if b == unswizzled else 'FAIL'}")

# Test encode/decode
print("\n=== Encode/Decode Test ===")
# Test absolute coordinate encoding (5 bytes, 7-bit per byte)
test_values = [0, 1000, 100000, 1000000]
for v in test_values:
    encoded = RuidaController._encode32(None, v)
    decoded = RuidaController._decode32(None, encoded)
    print(f"  {v} um -> encode -> {encoded.hex()} -> decode -> {decoded} um {'OK' if v == decoded else 'FAIL'}")

# Test relative coordinate encoding (2 bytes, 7-bit per byte)
print("\n=== Relative Coordinate Test ===")
test_rel = [0, 100, 1000, 5000]
for v in test_rel:
    encoded = RuidaController._encode14(None, v)
    # Decode manually
    decoded = (encoded[0] & 0x7F) << 7 | (encoded[1] & 0x7F)
    print(f"  {v} um -> encode -> {encoded.hex()} -> decode -> {decoded} um {'OK' if v == decoded else 'FAIL'}")

ctrl = RuidaController.__new__(RuidaController)
ctrl._magic = 0x88

# Test packet structure
print("\n=== Packet Structure Test ===")
# Create a test move command: 0x89 + relcoord(1000) + relcoord(-500)
cmd = RuidaController.MOVE_REL_XY + ctrl._encode_relcoord(1000) + ctrl._encode_relcoord(-500 & 0x3FFF)
print(f"  Command bytes: {cmd.hex()} ({len(cmd)} bytes)")
print(f"  Expected: 89 + 2 bytes dx + 2 bytes dy = 5 bytes")

# Test full packet
packet = ctrl._package(cmd)
print(f"  Full packet: {packet.hex()} ({len(packet)} bytes)")
print(f"  Expected: 2 bytes checksum + 5 bytes swizzled = 7 bytes")

# Verify checksum
swizzled = ctrl._swizzle(cmd)
expected_checksum = sum(swizzled) & 0xFFFF
actual_checksum = (packet[0] << 8) | packet[1]
print(f"  Checksum: expected 0x{expected_checksum:04X}, actual 0x{actual_checksum:04X} {'OK' if expected_checksum == actual_checksum else 'FAIL'}")
print(f"  Swizzled payload: {swizzled.hex()}")
print(f"  Packet payload: {packet[2:].hex()}")
print(f"  Payload match: {'OK' if swizzled == packet[2:] else 'FAIL'}")

print("\n=== Done ===")
