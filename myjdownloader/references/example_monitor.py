"""
Beispiel: Links hinzufügen und Download-Status überwachen
"""
import time
import myjdapi

# --- Verbindung ---
jd = myjdapi.Myjdapi()
jd.set_app_key("BigServerScript")
jd.connect("deine@email.de", "dein_passwort")
device = jd.get_device("BigServer")

# --- Links hinzufügen ---
device.linkgrabberv2.add_links([{
    "autostart": True,
    "links": "https://example.com/video.mkv",
    "packageName": "Test-Download",
    "destinationFolder": "/mnt/user/downloads/",
}])
print("Link hinzugefügt.")
time.sleep(3)  # kurz warten bis Crawler fertig

# --- Status-Loop ---
try:
    while True:
        packages = device.downloads.query_packages([{
            "name": True,
            "bytesLoaded": True,
            "bytesTotal": True,
            "percent": True,
            "status": True,
            "finished": True,
            "speed": True,
            "eta": True,
        }])

        if not packages:
            print("Keine aktiven Downloads.")
        else:
            for pkg in packages:
                name = pkg.get("name", "?")
                pct = pkg.get("percent", 0)
                speed_bps = pkg.get("speed", 0)
                speed_mb = speed_bps / 1_000_000
                eta = pkg.get("eta", -1)
                status = pkg.get("status", "")
                finished = pkg.get("finished", False)

                if finished:
                    print(f"✅ {name} — fertig")
                else:
                    print(f"⬇️  {name} — {pct:.1f}% @ {speed_mb:.2f} MB/s  ETA: {eta}s  [{status}]")

        time.sleep(5)

except KeyboardInterrupt:
    print("\nBeendet.")
finally:
    jd.disconnect()
