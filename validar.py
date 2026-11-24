#!/usr/bin/env python3
"""validar.py — confere o kit contra as regras do próprio OpenBot (v0.77.0, commit 20d1cd6).

Cada regra cita de onde saiu (arquivo:linha no repositório nightly-labs/openbot, tag v0.77.0).
Os limites estão copiados aqui, então este script não precisa da cópia do OpenBot para rodar.

Confere: skills (skills/*/SKILL.md), tema (themes/*.json), pacote de importação
(importar/agentes.json + o .zip montado), compose (instalacao/compose.yaml) e os scripts
de backup (bash -n). Tudo isto é "validado por formato, não testado em execução":
nenhum OpenBot rodou para este kit.

Uso: python3 validar.py [--raiz PASTA] [--zip ARQUIVO.zip]
Sai com 0 quando tudo passa e 1 quando algo falha.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent

# ---------------------------------------------------------------- skills
# src/main/skill-package.ts:12  SKILL_FRONTMATTER
SKILL_FRONTMATTER = re.compile(r"^---\s*\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)")
# resources/managed-skills/openbot-skill-creator/SKILL.md:12  name até 80 caracteres
# (também src/main/skill-package.ts:84)
NOME_MAX = 80
# openbot-skill-creator/SKILL.md:12  description até 500. O código aceita até 1024
# (packages/contracts/src/ipc-skills.ts:113, SKILL_DESCRIPTION_MAX_LENGTH); usamos o guia, que é o menor.
DESCRICAO_MAX = 500
# openbot-skill-creator/SKILL.md:12  example-prompt até 1.000 (também src/main/local-skill-library.ts:147)
EXEMPLO_MAX = 1000
# openbot-skill-creator/SKILL.md:14  até 200 arquivos e 10 MB expandido (skill-package.ts:14-15)
ARQUIVOS_MAX = 200
BYTES_MAX = 10 * 1024 * 1024
# openbot-skill-creator/SKILL.md:14  assets/icon.png até 512 KB (local-skill-library.ts:131, PNG pela assinatura)
ICONE_MAX = 512 * 1024
PNG_ASSINATURA = bytes.fromhex("89504e470d0a1a0a")
# skill-package.ts:40 e :25  pastas que o empacotador pula (não contam)
PULA_PASTAS = {".git", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
PULA_ARQUIVOS = {".DS_Store"}


def caminho_inseguro(nome: str) -> bool:
    """src/main/skill-package.ts:156-170  isUnsafeArchivePath."""
    partes = nome.split("/")
    arquivo = partes[-1].lower() if partes else ""
    return (
        not nome
        or nome.startswith("/")
        or any(p in ("", ".", "..") for p in partes)
        or ".git" in partes
        or "node_modules" in partes
        or arquivo.startswith(".env")
        or re.search(r"private.*key", arquivo, re.I) is not None
        or re.search(r"\.(?:zip|tar|tgz|gz|7z|rar)$", arquivo, re.I) is not None
    )


def slugify(nome: str) -> str:
    """src/main/skill-package.ts:172-183  slugify (sem o recurso de hash para nome vazio)."""
    v = unicodedata.normalize("NFKD", nome.lower())
    v = re.sub(r"[^a-z0-9]+", "-", v).strip("-")[:64]
    return v


def ler_frontmatter(texto: str):
    m = SKILL_FRONTMATTER.match(texto)
    if not m:
        return None, None
    try:
        meta = yaml.safe_load(m.group(1) or "")
    except yaml.YAMLError as e:
        return {"__erro__": str(e)}, texto[m.end():]
    return meta, texto[m.end():]


def validar_skill(pasta: Path) -> list[str]:
    erros: list[str] = []
    skill = pasta / "SKILL.md"
    if not skill.is_file():
        return [f"{pasta.name}: falta SKILL.md na raiz (skill-package.ts:80)"]
    try:
        texto = skill.read_text(encoding="utf-8")  # skill-package.ts:81 lê como UTF-8 estrito
    except UnicodeDecodeError:
        return [f"{pasta.name}: SKILL.md não é UTF-8 (skill-package.ts:81)"]
    meta, corpo = ler_frontmatter(texto)
    if meta is None:
        return [f"{pasta.name}: SKILL.md sem frontmatter YAML entre --- (skill-package.ts:83)"]
    if not isinstance(meta, dict) or "__erro__" in meta:
        return [f"{pasta.name}: frontmatter não é um mapa YAML válido (skill-package.ts:85-86)"]
    nome = meta.get("name").strip() if isinstance(meta.get("name"), str) else ""
    desc = meta.get("description").strip() if isinstance(meta.get("description"), str) else ""
    if not nome:
        erros.append(f"{pasta.name}: falta name (skill-package.ts:89)")
    elif len(nome) > NOME_MAX:
        erros.append(f"{pasta.name}: name com {len(nome)} caracteres, máximo {NOME_MAX} (skill-creator SKILL.md:12)")
    if not desc:
        erros.append(f"{pasta.name}: falta description (skill-package.ts:89)")
    elif len(desc) > DESCRICAO_MAX:
        erros.append(f"{pasta.name}: description com {len(desc)} caracteres, máximo {DESCRICAO_MAX} (skill-creator SKILL.md:12)")
    ex = meta.get("example-prompt")
    if ex is not None:
        if not isinstance(ex, str) or not ex.strip():
            erros.append(f"{pasta.name}: example-prompt tem que ser texto (local-skill-library.ts:128)")
        elif len(ex.strip()) > EXEMPLO_MAX:
            erros.append(f"{pasta.name}: example-prompt com {len(ex.strip())} caracteres, máximo {EXEMPLO_MAX} (skill-creator SKILL.md:12)")
    if nome and slugify(nome) != slugify(nome.encode("ascii", "ignore").decode()):
        erros.append(f"{pasta.name}: name com acento vira slug '{slugify(nome)}' (skill-package.ts:172); use só ASCII no name")
    if nome and not slugify(nome):
        erros.append(f"{pasta.name}: name não gera slug (skill-package.ts:180)")
    if corpo is not None and not corpo.strip():
        erros.append(f"{pasta.name}: SKILL.md sem instruções depois do frontmatter (skill-creator SKILL.md:13)")

    total, n = 0, 0
    for raiz, dirs, files in os.walk(pasta):
        r = Path(raiz)
        for d in list(dirs):
            if (r / d).is_symlink():
                erros.append(f"{pasta.name}: link simbólico {(r / d).relative_to(pasta)} (skill-package.ts:42)")
        dirs[:] = [d for d in dirs if d not in PULA_PASTAS and not (r / d).is_symlink()]
        for f in files:
            if f in PULA_ARQUIVOS:
                continue
            p = r / f
            rel = p.relative_to(pasta).as_posix()
            if p.is_symlink():
                erros.append(f"{pasta.name}: link simbólico {rel} (skill-package.ts:42; skill-creator SKILL.md:14)")
                continue
            if caminho_inseguro(rel):
                erros.append(f"{pasta.name}: arquivo proibido {rel} (.env, chave privada ou arquivo compactado; skill-package.ts:156)")
            total += p.stat().st_size
            n += 1
    if n > ARQUIVOS_MAX:
        erros.append(f"{pasta.name}: {n} arquivos, máximo {ARQUIVOS_MAX} (skill-creator SKILL.md:14)")
    if total > BYTES_MAX:
        erros.append(f"{pasta.name}: {total} bytes, máximo {BYTES_MAX} (skill-creator SKILL.md:14)")
    icone = pasta / "assets" / "icon.png"
    if icone.exists():
        b = icone.read_bytes()
        if len(b) > ICONE_MAX or b[:8] != PNG_ASSINATURA:
            erros.append(f"{pasta.name}: assets/icon.png tem que ser PNG até 512 KB (local-skill-library.ts:131)")
    return erros


def validar_skills(raiz: Path) -> tuple[list[str], int]:
    pastas = sorted(p for p in (raiz / "skills").iterdir() if p.is_dir()) if (raiz / "skills").is_dir() else []
    if not pastas:
        return ["nenhuma skill em skills/"], 0
    erros: list[str] = []
    slugs: dict[str, str] = {}
    for p in pastas:
        erros += validar_skill(p)
        meta, _ = ler_frontmatter((p / "SKILL.md").read_text(encoding="utf-8")) if (p / "SKILL.md").is_file() else (None, None)
        if isinstance(meta, dict) and isinstance(meta.get("name"), str):
            s = slugify(meta["name"].strip())
            if s in slugs:
                erros.append(f"{p.name}: mesmo slug '{s}' de {slugs[s]}")
            slugs[s] = p.name
    return erros, len(pastas)


# ---------------------------------------------------------------- tema
# packages/contracts/src/app-appearance.ts:12-25  as 12 cores
CORES = ["canvas", "frame", "sidebar", "surface", "text", "textMuted", "border",
         "accent", "accentForeground", "success", "warning", "danger"]
COR = re.compile(r"^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")          # app-appearance.ts:43
ID_TEMA = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")                 # app-appearance.ts:41
CONTROLE = re.compile(r"[\x00-\x1f\x7f-\x9f]")                     # theme-palette-files.ts:24 (\p{Cc})


def validar_tema(arquivo: Path) -> list[str]:
    """README.md "Theme palette files" + src/main/theme-palette-files.ts:20-40."""
    e: list[str] = []
    if arquivo.suffix != ".json" or not ID_TEMA.match(arquivo.stem):
        e.append(f"{arquivo.name}: o nome do arquivo é o id do tema: minúsculas, dígitos e '-' (app-appearance.ts:41)")
    try:
        t = json.loads(arquivo.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as x:
        return e + [f"{arquivo.name}: JSON inválido ({x})"]
    if not isinstance(t, dict):
        return e + [f"{arquivo.name}: tem que ser um objeto JSON"]
    nome = t.get("name")
    if not isinstance(nome, str) or not nome or nome != nome.strip() or len(nome) > 64 or CONTROLE.search(nome):
        e.append(f"{arquivo.name}: name de 1 a 64 caracteres, sem espaço nas pontas (theme-palette-files.ts:23)")
    if t.get("appearance") not in ("light", "dark"):
        e.append(f"{arquivo.name}: appearance tem que ser light ou dark (theme-palette-files.ts:26)")
    cores = t.get("colors")
    if not isinstance(cores, dict):
        return e + [f"{arquivo.name}: falta colors (theme-palette-files.ts:27)"]
    for c in CORES:
        v = cores.get(c)
        if v is None:
            e.append(f"{arquivo.name}: falta a cor {c}; o OpenBot ignora o arquivo (README, Theme palette files)")
        elif not isinstance(v, str) or not COR.match(v):
            e.append(f"{arquivo.name}: {c}={v!r} não é #rrggbb nem #rrggbbaa (app-appearance.ts:43)")
    sobra = sorted(set(cores) - set(CORES))
    if sobra:
        e.append(f"{arquivo.name}: cores que o OpenBot não conhece: {', '.join(sobra)}")
    return e


# ---------------------------------------------------------------- importação de agentes
# packages/contracts/src/input-limits.ts e ipc-agent-import.ts:20-27
LIM = {"agentName": 80, "agentTitle": 120, "agentDescription": 2000, "agentSkills": 32,
       "agentRoutines": 64, "routineName": 80, "routineInstruction": 100_000, "agentMemories": 64,
       "agentMemoryText": 500, "channelMemories": 32, "channels": 100, "key": 64, "sourceApp": 64,
       "routineCron": 255, "files": 200_000}
CHAVE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")           # ipc-agent-import.ts:102-104
HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")                     # ipc-routines.ts:70-72


def inteiro_entre(v, a, b) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and a <= v <= b


def agenda_valida(s) -> bool:
    """packages/contracts/src/ipc-routines.ts:32-68  isRoutineSchedule (sem 'advanced')."""
    if not isinstance(s, dict) or not isinstance(s.get("kind"), str):
        return False
    k = s["kind"]
    if k == "hourly":
        return inteiro_entre(s.get("minute"), 0, 59)
    if k in ("daily", "weekdays"):
        return isinstance(s.get("time"), str) and bool(HORA.match(s["time"]))
    if k == "weekly":
        return inteiro_entre(s.get("weekday"), 0, 6) and isinstance(s.get("time"), str) and bool(HORA.match(s["time"]))
    if k == "monthly":
        return inteiro_entre(s.get("day"), 1, 31) and isinstance(s.get("time"), str) and bool(HORA.match(s["time"]))
    if k == "interval":
        # agent-import-manifest.ts:213-216: sem anchorAt, o import põe a hora atual.
        # grok-bot SKILL.md:178: nunca mais que a cada 3 minutos (ipc-routines.ts:7).
        ok = inteiro_entre(s.get("amount"), 1, 100_000) and s.get("unit") in ("minutes", "hours", "days")
        return ok and not (s.get("unit") == "minutes" and s.get("amount", 0) < 3)
    if k == "custom":
        return isinstance(s.get("expression"), str) and 0 < len(s["expression"]) <= LIM["routineCron"]
    return False


def texto_limitado(v, maximo) -> bool:
    return isinstance(v, str) and len(v) <= maximo


def validar_manifesto(m: dict, arquivos: set[str] | None = None) -> list[str]:
    """src/main/agent-import-manifest.ts:49-256 + grok-bot SKILL.md "Format" e "Checklist".

    Avisos que o OpenBot só registra (rotina inválida pulada, memória longa cortada) aqui viram erro,
    para o pacote do kit entrar inteiro.
    """
    e: list[str] = []
    if not isinstance(m, dict) or m.get("format") != "openbot-agent-import":
        return ["manifesto: format tem que ser openbot-agent-import (agent-import-manifest.ts:60)"]
    if m.get("version") != 1:
        e.append("manifesto: version tem que ser 1 (agent-import-manifest.ts:62)")
    src = m.get("source", {})
    if not (isinstance(src, dict) and texto_limitado(src.get("app"), LIM["sourceApp"]) and src.get("app")):
        e.append("manifesto: source.app até 64 caracteres (agent-import-manifest.ts:64)")
    agentes = m.get("agents")
    if not isinstance(agentes, list) or not agentes:
        return e + ["manifesto: precisa de pelo menos um agente (agent-import-manifest.ts:67)"]
    chaves: set[str] = set()
    for i, a in enumerate(agentes, 1):
        if not isinstance(a, dict):
            e.append(f"agente {i}: inválido")
            continue
        k = a.get("key")
        if not (texto_limitado(k, LIM["key"]) and CHAVE.match(k)):
            e.append(f"agente {i}: key inválida {k!r} (ipc-agent-import.ts:102)")
            continue
        if k in chaves:
            e.append(f"agente {k}: key repetida (agent-import-manifest.ts:76)")
        chaves.add(k)
        nome = a.get("name").strip() if isinstance(a.get("name"), str) else ""
        if not nome or len(nome) > LIM["agentName"]:
            e.append(f"agente {k}: name de 1 a 80 caracteres (agent-import-manifest.ts:156)")
        if not texto_limitado(a.get("title", "") or "", LIM["agentTitle"]):
            e.append(f"agente {k}: title até 120 caracteres (agent-import-manifest.ts:158)")
        if not texto_limitado(a.get("description"), LIM["agentDescription"]) or not a.get("description", "").strip():
            e.append(f"agente {k}: description (instruções) obrigatória, até 2.000 caracteres (agent-import-manifest.ts:160)")
        prefixo = f"agents/{k}/"
        for campo in ("avatar", "files"):
            v = a.get(campo)
            if v is not None and not (isinstance(v, str) and v.rstrip("/").startswith(prefixo) and not caminho_inseguro(v.rstrip("/"))):
                e.append(f"agente {k}: {campo} tem que começar com {prefixo} (agent-import-manifest.ts:163-169)")
        skills = a.get("skills", [])
        if not isinstance(skills, list) or len(skills) > LIM["agentSkills"]:
            e.append(f"agente {k}: até 32 skills (agent-import-manifest.ts:170)")
            skills = []
        for s in skills:
            if not (isinstance(s, str) and s.rstrip("/").startswith(prefixo) and not caminho_inseguro(s.rstrip("/"))):
                e.append(f"agente {k}: caminho de skill inválido {s!r} (agent-import-manifest.ts:183)")
            elif arquivos is not None and f"{s.rstrip('/')}/SKILL.md" not in arquivos:
                e.append(f"agente {k}: {s}/SKILL.md não está no zip (grok-bot SKILL.md, Checklist)")
        e += validar_rotinas(a.get("routines", []), f"agente {k}")
        e += validar_memorias(a.get("memories", []), f"agente {k}", LIM["agentMemories"])

    canais = m.get("channels", [])
    if not isinstance(canais, list) or len(canais) > LIM["channels"]:
        return e + ["manifesto: channels tem que ser lista de até 100 (agent-import-manifest.ts:82)"]
    vistos: set[str] = set()
    for i, c in enumerate(canais, 1):
        k = c.get("key") if isinstance(c, dict) else None
        if not (texto_limitado(k, LIM["key"]) and CHAVE.match(k)):
            e.append(f"canal {i}: key inválida (agent-import-manifest.ts:111)")
            continue
        if k in vistos:
            e.append(f"canal {k}: key repetida (agent-import-manifest.ts:87)")
        vistos.add(k)
        nome = c.get("name").strip() if isinstance(c.get("name"), str) else ""
        if not nome or len(nome) > LIM["agentName"]:
            e.append(f"canal {k}: name de 1 a 80 caracteres (agent-import-manifest.ts:113)")
        if not texto_limitado(c.get("title", "") or "", LIM["agentTitle"]):
            e.append(f"canal {k}: title até 120 caracteres (agent-import-manifest.ts:115)")
        if not texto_limitado(c.get("instructions", "") or "", LIM["agentDescription"]):
            e.append(f"canal {k}: instructions até 2.000 caracteres (agent-import-manifest.ts:117)")
        membros = c.get("members")
        if not isinstance(membros, list) or not membros:
            e.append(f"canal {k}: precisa de pelo menos um membro (grok-bot SKILL.md, Channel field rules)")
            membros = []
        fora = [x for x in membros if x not in chaves]
        if fora:
            e.append(f"canal {k}: membros que não são agentes do pacote: {fora} (agent-import-manifest.ts:122)")
        lider = c.get("lead")
        if lider is not None and lider not in membros:
            e.append(f"canal {k}: lead tem que ser um membro (agent-import-manifest.ts:124)")
        e += validar_rotinas(c.get("routines", []), f"canal {k}")
        e += validar_memorias(c.get("memories", []), f"canal {k}", LIM["channelMemories"])
    return e


def validar_rotinas(rotinas, dono: str) -> list[str]:
    """agent-import-manifest.ts:200-237."""
    if not isinstance(rotinas, list):
        return [f"{dono}: routines tem que ser lista (agent-import-manifest.ts:172)"]
    e = []
    if len(rotinas) > LIM["agentRoutines"]:
        e.append(f"{dono}: até 64 rotinas (agent-import-manifest.ts:205)")
    for r in rotinas:
        if not isinstance(r, dict):
            e.append(f"{dono}: rotina inválida")
            continue
        n = r.get("name").strip() if isinstance(r.get("name"), str) else ""
        rot = f"{dono}, rotina {n or '?'}"
        if not n or len(n) > LIM["routineName"]:
            e.append(f"{rot}: name de 1 a 80 caracteres (agent-import-manifest.ts:220)")
        ins = r.get("instruction")
        if not isinstance(ins, str) or not ins.strip() or len(ins) > LIM["routineInstruction"]:
            e.append(f"{rot}: instruction obrigatória (agent-import-manifest.ts:221-223)")
        if not agenda_valida(r.get("schedule")):
            e.append(f"{rot}: schedule inválido {r.get('schedule')!r} (ipc-routines.ts:32)")
        tz = r.get("timezone")
        if tz is not None:
            try:
                import zoneinfo
                zoneinfo.ZoneInfo(tz)
            except Exception:
                e.append(f"{rot}: timezone {tz!r} não é um nome IANA (grok-bot SKILL.md, Field rules)")
        if "active" in r and not isinstance(r["active"], bool):
            e.append(f"{rot}: active tem que ser true ou false (agent-import-manifest.ts:231)")
    return e


def validar_memorias(mems, dono: str, maximo: int) -> list[str]:
    """agent-import-manifest.ts:240-256 (o OpenBot corta; aqui é erro)."""
    if not isinstance(mems, list):
        return [f"{dono}: memories tem que ser lista (agent-import-manifest.ts:174)"]
    e = []
    if len(mems) > maximo:
        e.append(f"{dono}: até {maximo} memórias")
    for t in mems:
        if not isinstance(t, str) or not t.strip() or len(t.strip()) > LIM["agentMemoryText"]:
            e.append(f"{dono}: memória vazia ou com mais de 500 caracteres: {str(t)[:40]!r}")
    return e


def validar_zip(caminho: Path) -> list[str]:
    """grok-bot SKILL.md "Checklist" + src/main/agent-import-service.ts:404-416."""
    e: list[str] = []
    try:
        z = zipfile.ZipFile(caminho)
    except zipfile.BadZipFile:
        return [f"{caminho.name}: não é um zip"]
    with z:
        nomes = [n for n in z.namelist() if not n.endswith("/")]
        if len(nomes) > LIM["files"]:
            e.append(f"{caminho.name}: mais de 200.000 arquivos (ipc-agent-import.ts:21)")
        if "openbot-import.json" not in nomes:
            return e + [f"{caminho.name}: openbot-import.json tem que estar na raiz (grok-bot SKILL.md, Checklist)"]
        for n in nomes:
            if caminho_inseguro(n):
                e.append(f"{caminho.name}: arquivo proibido no pacote: {n} (skill-package.ts:156)")
        m = json.loads(z.read("openbot-import.json").decode("utf-8"))
        e += validar_manifesto(m, set(nomes))
        # cada skill dentro do pacote também passa pelas regras de skill
        with tempfile.TemporaryDirectory() as tmp:
            z.extractall(tmp)
            for a in m.get("agents", []):
                for s in a.get("skills", []):
                    e += [f"zip/{s}: {x}" for x in validar_skill(Path(tmp) / s)]
    return e


# ---------------------------------------------------------------- compose
def validar_compose(arquivo: Path) -> list[str]:
    """docs/docker.md "Run", "Memory", "Data" e "Security" (v0.77.0) + docker/compose.yaml oficial."""
    e: list[str] = []
    try:
        c = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    except yaml.YAMLError as x:
        return [f"compose: YAML inválido ({x})"]
    servicos = (c or {}).get("services") or {}
    if "openbot" not in servicos:
        return ["compose: falta o serviço openbot"]
    s = servicos["openbot"] or {}
    img = str(s.get("image", ""))
    if not img.startswith("ghcr.io/nightly-labs/openbot:"):
        e.append("compose: imagem tem que ser ghcr.io/nightly-labs/openbot (docker.md, Run)")
    elif img.endswith(":latest"):
        e.append("compose: fixe a versão da imagem em vez de latest (docker.md, Run e Update automation)")
    sec = [str(x) for x in (s.get("security_opt") or [])]
    if not any(re.fullmatch(r"seccomp=\S+\.json", x) for x in sec):
        e.append("compose: falta security_opt seccomp=<arquivo>.json (docker.md, Security)")
    if any("unconfined" in x for x in sec):
        e.append("compose: seccomp=unconfined é proibido (docker.md, Security)")
    if "no-new-privileges:true" not in sec:
        e.append("compose: falta security_opt no-new-privileges:true (docker.md, Security)")
    if s.get("privileged"):
        e.append("compose: privileged é proibido (docker.md, Security)")
    if not s.get("mem_limit") and not (((s.get("deploy") or {}).get("resources") or {}).get("limits") or {}).get("memory"):
        e.append("compose: falta limite de memória mem_limit (docker.md, Memory)")
    if not s.get("restart"):
        e.append("compose: falta restart (self-hosted-server.md, Commands: sem política o container não volta)")
    vols = [str(v) for v in (s.get("volumes") or [])]
    dados = [v for v in vols if v.split(":")[1:2] == ["/data"]]
    if not dados:
        e.append("compose: falta volume em /data (docker.md, Data)")
    else:
        origem = dados[0].split(":")[0]
        if origem.startswith((".", "/", "~")):
            e.append("compose: use volume nomeado em /data, não pasta do host")
        elif origem not in ((c or {}).get("volumes") or {}):
            e.append(f"compose: o volume {origem} não está declarado em volumes:")
    for v in vols:
        if "docker.sock" in v or v.split(":")[0] in ("~", "$HOME", "/home", "/"):
            e.append(f"compose: não monte {v.split(':')[0]} (docker.md, Security)")
    return e


# ---------------------------------------------------------------- scripts
def validar_scripts(raiz: Path) -> list[str]:
    e = []
    for nome in ("backup.sh", "restaurar.sh", "achar-openbot.sh"):
        p = raiz / "instalacao" / nome
        if not p.is_file():
            e.append(f"falta instalacao/{nome}")
            continue
        r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
        if r.returncode:
            e.append(f"{nome}: bash -n falhou: {r.stderr.strip()}")
    return e


# ---------------------------------------------------------------- principal
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Confere o kit contra as regras do OpenBot v0.77.0.")
    ap.add_argument("--raiz", type=Path, default=RAIZ)
    ap.add_argument("--zip", type=Path, help="um pacote de importação já montado")
    a = ap.parse_args(argv)
    raiz = a.raiz.resolve()
    falhas = 0

    def item(titulo: str, erros: list[str]):
        nonlocal falhas
        print(("OK    " if not erros else "ERRO  ") + titulo)
        for x in erros:
            print("      - " + x)
        falhas += bool(erros)

    erros, n = validar_skills(raiz)
    item(f"skills ({n}) no formato do openbot-skill-creator", erros)
    temas = sorted((raiz / "themes").glob("*.json"))
    item(f"tema ({', '.join(t.name for t in temas) or 'nenhum'}) no formato Theme palette files",
         [x for t in temas for x in validar_tema(t)] or ([] if temas else ["nenhum tema em themes/"]))
    fonte = raiz / "importar" / "agentes.json"
    if fonte.is_file():
        sys.path.insert(0, str(raiz / "importar"))
        import montar_pacote  # noqa: E402
        item("manifesto de importação (openbot-agent-import v1)",
             validar_manifesto(montar_pacote.manifesto(json.loads(fonte.read_text(encoding="utf-8")))))
        if a.zip:
            zipado = a.zip
        else:
            zipado = Path(tempfile.mkdtemp()) / "seu-time-openbot.zip"
            montar_pacote.montar(zipado, fonte)
        item(f"pacote {zipado.name} (zip montado)", validar_zip(zipado))
    else:
        item("manifesto de importação", ["falta importar/agentes.json"])
    item("instalacao/compose.yaml (seccomp, no-new-privileges, memória, volume)",
         validar_compose(raiz / "instalacao" / "compose.yaml"))
    item("backup.sh e restaurar.sh (bash -n)", validar_scripts(raiz))
    print()
    print("Resultado: " + ("tudo certo" if not falhas else f"{falhas} item(ns) com erro")
          + " · validado por formato, não testado num OpenBot em execução")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
