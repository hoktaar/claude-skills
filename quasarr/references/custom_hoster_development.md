# Quasarr: Eigene Hoster entwickeln

Quasarr erkennt neue Quellen **automatisch** per Plugin-Discovery — es reichen zwei neue Python-Dateien.  
Jede Quelle besteht aus:

1. **Search Source** (`quasarr/search/sources/<kürzel>.py`) — Suche + Feed
2. **Download Source** (`quasarr/downloads/sources/<kürzel>.py`) — Link-Extraktion von der Seite

Beides muss das gleiche Kürzel (`initials`) haben. Das Kürzel entspricht auch dem Dateinamen.

---

## Schritt 1: Hostname registrieren

Das Kürzel wird automatisch aus dem Dateinamen der Search Source abgeleitet. Damit Quasarr ihn in der Konfig und im Web-UI anzeigt, reicht es, `quasarr/search/sources/<kürzel>.py` zu erstellen — `get_hostnames()` in `search/sources/helpers/__init__.py` liest alle Module automatisch ein.

Für Login-Quellen muss die Search Source `requires_login = True` haben (dann erscheint die Quelle in der Credentials-Sektion).

---

## Schritt 2: Search Source erstellen

**Pflicht-Properties:**

| Property | Typ | Beschreibung |
|----------|-----|-------------|
| `initials` | `str` | Kürzel, z.B. `"xy"` — muss Dateiname entsprechen |
| `supports_imdb` | `bool` | Suche per IMDb-ID möglich? |
| `supports_phrase` | `bool` | Freitextsuche möglich? |
| `supported_categories` | `list[int]` | Welche Kategorien werden unterstützt |
| `requires_login` | `bool` | Braucht die Quelle Login-Credentials? (default: `False`) |

**Pflicht-Methoden:**

| Methode | Beschreibung |
|---------|-------------|
| `search(...)` | Gezielte Suche (nach IMDb-ID / Suchbegriff) |
| `feed(...)` | Neueste Releases laden (kein Suchbegriff) |

**Kategorie-Konstanten** (aus `quasarr.constants`):

```python
SEARCH_CAT_MOVIES      = 2000   # Filme
SEARCH_CAT_MOVIES_HD   = 2040
SEARCH_CAT_MOVIES_UHD  = 2045
SEARCH_CAT_SHOWS       = 5000   # Serien
SEARCH_CAT_SHOWS_HD    = 5040
SEARCH_CAT_SHOWS_UHD   = 5045
SEARCH_CAT_SHOWS_ANIME = 5070
SEARCH_CAT_SHOWS_DOCUMENTARY = 5080
SEARCH_CAT_MUSIC       = 3000
SEARCH_CAT_BOOKS       = 7000
SEARCH_CAT_XXX         = 6000
```

### Minimal-Template (ohne Login)

