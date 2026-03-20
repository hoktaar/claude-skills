---
name: hoerspiel-tagger
description: Tag MP3 files for Hörspiele (audio dramas) and Hörbücher (audiobooks) with correct ID3v2.3 metadata using MusicBrainz as the primary source, including per-episode cover art from the Cover Art Archive. Use this skill whenever the user wants to tag, fix, or organize their Hörspiel or Hörbuch MP3 collection — including series like "Die drei ???", TKKG, Benjamin Blümchen, Bibi Blocksberg, or any EUROPA label release. Also trigger when the user asks about ID3 tags, cover art, MusicBrainz lookups, or batch tagging audio files.
---

# Hörspiel & Hörbuch MP3 Tagger

Tags MP3 collections with proper ID3v2.3 metadata for Hörspiele and Hörbücher.
Uses MusicBrainz for metadata, Cover Art Archive for per-episode covers.

## Quick Start

Run the tagger on a folder or single file:

```bash
pip install mutagen requests --quiet
python scripts/tagger.py --help
```

## Workflow

### 1. Single file / folder lookup
```bash
# Preview tags without writing (dry-run)
python scripts/tagger.py --path "/mnt/Hoerspiele/Die drei ???/Folge 001" --dry-run

# Tag a whole series folder
python scripts/tagger.py --path "/mnt/Hoerspiele/TKKG" --series "TKKG"

# Tag single file
python scripts/tagger.py --path "folge001.mp3" --title "und der Super-Papagei" --artist "Die drei ???"
```

### 2. Interactive mode (recommended for first use)
```bash
python scripts/tagger.py --path "/mnt/Hoerspiele" --interactive
```

### 3. Batch mode with CSV
```bash
python scripts/tagger.py --batch tags.csv
```

## Tag Schema

See `references/tag-schema.md` for the full mapping.

Key fields used:
- `ALBUM` = Episode/book title (e.g. "Die drei ??? und der Super-Papagei")
- `ALBUMARTIST` = Series/Author (e.g. "Die drei ???")
- `ARTIST` = Cast/Sprecher (from MusicBrainz credits)
- `COMPOSER` = Author/Writer
- `CONDUCTOR` = Narrator/Sprecher (main)
- `TRACKNUMBER` = Episode or chapter number (zero-padded, e.g. "001")
- `DISCNUMBER` = CD/disc number for multi-disc releases
- `YEAR` = Release year
- `GENRE` = "Hörspiel" or "Hörbuch"
- `COMMENT` = Short description
- `APIC` = Cover art (embedded JPEG from Cover Art Archive)

## MusicBrainz Search Tips

The script auto-searches by folder/filename patterns like:
- `Die drei ??? 001 - und der Super-Papagei`
- `TKKG - Folge 42 - Der Meisterdieb`
- `Benjamin Blümchen 005`

For ambiguous matches, the script presents options and asks to confirm.

## Cover Art

Cover art is fetched per release (per episode) from Cover Art Archive:
`https://coverartarchive.org/release/{mbid}/front`

Fallback chain:
1. Cover Art Archive (best quality, per episode)
2. Release Group image (series default)
3. Skip (no cover embedded)

Cover images are embedded as `APIC` frames (ID3v2.3, JPEG, type 3 = front cover).

## Error Handling

- Files already correctly tagged → skipped (unless `--force`)
- MusicBrainz not found → tags set from filename, cover skipped
- No internet → tags set from filename only
- Read-only files → error logged, skip

## Reference Files

- `references/tag-schema.md` — Full ID3 tag mapping for Hörspiele/Hörbücher
- `references/series-ids.md` — Known MusicBrainz Artist IDs for popular EUROPA series
