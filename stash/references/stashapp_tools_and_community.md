# stashapp-tools & CommunityScripts

## stashapp-tools — Offizielles Python-Paket

Das empfohlene Paket für Plugin- und Scraper-Entwicklung. Viel mächtiger als manuelle GraphQL-Calls.

```bash
pip install stashapp-tools
# Für Scrapers auch:
pip install stashapp-tools requests cloudscraper beautifulsoup4 lxml
```

### StashInterface — vollständige API

```python
from stashapi.stashapp import StashInterface
import stashapi.log as log

# Initialisierung aus Plugin-Input (stdin)
import json, sys
inp = json.loads(sys.stdin.read())
stash = StashInterface(inp["server_connection"])

# Initialisierung direkt (für externe Scripts)
stash = StashInterface({"Scheme": "http", "Host": "localhost", "Port": 9999})

# Mit API-Key
stash = StashInterface({
    "Scheme": "http", "Host": "localhost", "Port": 9999,
    "ApiKey": "dein-api-key"
})
```

### Alle verfügbaren Methoden

```python
# === FIND ===
stash.find_scene(id)                  # Scene per ID
stash.find_scenes(f=scene_filter)     # Scenes filtern
stash.find_scene_by_hash(hash)        # per Hash
stash.find_duplicate_scenes(distance=PhashDistance.EXACT)

stash.find_performer(id)
stash.find_performers(f=perf_filter)

stash.find_studio(id)
stash.find_studios(f=studio_filter)
stash.find_studio_hierarchy(id)       # Studio + alle Sub-Studios
stash.find_studio_root(id)            # Root-Studio finden

stash.find_tag(id)
stash.find_tags(f=tag_filter)

stash.find_gallery(id)
stash.find_galleries(f=gal_filter)
stash.find_gallery_images(gallery_id)

stash.find_image(id)
stash.find_images(f=img_filter)

stash.find_group(id)
stash.find_groups(f=group_filter)

stash.find_job(job_id)
stash.job_queue()

# === CREATE ===
stash.create_scene(input_dict)
stash.create_scenes(list_of_inputs)   # Bulk
stash.create_performer(input_dict)
stash.create_studio(input_dict)
stash.create_tag(input_dict)
stash.create_gallery(input_dict)
stash.create_gallery_chapter(input_dict)
stash.create_group(input_dict)
stash.create_image(input_dict)
stash.create_scene_marker(input_dict)

# === UPDATE ===
stash.update_scene(input_dict)        # input_dict muss 'id' enthalten
stash.update_scenes(list_of_inputs)   # Bulk
stash.update_performer(input_dict)
stash.update_performers(list_of_inputs)
stash.update_studio(input_dict)
stash.update_tag(input_dict)
stash.update_gallery(input_dict)
stash.update_galleries(list_of_inputs)
stash.update_gallery_images(input_dict)
stash.update_image(input_dict)
stash.update_images(list_of_inputs)
stash.update_group(input_dict)
stash.update_scene_marker(input_dict)

# === DESTROY ===
stash.destroy_scene(id, delete_file=False)
stash.destroy_scenes(ids, delete_file=False)
stash.destroy_performer(id)
stash.destroy_studio(id)
stash.destroy_tag(id)
stash.destroy_tags(ids)
stash.destroy_gallery(id, delete_file=False)
stash.destroy_gallery_chapter(id)
stash.destroy_image(id, delete_file=False)
stash.destroy_images(ids, delete_file=False)
stash.destroy_group(id)
stash.destroy_scene_marker(id)
stash.destroy_scene_markers(ids)
stash.destroy_scene_stash_id(scene_id, stash_id)
stash.destroy_files(ids)

# === MERGE ===
stash.merge_tags(source_ids, destination_id)
stash.merge_performers(source_ids, destination_id)
stash.merge_scenes(source_ids, destination_id, values={})
stash.merge_scene_markers(source_ids, destination_id)

# === METADATA JOBS ===
stash.metadata_scan(paths=[], flags={})
stash.metadata_generate(flags={})
stash.metadata_autotag(paths=[], performers=["*"], studios=["*"], tags=["*"])
stash.metadata_clean(paths=[], dry_run=False)
stash.metadata_clean_generated(flags={})
stash.stop_job(job_id)
stash.wait_for_job(job_id, timeout=60)  # Wartet bis Job fertig

# === SCRAPING ===
stash.scrape_scene(source, input_dict)
stash.scrape_scenes(source, input_dict)
stash.scrape_scene_url(url)
stash.scrape_performer(source, input_dict)
stash.scrape_performers(source, input_dict)
stash.scrape_performer_url(url)
stash.scrape_gallery(source, input_dict)
stash.scrape_gallery_url(url)
stash.scrape_group_url(url)
stash.list_scene_scrapers(types=["URL", "FRAGMENT", "NAME"])
stash.list_performer_scrapers(types)
stash.list_gallery_scrapers(types)
stash.reload_scrapers()

# === STASH-BOX ===
stash.stashbox_scene_scraper(scene_ids, stashbox_index=0)
stash.stashbox_identify_task(scene_ids, stashbox_index=0)
stash.stashbox_submit_scene_fingerprints(scene_ids, stashbox_index=0)
stash.submit_scene_draft(scene_id, stashbox_index=0)
stash.get_stashbox_connection(stashbox_index=0)
stash.get_stashbox_connections()

# === CONFIGURATION ===
stash.get_configuration()
stash.get_configuration_defaults()
stash.configure_plugin(plugin_id, config_dict)
stash.find_plugin_config(plugin_id)
stash.find_plugins_config()
stash.run_plugin_task(plugin_id, task_name, args_map={})

# === FILES ===
stash.move_files(ids, destination_folder, destination_basename=None)
stash.destroy_files(ids)
stash.file_set_fingerprints(input_dict)

# === GALLERY ===
stash.add_gallery_images(gallery_id, image_ids)
stash.remove_gallery_images(gallery_id, image_ids)

# === DATABASE ===
stash.optimise_database()
stash.backup_database()
result = stash.sql_query("SELECT id, title FROM scenes LIMIT 10")
stash.sql_commit("UPDATE scenes SET organized=1 WHERE rating100 >= 80")

# === MISC ===
stash.stash_version()
stash.paginate_GQL(query, variables, pages=-1, callback=fn)
stash.call_GQL(query, variables={})  # Roher GraphQL-Call
```

