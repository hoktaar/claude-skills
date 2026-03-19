# Stash Scraper Entwicklung

Scrapers liegen in `~/.stash/scrapers/` als `.yml`-Dateien (+ optionale `.py`-Scripts).
Installation über UI: **Settings → Metadata Providers → Available Scrapers → Community (stable)**

Community Scrapers: https://github.com/stashapp/CommunityScrapers (800+ Scrapers)

---

## Scraper YAML — Struktur

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/stashapp/CommunityScrapers/master/validator/scraper.schema.json
name: MeinScraper

# Unterstützte Trigger-Methoden:
sceneByURL:          # Szene per URL scrapen
  - action: scrapeXPath    # oder: scrapeJson | script
    url:
      - example.com/videos/  # URL-Pattern(e)
    scraper: sceneScraper    # Referenz auf xPathScrapers/jsonScrapers unten

sceneByName:         # Szene per Textsuche
  action: scrapeXPath
  queryURL: "https://example.com/search/{}"
  scraper: sceneSearch

sceneByFragment:     # Szene per Fragment (Titel/Dateiname)
  action: scrapeXPath
  queryURL: "https://example.com/search/{title}"
  scraper: sceneScraper

sceneByQueryFragment:  # Wie sceneByFragment aber URL-basiert
  action: scrapeXPath
  queryURL: "{url}"
  scraper: sceneScraper

performerByURL:
  - action: scrapeXPath
    url:
      - example.com/performers/
    scraper: performerScraper

performerByName:
  action: scrapeXPath
  queryURL: "https://example.com/search/performers/{}"
  scraper: performerSearch

galleryByURL:
  - action: scrapeXPath
    url:
      - example.com/galleries/
    scraper: galleryScraper

# Optionale Debug-Einstellungen
debug:
  printHTML: false

# Optionaler Browser-Driver (für JS-heavy Sites)
driver:
  useCDP: false    # true = Chrome DevTools Protocol (braucht konfigurierten CDP-Pfad in Stash)
  headless: true
```

---

## XPath Scraper

```yaml
xPathScrapers:
  sceneScraper:
    # Gemeinsame Variablen mit $-Prefix
    common:
      $baseURL: "https://example.com"
      $info: //div[@class="scene-info"]

    scene:
      Title: $info//h1/text()
      Code:
        selector: //span[@class="scene-code"]/text()
      Details:
        selector: //div[@class="description"]/text()
        postProcess:
          - replace:
              - regex: '^\s+|\s+$'
                with: ""
      Date:
        selector: $info//span[@class="date"]/text()
        postProcess:
          - parseDate: "January 2, 2006"  # Go time format!
      URL: //link[@rel="canonical"]/@href
      Image: //meta[@property="og:image"]/@content

      # Performers — Liste
      Performers:
        Name:
          selector: //a[@class="performer-link"]/text()
        URLs:
          selector: //a[@class="performer-link"]/@href
          postProcess:
            - replace:
                - regex: ^
                  with: "https://example.com"

      # Studio
      Studio:
        Name:
          fixed: "Mein Studio"    # fester Wert
        URL:
          fixed: "https://example.com"

      # Tags
      Tags:
        Name: //a[@class="tag"]/text()

      # Dauer
      Duration:
        selector: //span[@class="duration"]/text()
        postProcess:
          - replace:
              - regex: (\d+):(\d+):(\d+)
                with: "$1h $2m $3s"

  performerSearch:
    performer:
      Name: //h2[@class="name"]/text()
      URLs:
        selector: //a[@class="profile-link"]/@href
        postProcess:
          - replace:
              - regex: ^
                with: "https://example.com"

  performerScraper:
    performer:
      Name: //h1[@class="performer-name"]/text()
      Gender:
        selector: //span[@class="gender"]/text()
        postProcess:
          - replace:
              - regex: '^Female$'
                with: FEMALE
              - regex: '^Male$'
                with: MALE
      Birthdate:
        selector: //span[@class="birthdate"]/text()
        postProcess:
          - parseDate: "January 2, 2006"
      Country: //span[@class="country"]/text()
      Ethnicity:
        selector: //span[@class="ethnicity"]/text()
      HairColor:
        selector: //span[@class="hair"]/text()
      EyeColor:
        selector: //span[@class="eyes"]/text()
      Height:
        selector: //span[@class="height"]/text()
        postProcess:
          - replace:
              - regex: (\d+)cm.*
                with: $1
      Images:
        - selector: //img[@class="profile-photo"]/@src
      Tags:
        Name: //a[@class="category"]/text()
```

---

## JSON Scraper

```yaml
jsonScrapers:
  sceneScraper:
    scene:
      Title:
        selector: "[titleEn, title]"   # Fallback-Selector
        concat: "|"
        split: "|"
      Date:
        selector: releaseDate
        postProcess:
          - parseDate: "2006-01-02"
      Duration: duration
      Image: coverImage
      Performers:
        Name: actressNames   # JSON-Array direkt
      Studio:
        Name:
          fixed: "Studio Name"
      Tags:
        Name: tags
      URL:
        selector: id
        postProcess:
          - replace:
              - regex: ^
                with: "https://example.com/scene/"
```

---

## Python Scraper

Für komplexere Seiten (JavaScript, Login, API):

```python
# mein_scraper.py
import json
import sys

