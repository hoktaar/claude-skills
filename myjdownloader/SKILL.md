---
name: myjdownloader
description: Control JDownloader via the myJDownloader API using Python. Use this skill whenever the user wants to interact with JDownloader programmatically — adding links, controlling downloads, querying the download queue, managing packages, starting/stopping downloads, or building scripts/tools around JDownloader. Trigger on any mention of "JDownloader", "myjdownloader", "JD API", "jdapi", or tasks like "Links zu JDownloader hinzufügen", "Download starten", "JDownloader steuern", "JDownloader Script".
---

# myJDownloader API Skill

Die `myjdapi`-Bibliothek übernimmt die komplette AES128CBC/HMAC-SHA256-Verschlüsselung automatisch.

## Setup

```bash
pip install myjdapi --break-system-packages
```

**Abhängigkeiten (werden automatisch mitinstalliert):** `pycryptodome`, `requests`

---

## Verbindungsarten

### 1. Cloud-Verbindung (via my.jdownloader.org)
Funktioniert überall — JDownloader muss nur online und mit dem Account verbunden sein.

```python
import myjdapi

jd = myjdapi.Myjdapi()
jd.set_app_key("MEIN_APP_KEY")   # beliebiger String, z.B. "MyScript"
jd.connect("email@example.com", "password")

# Alle verbundenen Geräte auflisten
devices = jd.list_devices()
print(devices)

# Gerät ansprechen (per Name oder ID)
device = jd.get_device("BigServer")  # oder get_device(device_id="...")
```

### 2. Direkte Verbindung (LAN, kein Cloud-Relay)
JDownloader muss in den Advanced Options die "Deprecated API" aktiviert haben.

```python
jd = myjdapi.Myjdapi()
jd.connect_device("192.168.1.144", 3128, timeout=10)
device = jd.get_device()  # einziges Gerät bei Direktverbindung
```

---

## Häufige Operationen

### Links hinzufügen (Link Grabber)

```python
device.linkgrabberv2.add_links([{
    "autostart": False,              # True = sofort starten
    "links": "https://example.com/file.zip",
    "packageName": "Mein Paket",
    "destinationFolder": "/mnt/user/downloads/",
    "extractPassword": "",
    "downloadPassword": "",
    "priority": "DEFAULT",           # DEFAULT, LOWER, LOW, HIGH, HIGHEST
}])
```

Mehrere Links auf einmal (kommasepariert oder Liste):
```python
device.linkgrabberv2.add_links([{
    "autostart": True,
    "links": "https://site.com/a.zip\nhttps://site.com/b.zip",
    "packageName": "Batch",
}])
```

### Download starten/stoppen/pausieren

```python
device.downloadcontroller.start_downloads()
device.downloadcontroller.stop_downloads()
device.downloadcontroller.pause_downloads(True)   # True = pausieren, False = fortsetzen
speed = device.downloadcontroller.get_speed_in_bps()
state = device.downloadcontroller.get_current_state()  # RUNNING, STOPPED, PAUSE
```

### Download-Queue abfragen

```python
# Pakete abfragen
packages = device.downloads.query_packages([{
    "bytesLoaded": True,
    "bytesTotal": True,
    "comment": True,
    "enabled": True,
    "eta": True,
    "finished": True,
    "hosts": True,
    "name": True,
    "percent": True,
    "running": True,
    "saveTo": True,
    "speed": True,
    "status": True,
    "uuid": True,
}])

# Einzelne Links abfragen
links = device.downloads.query_links([{
    "bytesLoaded": True,
    "bytesTotal": True,
    "comment": True,
    "enabled": True,
    "eta": True,
    "name": True,
    "packageUUID": True,
    "percent": True,
    "priority": True,
    "running": True,
    "speed": True,
    "status": True,
    "url": True,
    "uuid": True,
}])
```

### Links/Pakete verwalten

```python
pkg_ids = [pkg["uuid"] for pkg in packages]
link_ids = [lnk["uuid"] for lnk in links]

# Entfernen (abgeschlossene aufräumen)
device.downloadsv2.remove_links(link_ids=[], package_ids=pkg_ids)

# Erzwingen (Force-Download, überspringt Queue-Limits)
device.downloadsv2.force_download(link_ids=link_ids, package_ids=[])

# Umbenennen
device.downloadsv2.rename_package(package_id=pkg_ids[0], new_name="Neuer Name")

# Download-Verzeichnis ändern
device.downloadsv2.set_download_directory("/mnt/user/downloads/neu/", package_ids=pkg_ids)

# Aktivieren/Deaktivieren
device.downloadsv2.set_enabled(True, link_ids=link_ids, package_ids=[])

# Priorität setzen
device.downloadsv2.set_priority("HIGH", link_ids=link_ids, package_ids=[])
# Mögliche Werte: HIGHEST, HIGHER, HIGH, DEFAULT, LOW, LOWER, LOWEST
```