### PhashDistance für Duplikate

```python
from stashapi.stash_types import PhashDistance

dupes = stash.find_duplicate_scenes(distance=PhashDistance.EXACT)   # 0
dupes = stash.find_duplicate_scenes(distance=PhashDistance.HIGH)    # 4
dupes = stash.find_duplicate_scenes(distance=PhashDistance.MEDIUM)  # 8
dupes = stash.find_duplicate_scenes(distance=PhashDistance.LOW)     # 10
```

### Pagination (alle Seiten automatisch)

```python
all_scenes = []
def process_page(page_data):
    all_scenes.extend(page_data["findScenes"]["scenes"])

stash.paginate_GQL("""
query FindScenes($filter: FindFilterType) {
  findScenes(filter: $filter) {
    count
    scenes { id title }
  }
}
""", {"filter": {"per_page": 200}}, callback=process_page)
```

### Logging in Plugins

```python
import stashapi.log as log

log.trace("sehr detailliert")
log.debug("debug info")
log.info("normale info")
log.warning("warnung")
log.error("fehler")
log.progress(0.5)  # Fortschrittsbalken (0.0 - 1.0)

# Als std-logging Handler:
import logging
logging.basicConfig(
    format="%(name)s| %(message)s",
    handlers=[log.StashLogHandler()],
    level="DEBUG"
)
```

---

## CommunityScripts — Wichtige Plugins

Installieren über: **Settings → Metadata Providers → Available Plugins → Community (stable)**

Oder manuell nach `~/.stash/plugins/` kopieren.