from py_common import log
from py_common.deps import ensure_requirements
from py_common.types import ScrapedScene, ScrapedPerformer, ScrapedStudio, ScrapedTag
from py_common.util import scraper_args

# Abhängigkeiten automatisch installieren
ensure_requirements("requests", "bs4:beautifulsoup4", "lxml")
import requests
from bs4 import BeautifulSoup


def scrape_scene(url: str) -> ScrapedScene | None:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0..."})
    if r.status_code != 200:
        log.error(f"HTTP {r.status_code} for {url}")
        return None

    soup = BeautifulSoup(r.text, "lxml")

    scene: ScrapedScene = {
        "title": soup.select_one("h1.title").text.strip(),
        "date": soup.select_one(".release-date").text.strip(),
        "details": soup.select_one(".description").text.strip(),
        "urls": [url],
        "image": soup.select_one("meta[property='og:image']")["content"],
        "studio": ScrapedStudio(name="Studio Name"),
        "performers": [
            ScrapedPerformer(name=a.text.strip(), urls=[a["href"]])
            for a in soup.select("a.performer")
        ],
        "tags": [
            ScrapedTag(name=t.text.strip())
            for t in soup.select("a.tag")
        ],
    }
    return scene


def scene_by_url(url: str):
    scene = scrape_scene(url)
    if scene:
        print(json.dumps(scene))
    else:
        print(json.dumps({}))


# Argument-Routing
if __name__ == "__main__":
    op, args = scraper_args()   # aus py_common.util

    if op == "scene-by-url":
        scene_by_url(args.get("url", ""))
    elif op == "performer-by-url":
        # ...
        pass
    else:
        log.error(f"Unbekannte Operation: {op}")
        print(json.dumps({}))
```

YAML für Python Scraper:
```yaml
name: MeinScraper
sceneByURL:
  - action: script
    url:
      - example.com/scenes/
    script:
      - python
      - MeinScraper.py
      - scene-by-url
performerByURL:
  - action: script
    url:
      - example.com/performers/
    script:
      - python
      - MeinScraper.py
      - performer-by-url
```

---

## PostProcess-Operationen

```yaml
postProcess:
  - replace:               # Regex-Replace
      - regex: '(\d+)cm'
        with: $1
  - parseDate: "2 January 2006"   # Go-Zeitformat:
                                   # 2006=Jahr, 01=Monat, 02=Tag
                                   # 15=Stunde, 04=Minute, 05=Sekunde
  - split: ", "            # String in Liste aufteilen
  - map:                   # Wert-Mapping
      Female: FEMALE
      Male: MALE
  - feetToCm: true         # 5'7" → 170
  - lbToKg: true           # 130lbs → 59
  - javascript: |          # Inline-JS-Transformation
      result.replace(/\s+/g, ' ').trim()
  - subScraper: //link[@rel="canonical"]/@href   # Ergebnis nochmal scrapen
```

---

## Go-Zeitformate (parseDate)

| Format | Beispiel |
|--------|---------|
| `2006-01-02` | 2024-12-31 |
| `01/02/2006` | 12/31/2024 |
| `2 January 2006` | 31 December 2024 |
| `January 2, 2006` | December 31, 2024 |
| `2. January 2006` | 31. Dezember 2024 |
| `Jan 2, 2006` | Dec 31, 2024 |
| `02.01.2006` | 31.12.2024 |
| `2006/01/02` | 2024/12/31 |

---

## py_common — Standardbibliothek für Scrapers

```python
# Importpfade (liegen in scrapers/py_common/)
from py_common import log                    # Logging
from py_common.deps import ensure_requirements  # Auto-Pip
from py_common.types import ScrapedScene, ScrapedPerformer, ScrapedStudio, ScrapedTag
from py_common.util import scraper_args, dig  # Argument-Parsing, dict-Helper
from py_common.graphql import callGraphQL    # Stash GraphQL (für Scrapers die Stash abfragen)
from py_common.cache import cache_or_load    # Request-Caching

# Logging
log.trace("sehr detailliert")
log.debug("debug info")
log.info("normale info")
log.warning("warnung")
log.error("fehler")

# Argument-Parsing
op, args = scraper_args()
# op = "scene-by-url" | "performer-by-url" | etc.
# args = {"url": "...", ...}

# Nested dict helper
value = dig(data, "studio", "name", default="")

# ensure_requirements — installiert Pakete falls nicht vorhanden
ensure_requirements("requests", "bs4:beautifulsoup4", "lxml", "cloudscraper")
```

---

## Scrapers testen

```bash
# Direkt aus Stash-Verzeichnis testen:
echo '{"url": "https://example.com/scene/123"}' | python3 mein_scraper.py scene-by-url

# Scrapers neu laden (nach Änderungen):
# Stash UI → Settings → Metadata Providers → Reload Scrapers
# Oder: GraphQL mutation { reloadScrapers }
```

---

## Wichtige Community Scrapers (Beispiele)

Über 800 Scrapers verfügbar. Installation: **Settings → Metadata Providers → Community (stable)**

Für eigene Scrapers: `~/.stash/scrapers/` — beliebiger Dateiname mit `.yml`-Extension.

Manuelle Installation wenn nötig:
```bash
# Alle Community Scrapers auf einmal
cd ~/.stash/scrapers
git clone https://github.com/stashapp/CommunityScrapers.git
# Dann in Stash: Settings → Reload Scrapers
```