```python
# quasarr/search/sources/xy.py
import time
import requests
from bs4 import BeautifulSoup
from quasarr.constants import (
    FEED_REQUEST_TIMEOUT_SECONDS,
    SEARCH_REQUEST_TIMEOUT_SECONDS,
    SEARCH_CAT_MOVIES,
    SEARCH_CAT_SHOWS,
)
from quasarr.providers import shared_state
from quasarr.providers.hostname_issues import clear_hostname_issue, mark_hostname_issue
from quasarr.providers.log import debug, warn
from quasarr.providers.utils import (
    convert_to_mb,
    generate_download_link,
    get_base_search_category_id,
    is_valid_release,
)
from quasarr.search.sources.helpers.search_release import SearchRelease
from quasarr.search.sources.helpers.search_source import AbstractSearchSource


class Source(AbstractSearchSource):
    initials = "xy"
    supports_imdb = True
    supports_phrase = False
    supported_categories = [SEARCH_CAT_MOVIES, SEARCH_CAT_SHOWS]

    def _get_hostname(self, shared_state):
        return shared_state.values["config"]("Hostnames").get(self.initials)

    def _parse_releases(self, soup, shared_state, password, search_category=None,
                         search_string=None, season=None, episode=None, is_search=False):
        releases = []
        hostname = self._get_hostname(shared_state)

        for item in soup.select("div.release"):  # ← Selektoren anpassen
            try:
                title = item.select_one("h2 a").get_text(strip=True)
                source_url = item.select_one("h2 a")["href"]

                if is_search and not is_valid_release(
                    title, search_category, search_string, season, episode
                ):
                    continue

                # Größe extrahieren
                size_text = item.select_one(".size")
                size_mb = 0
                if size_text:
                    import re
                    m = re.search(r"([\d.,]+)\s*(MB|GB)", size_text.text, re.I)
                    if m:
                        size_mb = convert_to_mb({"size": m.group(1).replace(",", "."),
                                                  "sizeunit": m.group(2)})

                # IMDb-ID extrahieren (optional)
                import re
                from quasarr.constants import IMDB_REGEX
                imdb_id = None
                m = IMDB_REGEX.search(str(item))
                if m:
                    imdb_id = m.group(1)

                link = generate_download_link(
                    shared_state, title, source_url, size_mb, password, imdb_id, self.initials
                )

                releases.append({
                    "details": {
                        "title": title,
                        "hostname": self.initials,
                        "imdb_id": imdb_id or "",
                        "link": link,
                        "size": size_mb * 1024 * 1024,
                        "date": "",
                        "source": source_url,
                    },
                    "type": "protected",
                })
            except Exception as e:
                debug(f"Error parsing release: {e}")
        return releases

    def feed(self, shared_state, start_time, search_category):
        hostname = self._get_hostname(shared_state)
        base_cat = get_base_search_category_id(search_category)

        if base_cat == SEARCH_CAT_MOVIES:
            url = f"https://{hostname}/filme/"        # ← URL anpassen
        elif base_cat == SEARCH_CAT_SHOWS:
            url = f"https://{hostname}/serien/"       # ← URL anpassen
        else:
            return []

        headers = {"User-Agent": shared_state.values["user_agent"]}
        try:
            r = requests.get(url, headers=headers, timeout=FEED_REQUEST_TIMEOUT_SECONDS)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")
            releases = self._parse_releases(soup, shared_state, hostname)
            clear_hostname_issue(self.initials)
        except Exception as e:
            warn(f"Feed error: {e}")
            mark_hostname_issue(self.initials, "feed", str(e))
            releases = []

        debug(f"Time taken: {time.time() - start_time:.2f}s")
        return releases

    def search(self, shared_state, start_time, search_category,
               search_string="", season=None, episode=None):
        hostname = self._get_hostname(shared_state)
        from urllib.parse import quote_plus
        q = quote_plus(search_string)
        url = f"https://{hostname}/?s={q}"            # ← URL anpassen

        headers = {"User-Agent": shared_state.values["user_agent"]}
        try:
            r = requests.get(url, headers=headers, timeout=SEARCH_REQUEST_TIMEOUT_SECONDS)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")
            releases = self._parse_releases(
                soup, shared_state, hostname,
                search_category=search_category,
                search_string=search_string,
                season=season,
                episode=episode,
                is_search=True,
            )
            clear_hostname_issue(self.initials)
        except Exception as e:
            warn(f"Search error: {e}")
            mark_hostname_issue(self.initials, "search", str(e))
            releases = []

        debug(f"Time taken: {time.time() - start_time:.2f}s")
        return releases
```

### Template mit Login (requires_login = True)

```python
class Source(AbstractSearchSource):
    initials = "xy"
    supports_imdb = True
    supports_phrase = False
    supported_categories = [SEARCH_CAT_MOVIES, SEARCH_CAT_SHOWS]
    requires_login = True          # ← Login-Pflicht

    def _get_session(self, shared_state):
        # Session-Modul importieren (muss in providers/sessions/<kürzel>.py existieren)
        from quasarr.providers.sessions.xy import retrieve_and_validate_session
        return retrieve_and_validate_session(shared_state)

    def feed(self, shared_state, start_time, search_category):
        hostname = shared_state.values["config"]("Hostnames").get(self.initials)
        sess = self._get_session(shared_state)
        if not sess:
            mark_hostname_issue(self.initials, "feed", "Session error")
            return []
        # ... wie oben, aber sess.get() statt requests.get() verwenden
```

---

## Schritt 3: Download Source erstellen

Die Download Source extrahiert die tatsächlichen Links von der Hoster-Seite (wird aufgerufen wenn Radarr/Sonarr einen Release herunterlädt).

**Pflicht:** `initials` + `get_download_links()`

