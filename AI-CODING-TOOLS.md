# AI Coding Tools — Installationsübersicht

Übersicht über alle gängigen AI-Coding-Agenten für das Terminal: Installation, Authentifizierung und Skill-Integration.

---

## Claude Code

Anthropics eigener Coding-Agent. Unterstützt Skills aus diesem Repo direkt.

```bash
# Installation
npm install -g @anthropic-ai/claude-code

# Start
claude

# Skill installieren (aus diesem Repo)
claude skill install https://github.com/hoktaar/claude-skills/tree/main/myjdownloader
claude skill install https://github.com/hoktaar/claude-skills/tree/main/quasarr
claude skill install https://github.com/hoktaar/claude-skills/tree/main/nginx-proxy-manager

# Skills verwalten
claude skill list
claude skill uninstall <name>
```

**Auth:** Beim ersten Start wird automatisch ein Browser-Login angeboten, oder API-Key via `ANTHROPIC_API_KEY` Umgebungsvariable.

🔗 [Docs](https://docs.anthropic.com/claude-code) · [GitHub](https://github.com/anthropics/claude-code)

---

## OpenClaw

Webbasierter Claude-Client zum Selbsthosten — läuft als Docker-Container.

```bash
# Docker Compose (Unraid/BigServer)
# Config: /mnt/user/appdata/openclaw/config/openclaw.json
# Container: OpenClaw
# Domain via NPM: https://oc-test.hoktaar.de

# API-Konfiguration in openclaw.json:
{
  "anthropic": {
    "apiKey": "<dein-anthropic-api-key>"
  }
}

# Ollama-Integration (lokale Modelle):
# Model-Pfad: ollama/modelname
# Ollama API läuft auf Port 11434
```

**Hinweis:** Für HTTPS muss Nginx Proxy Manager mit WebSocket-Support konfiguriert sein (`allow_websocket_upgrade: true`).

🔗 [GitHub](https://github.com/openclaw/openclaw)

---

## OpenCode

Open-Source Terminal-Coding-Agent. Unterstützt 75+ Provider (Claude, GPT, Gemini, Ollama, …).

```bash
# Installation
curl -fsSL https://opencode.ai/install | bash   # Linux/macOS (empfohlen)
npm i -g opencode-ai                             # via npm
brew install anomalyco/tap/opencode              # macOS/Linux Homebrew (immer aktuell)
brew install opencode                            # macOS/Linux (offizielle Formula, seltener updates)
sudo pacman -S opencode                          # Arch Linux (stable)
paru -S opencode-bin                             # Arch Linux (AUR, latest)

# Desktop App
brew install --cask opencode-desktop             # macOS
# Windows: https://opencode.ai/download

# Start
opencode                  # Interaktive TUI
opencode auth login       # Provider/API-Key einrichten

# Lokale Modelle (Ollama auf BigServer)
# In ~/.config/opencode/opencode.json:
{
  "providers": {
    "ollama": {
      "endpoint": "http://192.168.1.144:11434"
    }
  }
}
```

**Skill-Support:** OpenCode unterstützt das gleiche Skill-Format wie Claude Code — Skills aus diesem Repo können direkt verwendet werden:
```bash
# Skills nach ~/.config/opencode/skills/ kopieren oder Symlink setzen
cp -r /pfad/zu/myjdownloader ~/.config/opencode/skills/
```

**Modi:** `build` (Standard, kann Dateien ändern) und `plan` (read-only, Tab-Taste zum Wechseln).

🔗 [Docs](https://opencode.ai/docs) · [GitHub](https://github.com/sst/opencode) · [Download](https://opencode.ai/download)

---

## OpenAI Codex CLI

OpenAIs Terminal-Coding-Agent, gebaut in Rust. Benötigt ChatGPT Plus/Pro oder API-Key.

```bash
# Installation
npm i -g @openai/codex          # via npm (empfohlen)

# Direkter Install-Script (macOS/Linux)
curl -fsSL https://openai.github.io/codex/install.sh | bash

# Upgrade
npm update -g @openai/codex

# Start & Auth
codex                           # Interaktive TUI (Browser-Login beim ersten Start)
codex login                     # Explizit einloggen (ChatGPT Account oder API-Key)
printenv OPENAI_API_KEY | codex login --with-api-key   # API-Key via stdin

# Nicht-interaktiv (für Scripts)
codex exec "erkläre diese Funktion"
codex -p "was macht dieses Script?" --path ./myscript.sh

# Windows: WSL empfohlen
wsl --install   # PowerShell als Admin
# Dann in WSL: npm i -g @openai/codex
```

**Modelle:** GPT-5.4 (Standard), GPT-5.3-Codex-Spark (Pro), codex-mini-latest (API).  
**Approval-Modi:** `on-request` (fragt bei jeder Änderung), `on-failure` (fragt nur bei Fehler), `never` (vollautomatisch/yolo).

**Skill-Support:** Codex CLI unterstützt das gleiche Skill-Format (`SKILL.md` + optionale Dateien):
```bash
# Skills global installieren
codex skill install https://github.com/hoktaar/claude-skills/tree/main/myjdownloader
# oder manuell nach ~/.codex/skills/ kopieren
```

🔗 [Docs](https://developers.openai.com/codex/cli) · [GitHub](https://github.com/openai/codex) · [Changelog](https://developers.openai.com/codex/changelog)

---

## Gemini CLI

Googles Open-Source Terminal-Agent. Kostenlos mit Google-Account (großzügige Free-Tier-Limits).

```bash
# Installation
npx @google/gemini-cli          # Ohne Installation (einmalig ausführen)
npm install -g @google/gemini-cli   # Global installieren

# Start & Auth
gemini                          # Startet TUI + Browser-Login (Google-Account)

# Mit API-Key (für höhere Limits / Pay-as-you-go)
export GEMINI_API_KEY="dein-key"   # Key von https://aistudio.google.com/apikey
gemini

# Nicht-interaktiv
gemini -p "erkläre diese Datei" main.py

# Modell wählen
gemini -m gemini-2.5-pro
# Im TUI: /model → Auto (Gemini 3) für das beste Modell
```

**Free Tier (mit Google-Account):** Gemini 2.5 Pro/Flash täglich kostenlos, Gemini 3 Pro verfügbar mit Google AI Ultra Abo.  
**Kontext-Datei:** `GEMINI.md` im Projektordner für persistenten Kontext (ähnlich wie `CLAUDE.md`).

**Skill-Support:** Gemini CLI unterstützt "Agent Skills" im gleichen Format:
```bash
# Skills global installieren
gemini skill install https://github.com/hoktaar/claude-skills/tree/main/myjdownloader
# oder manuell nach ~/.config/gemini/skills/ kopieren
```

🔗 [Docs](https://github.com/google-gemini/gemini-cli/blob/main/docs/index.md) · [GitHub](https://github.com/google-gemini/gemini-cli)

---

## Skill-Kompatibilität

Skills aus diesem Repo folgen dem offenen [Agent Skills Spezifikation](https://developers.openai.com/codex/skills) und sind mit allen oben genannten Tools kompatibel:

| Tool | Skill-Befehl | Manueller Pfad |
|------|-------------|----------------|
| Claude Code | `claude skill install <url>` | `~/.claude/skills/` |
| OpenCode | `opencode skill install <url>` | `~/.config/opencode/skills/` |
| OpenAI Codex | `codex skill install <url>` | `~/.codex/skills/` |
| Gemini CLI | `gemini skill install <url>` | `~/.config/gemini/skills/` |

Für Projekte: Skills auch im Repo unter `.codex/skills/` (Claude Code) bzw. `.skills/` ablegen.
