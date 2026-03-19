# quasarr Skill

Setup, Konfiguration und Debugging von [Quasarr](https://github.com/rix1337/Quasarr) — der Brücke zwischen JDownloader und Radarr/Sonarr/LazyLibrarian. Quasarr täuscht einen Newznab-Indexer und einen SABnzbd-Client vor, scrapt intern deutsche Hoster-Seiten und schickt die gefundenen Links via MyJDownloader an JDownloader weiter.

```
Radarr/Sonarr  ←→  Quasarr (Newznab + SABnzbd)  ←→  JDownloader (via MyJD API)
                            ↕
                     Scraper-Quellen (Hoster-Sites)
                            ↕
                     FlareSolverr (für Cloudflare-Sites)
```

## Installation

```bash
claude skill install https://github.com/hoktaar/claude-skills/tree/main/quasarr
```

## Voraussetzungen

- JDownloader 2 läuft und ist mit [my.jdownloader.org](https://my.jdownloader.org) verbunden
- [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) (empfohlen, für Cloudflare-geschützte Seiten)

## Schnellstart (Docker)

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

Vollständiges Beispiel mit FlareSolverr und SponsorsHelper: siehe [`references/docker-compose-full.yml`](references/docker-compose-full.yml)

## Radarr / Sonarr konfigurieren

**Als Newznab-Indexer:**
- URL: `http://<INTERNAL_ADDRESS>`
- API Key: aus dem Quasarr Web-UI

**Als SABnzbd-Download-Client:**
- Host + Port aus `INTERNAL_ADDRESS`
- API Key: gleicher Key

> ⚠️ Sonarr: Serientyp aller Serien auf **Standard** setzen. Anime/Absolut wird nicht unterstützt.

## Was der Skill abdeckt

- Komplette Architektur & Funktionsweise
- Docker-Deployment (inkl. Unraid-spezifisches Setup)
- Alle 19 Quellen-Kürzel mit Login-Anforderungen
- Radarr / Sonarr / LazyLibrarian Konfiguration
- FlareSolverr-Integration
- CAPTCHA-Handling (manuell + SponsorsHelper für Sponsoren)
- Alle internen API-Endpunkte (`/api?t=...`, `/api?mode=...`)
- Download- & Such-Kategorien verwalten
- Discord / Telegram Benachrichtigungen
- Timeout / Slow-Mode Konfiguration
- Häufige Probleme & Lösungen

## Unterstützte Quellen

| Kürzel | Login | Kürzel | Login |
|--------|-------|--------|-------|
| `al`   | ✅ (+ FlareSolverr) | `nk` | ❌ |
| `at`   | ❌ | `nx` | ✅ |
| `by`   | ❌ | `rm` | ❌ |
| `dd`   | ✅ | `sf` | ❌ |
| `dj`   | ✅ | `sj` | ✅ |
| `dl`   | ✅ | `sl` | ❌ |
| `dt`   | ❌ | `wd` | ❌ |
| `dw`   | ❌ | `wx` | ❌ |
| `he`   | ❌ | | |
| `hs`   | ❌ | | |
| `mb`   | ❌ | | |

## Referenz-Dateien

| Datei | Beschreibung |
|-------|-------------|
| `references/docker-compose-full.yml` | Vollständiges Docker-Compose mit FlareSolverr + optionalem SponsorsHelper |

## Links

- [Quasarr GitHub](https://github.com/rix1337/Quasarr)
- [FlareSolverr GitHub](https://github.com/FlareSolverr/FlareSolverr)
- [my.jdownloader.org](https://my.jdownloader.org)
