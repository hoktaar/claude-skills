---
name: stash
description: Stash — selbst-gehosteter Medien-Manager — per GraphQL API steuern, automatisieren und erweitern. Verwende diesen Skill immer wenn der User Stash erwähnt, Szenen/Performers/Studios/Tags verwalten möchte, Scans oder Metadaten-Jobs starten will, Plugins oder Scrapers entwickeln oder konfigurieren möchte, oder die Stash GraphQL API ansprechen will. Auch bei Fragen zu StashDB, CommunityScrapers, Stash-Box, Docker-Setup oder der Bibliothek-Verwaltung.
---

# Stash Skill

Stash ist eine selbst-gehostete Web-App (Go) zum Organisieren, Taggen und Streamen von Video- und Bildsammlungen. Die gesamte Steuerung läuft über eine **GraphQL API**.

**Web-UI:** `http://localhost:9999`  
**GraphQL-Endpoint:** `http://localhost:9999/graphql`  
**Docs:** https://docs.stashapp.cc | **In-App Manual:** Shift+?

---

## Docker Setup (Unraid/BigServer)

```yaml
services:
  stash:
    image: stashapp/stash:latest
    container_name: stash
    restart: unless-stopped
    ports:
      - "9999:9999"
    environment:
      - STASH_STASH=/data/          # Medienpfad im Container
      - STASH_GENERATED=/generated/
      - STASH_METADATA=/metadata/
      - STASH_CACHE=/cache/
      - STASH_PORT=9999
    volumes:
      - /mnt/user/appdata/stash:/root/.stash      # Config, Plugins, Scrapers
      - /mnt/user/data/media:/data                 # Medienbibliothek
      - /mnt/user/appdata/stash/metadata:/metadata
      - /mnt/user/appdata/stash/cache:/cache
      - /mnt/user/appdata/stash/blobs:/blobs
      - /mnt/user/appdata/stash/generated:/generated
```

Stash bringt **ffmpeg** automatisch mit — kein separates Setup nötig.

---

## GraphQL API — Grundlagen

Alle Anfragen als POST an `/graphql`.

```python
import requests

STASH_URL = "http://localhost:9999/graphql"
# Mit API-Key (in Settings → Security generierbar):
API_KEY = ""  # leer = kein Auth nötig bei lokaler Nutzung

def gql(query, variables=None):
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["ApiKey"] = API_KEY
    r = requests.post(STASH_URL, json={"query": query, "variables": variables or {}}, headers=headers)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise Exception(data["errors"])
    return data["data"]
```

---

## Datenmodell — Kernentitäten

| Entität | Beschreibung |
|---------|-------------|
| **Scene** | Video-Datei mit Metadaten (Titel, Rating, Tags, Performers, Studio) |
| **Image** | Einzelbild |
| **Gallery** | Bildsammlung |
| **Performer** | Darsteller (Name, Aliases, Geburtsdatum, Maße, etc.) |
| **Studio** | Produzent/Studio |
| **Tag** | Schlagwort zum Kategorisieren |
| **Group** | Filmgruppe/Reihe (früher: Movie) |
| **SceneMarker** | Zeitstempel-Markierung innerhalb einer Scene |

---

## Häufige GraphQL-Operationen

### Scenes abfragen

```python
# Alle Szenen (paginiert)
scenes = gql("""
query FindScenes($filter: FindFilterType, $scene_filter: SceneFilterType) {
  findScenes(filter: $filter, scene_filter: $scene_filter) {
    count
    scenes {
      id
      title
      date
      rating100
      organized
      play_count
      o_counter
      tags { id name }
      performers { id name }
      studio { id name }
      files { path duration }
    }
  }
}
""", {
    "filter": {"per_page": 25, "page": 1, "sort": "created_at", "direction": "DESC"},
    "scene_filter": {}
})

# Nach Tag filtern
scenes = gql("...", {
    "filter": {"per_page": 100},
    "scene_filter": {
        "tags": {"value": ["TAG_ID"], "modifier": "INCLUDES"}
    }
})

# Nicht organisierte Szenen
scenes = gql("...", {
    "scene_filter": {"organized": {"value": False, "modifier": "EQUALS"}}
})
```

