"""
NPM Helper — Nginx Proxy Manager API Hilfsskript
Für Unraid BigServer (192.168.1.144)

Verwendung:
    python npm_helper.py list
    python npm_helper.py add --domain meinservice.domain.de --port 8080
    python npm_helper.py add --domain meinservice.domain.de --port 8080 --ssl
    python npm_helper.py add --domain ws-service.domain.de --port 3000 --websocket --ssl
    python npm_helper.py delete --id 5
    python npm_helper.py enable --id 5
    python npm_helper.py disable --id 5
    python npm_helper.py certs
"""

import argparse
import json
import sys
import requests

NPM_URL   = "http://192.168.1.144:81/api"
NPM_EMAIL = "admin@example.com"   # ← anpassen
NPM_PASS  = "deinPasswort"        # ← anpassen
UNRAID_IP = "192.168.1.144"


def get_token():
    r = requests.post(f"{NPM_URL}/tokens", json={
        "identity": NPM_EMAIL,
        "secret": NPM_PASS,
        "scope": "user"
    })
    r.raise_for_status()
    return r.json()["token"]


def h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def list_hosts(token):
    hosts = requests.get(f"{NPM_URL}/nginx/proxy-hosts", headers=h(token)).json()
    if not hosts:
        print("Keine Proxy Hosts vorhanden.")
        return
    print(f"{'ID':<5} {'Domain':<40} {'Ziel':<25} {'SSL':<5} {'Aktiv'}")
    print("-" * 90)
    for host in hosts:
        domain = ", ".join(host["domain_names"])
        ziel = f"{host['forward_host']}:{host['forward_port']}"
        ssl = "✓" if host.get("certificate_id", 0) > 0 else "-"
        aktiv = "✓" if host.get("enabled") else "✗"
        print(f"{host['id']:<5} {domain:<40} {ziel:<25} {ssl:<5} {aktiv}")


def list_certs(token):
    certs = requests.get(f"{NPM_URL}/nginx/certificates", headers=h(token)).json()
    if not certs:
        print("Keine Zertifikate vorhanden.")
        return
    print(f"{'ID':<5} {'Name':<35} {'Domains':<50} {'Läuft ab'}")
    print("-" * 110)
    for c in certs:
        name = c.get("nice_name", "")
        domains = ", ".join(c.get("domain_names", []))
        expires = c.get("expires_on", "?")
        print(f"{c['id']:<5} {name:<35} {domains:<50} {expires}")


def request_letsencrypt_cert(token, domain):
    print(f"Beantrage Let's Encrypt Zertifikat für {domain}...")
    r = requests.post(f"{NPM_URL}/nginx/certificates", headers=h(token), json={
        "provider": "letsencrypt",
        "domain_names": [domain],
        "meta": {"dns_challenge": False, "letsencrypt_agree": True}
    })
    if r.status_code != 201:
        print(f"Fehler beim Zertifikat: {r.status_code} {r.text}")
        sys.exit(1)
    cert_id = r.json()["id"]
    print(f"Zertifikat erstellt (ID: {cert_id})")
    return cert_id


def add_host(token, domain, port, ssl=False, websocket=False,
             scheme="http", https_backend=False):
    cert_id = 0
    if ssl:
        cert_id = request_letsencrypt_cert(token, domain)

    payload = {
        "domain_names": [domain],
        "forward_scheme": "https" if https_backend else scheme,
        "forward_host": UNRAID_IP,
        "forward_port": port,
        "certificate_id": cert_id,
        "ssl_forced": ssl,
        "hsts_enabled": False,
        "http2_support": ssl,
        "block_exploits": True,
        "caching_enabled": False,
        "allow_websocket_upgrade": websocket,
        "trust_forwarded_proto": https_backend,
        "meta": {"letsencrypt_agree": ssl, "dns_challenge": False},
    }

    r = requests.post(f"{NPM_URL}/nginx/proxy-hosts", headers=h(token), json=payload)
    if r.status_code != 201:
        print(f"Fehler: {r.status_code} {r.text}")
        sys.exit(1)

    host = r.json()
    print(f"✓ Host angelegt!")
    print(f"  ID:      {host['id']}")
    print(f"  Domain:  {', '.join(host['domain_names'])}")
    print(f"  Ziel:    {host['forward_scheme']}://{host['forward_host']}:{host['forward_port']}")
    print(f"  SSL:     {'Ja (Let\'s Encrypt)' if cert_id else 'Nein'}")
    print(f"  WS:      {'Ja' if websocket else 'Nein'}")


def delete_host(token, host_id):
    r = requests.delete(f"{NPM_URL}/nginx/proxy-hosts/{host_id}", headers=h(token))
    r.raise_for_status()
    print(f"Host {host_id} gelöscht.")


def enable_host(token, host_id):
    r = requests.post(f"{NPM_URL}/nginx/proxy-hosts/{host_id}/enable", headers=h(token))
    r.raise_for_status()
    print(f"Host {host_id} aktiviert.")


def disable_host(token, host_id):
    r = requests.post(f"{NPM_URL}/nginx/proxy-hosts/{host_id}/disable", headers=h(token))
    r.raise_for_status()
    print(f"Host {host_id} deaktiviert.")


def main():
    parser = argparse.ArgumentParser(description="NPM Helper für Unraid BigServer")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="Alle Proxy Hosts auflisten")
    sub.add_parser("certs", help="Alle Zertifikate auflisten")

    p_add = sub.add_parser("add", help="Neuen Proxy Host anlegen")
    p_add.add_argument("--domain", required=True, help="Domain/Subdomain")
    p_add.add_argument("--port", required=True, type=int, help="Container-Port")
    p_add.add_argument("--ssl", action="store_true", help="Let's Encrypt SSL anlegen")
    p_add.add_argument("--websocket", action="store_true", help="WebSocket-Support")
    p_add.add_argument("--https-backend", action="store_true", help="Backend läuft auf HTTPS")
    p_add.add_argument("--scheme", default="http", choices=["http", "https"])

    p_del = sub.add_parser("delete", help="Proxy Host löschen")
    p_del.add_argument("--id", required=True, type=int)

    p_en = sub.add_parser("enable", help="Proxy Host aktivieren")
    p_en.add_argument("--id", required=True, type=int)

    p_dis = sub.add_parser("disable", help="Proxy Host deaktivieren")
    p_dis.add_argument("--id", required=True, type=int)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    token = get_token()

    if args.cmd == "list":
        list_hosts(token)
    elif args.cmd == "certs":
        list_certs(token)
    elif args.cmd == "add":
        add_host(token, args.domain, args.port,
                 ssl=args.ssl,
                 websocket=args.websocket,
                 scheme=args.scheme,
                 https_backend=args.https_backend)
    elif args.cmd == "delete":
        delete_host(token, args.id)
    elif args.cmd == "enable":
        enable_host(token, args.id)
    elif args.cmd == "disable":
        disable_host(token, args.id)


if __name__ == "__main__":
    main()