### Link Grabber (Warteschlange vor dem Download)

```python
# Pakete in Link-Grabber anzeigen
lg_packages = device.linkgrabberv2.query_packages([{"name": True, "uuid": True}])
lg_link_ids = [...]
lg_pkg_ids = [...]

# In Download-Liste verschieben (startet den Download)
device.linkgrabberv2.move_to_downloadlist(link_ids=lg_link_ids, package_ids=lg_pkg_ids)

# Löschen
device.linkgrabberv2.remove_links(link_ids=lg_link_ids, package_ids=lg_pkg_ids)

# Liste leeren
device.linkgrabberv2.clear_list()
```

### System

```python
device.jd.get_core_revision()
device.system.get_system_infos()
device.system.exit_jd()
device.system.restart_jd()

# Speicherinfo
device.system.get_storage_infos("/mnt/user/downloads/")
```

### Accounts (Premium-Hoster)

```python
# Alle Accounts auflisten
accounts = device.accountsv2.list_accounts([{"enabled": True, "hoster": True, "username": True}])

# Account hinzufügen
device.accountsv2.add_account("mega.nz", "user@mail.com", "password123")

# Account entfernen
device.accountsv2.remove_accounts(ids=[account_id])
```

---

## Namespaces & verfügbare Module

| Namespace | Zugriff | Zweck |
|-----------|---------|-------|
| `/downloadcontroller` | `device.downloadcontroller` | Start/Stop/Pause/Speed |
| `/downloads` | `device.downloads` | Queue abfragen (v1) |
| `/downloadsV2` | `device.downloadsv2` | Queue verwalten (v2, bevorzugt) |
| `/linkgrabberv2` | `device.linkgrabberv2` | Links hinzufügen/verwalten |
| `/accountsV2` | `device.accountsv2` | Premium-Accounts |
| `/system` | `device.system` | JD/OS Steuerung |
| `/jd` | `device.jd` | Versioninfo, Plugins |
| `/config` | `device.config` | Einstellungen lesen/schreiben |
| `/extraction` | `device.extraction` | Archiv-Extraktion |
| `/events` | `device.events` | Event-Subscriptions |
| `/captcha` | `device.captcha` | Captcha-Handling |

---

## Vollständiges Beispiel: Link hinzufügen & Status pollen

Siehe `references/example_monitor.py`

---

## Fehlerbehandlung

```python
from myjdapi import exception

try:
    jd.connect("mail", "pass")
    device = jd.get_device("BigServer")
    device.downloadcontroller.start_downloads()
except exception.MYJDConnectionException as e:
    print(f"Verbindungsfehler: {e}")
except exception.MYJDDecodeException as e:
    print(f"Decode-Fehler (falsches Passwort?): {e}")
except Exception as e:
    print(f"Unbekannter Fehler: {e}")
```

Häufige Fehler:
- `TOKEN_INVALID` → Session abgelaufen, `jd.reconnect()` aufrufen
- `OFFLINE` → JDownloader-Client läuft nicht / hat keine Verbindung
- `AUTH_FAILED` → Falsches Passwort / E-Mail
- `BAD_PARAMETERS` → Falsche Parameternamen (Groß-/Kleinschreibung beachten!)

---

## Direktes API-Rohr (generisch)

Wenn eine Methode in `myjdapi` fehlt, kann man rohe API-Calls absetzen:

```python
# Beliebigen Namespace/Methode aufrufen
result = device.action("/downloadsV2/queryPackages", params=[{"name": True, "uuid": True}])
```

---

## Hinweise für BigServer (Daniels Setup)

- JDownloader läuft als Docker/App auf BigServer (192.168.1.144)
- Für Direktverbindung im LAN: Deprecated API in JD aktivieren → Advanced Options → `org.jdownloader.api.RemoteAPIConfig` → Port 3128
- Für Cloud-Verbindung: my.jdownloader.org Account in JD eingeloggt lassen
- App-Key kann ein beliebiger String sein (z.B. `"BigServerScript"`)
