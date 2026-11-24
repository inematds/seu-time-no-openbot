# 🤝 Your Team on OpenBot

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Your Team on OpenBot](guia/assets/banner-en.jpg)](https://inematds.github.io/seu-time-no-openbot/guia/en/)

**You can have your own team of agents working 24 hours a day, using the AI subscription you already have.**
OpenBot puts this team on your computer or a VPS. This kit provides a ready-made team
in Portuguese (a coordinator, a financial advisor, an organizer, and a reviewer), secure
installation with backups, and a checklist of what to change before letting the agents work
on their own.

## 📖 Guide

To understand what the kit does and how it can change your day (without the technical details):
**https://inematds.github.io/seu-time-no-openbot/guia/en/**

## What it is

It is a free kit for anyone who wants to use OpenBot, a program that runs AI agents on your
computer or a server, using the subscription you already have (ChatGPT/Codex, Claude, Gemini)
or free models. The kit includes four ready-made agents in Portuguese, a package to import them
all at once, Docker installation with protections and backups, a security checklist, and the
INEMA color theme. You need OpenBot installed (on your computer or VPS) and an AI account.

## How to get started (no technical skills needed)

Open Claude Code or Codex in any folder and paste this request:

```text
Read the kit at https://github.com/inematds/seu-time-no-openbot (README.md, SEGURANCA.md, and
instalacao/VPS.md). Explain in simple language whether OpenBot is suitable for what I do,
what each agent on the team does, what I need (a computer or VPS, an AI account, a separate
WhatsApp number), and how this affects my security. Then tell me, in up to 5 steps, where I
should start. Don’t install anything, run Docker, or change anything before I say yes.
```

## What comes in the kit

The kit's skills and agents are written in Portuguese; ask your agent to answer in your language.

| Part | What it does | Status |
|---|---|---|
| `skills/` | 4 skills in Portuguese in OpenBot format: Team Orchestrator, Financial Advisor (with `resumo_semana.py`), Personal Organizer, Deliverables Reviewer | format validated |
| `importar/` | `agentes.json` + `montar_pacote.py`: builds `dist/seu-time-openbot.zip` with the 4 agents, instructions, skills, 3 routines (disabled), and the “Meu time” channel | format validated |
| `instalacao/compose.yaml` | Docker with official seccomp, `no-new-privileges`, 6 GB limit, pinned version, and its own volume, with no published port | **tested on the VPS on 24/11/2026** (startup and `status`) |
| `instalacao/backup.sh`, `restaurar.sh` | full-volume backup with rotation, verification, and restoration | format validated + test with a dummy folder |
| `instalacao/VPS.md` | OpenBot on a VPS, from scratch, command by command | steps 1–5 tested on the VPS on 24/11; the rest format validated |
| `instalacao/servidor-sem-docker.md` | the official non-Docker option | format validated |
| `SEGURANCA.md` | checklist: permissions, AI account, WhatsApp, password vault, backup, license | checked against the documentation |
| `themes/inema.json` | INEMA theme (black `#0c0c10`, yellow `#FACC15`) | format validated |
| `validar.py` + `tests/` | checks all of this against the OpenBot v0.77.0 rules | run (output below) |

**“Format validated”** means the file follows the rules in OpenBot’s code and documentation, and
`validar.py` checks it. It does **not** mean it was run in OpenBot. Anything actually run is
marked as tested.

## ⚠️ Before using it

- OpenBot agents run with full access by default. Read [SEGURANCA.md](SEGURANCA.md) (in Portuguese)
  and switch to *Ask first* (ask before acting) wherever appropriate.
- WhatsApp: use a **separate SIM card**. OpenBot uses an unofficial client, and WhatsApp may
  block the number.
- OpenBot is free for personal, noncommercial use (PolyForm Noncommercial 1.0.0). **Commercial
  use requires a paid OpenBot license.** See [FONTE.md](FONTE.md) (in Portuguese).

---

## Technical installation

_The detailed files (SEGURANCA.md, instalacao/VPS.md, FONTE.md) are in Portuguese._

### Prerequisites

- To check the kit: Python 3.10+ with `pyyaml` and `pytest` (`pip install pyyaml pytest`), `bash`, `tar`.
- To run OpenBot: the app (macOS, Windows, Linux) from the [OpenBot releases](https://github.com/nightly-labs/openbot/releases),
  or an Ubuntu 24.04 VPS with Docker and Compose ([instalacao/VPS.md](instalacao/VPS.md) (in Portuguese)).

### The files

```
skills/<nome>/SKILL.md          frontmatter name/description/example-prompt + instructions
importar/agentes.json           package source (agents, routines, memories, channel)
importar/montar_pacote.py       generates dist/seu-time-openbot.zip (openbot-agent-import v1)
instalacao/compose.yaml         Docker (derived from the official version, PolyForm Noncommercial)
instalacao/seccomp.sha256       hash of the official seccomp.json from tag v0.77.0
instalacao/backup.sh            backup of /data with rotation
instalacao/restaurar.sh         restoration (backs up the current state first)
instalacao/achar-openbot.sh     finds the container and volume (used by the two scripts above)
themes/inema.json               theme in “Theme palette files” format
validar.py                      checks skills, theme, package, compose, and scripts
tests/test_kit.py               50 tests, without docker
```

### Check the kit

```bash
python3 validar.py
python3 -m pytest -q
```

Actual output on 24/11/2026:

```
OK    skills (4) no formato do openbot-skill-creator
OK    tema (inema.json) no formato Theme palette files
OK    manifesto de importação (openbot-agent-import v1)
OK    pacote seu-time-openbot.zip (zip montado)
OK    instalacao/compose.yaml (seccomp, no-new-privileges, memória, volume)
OK    backup.sh e restaurar.sh (bash -n)

Resultado: tudo certo · validado por formato, não testado num OpenBot em execução
50 passed
```

The tests cover: every skill limit (name 80, description 500, example-prompt 1,000,
200 files, `.env`, nested zip, symbolic link, PNG icon, accented name that becomes
an odd slug), the theme (missing color, incorrect hex, appearance, filename), compose
(without seccomp, without `no-new-privileges`, without memory, `latest`, host folder,
Docker socket, `unconfined`, and matching the test VPS version), the package (key,
duplicate key, instructions over 2,000 characters, invalid schedule, interval under
3 min, skill outside the agent folder, unknown member, invalid timezone, manifest outside
the root), backup with a dummy folder in place of the volume (round trip, 600/700 permissions,
rotation, refusal without a keychain without deleting old backups, refusal inside the data,
corrupted file), and the weekly summary. No test calls Docker: a fake `docker` in PATH fails
the test if called.

### Build the team package

```bash
python3 importar/montar_pacote.py
# Pacote pronto: .../dist/seu-time-openbot.zip
```

In OpenBot: **Server settings → Import**, select the `.zip`, check the agents, and import
(OpenBot `README.md`, “Import agents from Grok Bot”; the format is from
`resources/agent-import/grok-bot/SKILL.md`). Routines arrive **disabled**. Without importing,
you can create the skills one by one: ask an agent to register the `skills/<nome>` folder as
a local skill (`create_skill`, see `openbot-skill-creator`).

### INEMA theme

In the desktop app, on Linux (on macOS and Windows, the `themes` folder is inside the OpenBot
data folder):

```bash
mkdir -p ~/.config/OpenBot/themes
cp themes/inema.json ~/.config/OpenBot/themes/.inema.json.tmp
mv ~/.config/OpenBot/themes/.inema.json.tmp ~/.config/OpenBot/themes/inema.json
```

The `mv` replaces the file in one operation, as specified in the OpenBot README. Then: Settings > Appearance > Theme.

### On the VPS

Complete step-by-step instructions in [instalacao/VPS.md](instalacao/VPS.md) (in Portuguese). Summary:

```bash
sudo mkdir -p /opt/openbot && cd /opt/openbot
# copie para cá: compose.yaml, seccomp.sha256, backup.sh, restaurar.sh, achar-openbot.sh
sudo curl -fsSLO https://raw.githubusercontent.com/nightly-labs/openbot/v0.77.0/docker/seccomp.json
sudo sha256sum -c seccomp.sha256
sudo docker compose pull && sudo docker compose up -d       # testado na VPS em 24/11/2026
sudo docker compose exec -T openbot openbot status          # testado na VPS em 24/11/2026
sudo docker compose exec openbot openbot login               # validado por formato
sudo bash backup.sh                                          # validado por formato
```

## The process, start to finish

🧠 = session with Nei (or you, on your computer) · ⚙️ = script/timer · 🤖 = short `claude -p` (new session)

| # | Step | Command / what happens | Who | Status |
|---|---|---|---|---|
| 1 | Read the checklist | [SEGURANCA.md](SEGURANCA.md) (in Portuguese): permissions, account, WhatsApp, vault, license | 🧠 | — |
| 2 | Check the kit | `python3 validar.py && python3 -m pytest -q` | ⚙️ | run on 24/11 |
| 3 | Build the package | `python3 importar/montar_pacote.py` → `dist/seu-time-openbot.zip` | ⚙️ | format validated |
| 4 | Start OpenBot on the VPS | `instalacao/VPS.md` steps 1–5 (`docker compose pull && docker compose up -d`, `openbot status`) | ⚙️ | tested on the VPS on 24/11 |
| 5 | Sign in to OpenBot | `docker compose exec openbot openbot login` (email + code) | 🧠 | format validated |
| 6 | Connect AI | in the app or at `openbot.run/app`: Codex, Claude, Gemini, or OpenCode (Free) | 🧠 | format validated |
| 7 | Import the team | Server settings → Import → `seu-time-openbot.zip` | 🧠 | format validated |
| 8 | Reduce permissions | set each agent to *Ask first* (SEGURANCA.md §1) | 🧠 | format validated |
| 9 | Theme | copy `themes/inema.json` to the `themes` folder (above) | ⚙️ | format validated |
| 10 | Enable routines | one at a time: Daily plan, Weekly summary, Weekly review | 🧠 | format validated |
| 11 | Daily backup | `crontab`: `0 4 * * * cd /opt/openbot && bash backup.sh` + copy off the VPS | ⚙️ | format validated |
| 12 | Review the guide | independent reviewer (`claude -p`, runbook `revisor-independente.md`) reads the published guide | 🤖 | done on 24/11 |
| 13 | New OpenBot version | update the tag in FONTE.md, `compose.yaml`, `seccomp.sha256`, and the `validar.py` references; run step 2 | 🧠 + ⚙️ | — |

## The evidence

What actually ran: `validar.py` and the 50 tests in this repository (output above), and, on
an INEMA test VPS on 24/11/2026, starting the container with this `compose.yaml` and running
`openbot status` (`OpenBot 0.77.0 · Memory: 5428 MiB free of 6144 MiB (ok) · Turns at the same time: at most 8`).
What has **not** run yet: login, provider, WhatsApp, package import, the skills inside an
agent, the theme in the app, and backup against the actual volume.

## Sources

OpenBot v0.77.0 (`nightly-labs/openbot`, commit `20d1cd6`). Everything the kit states about
OpenBot comes from the documentation and code for this version, listed in
[FONTE.md](FONTE.md) (in Portuguese), along with the license and required notices. This kit is
unofficial and does not include OpenBot’s code.

## License

Kit files: MIT ([LICENSE](LICENSE)). `instalacao/compose.yaml` is derived from OpenBot and follows
PolyForm Noncommercial 1.0.0. OpenBot itself: PolyForm Noncommercial 1.0.0, commercial use
requires a paid license.

---

Made by [INEMA.CLUB](https://inema.club): open and free content about practical AI.