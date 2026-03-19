# stash Skill

[Stash](https://github.com/stashapp/stash) per GraphQL API steuern, automatisieren und erweitern. Stash ist eine selbst-gehostete Web-App zum Organisieren, Taggen und Streamen von Video- und Bildsammlungen.

## Installation

```bash
claude skill install https://github.com/hoktaar/claude-skills/tree/main/stash
```

## Voraussetzungen

- Stash läuft (Docker oder nativ) auf Port 9999
- Python mit `requests`: `pip install requests`

## Schnellstart

```python
from stash_api import StashAPI

stash = StashAPI("http://localhost:9999")

# Statistiken
s = stash.stats()
print(f"Szenen: {s['scene_count']}, Performer: {s['performer_count']}")

# Szenen suchen
result = stash.find_scenes(q="suchbegriff", per_page=10)

# Szene aktualisieren
stash.update_scene("42", rating100=80, organized=True, tag_ids=["1","2"])

# Bibliothek scannen
job_id = stash.scan()
```

## Was der Skill abdeckt

- Docker-Setup (Unraid/BigServer-optimiert)
- Vollständige GraphQL API Referenz (Queries & Mutations)
- Alle Kernentitäten: Scenes, Images, Galleries, Performers, Studios, Tags, Groups
- Jobs: Scan, Generate, Auto-Tag, Identify, Clean, Optimize
- Filter-System (Modifier, Sortierung, Paginierung)
- Scraping (StashDB, CommunityScrapers, URL-Scraping)
- Plugin-Entwicklung (Python & JavaScript) mit vollständigen Templates
- Alle verfügbaren Hook-Trigger
- Stash-Box / StashDB Integration

## Plugin-Entwicklung

Plugins liegen in `~/.stash/plugins/`. Jedes Plugin braucht eine `.yml`-Konfigurationsdatei und ein ausführbares Script (Python, JavaScript oder Go).

```yaml
# mein_plugin.yml
name: Mein Plugin
exec:
  - python
  - "{pluginDir}/mein_plugin.py"
interface: raw
tasks:
  - name: Aufgabe starten
    defaultArgs:
      mode: run
hooks:
  - name: Bei Scene-Update
    triggeredBy:
      - Scene.Update.Post
```

## Referenz-Dateien

| Datei | Beschreibung |
|-------|-------------|
| `references/stash_api.py` | Vollständige Python-Hilfsklasse für alle API-Operationen + Plugin-Logging |

## Links

- [Stash GitHub](https://github.com/stashapp/stash)
- [Dokumentation](https://docs.stashapp.cc)
- [In-App Manual](https://docs.stashapp.cc/in-app-manual) (auch per Shift+? im UI)
- [StashDB](https://stashdb.org)
- [CommunityScrapers](https://github.com/stashapp/CommunityScrapers)
- [Plugins](https://docs.stashapp.cc/plugins/)
- [Discord](https://discord.gg/2TsNFKt)
