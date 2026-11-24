# Fonte: OpenBot

Este kit funciona por cima do **OpenBot** (https://openbot.run), um programa de terceiros. O kit
não é oficial, não tem ligação com os autores do OpenBot e **não inclui o código do OpenBot**.

## Versão de referência

| | |
|---|---|
| Repositório | https://github.com/nightly-labs/openbot |
| Tag | `v0.77.0` |
| Commit | `20d1cd63d95ac91f049054b1afdd00ece27b322b` |
| Imagem Docker | `ghcr.io/nightly-labs/openbot:0.77.0` |
| `docker/seccomp.json` (sha256) | `665289e6a1c41045f55166d0b01993c929f71df78e3a3b264f3252bb8e0b3d9e` |
| `docker/compose.yaml` oficial (sha256) | `38ac3086bd112125f073ee515881c5a2db981a35d70d1dee160f00fab996d5b7` |

Arquivos do OpenBot lidos para montar o kit (todos nessa tag): `README.md`, `LICENSE`, `NOTICE`,
`CLA.md`, `SECURITY.md`, `docs/docker.md`, `docs/self-hosted-server.md`, `docs/messaging.md`,
`docs/automation.md`, `docs/webhooks.md`, `docs/provider-terms.md`, `docker/compose.yaml`,
`docker/seccomp.json`, `docker/Dockerfile`, `docker/instances/openbot-instance`,
`resources/managed-skills/openbot-skill-creator/SKILL.md`,
`resources/agent-import/grok-bot/SKILL.md` e, para os limites do `validar.py`,
`src/main/skill-package.ts`, `src/main/local-skill-library.ts`, `src/main/agent-import-manifest.ts`,
`src/main/theme-palette-files.ts`, `packages/contracts/src/{input-limits,ipc-agent-import,ipc-routines,app-appearance,ipc-skills}.ts`.

## Licença do OpenBot

O OpenBot é licenciado pela **PolyForm Noncommercial License 1.0.0**:
https://polyformproject.org/licenses/noncommercial/1.0.0 (texto oficial no
[LICENSE](https://github.com/nightly-labs/openbot/blob/v0.77.0/LICENSE) do repositório).

- Grátis para uso pessoal e outros fins não comerciais permitidos pela licença.
- O README do OpenBot: "OpenBot is not free software" e "Commercial use requires a separate license
  from the copyright owner" (Settings → Billing, planos Starter e Team, ou licenses@openbot.run).
- Versões até 0.1.11 continuam sob Apache-2.0; a 0.77.0, usada aqui, não.

Avisos obrigatórios do licenciante (`LICENSE`, linhas 75 e 77), repassados como a licença pede:

```
Required Notice: Copyright 2026 Synthetify Labs spółka z ograniczoną odpowiedzialnością.
Required Notice: For a commercial license, contact licenses@openbot.run.
```

Atribuição e avisos de terceiros: [NOTICE](https://github.com/nightly-labs/openbot/blob/v0.77.0/NOTICE)
do OpenBot ("Copyright 2026 Synthetify Labs spółka z ograniczoną odpowiedzialnością").

## O que é derivado do OpenBot neste kit

| Arquivo do kit | Derivado de | Licença |
|---|---|---|
| `instalacao/compose.yaml` | `docker/compose.yaml` (v0.77.0) | PolyForm Noncommercial 1.0.0; os avisos acima estão no cabeçalho do arquivo |
| `instalacao/seccomp.sha256` | só o hash do `docker/seccomp.json` oficial | o `seccomp.json` **não** vem no kit: você baixa da fonte oficial na tag `v0.77.0` |
| `validar.py` | os limites e regras de formato citados linha a linha no código | o código do validador é nosso; os números e expressões regulares vêm dos arquivos citados |

As skills, o pacote de importação, o tema, os scripts de backup e a documentação são do kit
(ver [LICENSE](LICENSE)). O formato que eles seguem é o do OpenBot.

## O que foi testado

- **Testado numa VPS de teste do INEMA em 24/11/2026:** `docker compose pull && docker compose up -d`
  com o `instalacao/compose.yaml` e o `openbot status` (detalhes em [instalacao/VPS.md](instalacao/VPS.md)).
- **Validado por formato, não testado em execução:** as skills, o pacote de importação, o tema, o
  login, a conexão com provedores, o WhatsApp, e o `backup.sh`/`restaurar.sh` contra um volume real
  (os dois passaram no teste com uma pasta falsa no lugar do volume).
