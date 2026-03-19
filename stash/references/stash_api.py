"""
Stash GraphQL API Helper
Vollständige Python-Hilfsklasse für die Stash API.

Verwendung:
    from stash_api import StashAPI
    stash = StashAPI("http://localhost:9999", api_key="optional")
    scenes = stash.find_scenes(q="suchbegriff", per_page=25)
"""

import requests
import sys


class StashAPI:
    def __init__(self, url="http://localhost:9999", api_key=None, session_cookie=None):
        self.url = url.rstrip("/") + "/graphql"
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.cookies = {}
        if api_key:
            self.headers["ApiKey"] = api_key
        if session_cookie:
            self.cookies["session"] = session_cookie

    # -------------------------------------------------------------------------
    # Core
    # -------------------------------------------------------------------------

    def gql(self, query, variables=None):
        r = requests.post(self.url,
            json={"query": query, "variables": variables or {}},
            headers=self.headers,
            cookies=self.cookies
        )
        r.raise_for_status()
        result = r.json()
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        return result.get("data", {})

    # -------------------------------------------------------------------------
    # Scenes
    # -------------------------------------------------------------------------

    def find_scenes(self, q="", per_page=25, page=1, sort="created_at",
                    direction="DESC", scene_filter=None):
        return self.gql("""
query FindScenes($filter: FindFilterType, $scene_filter: SceneFilterType) {
  findScenes(filter: $filter, scene_filter: $scene_filter) {
    count
    scenes {
      id title code details date director
      rating100 organized o_counter play_count
      resume_time play_duration last_played_at
      created_at updated_at
      urls
      tags { id name }
      performers { id name }
      studio { id name }
      groups { group { id name } scene_index }
      files { id path size duration video_codec audio_codec width height framerate bitrate }
      paths { screenshot preview stream webp vtt sprite }
      scene_markers { id title seconds primary_tag { id name } }
      stash_ids { endpoint stash_id }
    }
  }
}
""", {
            "filter": {"q": q, "per_page": per_page, "page": page,
                       "sort": sort, "direction": direction},
            "scene_filter": scene_filter or {}
        })

    def find_scene(self, scene_id):
        return self.gql("query FindScene($id: ID!) { findScene(id: $id) { id title rating100 organized tags { id name } performers { id name } studio { id name } files { path } } }",
                        {"id": scene_id})["findScene"]

    def update_scene(self, scene_id, **kwargs):
        kwargs["id"] = scene_id
        return self.gql("""
mutation SceneUpdate($input: SceneUpdateInput!) {
  sceneUpdate(input: $input) { id title organized rating100 }
}
""", {"input": kwargs})["sceneUpdate"]

    def bulk_update_scenes(self, ids, **kwargs):
        """Update multiple scenes at once."""
        kwargs["ids"] = ids
        return self.gql("""
mutation BulkSceneUpdate($input: BulkSceneUpdateInput!) {
  bulkSceneUpdate(input: $input) { id title }
}
""", {"input": kwargs})["bulkSceneUpdate"]

    def scene_add_play(self, scene_id):
        return self.gql("mutation { sceneAddPlay(id: $id) { count } }",
                        {"id": scene_id})

    def find_duplicate_scenes(self, distance=0, duration_diff=None):
        vars = {"distance": distance}
        if duration_diff is not None:
            vars["duration_diff"] = duration_diff
        return self.gql("""
query FindDuplicateScenes($distance: Int, $duration_diff: Float) {
  findDuplicateScenes(distance: $distance, duration_diff: $duration_diff) {
    id title files { path size duration }
  }
}
""", vars)["findDuplicateScenes"]

    # -------------------------------------------------------------------------
    # Performers
    # -------------------------------------------------------------------------

    def find_performers(self, q="", per_page=25, page=1, performer_filter=None):
        return self.gql("""
query FindPerformers($filter: FindFilterType, $performer_filter: PerformerFilterType) {
  findPerformers(filter: $filter, performer_filter: $performer_filter) {
    count
    performers {
      id name disambiguation gender
      birthdate country height_cm favorite
      rating100 scene_count o_counter
      alias_list urls tags { id name }
      stash_ids { endpoint stash_id }
      created_at updated_at
    }
  }
}
""", {
            "filter": {"q": q, "per_page": per_page, "page": page},
            "performer_filter": performer_filter or {}
        })

    def create_performer(self, name, **kwargs):
        kwargs["name"] = name
        return self.gql("""
mutation PerformerCreate($input: PerformerCreateInput!) {
  performerCreate(input: $input) { id name }
}
""", {"input": kwargs})["performerCreate"]

    def update_performer(self, performer_id, **kwargs):
        kwargs["id"] = performer_id
        return self.gql("""
mutation PerformerUpdate($input: PerformerUpdateInput!) {
  performerUpdate(input: $input) { id name }
}
""", {"input": kwargs})["performerUpdate"]

    # -------------------------------------------------------------------------
    # Studios
    # -------------------------------------------------------------------------

    def find_studios(self, q="", per_page=25):
        return self.gql("""
query FindStudios($filter: FindFilterType) {
  findStudios(filter: $filter) {
    count
    studios { id name url scene_count rating100 aliases parent_studio { id name } }
  }
}
""", {"filter": {"q": q, "per_page": per_page}})

    def create_studio(self, name, **kwargs):
        kwargs["name"] = name
        return self.gql("mutation { studioCreate(input: $input) { id name } }",
                        {"input": kwargs})["studioCreate"]

    def update_studio(self, studio_id, **kwargs):
        kwargs["id"] = studio_id
        return self.gql("mutation { studioUpdate(input: $input) { id name } }",
                        {"input": kwargs})["studioUpdate"]

    # -------------------------------------------------------------------------
    # Tags
    # -------------------------------------------------------------------------

    def find_tags(self, q="", per_page=-1):
        return self.gql("""
query FindTags($filter: FindFilterType) {
  findTags(filter: $filter) {
    count
    tags { id name description scene_count performer_count aliases parents { id name } children { id name } }
  }
}
""", {"filter": {"q": q, "per_page": per_page}})

    def create_tag(self, name, **kwargs):
        kwargs["name"] = name
        return self.gql("mutation { tagCreate(input: $input) { id name } }",
                        {"input": kwargs})["tagCreate"]

    def find_or_create_tag(self, name):
        """Sucht einen Tag per Namen und erstellt ihn falls nicht vorhanden."""
        result = self.find_tags(q=name, per_page=5)
        for tag in result["findTags"]["tags"]:
            if tag["name"].lower() == name.lower():
                return tag
        return self.create_tag(name)

    def merge_tags(self, source_ids, destination_id):
        return self.gql("""
mutation { tagsMerge(input: {source: $source, destination: $dest}) { id name } }
""", {"source": source_ids, "dest": destination_id})

    # -------------------------------------------------------------------------
    # Images & Galleries
    # -------------------------------------------------------------------------

    def find_images(self, q="", per_page=25, image_filter=None):
        return self.gql("""
query FindImages($filter: FindFilterType, $image_filter: ImageFilterType) {
  findImages(filter: $filter, image_filter: $image_filter) {
    count
    images { id title rating100 organized o_counter
             tags { id name } performers { id name } studio { id name }
             files { path width height size } }
  }
}
""", {"filter": {"q": q, "per_page": per_page}, "image_filter": image_filter or {}})

    def find_galleries(self, q="", per_page=25):
        return self.gql("""
query FindGalleries($filter: FindFilterType) {
  findGalleries(filter: $filter) {
    count
    galleries { id title date rating100 organized image_count
                tags { id name } performers { id name } studio { id name } }
  }
}
""", {"filter": {"q": q, "per_page": per_page}})

    # -------------------------------------------------------------------------
    # Jobs & Metadata
    # -------------------------------------------------------------------------

    def scan(self, paths=None, **kwargs):
        inp = kwargs
        if paths:
            inp["paths"] = paths
        return self.gql("mutation Scan($input: ScanMetadataInput!) { metadataScan(input: $input) }",
                        {"input": inp})["metadataScan"]

    def generate(self, **kwargs):
        """kwargs: covers, sprites, previews, phashes, markers, transcodes, etc."""
        return self.gql("mutation Generate($input: GenerateMetadataInput!) { metadataGenerate(input: $input) }",
                        {"input": kwargs})["metadataGenerate"]

    def auto_tag(self, performers=None, studios=None, tags=None):
        return self.gql("mutation { metadataAutoTag(input: $input) }",
                        {"input": {
                            "performers": performers or ["*"],
                            "studios": studios or ["*"],
                            "tags": tags or ["*"]
                        }})["metadataAutoTag"]

    def identify(self, scene_ids=None, stash_box_index=0, set_organized=False,
                 set_cover=True):
        inp = {
            "sources": [{"source": {"stash_box_index": stash_box_index}}],
            "options": {"setCoverImage": set_cover, "setOrganized": set_organized}
        }
        if scene_ids:
            inp["sceneIDs"] = scene_ids
        return self.gql("mutation Identify($input: IdentifyMetadataInput!) { metadataIdentify(input: $input) }",
                        {"input": inp})["metadataIdentify"]

    def clean(self, dry_run=True):
        return self.gql("mutation { metadataClean(input: {dryRun: $dry}) }",
                        {"dry": dry_run})["metadataClean"]

    def job_queue(self):
        return self.gql("query { jobQueue { id status description progress } }")["jobQueue"]

    def stop_job(self, job_id):
        return self.gql("mutation { stopJob(job_id: $id) }", {"id": job_id})["stopJob"]

    def optimize_db(self):
        return self.gql("mutation { optimiseDatabase }")["optimiseDatabase"]

    def backup_db(self):
        return self.gql("mutation { backupDatabase(input: {}) }")["backupDatabase"]

    # -------------------------------------------------------------------------
    # Stats & System
    # -------------------------------------------------------------------------

    def stats(self):
        return self.gql("""
query {
  stats {
    scene_count scenes_size scenes_duration
    image_count images_size gallery_count
    performer_count studio_count tag_count group_count
    total_o_count total_play_count total_play_duration scenes_played
  }
}
""")["stats"]

    def version(self):
        return self.gql("query { version { version build_time hash } }")["version"]

    def system_status(self):
        return self.gql("query { systemStatus { databaseSchema appSchema status databasePath } }")["systemStatus"]

    # -------------------------------------------------------------------------
    # Plugins
    # -------------------------------------------------------------------------

    def list_plugins(self):
        return self.gql("query { plugins { id name version enabled tasks { name } hooks { name hooks } } }")["plugins"]

    def run_plugin_task(self, plugin_id, task_name=None, args_map=None):
        return self.gql("""
mutation RunPluginTask($plugin_id: ID!, $task_name: String, $args_map: Map) {
  runPluginTask(plugin_id: $plugin_id, task_name: $task_name, args_map: $args_map)
}
""", {"plugin_id": plugin_id, "task_name": task_name, "args_map": args_map})["runPluginTask"]

    # -------------------------------------------------------------------------
    # Scrapers
    # -------------------------------------------------------------------------

    def list_scrapers(self, content_types=None):
        types = content_types or ["SCENE", "PERFORMER", "GALLERY"]
        return self.gql("query ListScrapers($types: [ScrapeContentType!]!) { listScrapers(types: $types) { id name scene { urls } performer { urls } } }",
                        {"types": types})["listScrapers"]

    def scrape_scene_url(self, url):
        return self.gql("query { scrapeSceneURL(url: $url) { title date details performers { name } studio { name } tags { name } } }",
                        {"url": url})["scrapeSceneURL"]

    def scrape_performer_url(self, url):
        return self.gql("query { scrapePerformerURL(url: $url) { name gender birthdate country urls tags { name } } }",
                        {"url": url})["scrapePerformerURL"]


