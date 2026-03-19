---
name: nginx-proxy-manager
description: Nginx Proxy Manager (NPM) per API steuern — Proxy Hosts anlegen, bearbeiten, löschen, aktivieren/deaktivieren, SSL-Zertifikate verwalten und bestehende Hosts abfragen. Immer verwenden wenn der User NPM, Nginx Proxy Manager, Reverse Proxy, Proxy Host, neue Domain, Subdomain für Docker-Container oder SSL-Zertifikat auf seinem Unraid-System erwähnt. Auch triggern bei "leg mir einen Host an", "füge eine Domain hinzu", "richte einen Reverse Proxy ein" — der Skill enthält alle nötigen API-Calls als fertiges Python-Script.
---

# Nginx Proxy Manager Skill

NPM läuft auf BigServer (Unraid, 192.168.1.144) als Docker-Container und ist über seine REST API steuerbar.

**NPM API Base URL:** `http://192.168.1.144:81/api`  
**Authentifizierung:** JWT Bearer Token (läuft nach 1 Tag ab → neu anfordern)

---

## Authentifizierung

```python
import requests

NPM_URL = "http://192.168.1.144:81/api"
NPM_EMAIL = "admin@example.com"   # NPM-Login E-Mail
NPM_PASS  = "deinPasswort"        # NPM-Login Passwort

def get_token():
    r = requests.post(f"{NPM_URL}/tokens", json={
        "identity": NPM_EMAIL,
        "secret": NPM_PASS,
        "scope": "user"
    })
    r.raise_for_status()
    return r.json()["token"]

def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
```

---

## Proxy Host anlegen (häufigster Use Case)

### Minimal (nur HTTP, kein SSL)

```python
token = get_token()

r = requests.post(f"{NPM_URL}/nginx/proxy-hosts", headers=headers(token), json={
    "domain_names": ["meinservice.deine-domain.de"],
    "forward_scheme": "http",
    "forward_host": "192.168.1.144",   # Unraid IP
    "forward_port": 8080,              # Container-Port
    "block_exploits": True,
    "allow_websocket_upgrade": False,
})
r.raise_for_status()
print("Host erstellt, ID:", r.json()["id"])
```

### Mit neuem Let's Encrypt SSL-Zertifikat

```python
token = get_token()
domain = "meinservice.deine-domain.de"

# 1. Zertifikat erstellen (dauert ~30 Sek, domain muss öffentlich erreichbar sein)
cert = requests.post(f"{NPM_URL}/nginx/certificates", headers=headers(token), json={
    "provider": "letsencrypt",
    "domain_names": [domain],
    "meta": {"dns_challenge": False, "letsencrypt_agree": True}
})
cert.raise_for_status()
cert_id = cert.json()["id"]

# 2. Proxy Host mit SSL anlegen
r = requests.post(f"{NPM_URL}/nginx/proxy-hosts", headers=headers(token), json={
    "domain_names": [domain],
    "forward_scheme": "http",
    "forward_host": "192.168.1.144",
    "forward_port": 8080,
    "certificate_id": cert_id,
    "ssl_forced": True,
    "hsts_enabled": False,
    "http2_support": True,
    "block_exploits": True,
    "allow_websocket_upgrade": False,
    "meta": {"letsencrypt_agree": True, "dns_challenge": False}
})
r.raise_for_status()
print("Host mit SSL erstellt, ID:", r.json()["id"])
```

### Mit vorhandenem Zertifikat

```python
# Zertifikate auflisten → ID raussuchen
certs = requests.get(f"{NPM_URL}/nginx/certificates", headers=headers(token)).json()
for c in certs:
    print(c["id"], c.get("nice_name"), c.get("domain_names"))

# Dann cert_id = <gefundene ID> im Host-Create verwenden
```

### Backend läuft auf HTTPS

```python
r = requests.post(f"{NPM_URL}/nginx/proxy-hosts", headers=headers(token), json={
    "domain_names": ["secure-service.domain.de"],
    "forward_scheme": "https",        # ← https statt http
    "forward_host": "192.168.1.144",
    "forward_port": 8443,
    "certificate_id": cert_id,
    "ssl_forced": True,
    "trust_forwarded_proto": True,    # ← wichtig bei HTTPS-Backend
    "block_exploits": True,
})
```

### Mit WebSocket-Support (z.B. für Home Assistant, Grafana, OpenWebUI)

```python
r = requests.post(f"{NPM_URL}/nginx/proxy-hosts", headers=headers(token), json={
    "domain_names": ["homeassistant.domain.de"],
    "forward_scheme": "http",
    "forward_host": "192.168.1.144",
    "forward_port": 8123,
    "allow_websocket_upgrade": True,  # ← WebSocket aktivieren
    "block_exploits": True,
    "certificate_id": cert_id,
    "ssl_forced": True,
})
```

