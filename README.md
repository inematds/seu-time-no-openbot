# 🤝 Seu time no OpenBot

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Seu time no OpenBot](guia/assets/banner.jpg)](https://inematds.github.io/seu-time-no-openbot/guia/)

**Você pode ter o seu próprio time de agentes trabalhando 24 horas, usando a IA que você já assina.**
O OpenBot põe esse time no seu computador ou numa VPS. Este kit entrega o time pronto em
português (um coordenador, um assessor financeiro, um organizador e um revisor), a instalação
segura com backup e o checklist do que mudar antes de deixar os agentes trabalhando sozinhos.

## 📖 Guia

Para entender o que o kit faz e como ele muda o seu dia (sem parte técnica):
**https://inematds.github.io/seu-time-no-openbot/guia/**

## O que é

É um kit gratuito para quem quer usar o OpenBot, um programa que roda agentes de IA no seu
computador ou num servidor, usando a assinatura que você já tem (ChatGPT/Codex, Claude, Gemini)
ou modelos grátis. O kit traz quatro agentes prontos em português, um pacote para importar todos
de uma vez, a instalação em Docker com proteções e backup, um checklist de segurança e o tema de
cores do INEMA. Você precisa do OpenBot instalado (computador ou VPS) e de uma conta de IA.

## Como começar (sem ser técnico)

Abra a IA que você já usa (ChatGPT, Claude ou Gemini, com a pesquisa na internet ligada, ou o
Claude Code / Codex, se você já usa) numa conversa nova e cole este pedido:

```text
Leia o kit https://github.com/inematds/seu-time-no-openbot (README.md, SEGURANCA.md e
instalacao/VPS.md). Me explique em linguagem simples: se o OpenBot serve para o que eu faço,
o que cada agente do time faz, o que eu preciso ter (computador ou VPS, conta de IA, número
de WhatsApp separado) e o que muda na minha segurança. Depois me diga, em até 5 passos, por
onde eu começaria. Não instale nada, não rode docker e não mude nada antes do meu sim.
```

## O que vem no kit

| Parte | O que faz | Status |
|---|---|---|
| `skills/` | 4 skills em português no formato do OpenBot: Orquestrador do time, Assessor financeiro (com `resumo_semana.py`), Organizador pessoal, Revisor de entregas | validado por formato |
| `importar/` | `agentes.json` + `montar_pacote.py`: monta `dist/seu-time-openbot.zip` com os 4 agentes, as instruções, as skills, 3 rotinas (desligadas) e o canal "Meu time" | validado por formato |
| `instalacao/compose.yaml` | Docker com o seccomp oficial, `no-new-privileges`, limite de 6 GB, versão fixa e volume próprio, sem porta publicada | **testado na VPS em 24/11/2026** (subida e `status`) |
| `instalacao/backup.sh`, `restaurar.sh` | backup do volume inteiro com rotação, conferência e restauração | testado na VPS em 24/11 (backup de 50 MB + restauração no volume real) + teste com pasta falsa |
| `instalacao/VPS.md` | OpenBot numa VPS, do zero, comando por comando | passos 1–5 testados na VPS em 24/11; o resto validado por formato |
| `instalacao/servidor-sem-docker.md` | a opção oficial sem Docker | validado por formato |
| `SEGURANCA.md` | checklist: permissão, conta de IA, WhatsApp, cofre de senhas, backup, licença | conferido na documentação |
| `themes/inema.json` | tema INEMA (preto `#0c0c10`, amarelo `#FACC15`) | validado por formato |
| `validar.py` + `tests/` | confere tudo isso contra as regras do OpenBot v0.77.0 | rodado (saída abaixo) |

**"Validado por formato"** quer dizer: o arquivo segue as regras escritas no código e na
documentação do OpenBot, e o `validar.py` confere. **Não quer dizer** que rodou num OpenBot.
O que rodou de verdade está marcado como testado.

## ⚠️ Antes de usar

- Os agentes do OpenBot rodam com acesso completo por padrão. Leia o [SEGURANCA.md](SEGURANCA.md)
  e troque para *Ask first* (perguntar antes) onde fizer sentido.
- WhatsApp: use um **chip separado**. O OpenBot usa um cliente não oficial e o WhatsApp pode
  bloquear o número.
- O OpenBot é grátis para uso pessoal e não comercial (PolyForm Noncommercial 1.0.0). **Uso
  comercial pede licença paga do OpenBot.** Ver [FONTE.md](FONTE.md).

---

## Instalação técnica

### Pré-requisitos

- Para conferir o kit: Python 3.10+ com `pyyaml` e `pytest` (`pip install pyyaml pytest`), `bash`, `tar`.
- Para rodar o OpenBot: o app (macOS, Windows, Linux) das [releases do OpenBot](https://github.com/nightly-labs/openbot/releases),
  ou uma VPS Ubuntu 24.04 com Docker e Compose ([instalacao/VPS.md](instalacao/VPS.md)).

### Os arquivos

```
skills/<nome>/SKILL.md          frontmatter name/description/example-prompt + instruções
importar/agentes.json           fonte do pacote (agentes, rotinas, memórias, canal)
importar/montar_pacote.py       gera dist/seu-time-openbot.zip (openbot-agent-import v1)
instalacao/compose.yaml         Docker (derivado do oficial, PolyForm Noncommercial)
instalacao/seccomp.sha256       hash do seccomp.json oficial da tag v0.77.0
instalacao/backup.sh            backup do /data com rotação
instalacao/restaurar.sh         restauração (faz backup do estado atual antes)
instalacao/achar-openbot.sh     acha o container e o volume (usado pelos dois acima)
themes/inema.json               tema no formato "Theme palette files"
validar.py                      confere skills, tema, pacote, compose e scripts
tests/test_kit.py               50 testes, sem docker
```

### Conferir o kit

```bash
python3 validar.py
python3 -m pytest -q
```

Saída real em 24/11/2026:

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

Os testes cobrem: cada limite das skills (name 80, description 500, example-prompt 1.000,
200 arquivos, `.env`, zip dentro, link simbólico, ícone PNG, nome com acento que vira slug
estranho), o tema (cor faltando, hex errado, aparência, nome do arquivo), o compose (sem
seccomp, sem `no-new-privileges`, sem memória, `latest`, pasta do host, socket do Docker,
`unconfined`, e igual ao da VPS de teste), o pacote (key, key repetida, instruções acima de
2.000, agenda inválida, intervalo menor que 3 min, skill fora da pasta do agente, membro
desconhecido, fuso inválido, manifesto fora da raiz), o backup com uma pasta falsa no lugar do
volume (ida e volta, permissões 600/700, rotação, recusa sem chaveiro sem apagar os antigos,
recusa dentro dos dados, arquivo corrompido) e o resumo semanal. Nenhum teste chama docker: um
`docker` falso no PATH reprova o teste se for chamado.

### Montar o pacote do time

```bash
python3 importar/montar_pacote.py
# Pacote pronto: .../dist/seu-time-openbot.zip
```

No OpenBot: **Server settings → Import**, escolha o `.zip`, marque os agentes e importe
(`README.md` do OpenBot, "Import agents from Grok Bot"; o formato é o de
`resources/agent-import/grok-bot/SKILL.md`). As rotinas chegam **desligadas**. Sem importar,
dá para criar as skills uma a uma: peça a um agente para registrar a pasta de `skills/<nome>`
como skill local (`create_skill`, ver `openbot-skill-creator`).

### Tema INEMA

No app de computador, no Linux (no macOS e no Windows, a pasta `themes` fica dentro da pasta de
dados do OpenBot):

```bash
mkdir -p ~/.config/OpenBot/themes
cp themes/inema.json ~/.config/OpenBot/themes/.inema.json.tmp
mv ~/.config/OpenBot/themes/.inema.json.tmp ~/.config/OpenBot/themes/inema.json
```

O `mv` troca o arquivo de uma vez, como pede o README do OpenBot. Depois: Settings > Appearance > Theme.

### Na VPS

Passo a passo completo em [instalacao/VPS.md](instalacao/VPS.md). Resumo:

```bash
sudo mkdir -p /opt/openbot && cd /opt/openbot
# copie para cá: compose.yaml, seccomp.sha256, backup.sh, restaurar.sh, achar-openbot.sh
sudo curl -fsSLO https://raw.githubusercontent.com/nightly-labs/openbot/v0.77.0/docker/seccomp.json
sudo sha256sum -c seccomp.sha256
sudo docker compose pull && sudo docker compose up -d       # testado na VPS em 24/11/2026
sudo docker compose exec -T openbot openbot status          # testado na VPS em 24/11/2026
sudo docker compose exec openbot openbot login               # validado por formato
sudo bash backup.sh                                          # testado na VPS em 24/11
```

## O processo, do início ao fim

🧠 = sessão com o Nei (ou você, no seu computador) · ⚙️ = script/timer · 🤖 = `claude -p` curto (sessão nova)

| # | Passo | Comando / o que acontece | Quem | Status |
|---|---|---|---|---|
| 1 | Ler o checklist | [SEGURANCA.md](SEGURANCA.md): permissão, conta, WhatsApp, cofre, licença | 🧠 | — |
| 2 | Conferir o kit | `python3 validar.py && python3 -m pytest -q` | ⚙️ | rodado em 24/11 |
| 3 | Montar o pacote | `python3 importar/montar_pacote.py` → `dist/seu-time-openbot.zip` | ⚙️ | validado por formato |
| 4 | Subir o OpenBot na VPS | `instalacao/VPS.md` passos 1–5 (`docker compose pull && docker compose up -d`, `openbot status`) | ⚙️ | testado na VPS em 24/11 |
| 5 | Entrar na conta OpenBot | `docker compose exec openbot openbot login` (e-mail + código) | 🧠 | validado por formato |
| 6 | Conectar a IA | no app ou em `openbot.run/app`: Codex, Claude, Gemini ou OpenCode (Free) | 🧠 | validado por formato |
| 7 | Importar o time | Server settings → Import → `seu-time-openbot.zip` | 🧠 | validado por formato |
| 7b | Ligar o WhatsApp (opcional) | chip separado; Marketplace → Apps → WhatsApp → *A number only for OpenBot*. Quem responde é o *WhatsApp Orchestrator* do próprio OpenBot, que deve passar gastos ao Financeiro ([VPS.md](instalacao/VPS.md), passo 10) | 🧠 | não testado |
| 8 | Baixar as permissões | cada agente em *Ask first* (SEGURANCA.md §1) | 🧠 | validado por formato |
| 9 | Tema | copiar `themes/inema.json` para a pasta `themes` (acima) | ⚙️ | validado por formato |
| 10 | Ligar as rotinas | uma por vez: Plano do dia, Resumo da semana, Revisão da semana | 🧠 | validado por formato |
| 11 | Backup diário | `crontab`: `0 4 * * * cd /opt/openbot && bash backup.sh` + cópia para fora da VPS | ⚙️ | validado por formato |
| 12 | Revisar o guia | revisor independente (`claude -p`, runbook `revisor-independente.md`) lê o guia publicado | 🤖 | feito em 24/11 |
| 13 | Nova versão do OpenBot | trocar a tag em FONTE.md, `compose.yaml`, `seccomp.sha256` e as citações do `validar.py`; rodar o passo 2 | 🧠 + ⚙️ | — |

## A prova

O que rodou de verdade: o `validar.py` e os 50 testes deste repositório (saída acima) e, numa VPS
de teste do INEMA em 24/11/2026, a subida do container com este `compose.yaml` e o `openbot
status` (`OpenBot 0.77.0 · Memory: 5428 MiB free of 6144 MiB (ok) · Turns at the same time: at most 8`).
O que **não** rodou ainda: login, provedor, WhatsApp, importação do pacote, as skills dentro de
um agente, o tema no app e o backup contra o volume real.

## De onde vem

OpenBot v0.77.0 (`nightly-labs/openbot`, commit `20d1cd6`). Tudo o que o kit afirma sobre o
OpenBot vem da documentação e do código dessa versão, listados em [FONTE.md](FONTE.md), junto
com a licença e os avisos obrigatórios. Este kit não é oficial e não inclui o código do OpenBot.

## Licença

Arquivos do kit: MIT ([LICENSE](LICENSE)). `instalacao/compose.yaml` é derivado do OpenBot e segue a
PolyForm Noncommercial 1.0.0. O OpenBot em si: PolyForm Noncommercial 1.0.0, uso comercial com
licença paga dele.

---

Feito pelo [INEMA.CLUB](https://inema.club): conteúdo aberto e gratuito sobre IA na prática.
