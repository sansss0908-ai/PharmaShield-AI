import subprocess
import sys
import time
import os
import re
import threading

BASE = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"

print("=" * 55)
print("   🧊 PharmaShield AI — One-Click Launcher")
print("=" * 55)

def start(name, cmd, cwd=BASE):
    def run():
        subprocess.Popen(cmd, cwd=cwd, shell=True,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    print(f"  ✅ {name} started")

# 1. Kill any old instances on these ports
os.system("for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :5002') do taskkill /PID %a /F >nul 2>&1")
os.system("for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :5000') do taskkill /PID %a /F >nul 2>&1")
os.system("for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :5001') do taskkill /PID %a /F >nul 2>&1")
time.sleep(1)

# 2. Start all backend servers
start("SAP Mock Server (port 5000)",  "python sap_mock/app.py")
time.sleep(1)
start("Live Data Server (port 5001)", "python dashboard/live_data_server.py")
time.sleep(1)
start("Hospital App Server (port 5002)", "python hospital_app_server/app.py")
time.sleep(2)

# 3. Start Cloudflare tunnel and capture the URL
print("\n  🌐 Starting Cloudflare public tunnel...")
tunnel_proc = subprocess.Popen(
    [CLOUDFLARED, "tunnel", "--url", "http://localhost:5002"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=BASE
)

public_url = None
for line in tunnel_proc.stdout:
    match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', line)
    if match:
        public_url = match.group(0)
        break

if public_url:
    print("\n" + "=" * 55)
    print(f"  📱 PHONE APP URL:")
    print(f"  👉  {public_url}")
    print("=" * 55)
    print("\n  Open this URL on your phone (any network — 4G/5G/Wi-Fi)")
    print("  In Chrome → tap ⋮ → 'Add to Home screen' to install.")
    print("\n  💡 Local Wi-Fi URL (always works on home network):")
    print("  👉  http://192.168.29.144:5002")
    print("\n  Press Ctrl+C to stop all servers.\n")

    # Save URL to file for reference
    with open(os.path.join(BASE, "current_public_url.txt"), "w") as f:
        f.write(public_url)

    # Keep tunnel alive
    try:
        tunnel_proc.wait()
    except KeyboardInterrupt:
        tunnel_proc.terminate()
        print("\n  Shutting down...")
else:
    print("  ⚠️  Could not get public URL. Check cloudflared is installed.")
    print("  Try running manually: cloudflared tunnel --url http://localhost:5002")