# -------------------------------------------------------------------------
# Plugin-Logging-Hilfsfunktionen (für Plugin-Scripts)
# -------------------------------------------------------------------------

def log_trace(msg):   print(f"\x01trace\x02{msg}\n", file=sys.stderr)
def log_debug(msg):   print(f"\x01debug\x02{msg}\n", file=sys.stderr)
def log_info(msg):    print(f"\x01info\x02{msg}\n", file=sys.stderr)
def log_warning(msg): print(f"\x01warning\x02{msg}\n", file=sys.stderr)
def log_error(msg):   print(f"\x01error\x02{msg}\n", file=sys.stderr)
def log_progress(p):  print(f"\x01progress\x02{p}\n", file=sys.stderr)


# -------------------------------------------------------------------------
# Schnellstart
# -------------------------------------------------------------------------

if __name__ == "__main__":
    stash = StashAPI("http://localhost:9999")

    v = stash.version()
    print(f"Stash {v['version']} ({v['build_time']})")

    s = stash.stats()
    print(f"Szenen: {s['scene_count']} ({s['scenes_size']/1024/1024/1024:.1f} GB)")
    print(f"Performer: {s['performer_count']}, Studios: {s['studio_count']}, Tags: {s['tag_count']}")
    print(f"Gespielt: {s['scenes_played']} Szenen, {s['total_play_count']}x gesamt")
