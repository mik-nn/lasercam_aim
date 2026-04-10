# mvp/plugins/verify_servers.py
"""Quick verification that LaserCam HTTP servers are running."""
import sys
import urllib.request
import json

ports = [("Laser", 8080), ("Camera", 8081)]
ok = True
for name, port in ports:
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health")
        data = json.loads(resp.read())
        if data.get("status") == "ok":
            print(f"  {name} Emulator (port {port}): RUNNING")
        else:
            print(f"  {name} Emulator (port {port}): UNEXPECTED RESPONSE")
            ok = False
    except Exception as e:
        print(f"  {name} Emulator (port {port}): NOT RUNNING ({e})")
        ok = False

if not ok:
    print()
    print("WARNING: Some servers failed to start.")
    print("Check the new console windows for errors.")
    sys.exit(1)
