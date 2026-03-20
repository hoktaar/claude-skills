# ID3 Tag Schema für Hörspiele & Hörbücher

## Pflichtfelder

| ID3-Frame | Feld       | Hörspiel-Bedeutung                        | Beispiel                              |
|-----------|------------|-------------------------------------------|---------------------------------------|
| TIT2      | TITLE      | Episodentitel oder Kapitelname            | "und der Super-Papagei"               |
| TALB      | ALBUM      | Voller Titel der Folge/des Buchs          | "Die drei ??? und der Super-Papagei"  |
| TPE2      | ALBUMARTIST| Serienname oder Autor                     | "Die drei ???"                        |
| TRCK      | TRACKNUMBER| Episodennummer (nullgepaddet)             | "001"                                 |
| TYER      | YEAR       | Erscheinungsjahr                          | "1979"                                |
| TCON      | GENRE      | "Hörspiel" oder "Hörbuch"                 | "Hörspiel"                            |

## Empfohlene Felder

| ID3-Frame | Feld       | Hörspiel-Bedeutung                        | Beispiel                              |
|-----------|------------|-------------------------------------------|---------------------------------------|
| TPE1      | ARTIST     | Hauptsprecher oder Ensemble               | "Friedrich W. Bauschulte; Oliver Rohrbeck" |
| TCOM      | COMPOSER   | Buchautor / Drehbuchautor                 | "Robert Arthur"                       |
| TPE3      | CONDUCTOR  | Sprecher/Narrator (primär)                | "Friedrich W. Bauschulte"             |
| TPOS      | DISCNUMBER | CD-Nummer bei Mehrteiler                  | "2"                                   |
| COMM      | COMMENT    | Kurzbeschreibung / Inhaltsangabe          | "Die drei ??? lösen einen Fall..."    |
| APIC      | COVER      | Cover-Bild (JPEG, Type 3 = Front)         | [embedded binary]                     |

## Optionale Felder

| ID3-Frame | Feld       | Bedeutung                                 | Beispiel                              |
|-----------|------------|-------------------------------------------|---------------------------------------|
| TPUB      | PUBLISHER  | Verlag/Label                              | "EUROPA"                              |
| TCOP      | COPYRIGHT  | Copyright-Hinweis                         | "2024 Sony Music Entertainment"       |
| TXXX      | SERIES     | Serienname (Custom Frame)                 | "Die drei ???"                        |
| TXXX      | SERIES_NUM | Nummer in der Serie (Custom Frame)        | "1"                                   |
| TXXX      | MBID       | MusicBrainz Release ID (Custom Frame)     | "830ad0b5-16aa-..."                   |

## Spezialregeln

### Episodennummer
- Immer nullgepaddet auf 3 Stellen: `001`, `042`, `210`
- Sonderfolgen: `S01`, `X01` o.ä.

### ARTIST vs ALBUMARTIST vs CONDUCTOR
- `ALBUMARTIST` = **immer** der Serienname (z.B. "Die drei ???") → für Sortierung
- `ARTIST` = Sprecher/Cast (aus MusicBrainz), kommagetrennt
- `CONDUCTOR` = Hauptsprecher/Narrator (einer, primär)
- `COMPOSER` = Buchautor (Robert Arthur, Stefan Wolf, etc.)

### Mehrteiler (mehrere CDs)
- Alle Teile bekommen denselben `ALBUM`-Tag (den Gesamttitel)
- `DISCNUMBER` gibt die CD-Nummer an
- `TRACKNUMBER` läuft **über alle CDs** weiter durch (nicht 1-x pro CD)

### Cover Art
- Format: JPEG, mind. 500×500px empfohlen
- ID3 APIC Frame: Type 3 (Cover front), MIME: image/jpeg
- Pro Folge individuell — nicht das Serienbanner nehmen

## Beispiel: Die drei ??? Folge 1

```
TITLE      = und der Super-Papagei
ALBUM      = Die drei ??? und der Super-Papagei
ALBUMARTIST= Die drei ???
ARTIST     = Oliver Rohrbeck; Jens Wawrczeck; Andreas Fröhlich
COMPOSER   = Robert Arthur
CONDUCTOR  = Oliver Rohrbeck
TRACKNUMBER= 001
YEAR       = 1979
GENRE      = Hörspiel
PUBLISHER  = EUROPA
COMMENT    = Justus Jonas, Peter Shaw und Bob Andrews lösen ihren ersten Fall.
TXXX:MBID  = 830ad0b5-16aa-4e8d-8134-4de1c5f54bf8
```

## Beispiel: TKKG Folge 42

```
TITLE      = Der Meisterdieb
ALBUM      = TKKG - Der Meisterdieb
ALBUMARTIST= TKKG
ARTIST     = Sascha Draeger; Tobias Diakow; Manou Lubowski; Rhea Harder
COMPOSER   = Stefan Wolf
CONDUCTOR  = Sascha Draeger
TRACKNUMBER= 042
YEAR       = 1986
GENRE      = Hörspiel
PUBLISHER  = EUROPA
```
