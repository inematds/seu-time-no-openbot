#!/usr/bin/env python3
"""Resumo semanal de financas/despesas.csv (colunas: data,valor,descricao,categoria,forma,origem).

Uso: python3 resumo_semana.py despesas.csv [--semana AAAA-MM-DD]
Sem --semana, resume a semana anterior (segunda a domingo) à data de hoje.
Só lê o arquivo: não escreve nada, não usa rede.
"""
import argparse
import csv
import datetime as dt
import sys
from collections import defaultdict


def segunda_da_semana(dia: dt.date) -> dt.date:
    return dia - dt.timedelta(days=dia.weekday())


def ler(caminho):
    linhas = []
    with open(caminho, newline="", encoding="utf-8") as f:
        for n, linha in enumerate(csv.DictReader(f), start=2):
            try:
                data = dt.date.fromisoformat(linha["data"].strip())
                valor = float(linha["valor"].strip().replace(",", "."))
            except (KeyError, ValueError, AttributeError):
                print(f"aviso: linha {n} ignorada (data ou valor inválido)", file=sys.stderr)
                continue
            linhas.append({
                "data": data,
                "valor": valor,
                "descricao": (linha.get("descricao") or "").strip(),
                "categoria": (linha.get("categoria") or "Outros").strip() or "Outros",
            })
    return linhas


def resumir(linhas, inicio: dt.date):
    fim = inicio + dt.timedelta(days=6)
    semana = [l for l in linhas if inicio <= l["data"] <= fim]
    anterior_ini = inicio - dt.timedelta(days=7)
    anterior = [l for l in linhas if anterior_ini <= l["data"] < inicio]
    por_cat = defaultdict(float)
    for l in semana:
        por_cat[l["categoria"]] += l["valor"]
    return {
        "inicio": inicio,
        "fim": fim,
        "total": round(sum(l["valor"] for l in semana), 2),
        "total_anterior": round(sum(l["valor"] for l in anterior), 2),
        "por_categoria": sorted(((c, round(v, 2)) for c, v in por_cat.items()), key=lambda x: (-x[1], x[0])),
        "maiores": sorted(semana, key=lambda l: -l["valor"])[:3],
        "lancamentos": len(semana),
    }


def reais(v: float) -> str:
    inteiro, centavos = f"{v:,.2f}".split(".")
    return "R$ " + inteiro.replace(",", ".") + "," + centavos


def texto(r) -> str:
    out = [f"Semana {r['inicio']:%d/%m} a {r['fim']:%d/%m}: {reais(r['total'])} em {r['lancamentos']} lançamentos"]
    for cat, v in r["por_categoria"]:
        out.append(f"- {cat}: {reais(v)}")
    if r["maiores"]:
        out.append("Maiores: " + "; ".join(f"{l['descricao'] or '?'} {reais(l['valor'])}" for l in r["maiores"]))
    dif = round(r["total"] - r["total_anterior"], 2)
    sinal = "+" if dif >= 0 else "-"
    out.append(f"Semana anterior: {reais(r['total_anterior'])} ({sinal}{reais(abs(dif))})")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("csv")
    p.add_argument("--semana", help="qualquer dia da semana a resumir (AAAA-MM-DD)")
    a = p.parse_args(argv)
    if a.semana:
        inicio = segunda_da_semana(dt.date.fromisoformat(a.semana))
    else:
        inicio = segunda_da_semana(dt.date.today()) - dt.timedelta(days=7)
    print(texto(resumir(ler(a.csv), inicio)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
