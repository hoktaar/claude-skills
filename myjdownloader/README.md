# myjdownloader Skill

Steuere JDownloader über die [myJDownloader API](https://my.jdownloader.org/developers/index.html) mit Python. Der Skill nutzt die [`myjdapi`](https://pypi.org/project/myjdapi/)-Bibliothek, die das komplette AES128CBC/HMAC-SHA256-Verschlüsselungsprotokoll automatisch übernimmt.

## Installation

```bash
claude skill install https://github.com/hoktaar/claude-skills/tree/main/myjdownloader
```

## Voraussetzungen

- JDownloader 2 läuft und ist mit [my.jdownloader.org](https://my.jdownloader.org) verbunden
- Python-Abhängigkeit:

```bash
pip install myjdapi
```

## Schnellstart

```python
import myjdapi

jd = myjdapi.Myjdapi()
jd.set_app_key("MeinScript")
jd.connect("email@example.com", "passwort")
device = jd.get_device("BigServer")

# Link hinzufügen
device.linkgrabberv2.add_links([{
    "autostart": True,
    "links": "https://example.com/datei.zip",
    "packageName": "Mein Download",
    "destinationFolder": "/mnt/user/downloads/",
}])

# Downloads starten/stoppen
device.downloadcontroller.start_downloads()
device.downloadcontroller.stop_downloads()

# Queue abfragen
packages = device.downloads.query_packages([{
    "name": True, "percent": True, "status": True, "finished": True
}])
```

## Verbindungsarten

**Cloud (via my.jdownloader.org)** — funktioniert überall, JDownloader muss nur online sein:
```python
jd = myjdapi.Myjdapi()
jd.set_app_key("MeinScript")
jd.connect("email@example.com", "passwort")
device = jd.get_device("BigServer")
```

**Direkt im LAN** — kein Cloud-Relay, JDownloader muss "Deprecated API" aktiviert haben:
```python
jd = myjdapi.Myjdapi()
jd.connect_device("192.168.1.144", 3128, timeout=10)
device = jd.get_device()
```

## Was der Skill abdeckt

- Links hinzufügen mit allen Optionen (autostart, Passwörter, Zielordner, Priorität)
- Download starten / stoppen / pausieren / Speed abfragen
- Download-Queue abfragen (Pakete & Links mit Status, Prozent, ETA)
- Queue verwalten: entfernen, umbenennen, Verzeichnis ändern, erzwingen, priorisieren
- Link Grabber verwalten & in Download-Liste verschieben
- Premium-Accounts (Hoster) verwalten
- System-Steuerung (JDownloader neu starten etc.)
- Fehlerbehandlung (Token abgelaufen, Offline, Auth-Fehler)
- Generischer API-Rohr-Fallback für nicht direkt unterstützte Methoden

## Referenz-Dateien

| Datei | Beschreibung |
|-------|-------------|
| `references/example_monitor.py` | Komplettes Beispiel: Link hinzufügen und Download-Status live pollen |

## Links

- [myJDownloader API Docs](https://my.jdownloader.org/developers/index.html)
- [myjdapi auf PyPI](https://pypi.org/project/myjdapi/)
- [myjdapi GitHub](https://github.com/mmarquezs/My.Jdownloader-API-Python-Library)
