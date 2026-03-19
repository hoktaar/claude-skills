# nginx-proxy-manager Skill

Nginx Proxy Manager (NPM) per API steuern — Proxy Hosts anlegen, bearbeiten, löschen, aktivieren/deaktivieren und SSL-Zertifikate verwalten. Alles über die offizielle REST API von NPM.

## Installation

```bash
claude skill install https://github.com/hoktaar/claude-skills/tree/main/nginx-proxy-manager
```

## Voraussetzungen

- Nginx Proxy Manager läuft als Docker auf Unraid (BigServer, `192.168.1.144:81`)
- Python mit `requests`: `pip install requests`

## Schnellstart

```python
import requests

NPM_URL = "http://192.168.1.144:81/api"

# Token holen
token = requests.post(f"{NPM_URL}/tokens", json={
    "identity": "admin@example.com",
    "secret": "deinPasswort"
}).json()["token"]

h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Neuen Proxy Host anlegen
requests.post(f"{NPM_URL}/nginx/proxy-hosts", headers=h, json={
    "domain_names": ["meinservice.domain.de"],
    "forward_scheme": "http",
    "forward_host": "192.168.1.144",
    "forward_port": 8080,
    "block_exploits": True,
}).raise_for_status()
```

## Was der Skill abdeckt

- Token-Authentifizierung (JWT, läuft nach 1 Tag ab)
- Proxy Host anlegen: HTTP, HTTPS, mit/ohne SSL, mit WebSocket-Support
- Let's Encrypt SSL-Zertifikat automatisch beantragen und dem Host zuweisen
- Alle Host-Felder dokumentiert (domain, port, SSL, HSTS, HTTP/2, WebSocket, Advanced Config…)
- Bestehende Hosts auflisten, bearbeiten, aktivieren, deaktivieren, löschen
- Zertifikate auflisten, erneuern, löschen
- Häufige Fehler und ihre Lösung

## Kommandozeilen-Tool

Das mitgelieferte `references/npm_helper.py` kann direkt als CLI verwendet werden:

```bash
# Alle Hosts auflisten
python npm_helper.py list

# Neuen Host ohne SSL
python npm_helper.py add --domain service.domain.de --port 8080

# Neuen Host mit Let's Encrypt SSL
python npm_helper.py add --domain service.domain.de --port 8080 --ssl

# Mit WebSocket + SSL (z.B. für Home Assistant, Grafana, OpenWebUI)
python npm_helper.py add --domain ha.domain.de --port 8123 --ssl --websocket

# Host löschen/aktivieren/deaktivieren
python npm_helper.py delete --id 5
python npm_helper.py enable --id 5
python npm_helper.py disable --id 5

# Zertifikate auflisten
python npm_helper.py certs
```

## Referenz-Dateien

| Datei | Beschreibung |
|-------|-------------|
| `references/npm_helper.py` | Fertiges CLI-Skript für alle gängigen Operationen |

## Links

- [NPM GitHub](https://github.com/NginxProxyManager/nginx-proxy-manager)
- [NPM Web-UI (BigServer)](http://192.168.1.144:81)
