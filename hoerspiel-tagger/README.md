# hoerspiel-tagger Skill

MP3-Sammlungen von Hörspielen und Hörbüchern automatisch mit korrekten ID3v2.3-Tags versehen — inklusive Cover-Art pro Folge. Nutzt [MusicBrainz](https://musicbrainz.org) als Metadatenquelle und das [Cover Art Archive](https://coverartarchive.org) für Folgen-spezifische Cover.

Besonders geeignet für EUROPA-Serien wie „Die drei ???", TKKG, Benjamin Blümchen, Bibi Blocksberg und andere Hörspielserien.

## Installation

```bash
claude skill install https://github.com/hoktaar/claude-skills/tree/main/hoerspiel-tagger
```

## Voraussetzungen

- Python-Abhängigkeit:

```bash
pip install mutagen
```

## Schnellstart

```bash
# Trockentest — keine Dateien werden verändert
python tagger.py --path "/mnt/Hoerspiele/Die drei ???" --dry-run

# Ordner taggen (interaktiv, fragt bei mehreren Treffern)
python tagger.py --path "/mnt/Hoerspiele/Die drei ???" --series "Die drei ???"

# Einzeldatei taggen
python tagger.py --path "folge001.mp3" --series "TKKG"

# Automatisch (besten Treffer nehmen, keine Rückfragen)
python tagger.py --path "/mnt/Hoerspiele/TKKG" --no-interactive

# Ohne Cover-Art (nur Metadaten)
python tagger.py --path "/mnt/Hoerspiele" --series "Benjamin Blümchen" --no-cover

# Bereits getaggte Dateien überschreiben
python tagger.py --path "/mnt/Hoerspiele/TKKG" --force
```

## Tag-Schema

| ID3-Feld      | Bedeutung                         | Beispiel                            |
|---------------|-----------------------------------|-------------------------------------|
| `ALBUM`       | Voller Episodentitel              | Die drei ??? und der Super-Papagei  |
| `ALBUMARTIST` | Serienname                        | Die drei ???                        |
| `ARTIST`      | Sprecher/Cast (aus MusicBrainz)   | Oliver Rohrbeck; Jens Wawrczeck     |
| `COMPOSER`    | Buchautor                         | Robert Arthur                       |
| `CONDUCTOR`   | Hauptsprecher/Narrator            | Friedrich W. Bauschulte             |
| `TRACKNUMBER` | Episodennummer (nullgepaddet)     | 001                                 |
| `YEAR`        | Erscheinungsjahr                  | 1979                                |
| `GENRE`       | `Hörspiel` oder `Hörbuch`         | Hörspiel                            |
| `COMMENT`     | Kurzbeschreibung                  | Justus Jonas löst seinen ersten...  |
| `APIC`        | Cover-Art (JPEG, Front Cover)     | [embedded, 500×500 px]              |

## Unterstützte Dateinamen-Formate

Der Skill erkennt folgende Muster automatisch:

```
Die drei ??? - 001 - und der Super-Papagei.mp3
TKKG 042 - Der Meisterdieb.mp3
Benjamin Blümchen 005 - Er wird Lokomotivführer.mp3
001 - und der Super-Papagei.mp3   ← Serienname aus Ordnername
```

## Cover-Art

Cover werden pro Release (d.h. pro Folge) aus dem Cover Art Archive geladen:

```
https://coverartarchive.org/release/{mbid}/front
```

Abdeckung bei EUROPA-Serien laut Stichprobe ~84 % aller Folgen. Fehlendes Cover wird übersprungen, die übrigen Tags werden trotzdem geschrieben.

## Batch-Modus

Mehrere Dateien mit unterschiedlichen Serien über eine CSV-Datei verarbeiten:

```csv
path,series,genre
/mnt/Hoerspiele/3F/001.mp3,Die drei ???,Hörspiel
/mnt/Hoerspiele/TKKG/042.mp3,TKKG,Hörspiel
/mnt/Hoerspiele/Buecher/kapitel01.mp3,Terry Pratchett,Hörbuch
```

```bash
python tagger.py --batch meine_sammlung.csv
```

## Ergebnis als JSON speichern

```bash
python tagger.py --path "/mnt/Hoerspiele" --output-json ergebnis.json
```

## Bekannte MusicBrainz-Serien-IDs

| Serie             | MusicBrainz Artist ID                        | Releases |
|-------------------|----------------------------------------------|----------|
| Die drei ???      | `e028fab5-39ae-4ed9-b8c2-c4344d88b171`       | ~1190    |
| TKKG              | `d3d9bc09-f1c1-49bc-94e0-e7897f60f4c3`       | ~686     |
| Benjamin Blümchen | (Suche per Name)                             | ~537     |
| Bibi Blocksberg   | (Suche per Name)                             | ~456     |
| Hui Buh           | (Suche per Name)                             | ~163     |

## Referenz-Dateien

| Datei                           | Beschreibung                                        |
|---------------------------------|-----------------------------------------------------|
| `scripts/tagger.py`             | Haupt-Script: MusicBrainz-Lookup, Cover, ID3-Schreiben |
| `references/tag-schema.md`      | Vollständiges ID3-Tag-Schema mit Beispielen         |
| `references/series-ids.md`      | Bekannte MusicBrainz-IDs + API-Endpoints            |

## Links

- [MusicBrainz](https://musicbrainz.org)
- [Cover Art Archive](https://coverartarchive.org)
- [MusicBrainz API Docs](https://musicbrainz.org/doc/MusicBrainz_API)
- [mutagen (Python)](https://mutagen.readthedocs.io)
- [ID3-Standard](https://id3.org)