### Scene updaten

```python
gql("""
mutation SceneUpdate($input: SceneUpdateInput!) {
  sceneUpdate(input: $input) { id title }
}
""", {"input": {
    "id": "42",
    "title": "Neuer Titel",
    "rating100": 80,
    "organized": True,
    "tag_ids": ["1", "2", "3"],
    "performer_ids": ["5"],
    "studio_id": "7",
    "details": "Beschreibung",
    "date": "2024-01-15",
    "urls": ["https://example.com/scene"]
}})
```

### Performer erstellen/abfragen

```python
# Erstellen
result = gql("""
mutation PerformerCreate($input: PerformerCreateInput!) {
  performerCreate(input: $input) { id name }
}
""", {"input": {
    "name": "Name",
    "gender": "FEMALE",    # MALE, FEMALE, TRANSGENDER_MALE, TRANSGENDER_FEMALE, INTERSEX, NON_BINARY
    "birthdate": "1990-01-01",
    "country": "US",
    "height_cm": 165,
    "favorite": False,
    "tag_ids": [],
    "urls": ["https://example.com/performer"]
}})

# Suchen
gql("""
query FindPerformers($filter: FindFilterType) {
  findPerformers(filter: $filter) {
    count
    performers { id name scene_count favorite rating100 }
  }
}
""", {"filter": {"q": "Suchbegriff", "per_page": 20}})
```

### Tags verwalten

```python
# Tag erstellen
gql("mutation { tagCreate(input: {name: \"MeinTag\"}) { id name } }")

# Alle Tags
result = gql("query { findTags(filter: {per_page: -1}) { tags { id name scene_count } } }")

# Tags zusammenführen
gql("""
mutation { tagsMerge(input: {source: ["ID1", "ID2"], destination: "ZIEL_ID"}) { id name } }
""")
```

### Studio erstellen/abfragen

```python
gql("""
mutation StudioCreate($input: StudioCreateInput!) {
  studioCreate(input: $input) { id name }
}
""", {"input": {
    "name": "Studio Name",
    "url": "https://studio.com",
    "parent_id": None    # Für Sub-Studios
}})
```

---

## Jobs & Metadaten-Operationen

Alle Jobs laufen asynchron und geben eine Job-ID zurück.

```python
# Bibliothek scannen
job_id = gql("mutation { metadataScan(input: {}) }")["metadataScan"]

# Scan mit Optionen
job_id = gql("""
mutation { metadataScan(input: {
    rescan: false,
    scanGeneratePreviews: true,
    scanGenerateSprites: true,
    scanGeneratePhashes: true,
    scanGenerateThumbnails: true
}) }
""")

# Thumbnails/Previews generieren
gql("""
mutation { metadataGenerate(input: {
    covers: true, sprites: true, previews: true,
    imagePreviews: false, phashes: true,
    markers: false, transcodes: false
}) }
""")

# Auto-Tagging starten
gql("mutation { metadataAutoTag(input: {performers: [\"*\"], studios: [\"*\"], tags: [\"*\"]}) }")

# Identify (Metadaten von StashDB abrufen)
gql("""
mutation { metadataIdentify(input: {
    sources: [{source: {stash_box_index: 0}}],
    options: {
        fieldOptions: [],
        setCoverImage: true,
        setOrganized: false,
        includeMalePerformers: true
    }
}) }
""")

# Job-Status prüfen
jobs = gql("query { jobQueue { id status description progress } }")

# Datenbank optimieren
gql("mutation { optimiseDatabase }")
```

---

## Statistiken

```python
stats = gql("""
query {
  stats {
    scene_count scenes_size scenes_duration
    image_count images_size
    gallery_count performer_count studio_count tag_count group_count
    total_o_count total_play_count total_play_duration scenes_played
  }
}
""")
```

---

## Plugins & Scrapers installieren

Stash hat einen eingebauten Package Manager. Plugins und Scrapers lassen sich per API installieren — kein manuelles Kopieren nötig.

**Package-Quellen:**
- Plugins:  `https://stashapp.github.io/CommunityScripts/stable/index.yml`
- Scrapers: `https://stashapp.github.io/CommunityScrapers/stable/index.yml`

