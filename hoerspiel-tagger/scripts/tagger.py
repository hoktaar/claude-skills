#!/usr/bin/env python3
"""
Hörspiel & Hörbuch MP3 Tagger
Fetches metadata from MusicBrainz + Cover Art Archive and writes ID3v2.3 tags.

Usage:
    python tagger.py --path <folder_or_file> [options]
    python tagger.py --help
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from mutagen.id3 import (APIC, COMM, ID3, TALB, TCOM, TCON, TCOP, TPE1,
                              TPE2, TPE3, TPOS, TPUB, TRCK, TXXX, TYER, TIT2,
                              ID3NoHeaderError)
    from mutagen.mp3 import MP3
except ImportError:
    print("ERROR: mutagen nicht installiert. Bitte ausführen:")
    print("  pip install mutagen requests")
    sys.exit(1)

# ── MusicBrainz API ──────────────────────────────────────────────────────────

MB_BASE = "https://musicbrainz.org/ws/2"
CAA_BASE = "https://coverartarchive.org"
UA = "HoerspielTagger/1.0 ( hoerspiel-tagger@github )"
HEADERS = {"User-Agent": UA, "Accept": "application/json"}
LAST_MB_CALL = 0.0


def mb_get(path: str, params: dict = None) -> dict:
    """Rate-limited MusicBrainz GET (1 req/s)."""
    global LAST_MB_CALL
    since = time.time() - LAST_MB_CALL
    if since < 1.05:
        time.sleep(1.05 - since)
    url = f"{MB_BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            LAST_MB_CALL = time.time()
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise
    except Exception as e:
        print(f"  [WARN] MusicBrainz request failed: {e}")
        return {}


def search_release(title: str, artist: str = None) -> list[dict]:
    """Search for a release by title and optional artist."""
    q = f'release:"{title}"'
    if artist:
        q += f' AND artist:"{artist}"'
    data = mb_get("release/", {"query": q, "fmt": "json", "limit": 5})
    return data.get("releases", [])


def search_artist_releases(artist_id: str, limit: int = 100) -> list[dict]:
    """Get all releases for a known artist MBID."""
    data = mb_get("release/", {
        "artist": artist_id,
        "fmt": "json",
        "limit": limit,
        "inc": "artist-credits labels"
    })
    return data.get("releases", [])


def get_release_details(mbid: str) -> dict:
    """Get full release details including artist credits and recordings."""
    return mb_get(f"release/{mbid}", {
        "fmt": "json",
        "inc": "artist-credits recordings labels release-groups"
    })


def fetch_cover(mbid: str, size: int = 500) -> bytes | None:
    """Fetch front cover from Cover Art Archive. Returns JPEG bytes or None.

    CAA redirects to archive.org. Uses browser-like UA to avoid 403 blocks.
    """
    BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36")
    img_headers = {"User-Agent": BROWSER_UA, "Accept": "image/jpeg,image/*"}

    for url in [f"{CAA_BASE}/release/{mbid}/front-{size}",
                f"{CAA_BASE}/release/{mbid}/front"]:
        try:
            req = urllib.request.Request(url, headers=img_headers)
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
                if len(data) > 1000:
                    return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            # Handle redirect to archive.org manually
            loc = e.headers.get("Location", "")
            if loc and "archive.org" in loc:
                try:
                    req2 = urllib.request.Request(loc, headers=img_headers)
                    with urllib.request.urlopen(req2, timeout=15) as r2:
                        data = r2.read()
                        if len(data) > 1000:
                            return data
                except Exception:
                    pass
        except Exception:
            pass
    return None


# ── Filename Parsing ──────────────────────────────────────────────────────────

# Known series names for smarter parsing
KNOWN_SERIES = {
    "die drei ???": "Die drei ???",
    "die drei fragezeichen": "Die drei ???",
    "die drei ?": "Die drei ???",
    "3fragezeichen": "Die drei ???",
    "tkkg": "TKKG",
    "benjamin blümchen": "Benjamin Blümchen",
    "bibi blocksberg": "Bibi Blocksberg",
    "hui buh": "Hui Buh",
    "fünf freunde": "Fünf Freunde",
    "hanni und nanni": "Hanni und Nanni",
    "rocky beach": "Die drei ???",
}

KNOWN_ARTIST_IDS = {
    "Die drei ???": "e028fab5-39ae-4ed9-b8c2-c4344d88b171",
    "TKKG": "d3d9bc09-f1c1-49bc-94e0-e7897f60f4c3",
}


def parse_filename(filepath: Path) -> dict:
    """Extract series, episode number, and title from filename."""
    name = filepath.stem
    result = {"raw": name, "series": None, "episode": None, "title": None}

    # Pattern 1: "Die drei ??? 001 - Titel" or "Serie - 042 - Titel"
    m = re.match(
        r'^(.+?)\s*[-–]\s*(?:Folge\s*)?(\d{1,3})\s*[-–]\s*(.+)$', name, re.IGNORECASE)
    if m:
        result["series"] = m.group(1).strip()
        result["episode"] = int(m.group(2))
        result["title"] = m.group(3).strip()
        return result

    # Pattern 2: "Die drei ??? 001 Titel" or "TKKG 042 - Titel" (space separated)
    m = re.match(
        r'^(.+?)\s+(\d{1,3})\s*[-–]?\s*(.+)$', name, re.IGNORECASE)
    if m:
        result["series"] = m.group(1).strip()
        result["episode"] = int(m.group(2))
        result["title"] = m.group(3).strip().lstrip("-–").strip()
        return result

    # Pattern 3: "001 - Titel" (no series in filename, use folder)
    m = re.match(r'^(\d{1,3})\s*[-–]\s*(.+)$', name)
    if m:
        result["episode"] = int(m.group(1))
        result["title"] = m.group(2).strip()
        result["series"] = filepath.parent.name
        return result

    # Pattern 4: "Folge 001" only
    m = re.match(r'^(?:Folge|Episode|Teil)\s*(\d{1,3})$', name, re.IGNORECASE)
    if m:
        result["episode"] = int(m.group(1))
        result["series"] = filepath.parent.name
        return result

    # Fallback: use filename as title, folder as series
    result["title"] = name
    result["series"] = filepath.parent.name
    return result


def normalize_series(name: str) -> str:
    """Normalize a series name to canonical form."""
    return KNOWN_SERIES.get(name.lower().strip(), name.strip())


# ── ID3 Writing ───────────────────────────────────────────────────────────────

def write_tags(filepath: Path, tags: dict, cover_bytes: bytes | None = None,
               dry_run: bool = False, force: bool = False) -> bool:
    """Write ID3v2.3 tags to an MP3 file. Returns True on success."""

    if dry_run:
        print(f"\n  [DRY-RUN] Würde schreiben: {filepath.name}")
        for k, v in tags.items():
            if v:
                print(f"    {k:14} = {str(v)[:70]}")
        if cover_bytes:
            print(f"    COVER          = {len(cover_bytes)//1024} KB JPEG")
        return True

    try:
        try:
            audio = ID3(str(filepath))
        except ID3NoHeaderError:
            audio = ID3()

        if not force:
            # Skip if already tagged (has ALBUM and TRACKNUMBER)
            if audio.get("TALB") and audio.get("TRCK"):
                existing_mbid = None
                for frame in audio.getall("TXXX"):
                    if frame.desc == "MBID":
                        existing_mbid = frame.text[0] if frame.text else None
                new_mbid = tags.get("MBID")
                if existing_mbid and new_mbid and existing_mbid == new_mbid:
                    print(f"  [SKIP] Bereits korrekt getaggt: {filepath.name}")
                    return True

        # Clear existing tags selectively
        for frame in ["TIT2", "TALB", "TPE1", "TPE2", "TPE3", "TCOM",
                      "TRCK", "TPOS", "TYER", "TCON", "COMM", "TPUB"]:
            audio.delall(frame)
        audio.delall("TXXX")

        def s(v):
            return str(v) if v is not None else ""

        if tags.get("TITLE"):
            audio.add(TIT2(encoding=3, text=s(tags["TITLE"])))
        if tags.get("ALBUM"):
            audio.add(TALB(encoding=3, text=s(tags["ALBUM"])))
        if tags.get("ALBUMARTIST"):
            audio.add(TPE2(encoding=3, text=s(tags["ALBUMARTIST"])))
        if tags.get("ARTIST"):
            audio.add(TPE1(encoding=3, text=s(tags["ARTIST"])))
        if tags.get("COMPOSER"):
            audio.add(TCOM(encoding=3, text=s(tags["COMPOSER"])))
        if tags.get("CONDUCTOR"):
            audio.add(TPE3(encoding=3, text=s(tags["CONDUCTOR"])))
        if tags.get("TRACKNUMBER"):
            audio.add(TRCK(encoding=3, text=s(tags["TRACKNUMBER"])))
        if tags.get("DISCNUMBER"):
            audio.add(TPOS(encoding=3, text=s(tags["DISCNUMBER"])))
        if tags.get("YEAR"):
            audio.add(TYER(encoding=3, text=s(tags["YEAR"])))
        if tags.get("GENRE"):
            audio.add(TCON(encoding=3, text=s(tags["GENRE"])))
        if tags.get("PUBLISHER"):
            audio.add(TPUB(encoding=3, text=s(tags["PUBLISHER"])))
        if tags.get("COMMENT"):
            audio.add(COMM(encoding=3, lang="deu", desc="", text=s(tags["COMMENT"])))
        if tags.get("SERIES"):
            audio.add(TXXX(encoding=3, desc="SERIES", text=s(tags["SERIES"])))
        if tags.get("SERIES_NUM"):
            audio.add(TXXX(encoding=3, desc="SERIES_NUM", text=s(tags["SERIES_NUM"])))
        if tags.get("MBID"):
            audio.add(TXXX(encoding=3, desc="MBID", text=s(tags["MBID"])))

        # Embed cover
        if cover_bytes:
            audio.delall("APIC")
            audio.add(APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,  # Front cover
                desc="Cover",
                data=cover_bytes
            ))

        audio.save(str(filepath), v2_version=3)
        return True

    except Exception as e:
        print(f"  [ERROR] Fehler beim Schreiben: {filepath.name}: {e}")
        return False


# ── MusicBrainz → Tags Mapping ────────────────────────────────────────────────

def release_to_tags(release: dict, episode_num: int = None,
                    series_name: str = None, genre: str = "Hörspiel") -> dict:
    """Convert a MusicBrainz release dict to our tag dict."""
    tags = {}

    # Title
    tags["ALBUM"] = release.get("title", "")
    tags["TITLE"] = release.get("title", "")

    # Series / AlbumArtist
    if series_name:
        tags["ALBUMARTIST"] = series_name
        tags["SERIES"] = series_name

    # Artist credits
    credits = release.get("artist-credit", [])
    artists = []
    for credit in credits:
        if isinstance(credit, dict) and "artist" in credit:
            artists.append(credit["artist"].get("name", ""))
    if artists:
        tags["ARTIST"] = "; ".join(artists)
        if len(artists) == 1 and not tags.get("ALBUMARTIST"):
            tags["ALBUMARTIST"] = artists[0]

    # Label / Publisher
    label_info = release.get("label-info", [])
    for li in label_info:
        label = li.get("label", {})
        if label.get("name"):
            tags["PUBLISHER"] = label["name"]
            break

    # Year
    date = release.get("date", "")
    if date:
        tags["YEAR"] = date[:4]

    # Episode number
    if episode_num is not None:
        tags["TRACKNUMBER"] = f"{episode_num:03d}"
        tags["SERIES_NUM"] = str(episode_num)

    # Genre
    tags["GENRE"] = genre

    # MusicBrainz ID
    if release.get("id"):
        tags["MBID"] = release["id"]

    return tags


# ── Interactive Matching ──────────────────────────────────────────────────────

def choose_release(candidates: list[dict], parsed: dict,
                   interactive: bool = True) -> dict | None:
    """Let user pick from multiple MusicBrainz candidates."""
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if not interactive:
        return candidates[0]  # Take best match

    print(f"\n  Mehrere Treffer für '{parsed.get('title', parsed.get('raw'))}':")
    for i, r in enumerate(candidates):
        year = r.get("date", "")[:4]
        label = ""
        for li in r.get("label-info", []):
            label = li.get("label", {}).get("name", "")
            break
        has_cover = r.get("cover-art-archive", {}).get("front", False)
        cover_icon = "🖼 " if has_cover else "   "
        print(f"  [{i+1}] {cover_icon}{r.get('title', '?')[:55]:<55} "
              f"({year}) {label}")
    print(f"  [0] Überspringen / manuell später")
    while True:
        try:
            choice = input("  Auswahl [1]: ").strip() or "1"
            idx = int(choice)
            if idx == 0:
                return None
            if 1 <= idx <= len(candidates):
                return candidates[idx - 1]
        except (ValueError, KeyboardInterrupt):
            return None


# ── Main Processing ───────────────────────────────────────────────────────────

def process_file(filepath: Path, series_override: str = None,
                 genre: str = "Hörspiel", dry_run: bool = False,
                 force: bool = False, interactive: bool = True,
                 no_cover: bool = False) -> dict:
    """Process a single MP3 file: lookup + tag. Returns result dict."""

    print(f"\n📄 {filepath.name}")

    parsed = parse_filename(filepath)
    series = normalize_series(series_override or parsed.get("series", ""))
    episode = parsed.get("episode")
    title = parsed.get("title", parsed["raw"])

    print(f"  Serie: {series or '(unbekannt)'} | "
          f"Folge: {episode or '?'} | Titel: {title or '?'}")

    # Build MusicBrainz search query
    candidates = []
    search_title = title or parsed["raw"]
    if series:
        full_title = f"{series} {episode:03d}" if episode else series
        candidates = search_release(search_title, series)
        if not candidates and episode:
            candidates = search_release(f"{series} {episode}", series)
        if not candidates:
            candidates = search_release(search_title, series)
    else:
        candidates = search_release(search_title)

    release = choose_release(candidates, parsed, interactive=interactive)

    if release:
        mbid = release["id"]
        print(f"  ✓ MusicBrainz: {release.get('title', '')} [{mbid[:8]}...]")

        # Get full details for better artist credits
        details = get_release_details(mbid)
        if details:
            release = details

        tags = release_to_tags(
            release, episode_num=episode,
            series_name=series, genre=genre
        )

        # Fetch cover
        cover_bytes = None
        if not no_cover:
            cover_bytes = fetch_cover(mbid)
            if cover_bytes:
                print(f"  🖼  Cover: {len(cover_bytes)//1024} KB")
            else:
                print(f"  ⚠️  Kein Cover in Cover Art Archive")
    else:
        print(f"  ⚠️  Nicht in MusicBrainz gefunden — schreibe aus Dateiname")
        tags = {
            "TITLE": title,
            "ALBUM": f"{series} {title}".strip() if series else title,
            "ALBUMARTIST": series or "",
            "TRACKNUMBER": f"{episode:03d}" if episode else "",
            "GENRE": genre,
            "SERIES": series or "",
            "SERIES_NUM": str(episode) if episode else "",
        }
        cover_bytes = None

    success = write_tags(filepath, tags, cover_bytes=cover_bytes,
                         dry_run=dry_run, force=force)

    return {
        "file": str(filepath),
        "success": success,
        "mbid": tags.get("MBID"),
        "title": tags.get("ALBUM"),
        "has_cover": cover_bytes is not None,
    }


def process_folder(folder: Path, series_override: str = None,
                   genre: str = "Hörspiel", dry_run: bool = False,
                   force: bool = False, interactive: bool = True,
                   no_cover: bool = False) -> list[dict]:
    """Process all MP3 files in a folder (recursive)."""
    mp3_files = sorted(folder.rglob("*.mp3"))
    if not mp3_files:
        print(f"Keine MP3-Dateien in {folder} gefunden.")
        return []

    print(f"\n🎧 Verarbeite {len(mp3_files)} MP3-Datei(en) in {folder}")
    results = []
    for f in mp3_files:
        r = process_file(f, series_override=series_override, genre=genre,
                         dry_run=dry_run, force=force, interactive=interactive,
                         no_cover=no_cover)
        results.append(r)

    ok = sum(1 for r in results if r["success"])
    covers = sum(1 for r in results if r["has_cover"])
    print(f"\n✅ Fertig: {ok}/{len(results)} erfolgreich, {covers} Cover eingebettet")
    return results


def process_batch(csv_path: Path, **kwargs) -> list[dict]:
    """Process files listed in a CSV (columns: path, series, episode, title)."""
    import csv
    results = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fp = Path(row["path"])
            if not fp.exists():
                print(f"  [SKIP] Datei nicht gefunden: {fp}")
                continue
            r = process_file(fp,
                             series_override=row.get("series"),
                             genre=row.get("genre", "Hörspiel"),
                             **kwargs)
            results.append(r)
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Hörspiel/Hörbuch MP3 Tagger via MusicBrainz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Ordner taggen (interaktiv)
  python tagger.py --path "/Musik/Die drei ???" --series "Die drei ???"

  # Trockentest (keine Dateien ändern)
  python tagger.py --path "/Musik/TKKG" --dry-run

  # Einzeldatei
  python tagger.py --path "folge001.mp3" --title "Der Super-Papagei"

  # Alle überspringen die schon getaggt sind
  python tagger.py --path "/Musik" --no-interactive

  # Nur Metadaten, kein Cover
  python tagger.py --path "/Musik" --no-cover
        """
    )
    parser.add_argument("--path", required=False, help="MP3-Datei oder Ordner")
    parser.add_argument("--series", help="Serienname (überschreibt Parsing)")
    parser.add_argument("--title", help="Titel (nur bei Einzeldatei)")
    parser.add_argument("--artist", help="Künstler/Sprecher (optional)")
    parser.add_argument("--genre", default="Hörspiel",
                        choices=["Hörspiel", "Hörbuch", "Audiobook"],
                        help="Genre (Standard: Hörspiel)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Keine Dateien schreiben, nur anzeigen")
    parser.add_argument("--force", action="store_true",
                        help="Bereits getaggte Dateien überschreiben")
    parser.add_argument("--no-interactive", action="store_true",
                        help="Besten Treffer automatisch nehmen")
    parser.add_argument("--no-cover", action="store_true",
                        help="Kein Cover-Art einbetten")
    parser.add_argument("--batch", help="CSV-Datei für Batch-Modus")
    parser.add_argument("--output-json", help="Ergebnis als JSON speichern")

    args = parser.parse_args()

    kwargs = dict(
        genre=args.genre,
        dry_run=args.dry_run,
        force=args.force,
        interactive=not args.no_interactive,
        no_cover=args.no_cover,
    )

    results = []

    if args.batch:
        results = process_batch(Path(args.batch), **kwargs)

    elif args.path:
        p = Path(args.path)
        if not p.exists():
            print(f"ERROR: Pfad nicht gefunden: {p}")
            sys.exit(1)
        if p.is_dir():
            results = process_folder(p, series_override=args.series, **kwargs)
        elif p.suffix.lower() == ".mp3":
            results = [process_file(p, series_override=args.series, **kwargs)]
        else:
            print(f"ERROR: Kein MP3 oder Ordner: {p}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    if args.output_json and results:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📋 Ergebnis gespeichert: {args.output_json}")


if __name__ == "__main__":
    main()
