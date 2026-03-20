# Bekannte MusicBrainz Artist-IDs — EUROPA Hörspiele

Direkt verwenden um API-Suche zu beschleunigen und Fehlmatches zu vermeiden.

## EUROPA Serien

| Serie              | MB Artist ID                           | Releases | Genre    |
|--------------------|----------------------------------------|----------|----------|
| Die drei ???       | e028fab5-39ae-4ed9-b8c2-c4344d88b171   | ~1190    | Hörspiel |
| Die drei ??? Kids  | 92bc25ee-decc-4d83-9932-e1b4bd20a749   | ~150     | Hörspiel |
| TKKG (Stefan Wolf) | d3d9bc09-f1c1-49bc-94e0-e7897f60f4c3   | ~686     | Hörspiel |
| Benjamin Blümchen  | (suchen per Name)                      | ~537     | Hörspiel |
| Bibi Blocksberg    | (suchen per Name)                      | ~456     | Hörspiel |
| Hui Buh            | (suchen per Name)                      | ~163     | Hörspiel |

## EUROPA Label

| Label   | MB Label ID                            |
|---------|----------------------------------------|
| EUROPA  | 0acc7c46-8f5f-4ea5-9429-a029bfd718c0   |

## API Endpoints

```
# Artist-Suche
GET https://musicbrainz.org/ws/2/artist/?query={name}&fmt=json

# Releases eines Artists
GET https://musicbrainz.org/ws/2/release/?artist={mbid}&fmt=json&limit=100

# Release suchen (Titel + Artist)
GET https://musicbrainz.org/ws/2/release/?query=release:"{title}"+AND+artist:"{artist}"&fmt=json

# Cover Art (front)
GET https://coverartarchive.org/release/{release-mbid}/front

# Cover Art (alle)
GET https://coverartarchive.org/release/{release-mbid}
```

## Rate Limits

MusicBrainz: max. 1 Request/Sekunde ohne Auth-Key.
Mit Account + API-Key: höhere Limits möglich.
User-Agent Header ist Pflicht: `MyApp/1.0 ( user@example.com )`

Cover Art Archive: keine bekannten strikten Limits, trotzdem Rate-Limiting empfohlen.

## Namenskonventionen in MusicBrainz

Für die Suche wichtig:
- "Die drei ???" → korrekt mit Fragezeichen, ohne Anführungszeichen
- "TKKG" → wird unter Artist "Stefan Wolf" geführt
- Episodentitel: oft mit Folgen-Präfix, z.B. "Die drei ??? 1: und der Super-Papagei"