### Per stash_api.py (empfohlen)

```python
from stash_api import StashAPI
stash = StashAPI("http://localhost:9999")

# Plugin per Name installieren (case-insensitive, Teilstring reicht)
stash.install_package("RenameFile")
stash.install_package("FileMonitor")
stash.install_package("DupFileManager")
stash.install_package("ThumbPreviews")
stash.install_package("stashAI")

# Scraper installieren
stash.install_package("StashDB", "Scraper")

# Suchen wenn Name unbekannt
stash.search_packages("rename")    # findet: renamefile, scenerename, ...
stash.search_packages("duplicate")

# Alle installierten Plugins anzeigen
stash.installed_packages("Plugin")

# Alle aktualisieren
stash.update_all_packages()

# Einzeln aktualisieren
stash.update_package("RenameFile")

# Deinstallieren
stash.uninstall_package("ThumbPreviews")
```

### Alle 80 verfügbaren Plugins (package_id → Name)

```
AIOverhaul               AIOverhaul
AHavenVLMConnector       Haven VLM Connector
AdulttimeInteractiveDL   Adulttime Interactive Downloader
AudioPlayer              AudioPlayer
AudioPlayerLite          AudioPlayerLite
BulkImageScrape          Bulk Image Scrape
CommunityScriptsUILibrary CommunityScriptsUILibrary
DupFileManager           DupFileManager
PythonDepManager         PythonDepManager
PythonToolsInstaller     Python Tools Installer
LocalVisage              Local Visage
PlexSync                 Plex Sync
GroupAutoScraper         GroupAutoScraper
TPDBMarkers              The Porn DB Markers
ThumbPreviews            Thumbnail Previews
VideoScrollWheel         VideoScrollWheel
VideoBanner              Video Banner
ai_tagger                AI Tagger
audio-transcodes         audio-transcodes
chooseYourAdventurePlayer Choose Your Adventure Player
cjCardTweaks             CJ's Card Tweaks
comicInfoExtractor       Comic Info Extractor
date_parser              Gallery Date Parser
defaultDataForPath       Default Data For Path
deleter                  Additional Files Deleter
dupeMarker               Dupe Marker Detector
e621_tagger              e621_tagger
externalLinksEnhanced    External Links Enhanced
extraPerformerInfo       Extra Performer Info
filemonitor              FileMonitor
filenameParser           Filename Parser
funscript_haven          Funscript Haven
funscriptMarkers         Funscript Markers
hotCards                 Hot Cards
image_date_from_metadata Image Date From Metadata
imageGalleryNavigation   Image Gallery Navigation
markerDeleteButton       Marker Delete Button
markerTagToScene         Scene Marker Tags to Scene
miscTags                 Misc Tags
mobileWallLayout         Mobile Wall Layout
nfoSceneParser           nfoSceneParser
pathParser               Path Parser
performer-poster-backdrop Performer Poster Backdrop
performerStashboxUrlToID Performer Stashbox Url to ID
random_button            RandomButton
renamefile               RenameFile
sceneCoverCropper        Scene Cover Cropper
scenePageRememberStates  Scene Page Remember States
scenerename              SceneRename
secondaryPerformerImage  Add Secondary Performer Image
set_scene_cover          Set Scene Cover
setPerformersFromTags    Set Performers From Tags
sfwswitch                SFW Switch
star_identifier          Star Identifier
stashAppAndroidTvCompanion StashApp Android TV Companion
stashNotes               Stash Notes
stashNotifications       StashNotifications
stashdb-performer-gallery stashdb Performer Gallery
stashai                  Stash AI
stats                    Extended Stats
tagCopyPaste             tagCopyPaste
tagGalleriesFromImages   Tag Galleries From Images
tagImagesWithPerfTags    Tag Images From Performer Tags
tagScenesWithPerfTags    Tag Scenes From Performer Tags
themeSwitch              Theme Switch
timestampTrade           Timestamp Trade
titleFromFilename        titleFromFilename
untagRedundantTags       Remove Redundant Parent Tags
videoChapterMarkers      Video Chapter Markers
Theme-Minimal            Theme - Minimal
Theme-BlackHole          Theme - BlackHole
Theme-Night              Theme - Night
Theme-PulsarLight        Theme - PulsarLight
Theme-NeonDark           Theme - NeonDark
Theme-PornHub            Theme - Pornhub
Theme-Plex               Theme - Plex
Theme-ColorPalette       Theme - colorPalette
Theme-RoundedYellow      Theme - Rounded Yellow
Theme-ModernDark         Theme - ModernDark
```

