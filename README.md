# claude-skills

Eine Sammlung von Skills für [Claude Code](https://claude.ai/code) — erweiterbare Wissenspakete, die Claude beibringen, wie man mit bestimmten Tools, APIs und Projekten umgeht.

---

## Was sind Skills?

Skills sind Wissenspakete (`.skill`-Dateien), die Claude Code geladen werden. Sie enthalten strukturierte Dokumentation, Code-Beispiele und Best Practices zu einem bestimmten Thema. Sobald ein Skill installiert ist, erkennt Claude Code automatisch, wann er relevant ist, und zieht das entsprechende Wissen heran — ohne dass man es jedes Mal neu erklären muss.

---

## Installation

### Einzelnen Skill installieren (direkt aus GitHub)

```bash
claude skill install https://github.com/hoktaar/claude-skills/tree/main/myjdownloader
claude skill install https://github.com/hoktaar/claude-skills/tree/main/quasarr
```

### Aus heruntergeladener `.skill`-Datei installieren

```bash
claude skill install myjdownloader.skill
claude skill install quasarr.skill
```

### Alle installierten Skills anzeigen

```bash
claude skill list
```

### Skill deinstallieren

```bash
claude skill uninstall myjdownloader
claude skill uninstall quasarr
```

---

## Skills in dieser Sammlung

### 🔽 myjdownloader

**Steuere JDownloader über die myJDownloader API mit Python.**

Der Skill deckt die komplette [`myjdapi`](https://pypi.org/project/myjdapi/)-Bibliothek ab, die das AES128CBC/HMAC-SHA256-Verschlüsselungsprotokoll der MyJDownloader API automatisch übernimmt. Kein manuelles Krypto nötig.

| | |
|---|---|
| **Installieren** | `claude skill install https://github.com/hoktaar/claude-skills/tree/main/myjdownloader` |
| **Abhängigkeit** | `pip install myjdapi` |
| **Benötigt** | JDownloader 2 mit aktivem my.jdownloader.org Account |

**Was der Skill kann:**
- Cloud-Verbindung via my.jdownloader.org + Direktverbindung im LAN
- Links hinzufügen (autostart, Passwörter, Zielordner, Priorität)
- Download starten / stoppen / pausieren, Speed abfragen
- Download-Queue abfragen (Pakete & Links mit Status, Prozent, ETA)
- Queue verwalten: entfernen, umbenennen, Verzeichnis ändern, erzwingen, priorisieren
- Link Grabber verwalten
- Premium-Accounts verwalten
- System-Steuerung (JDownloader neu starten etc.)
- Fehlerbehandlung & generischer API-Rohr-Fallback

**Beispiel:**

```python
import myjdapi

jd = myjdapi.Myjdapi()
jd.set_app_key("MeinScript")
jd.connect("email@example.com", "passwort")
device = jd.get_device("BigServer")

device.linkgrabberv2.add_links([{
    "autostart": True,
    "links": "https://example.com/datei.zip",
    "packageName": "Mein Download",
    "destinationFolder": "/mnt/user/downloads/",
}])
```

---

### 🔀 quasarr

**Setup, Konfiguration und Debugging von Quasarr.**

[Quasarr](https://github.com/rix1337/Quasarr) verbindet JDownloader mit Radarr, Sonarr und LazyLibrarian. Es täuscht einen Newznab-Indexer und einen SABnzbd-Client vor, scrapt intern deutsche Hoster-Seiten und schickt gefundene Links via MyJDownloader an JDownloader weiter. Zusätzlich kann es CAPTCHA-geschützte Links entschlüsseln.

| | |
|---|---|
| **Installieren** | `claude skill install https://github.com/hoktaar/claude-skills/tree/main/quasarr` |
| **Docker Image** | `ghcr.io/rix1337/quasarr:latest` |
| **Benötigt** | JDownloader 2 (mit MyJD-Account), FlareSolverr (optional, aber empfohlen) |

**Was der Skill kann:**
- Komplette Architektur erklären (Newznab + SABnzbd-Fake → JDownloader)
- Docker-Deployment aufsetzen (inkl. Unraid-Setup)
- Radarr / Sonarr / LazyLibrarian konfigurieren
- Alle 19 Quellen-Kürzel (mit Login-Anforderungen) dokumentieren
- CAPTCHA-Handling erklären (manuell + SponsorsHelper)
- Alle internen API-Endpunkte referenzieren
- Download- & Such-Kategorien verwalten
- Discord/Telegram-Benachrichtigungen einrichten
- Häufige Probleme diagnostizieren und lösen

**Schnellstart (Docker):**

```yaml
services:
  quasarr:
    container_name: 'Quasarr'
    image: 'ghcr.io/rix1337/quasarr:latest'
    ports:
      - '8080:8080'
    volumes:
      - '/pfad/zu/config:/config:rw'
    environment:
      - 'DOCKER=true'
      - 'INTERNAL_ADDRESS=http://192.168.1.x:8080'
      - 'AUTH=form'
      - 'USER=admin'
      - 'PASS=passwort'
      - 'TZ=Europe/Berlin'
```

---

## Repo-Struktur

```
claude-skills/
├── README.md
├── myjdownloader/
│   ├── SKILL.md                        # Hauptdokumentation
│   └── references/
│       └── example_monitor.py          # Beispiel: Links hinzufügen & Status pollen
└── quasarr/
    ├── SKILL.md                        # Hauptdokumentation
    └── references/
        └── docker-compose-full.yml     # Vollständiges Docker-Compose-Beispiel
```

---

## Eigene Skills erstellen

Skills können mit dem integrierten `skill-creator` in Claude Code erstellt werden:

1. Claude Code öffnen
2. Beschreiben, was der Skill können soll
3. Claude erstellt `SKILL.md` + optionale Referenz-Dateien
4. Mit `python package_skill.py <ordner>` als `.skill` paketieren
5. Installieren mit `claude skill install <datei>`

Mehr Infos: [Claude Code Dokumentation](https://docs.claude.ai)

---

## Lizenz

MIT