### Minimal-Template (ohne Login)

```python
# quasarr/downloads/sources/xy.py
import requests
from bs4 import BeautifulSoup
from quasarr.constants import DOWNLOAD_REQUEST_TIMEOUT_SECONDS
from quasarr.downloads.sources.helpers.abstract_source import AbstractDownloadSource
from quasarr.providers.hostname_issues import clear_hostname_issue, mark_hostname_issue
from quasarr.providers.log import debug, info


class Source(AbstractDownloadSource):
    initials = "xy"

    def get_download_links(self, shared_state, url, mirrors, title, password):
        headers = {"User-Agent": shared_state.values["user_agent"]}

        try:
            r = requests.get(url, headers=headers, timeout=DOWNLOAD_REQUEST_TIMEOUT_SECONDS)
            r.raise_for_status()
        except Exception as e:
            info(f"Failed to fetch page for {title}: {e}")
            mark_hostname_issue(self.initials, "download", str(e))
            return {"links": []}

        soup = BeautifulSoup(r.text, "html.parser")
        download_links = []

        # Beispiel: filecrypt-Links extrahieren
        import re
        pattern = re.compile(r"https?://(?:www\.)?filecrypt\.[^/]+/Container/", re.IGNORECASE)
        for a in soup.find_all("a", href=pattern):
            href = a["href"]
            hoster = a.get_text(strip=True).lower()

            # Nur gewünschte Mirror (wenn mirrors-Filter gesetzt)
            if mirrors and not any(m.lower() in hoster for m in mirrors):
                debug(f'Skipping link from "{hoster}" (not in mirrors {mirrors})')
                continue

            download_links.append([href, hoster])

        if not download_links:
            info(f"No download links found for {title} - {url}")
            mark_hostname_issue(self.initials, "download", "No links found")
            return {"links": []}

        clear_hostname_issue(self.initials)
        return {"links": download_links}
```

**Return-Format:**
```python
# Minimal:
{"links": [["https://filecrypt.cc/Container/abc123", "rapidgator"]]}

# Mit Passwort-Override (überschreibt was die Search Source gefunden hat):
{"links": [...], "password": "geheimesPasswort"}

# Mit IMDb-ID-Override:
{"links": [...], "imdb_id": "tt1234567"}

# Links mit Status-URL (für Online-Check):
{"links": [["https://filecrypt.cc/Container/abc", "rapidgator", "https://filecrypt.cc/Stat/abc"]]}
```

---

## Schritt 4: Session-Provider (nur bei Login-Pflicht)

Für Login-Quellen braucht Quasarr ein Session-Modul in `quasarr/providers/sessions/<kürzel>.py`.  
Außerdem muss die Config-Sektion in `quasarr/storage/config.py` → `_DEFAULT_CONFIG` eingetragen werden.

### Config-Eintrag (in `storage/config.py`)

```python
_DEFAULT_CONFIG = {
    ...
    "XY": [(\"user\", \"secret\", \"\"), (\"password\", \"secret\", \"\")],  # ← hinzufügen
}
```

### Session-Template

