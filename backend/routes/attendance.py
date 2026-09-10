import os
import subprocess
import sys
import time
import requests

BASE = "/content/agentx_qr_attendance"
os.chdir(BASE)

# Fix the broken line in app.py
path = os.path.join(BASE, "app.py")

with open(path, "r") as f:
    code = f.read()

code = code.replace(
    'session_id =\n    request.args.get("session")',
    'session_id = request.args.get("session")'
)

with open(path, "w") as f:
    f.write(code)

print("✅ Code fixed")

# Check syntax BEFORE starting Flask
result = subprocess.run(
    [sys.executable, "-m", "py_compile", "app.py"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("❌ There is still a Python error:")
    print(result.stderr)
else:
    print("✅ Python syntax is correct")

    # Stop old Flask
    subprocess.run(
        ["pkill", "-f", "python.*app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(2)

    # Start Flask
    log = open(
        os.path.join(BASE, "flask.log"),
        "w"
    )

    process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True
    )

    time.sleep(5)

    # Test server
    try:
        r = requests.get(
            "http://127.0.0.1:5000/health",
            timeout=10
        )

        print("\n" + "=" * 50)
        print("FLASK TEST")
        print("=" * 50)
        print("Status:", r.status_code)
        print("Response:", r.text)

        if r.status_code == 200:
            print("\n🎉 FLASK IS RUNNING CORRECTLY!")
            print("Now we can start the HTTPS tunnel.")
        else:
            print("\n❌ Flask responded incorrectly.")

    except Exception as e:

        print("\n❌ Flask still did not start.")
        print("\n--- FLASK LOG ---")

        try:
            print(
                open(
                    os.path.join(BASE, "flask.log")
                ).read()
            )
        except:
            pass



# ============================================================
# START CLOUDFLARE HTTPS TUNNEL
# ============================================================

import os
import re
import time
import subprocess
import requests

BASE = "/content/agentx_qr_attendance"
os.chdir(BASE)

print("Preparing Cloudflare HTTPS tunnel...")

# ------------------------------------------------------------
# 1. Download cloudflared if needed
# ------------------------------------------------------------

cloudflared = os.path.join(BASE, "cloudflared")

if not os.path.exists(cloudflared):

    print("Downloading cloudflared...")

    subprocess.run(
        [
            "wget",
            "-q",
            "-O",
            cloudflared,
            "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        ],
        check=True
    )

    os.chmod(cloudflared, 0o755)

print("✅ cloudflared ready")


# ------------------------------------------------------------
# 2. Start tunnel
# ------------------------------------------------------------

log_path = os.path.join(BASE, "cloudflare.log")

# Remove old log
open(log_path, "w").close()

log_file = open(log_path, "a")

cloudflare_process = subprocess.Popen(
    [
        cloudflared,
        "tunnel",
        "--url",
        "http://127.0.0.1:5000",
        "--no-autoupdate"
    ],
    stdout=log_file,
    stderr=subprocess.STDOUT,
    start_new_session=True
)

print("⏳ Waiting for Cloudflare URL...")


# ------------------------------------------------------------
# 3. Find URL
# ------------------------------------------------------------

live_url = None

for attempt in range(60):

    time.sleep(2)

    try:

        with open(log_path, "r") as f:
            log = f.read()

        urls = re.findall(
            r"https://[a-zA-Z0-9-]+\.trycloudflare\.com",
            log
        )

        if urls:

            candidate = urls[-1]

            # Verify that the URL actually reaches Flask
            try:

                response = requests.get(
                    candidate + "/health",
                    timeout=10
                )

                if response.status_code == 200:

                    live_url = candidate

                    break

            except Exception:
                pass

    except Exception:
        pass


# ------------------------------------------------------------
# 4. Display only VERIFIED URL
# ------------------------------------------------------------

print("\n" + "=" * 65)

if live_url:

    print("🎉 CLOUDFLARE HTTPS TUNNEL IS LIVE")
    print("=" * 65)

    print("\n🌐 MAIN URL:")
    print("\n" + live_url)

    print("\n👨‍🏫 MENTOR DASHBOARD:")
    print("\n" + live_url + "/mentor")

    print("\n❤️ HEALTH CHECK:")
    print("\n" + live_url + "/health")

    print("\n" + "=" * 65)
    print("QR + GPS FLOW")
    print("=" * 65)

    print("""
1. Open Mentor Dashboard on computer:
      /mentor

2. Click:
      📍 GET GPS + GENERATE QR

3. Allow mentor GPS.

4. QR code will appear.

5. Student scans QR using phone camera.

6. Student enters:
      STU001

7. Student clicks:
      📍 ALLOW GPS & MARK ATTENDANCE

8. Student allows GPS.

9. Server calculates distance.

10. If within 100 meters:
      ✅ PRESENT

11. Mentor screen automatically shows:
      Student ID
      Student Name
      Distance
      Time
      PRESENT
""")

    print("=" * 65)
    print("⚠️ IMPORTANT")
    print("=" * 65)

    print("""
KEEP THIS COLAB RUNTIME RUNNING.

DO NOT CLOSE/STOP THE RUNTIME.

DO NOT use an old trycloudflare URL.

Use ONLY the NEW VERIFIED URL printed above.
""")

else:

    print("❌ Could not create a verified HTTPS tunnel.")

    print("\nCloudflare log:")
    print("=" * 65)

    try:
        print(open(log_path).read())
    except:
        pass