Scrapers: 801 verfügbar — `stash.search_packages("sitename", "Scraper")` zum Suchen.

### Per GraphQL direkt

```python
# Verfügbare Pakete auflisten
gql("""
query {
  availablePackages(
    type: Plugin,
    source: "https://stashapp.github.io/CommunityScripts/stable/index.yml"
  ) { package_id name version metadata }
}
""")

# Installieren
gql("""
mutation {
  installPackages(type: Plugin, packages: [{
    id: "renamefile",
    sourceURL: "https://stashapp.github.io/CommunityScripts/stable/index.yml"
  }])
}
""")

# Alle aktualisieren
gql("mutation { updatePackages(type: Plugin, packages: null) }")

# Installierte anzeigen
gql("query { installedPackages(type: Plugin) { package_id name version } }")
```

---

## stashapp-tools — Empfohlenes Python-Paket

Für Plugins und Scrapers immer `stashapp-tools` statt eigener HTTP-Calls verwenden.

```bash
pip install stashapp-tools
```

```python
from stashapi.stashapp import StashInterface
import stashapi.log as log

# In einem Plugin (aus stdin lesen):
import json, sys
inp = json.loads(sys.stdin.read())
stash = StashInterface(inp["server_connection"])

# Extern / direkt:
stash = StashInterface({"Scheme": "http", "Host": "localhost", "Port": 9999, "ApiKey": "key"})

# Wichtige Methoden:
stash.find_scene(id)
stash.find_scenes(f=scene_filter)
stash.find_duplicate_scenes(distance=PhashDistance.EXACT)   # HIGH=4, MEDIUM=8, LOW=10
stash.update_scene({"id": "42", "title": "...", "organized": True})
stash.merge_tags(source_ids=["1","2"], destination_id="3")
stash.merge_performers(source_ids, destination_id)
stash.wait_for_job(job_id)              # Wartet bis Job fertig
stash.paginate_GQL(query, vars, callback=fn)  # Alle Seiten automatisch

log.info("Nachricht")                   # Logging direkt in Stash
log.progress(0.5)                       # Fortschrittsbalken (0.0–1.0)
```

Vollständige Methodenliste + Pagination + StashDB-Integration: `references/stashapp_tools_and_community.md`

---

## Scraping (Metadaten von externen Quellen)

```python
# Verfügbare Scraper auflisten
scrapers = gql("query { listScrapers(types: [SCENE]) { id name scene { urls } } }")

# Scene per URL scrapen
result = gql("""
query {
  scrapeSceneURL(url: "https://example.com/scene/123") {
    title date details
    performers { name }
    studio { name }
    tags { name }
  }
}
""")

# Identify einzelne Scene
gql("""
mutation { metadataIdentify(input: {
    sceneIDs: ["42"],
    sources: [{source: {stash_box_index: 0}}],
    options: {setCoverImage: true, setOrganized: true}
}) }
""")
```

### StashDB verbinden