```python
# quasarr/providers/sessions/xy.py
import pickle
import requests
from quasarr.constants import SESSION_REQUEST_TIMEOUT_SECONDS
from quasarr.providers.hostname_issues import clear_hostname_issue, mark_hostname_issue
from quasarr.providers.log import debug, info

hostname = "xy"

def create_and_persist_session(shared_state):
    host = shared_state.values["config"]("Hostnames").get(hostname)
    creds = shared_state.values["config"](hostname.upper())
    user = creds.get("user")
    password = creds.get("password")

    if not user or not password:
        mark_hostname_issue(hostname, "session", "Missing credentials")
        return None

    sess = requests.Session()
    sess.headers.update({"User-Agent": shared_state.values["user_agent"]})

    try:
        # Login-Flow der Seite nachbauen
        login_url = f"https://www.{host}/login/"
        r = sess.get(login_url, timeout=SESSION_REQUEST_TIMEOUT_SECONDS)
        r.raise_for_status()

        # CSRF-Token extrahieren (falls nötig)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        csrf = soup.find("input", {"name": "_token"})
        csrf_val = csrf["value"] if csrf else ""

        # Login POST
        login_data = {"username": user, "password": password, "_token": csrf_val}
        r = sess.post(login_url, data=login_data, timeout=SESSION_REQUEST_TIMEOUT_SECONDS)
        r.raise_for_status()

        # Login prüfen (z.B. Profil-Element vorhanden?)
        if "logout" not in r.text.lower():
            info("Login failed - check credentials")
            mark_hostname_issue(hostname, "session", "Login failed")
            return None

        # Session speichern
        shared_state.get_db("sessions").update_store(
            hostname, pickle.dumps(sess).hex()
        )
        clear_hostname_issue(hostname)
        debug("Session created and persisted")
        return sess

    except Exception as e:
        mark_hostname_issue(hostname, "session", str(e))
        return None


def retrieve_and_validate_session(shared_state):
    raw = shared_state.get_db("sessions").retrieve(hostname)
    if raw:
        try:
            return pickle.loads(bytes.fromhex(raw))
        except Exception:
            pass
    return create_and_persist_session(shared_state)


def invalidate_session(shared_state):
    shared_state.get_db("sessions").delete(hostname)


def fetch_via_requests_session(shared_state, method, target_url, **kwargs):
    sess = retrieve_and_validate_session(shared_state)
    if not sess:
        return None
    return sess.request(method, target_url, **kwargs)
```

---

## Hilfs-Funktionen (aus `quasarr.providers.utils`)

| Funktion | Beschreibung |
|----------|-------------|
| `generate_download_link(shared_state, title, url, size_mb, password, imdb_id, source_key)` | Erzeugt den verschlüsselten Quasarr-Download-Link für Radarr/Sonarr |
| `convert_to_mb({"size": "1.5", "sizeunit": "GB"})` | Konvertiert Größenangaben in MB |
| `is_valid_release(title, category, search_string, season, episode)` | Prüft ob ein Release-Titel zur Suche passt |
| `get_base_search_category_id(search_category)` | Gibt die Basis-Kategorie zurück (z.B. 5040 → 5000) |
| `is_imdb_id(string)` | Gibt IMDb-ID zurück falls der String eine ist, sonst `None` |
| `generate_status_url(href, crypter_type)` | Erzeugt Status-URL für Link-Online-Check |
| `check_links_online_status(links, shared_state)` | Prüft welche Links online sind |

**Hostname-Issue-Tracking** (aus `quasarr.providers.hostname_issues`):

```python
from quasarr.providers.hostname_issues import clear_hostname_issue, mark_hostname_issue

mark_hostname_issue("xy", "search", "Beschreibung des Fehlers")  # Fehler markieren
mark_hostname_issue("xy", "feed", "Feed nicht erreichbar")
mark_hostname_issue("xy", "download", "Seite geändert")
mark_hostname_issue("xy", "session", "Login fehlgeschlagen")

clear_hostname_issue("xy")  # Problem behoben → grüner Status im Web-UI
```

---

## Checkliste: Neue Quelle hinzufügen

```
[ ] quasarr/search/sources/<kürzel>.py      → AbstractSearchSource implementieren
[ ] quasarr/downloads/sources/<kürzel>.py   → AbstractDownloadSource implementieren
[ ] Bei Login-Pflicht:
    [ ] quasarr/providers/sessions/<kürzel>.py  → Session-Provider erstellen
    [ ] quasarr/storage/config.py               → "<KÜRZEL>" Section in _DEFAULT_CONFIG
[ ] Quasarr neu starten → Kürzel erscheint automatisch im Hostnames-UI
[ ] Hostname eintragen → Quelle ist aktiv
```

---

## Linkcrypter-Typen (in Download Sources erkennbar)

Quasarr versteht folgende Linkcrypter-Typen:

| Typ | Pattern | Besonderheit |
|-----|---------|-------------|
| `filecrypt` | `filecrypt.` | CAPTCHA möglich, Status-URL via Stat-Endpoint |
| `hide` | `hide.` | Auto-decrypt (kein CAPTCHA), Status-URL generierbar |
| `tolink` | `tolink.` | CAPTCHA möglich, Status-URL generierbar |
| `keeplinks` | `keeplinks.` | CAPTCHA möglich |

Links werden nach dem Extrahieren automatisch durch `quasarr/downloads/linkcrypters/` entschlüsselt.  
Eigene Linkcrypter können dort analog hinzugefügt werden.
