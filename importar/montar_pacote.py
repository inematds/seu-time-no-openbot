#!/usr/bin/env python3
"""Monta dist/seu-time-openbot.zip no formato de importação de agentes do OpenBot.

Formato: openbot-agent-import versão 1, como descrito em
resources/agent-import/grok-bot/SKILL.md (OpenBot v0.77.0, commit 20d1cd6), seção "Format":
  openbot-import.json na raiz + agents/<key>/skills/<skill>/SKILL.md.
Validado por formato (validar.py); não testado num OpenBot em execução.

Uso: python3 importar/montar_pacote.py [--saida dist/seu-time-openbot.zip]
"""
import argparse
import datetime as dt
import json
import os
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "importar" / "agentes.json"
SKILLS = RAIZ / "skills"
PADRAO = RAIZ / "dist" / "seu-time-openbot.zip"
IGNORAR = {"__pycache__", ".pytest_cache", ".DS_Store"}


def manifesto(fonte: dict, exportado_em: str | None = None) -> dict:
    tz = fonte.get("timezone", "America/Sao_Paulo")
    agentes = []
    for a in fonte["agents"]:
        key = a["key"]
        agentes.append({
            "key": key,
            "name": a["name"],
            "title": a.get("title", ""),
            "description": a["description"],
            "avatar": None,
            "skills": [f"agents/{key}/skills/{s}" for s in a.get("skills", [])],
            "routines": [{**r, "timezone": r.get("timezone", tz)} for r in a.get("routines", [])],
            "memories": a.get("memories", []),
            "files": None,
        })
    canais = []
    for c in fonte.get("channels", []):
        canais.append({**c, "routines": [{**r, "timezone": r.get("timezone", tz)} for r in c.get("routines", [])]})
    return {
        "format": "openbot-agent-import",
        "version": 1,
        "source": {
            "app": "seu-time-no-openbot",
            "exportedAt": exportado_em or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "agents": agentes,
        "channels": canais,
    }


def arquivos_da_skill(pasta: Path):
    for raiz, dirs, files in os.walk(pasta):
        dirs[:] = sorted(d for d in dirs if d not in IGNORAR)
        for nome in sorted(files):
            if nome in IGNORAR:
                continue
            p = Path(raiz) / nome
            yield p, p.relative_to(pasta).as_posix()


def montar(saida: Path = PADRAO, fonte_path: Path = FONTE, exportado_em: str | None = None) -> Path:
    fonte = json.loads(fonte_path.read_text(encoding="utf-8"))
    man = manifesto(fonte, exportado_em)
    saida.parent.mkdir(parents=True, exist_ok=True)
    tmp = saida.with_name("." + saida.name + ".part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for a in fonte["agents"]:
            for s in a.get("skills", []):
                pasta = SKILLS / s
                if not (pasta / "SKILL.md").is_file():
                    raise SystemExit(f"skill sem SKILL.md: {pasta}")
                for p, rel in arquivos_da_skill(pasta):
                    z.write(p, f"agents/{a['key']}/skills/{s}/{rel}")
        # o manifesto vai por último, como pede a seção "Workflow" passo 5 do formato
        z.writestr("openbot-import.json", json.dumps(man, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, saida)  # troca de uma vez, para nunca deixar um zip pela metade
    return saida


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--saida", type=Path, default=PADRAO)
    a = p.parse_args(argv)
    print(f"Pacote pronto: {montar(a.saida)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