---

## Alle Felder eines Proxy Hosts

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|-------------|
| `domain_names` | `list[str]` | **Pflicht** | Domains/Subdomains |
| `forward_scheme` | `str` | **Pflicht** | `"http"` oder `"https"` |
| `forward_host` | `str` | **Pflicht** | Ziel-IP oder Hostname |
| `forward_port` | `int` | **Pflicht** | Ziel-Port (1–65535) |
| `certificate_id` | `int\|0` | `0` | SSL-Zertifikat ID (0 = keins) |
| `ssl_forced` | `bool` | `false` | HTTP → HTTPS Redirect |
| `hsts_enabled` | `bool` | `false` | HSTS-Header aktivieren |
| `hsts_subdomains` | `bool` | `false` | HSTS auch für Subdomains |
| `http2_support` | `bool` | `false` | HTTP/2 aktivieren |
| `block_exploits` | `bool` | `false` | Basis-Exploit-Schutz |
| `caching_enabled` | `bool` | `false` | Response-Caching |
| `allow_websocket_upgrade` | `bool` | `false` | WebSocket-Support |
| `trust_forwarded_proto` | `bool` | `false` | X-Forwarded-Proto vertrauen |
| `access_list_id` | `int` | `0` | Access List ID (0 = keine) |
| `advanced_config` | `str` | `""` | Roh-Nginx-Direktiven |
| `enabled` | `bool` | `true` | Host aktiv? |
| `locations` | `list` | `[]` | Custom Location-Regeln |
| `meta` | `dict` | `{}` | Metadaten (LE-Agree, DNS-Challenge) |

---

## Hosts verwalten

```python
# Alle Hosts auflisten
hosts = requests.get(f"{NPM_URL}/nginx/proxy-hosts", headers=headers(token)).json()
for h in hosts:
    print(h["id"], h["domain_names"], "→", h["forward_host"], h["forward_port"],
          "SSL:", h["certificate_id"] > 0, "Aktiv:", h["enabled"])

# Einzelnen Host abrufen
host = requests.get(f"{NPM_URL}/nginx/proxy-hosts/{host_id}", headers=headers(token)).json()

# Host aktualisieren (nur geänderte Felder nötig)
requests.put(f"{NPM_URL}/nginx/proxy-hosts/{host_id}", headers=headers(token), json={
    "forward_port": 9090,
    "allow_websocket_upgrade": True,
}).raise_for_status()

# Host aktivieren / deaktivieren
requests.post(f"{NPM_URL}/nginx/proxy-hosts/{host_id}/enable",  headers=headers(token))
requests.post(f"{NPM_URL}/nginx/proxy-hosts/{host_id}/disable", headers=headers(token))

# Host löschen
requests.delete(f"{NPM_URL}/nginx/proxy-hosts/{host_id}", headers=headers(token))
```

---

## SSL-Zertifikate verwalten

```python
# Alle Zertifikate auflisten
certs = requests.get(f"{NPM_URL}/nginx/certificates", headers=headers(token)).json()

# Zertifikat erneuern
requests.post(f"{NPM_URL}/nginx/certificates/{cert_id}/renew", headers=headers(token))

# Zertifikat löschen
requests.delete(f"{NPM_URL}/nginx/certificates/{cert_id}", headers=headers(token))
```

---

## Fertiges Hilfsskript

Für komplexere Automatisierungen: `references/npm_helper.py`

---

## Unraid-Kontext (BigServer)

- NPM Web-UI:  `http://192.168.1.144:81`
- NPM API:     `http://192.168.1.144:81/api`
- Unraid IP:   `192.168.1.144`
- Docker-Container sind per `192.168.1.144:<port>` erreichbar
- Für öffentliche Domains muss Port 80/443 am Router auf BigServer weitergeleitet sein
- Let's Encrypt benötigt öffentliche Erreichbarkeit von Port 80 (HTTP-Challenge)
- DNS-Challenge als Alternative wenn Port 80 nicht erreichbar

---

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `401 Unauthorized` | Token abgelaufen | `get_token()` erneut aufrufen |
| `400 Domains are invalid` | Domain nicht öffentlich auflösbar | DNS-Eintrag prüfen |
| `502 Bad Gateway` | NPM kann Container nicht erreichen | `forward_host`/`forward_port` prüfen, Container läuft? |
| `400 Domains already exist` | Domain bereits als Host eingetragen | Bestehenden Host aktualisieren statt neu anlegen |
| LE-Zertifikat schlägt fehl | Port 80 nicht öffentlich | Router-Port-Forwarding oder DNS-Challenge nutzen |