In Settings → Metadata Providers → Stash-Box:
- Endpoint: `https://stashdb.org/graphql`
- API Key: erhält man per Einladung (→ https://guidelines.stashdb.org/docs/faq_getting-started/stashdb/accessing-stashdb/)

---

## Plugin-Entwicklung

Plugins liegen im Stash-Plugins-Verzeichnis (`~/.stash/plugins/`). Jedes Plugin braucht eine `.yml`-Datei.

### Plugin-Konfiguration (`mein_plugin.yml`)

```yaml
name: Mein Plugin
description: Was das Plugin macht
version: 1.0
url: https://github.com/...

# Ausführbarer Befehl
exec:
  - python
  - "{pluginDir}/mein_plugin.py"
interface: raw    # raw | rpc | js

# Tasks (manuell ausführbar im UI: Settings → Tasks)
tasks:
  - name: Hauptaufgabe
    description: Beschreibung der Aufgabe
    defaultArgs:
      mode: run

# Hooks (automatisch ausgeführt bei Events)
hooks:
  - name: Bei Scene-Update
    triggeredBy:
      - Scene.Update.Post
    defaultArgs:
      mode: hook

# UI-Erweiterung (JS/CSS ins Frontend injizieren)
ui:
  javascript:
    - mein_plugin.js
  css:
    - mein_plugin.css
```

### Python-Plugin-Template

```python
# mein_plugin.py
import json
import sys
import requests

FRAGMENT_SERVER = None

def main():
    input_data = json.loads(sys.stdin.read())
    server = input_data.get("server_connection", {})
    args = input_data.get("args", {})

    global FRAGMENT_SERVER
    FRAGMENT_SERVER = server

    mode = args.get("mode", "run")

    try:
        if mode == "run":
            run_main()
        elif mode == "hook":
            handle_hook(input_data)
    except Exception as e:
        output = {"error": str(e)}
    else:
        output = {"output": "ok"}

    print(json.dumps(output))

def gql(query, variables=None):
    scheme = FRAGMENT_SERVER.get("Scheme", "http")
    port = FRAGMENT_SERVER.get("Port", 9999)
    url = f"{scheme}://localhost:{port}/graphql"
    cookie = FRAGMENT_SERVER.get("SessionCookie", {}).get("Value", "")
    r = requests.post(url,
        json={"query": query, "variables": variables or {}},
        headers={"Content-Type": "application/json"},
        cookies={"session": cookie}
    )
    return r.json()["data"]

def log_info(msg):
    print(f"\x01info\x02{msg}\n", file=sys.stderr)

def log_progress(progress: float):
    # progress between 0.0 and 1.0
    print(f"\x01progress\x02{progress}\n", file=sys.stderr)

def run_main():
    log_info("Plugin gestartet")
    # Hier eigene Logik...

def handle_hook(input_data):
    # Hook-Input enthält: args.hook_context mit type und id
    hook_ctx = input_data.get("args", {}).get("hookContext", {})
    entity_id = hook_ctx.get("id")
    entity_type = hook_ctx.get("type")  # Scene, Performer, Tag, etc.
    log_info(f"Hook ausgelöst: {entity_type} ID={entity_id}")

main()
```

### Verfügbare Hook-Trigger

```yaml
# Scene
- Scene.Create.Post
- Scene.Update.Post
- Scene.Destroy.Post
# SceneMarker
- SceneMarker.Create.Post
- SceneMarker.Update.Post
- SceneMarker.Destroy.Post
# Image / Gallery
- Image.Create.Post / Update / Destroy
- Gallery.Create.Post / Update / Destroy
- GalleryChapter.Create.Post / Update / Destroy
# Performer / Studio / Tag / Group
- Performer.Create.Post / Update / Destroy
- Studio.Create.Post / Update / Destroy
- Tag.Create.Post / Update / Merge.Post / Destroy
- Group.Create.Post / Update / Destroy
```

---

## Filter-System

Stash hat ein mächtiges Filter-System für alle Queries:

```python
# FindFilterType — Paginierung und Sortierung
{
    "per_page": 25,           # -1 = alle
    "page": 1,
    "q": "suchbegriff",       # Volltext-Suche
    "sort": "created_at",     # title, date, rating100, play_count, ...
    "direction": "DESC"       # ASC | DESC
}

# SceneFilterType — Beispiele
{
    "organized": {"value": True, "modifier": "EQUALS"},
    "rating100": {"value": 75, "modifier": "GREATER_THAN"},
    "tags": {"value": ["ID1"], "modifier": "INCLUDES"},   # INCLUDES | INCLUDES_ALL | EXCLUDES
    "performers": {"value": ["ID1"], "modifier": "INCLUDES"},
    "studio": {"value": {"id": "1", "depth": 0}, "modifier": "INCLUDES"},
    "play_count": {"value": 0, "modifier": "EQUALS"},
    "duration": {"min": 600, "max": 7200},  # in Sekunden
    "resolution": {"min": "1080P", "max": "ORIGINAL"},
    "has_markers": "true",
    "is_missing": "studio"    # performer, studio, tags, gallery, ...
}

# Modifier-Werte: EQUALS, NOT_EQUALS, GREATER_THAN, LESS_THAN, IS_NULL, NOT_NULL
#                INCLUDES, INCLUDES_ALL, EXCLUDES, MATCHES_REGEX, NOT_MATCHES_REGEX
```

---

## Nützliche Queries & Mutations

```python
# Version abfragen
gql("query { version { version build_time hash } }")

# System-Status
gql("query { systemStatus { databaseSchema databasePath appSchema status } }")

# Duplikate finden (perceptual hash)
dupes = gql("query { findDuplicateScenes(distance: 0) { id title files { path } } }")

# Scene-Aktivität aufzeichnen
gql("mutation { sceneSaveActivity(id: \"42\", resume_time: 120.5, playDuration: 30.0) }")

# API-Key generieren
gql("mutation { generateAPIKey(input: {}) }")

# Datenbank-Backup
gql("mutation { backupDatabase(input: {}) }")

# Raw SQL (GEFÄHRLICH — nur für Debugging)
gql("""
mutation { querySQL(sql: "SELECT COUNT(*) FROM scenes", args: []) {
  columns rows
} }
""")

# Plugins auflisten
gql("query { plugins { id name version enabled tasks { name } hooks { name hooks } } }")

# Plugin-Task ausführen
gql("""
mutation {
  runPluginTask(plugin_id: "mein_plugin", task_name: "Hauptaufgabe")
}
""")
```

---

## Scraper-Entwicklung

Scrapers liegen in `~/.stash/scrapers/` als `.yml`-Dateien. Vollständige Doku: https://docs.stashapp.cc/scraping/

Community Scrapers installieren: Settings → Metadata Providers → Available Scrapers → Community (stable)

---

## Unraid-Kontext (BigServer)

- Stash läuft als Docker-Container auf `192.168.1.144:9999`
- Config/Plugins/Scrapers: `/mnt/user/appdata/stash/`
- Stash AI-Tagging war bereits konfiguriert: Stash-AIServer (Port 4153) + nsfw_ai_model_server (Port 4573)
- Mediendaten unter `/mnt/user/` (Unraid Array)

---

## Scraper-Entwicklung

Scrapers liegen in `~/.stash/scrapers/` als `.yml`-Dateien (+ optionale Python-Scripts).
**800+ Community-Scrapers** installierbar via: Settings → Metadata Providers → Community (stable)

Drei Scraper-Typen:
- **XPath** — HTML-Parsing via XPath-Selektoren (nur `.yml`)
- **JSON** — JSON-API-Parsing (nur `.yml`)
- **Script** — Python für JS-heavy Sites, Login, komplexe APIs

Vollständige Templates, PostProcess-Operationen, py_common-Bibliothek, Go-Datumsformate:
→ `references/scraper_development.md`

---

## CommunityScripts — Empfohlene Plugins

| Plugin | Funktion |
|--------|---------|
| **RenameFile** | Dateien umbenennen wenn Titel geändert wird |
| **titleFromFilename** | Titel beim Scan aus Dateinamen setzen |
| **FileMonitor** | Ordner überwachen → auto-Scan bei Änderungen |
| **DupFileManager** | Duplikate verwalten + Metadaten mergen |
| **stashAI** | Tags/Marker per KI (Stash-AIServer) |
| **LocalVisage** | Darsteller per Gesichtserkennung erkennen |
| **PlexSync** | Metadaten mit Plex synchronisieren |
| **tagScenesWithPerfTags** | Performer-Tags auf Szenen übertragen |
| **pathParser** | Metadaten aus Dateipfad-Struktur extrahieren |

GitHub: https://github.com/stashapp/CommunityScripts

---

## Referenz-Dateien

- `references/stash_api.py` — Python-Hilfsklasse für alle GraphQL-Operationen
- `references/stashapp_tools_and_community.md` — stashapp-tools vollständig, CommunityScripts, stash-box/StashDB API
- `references/scraper_development.md` — XPath/JSON/Python-Scraper-Templates, py_common, PostProcess-Ops