| Plugin | Funktion |
|--------|---------|
| **RenameFile** | Dateinamen automatisch umbenennen wenn Titel geändert wird. Format: `title,performers,studio,tags,resolution,date` |
| **titleFromFilename** | Szene-Titel aus Dateinamen beim Erstellen setzen |
| **FileMonitor** | Bibliotheksordner überwachen → automatischer Scan bei Änderungen |
| **DupFileManager** | Duplikate verwalten und löschen, inkl. Metadaten-Merge |
| **stashNotifications** | Browser-Notifications bei Plugin/Scraper-Änderungen |
| **stashAI** | Tags/Marker per KI hinzufügen (Stash-AIServer) |
| **LocalVisage** | Darsteller per Gesichtserkennung lokal identifizieren |
| **PlexSync** | Metadaten mit Plex synchronisieren |
| **stats** | Erweiterte Statistiken im UI |
| **sceneRename** | Szenen nach konfigurierbarem Muster umbenennen |
| **pathParser** | Metadaten aus Dateipfad-Struktur extrahieren |
| **tagScenesWithPerfTags** | Performer-Tags auf Szenen übertragen |
| **setPerformersFromTags** | Performer aus Tags setzen |
| **untagRedundantTags** | Redundante Tags entfernen (Eltern-Kind-Hierarchie) |

GitHub: https://github.com/stashapp/CommunityScripts

### Plugin-Settings lesen (im Plugin selbst)

```python
# Plugin-Settings aus der Stash-Konfiguration lesen
config = stash.find_plugin_config("mein_plugin_id")
my_setting = config.get("meineSetting", "default_wert")

# Oder via get_configuration:
all_plugins_config = stash.find_plugins_config()
```

---

## stash-box / StashDB API

stash-box ist die Software hinter StashDB (https://stashdb.org) — der Community-Metadaten-Datenbank.

```python
import requests

STASHDB_URL = "https://stashdb.org/graphql"
STASHDB_API_KEY = "dein-stashdb-api-key"  # aus StashDB Account-Einstellungen

def stashdb_query(query, variables=None):
    r = requests.post(STASHDB_URL,
        json={"query": query, "variables": variables or {}},
        headers={"ApiKey": STASHDB_API_KEY, "Content-Type": "application/json"}
    )
    return r.json()["data"]

# Performer suchen
result = stashdb_query("""
query {
  searchPerformers(term: "Name", limit: 5) {
    performers { id name gender aliases { name } urls { url } images { url } }
    count
  }
}
""")

# Scene per Fingerprint suchen
result = stashdb_query("""
query FindScenesByFingerprint($fingerprints: [[FingerprintQueryInput!]!]!) {
  findScenesBySceneFingerprints(fingerprints: $fingerprints) {
    id title date
    performers { performer { id name } }
    studio { id name }
  }
}
""", {"fingerprints": [[{"hash": "abc123", "algorithm": "OSHASH"}]]})
```

### StashDB über Stash nutzen (empfohlen)

```python
# Stash kümmert sich um Auth — einfach stashbox_index=0 nutzen
# (Index entspricht Reihenfolge in Settings → Metadata Providers)

# Szene per ID auf StashDB identifizieren
job_id = stash.stashbox_identify_task(
    scene_ids=["42", "43"],
    stashbox_index=0
)
stash.wait_for_job(job_id)

# Fingerprints einreichen
stash.stashbox_submit_scene_fingerprints(["42"], stashbox_index=0)

# Szene als Draft einreichen
stash.submit_scene_draft(scene_id="42", stashbox_index=0)

# Stash-Box-Verbindung prüfen
conn = stash.get_stashbox_connection(0)
print(conn["endpoint"], conn["name"])
```

### Andere Stash-Boxen

Neben StashDB gibt es weitere Community-Stash-Box-Instanzen für verschiedene Nischen.
Liste + Zugangsdaten: https://guidelines.stashdb.org/docs/faq_getting-started/stashdb/accessing-stash-boxes/
