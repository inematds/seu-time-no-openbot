# OpenBot numa VPS, do zero (Docker)

Para ter o time rodando 24 horas, mesmo com o seu computador desligado. Tudo aqui vem de
`docs/docker.md` e `docs/self-hosted-server.md` do OpenBot v0.77.0 (ver [../FONTE.md](../FONTE.md)).

**O que já foi testado de verdade:** numa VPS de teste do INEMA (Ubuntu 24.04, Docker 29.1.3,
Compose 2.40.3), em 24/11/2026, os passos 1 a 5 abaixo rodaram com este `compose.yaml`: a imagem
(1,45 GB) baixou, o container subiu sem erro, parado usa cerca de 716 MiB de RAM, nenhuma porta
ficou publicada e o `status` respondeu:

```
OpenBot 0.77.0
Account: signed out
Server: unconfigured
Memory: 5428 MiB free of 6144 MiB (ok)
Turns at the same time: at most 8
```

Do passo 6 em diante (login, provedor, celular, importação, backup e restauração na VPS):
**validado por formato, ainda não testado em execução.**

## Antes de começar

- VPS com Ubuntu 24.04 (ou 26.04), Docker e o plugin Compose, e pelo menos 8 GB de RAM (o
  `compose.yaml` limita o OpenBot a 6 GB; com 4 GB de VPS, troque `mem_limit: 6g` por `3g`, e o
  OpenBot roda 2 turnos por vez em vez de 8; `docs/docker.md`, "Memory").
- Espaço em disco: a imagem tem 1,45 GB, mais os dados dos agentes e os backups.
- Leia o [checklist de segurança](../SEGURANCA.md) antes do passo 6.

## Passo a passo

| # | Passo | Comando | Status |
|---|---|---|---|
| 1 | Pasta do OpenBot | `sudo mkdir -p /opt/openbot && cd /opt/openbot` | testado na VPS em 24/11 |
| 2 | Arquivos do kit | copie `compose.yaml`, `seccomp.sha256`, `backup.sh`, `restaurar.sh` e `achar-openbot.sh` desta pasta `instalacao/` para `/opt/openbot` (ex.: `scp instalacao/* usuario@vps:/tmp/` e `sudo mv /tmp/{compose.yaml,seccomp.sha256,*.sh} /opt/openbot/`) | compose testado na VPS em 24/11 |
| 3 | Perfil de segurança oficial | `sudo curl -fsSLO https://raw.githubusercontent.com/nightly-labs/openbot/v0.77.0/docker/seccomp.json && sudo sha256sum -c seccomp.sha256` | testado na VPS em 24/11 (a conferência do sha256: validado por formato) |
| 4 | Baixar e subir | `sudo docker compose pull && sudo docker compose up -d` | testado na VPS em 24/11 |
| 5 | Conferir | `sudo docker compose exec -T openbot openbot status` | testado na VPS em 24/11 |
| 6 | Entrar na sua conta OpenBot | `sudo docker compose exec openbot openbot login` (pede o seu e-mail e o código que chega nele) | validado por formato |
| 7 | Conectar a IA | no app do OpenBot (computador) ou em `openbot.run/app`, abra o servidor e conecte o provedor (Codex, Claude, Gemini ou os modelos grátis do OpenCode) | validado por formato |
| 8 | Celular | `sudo docker compose exec openbot openbot mobile-connect` mostra o QR code do app do celular | validado por formato |
| 9 | Seu time | monte o pacote no seu computador (`python3 importar/montar_pacote.py`) e escolha `dist/seu-time-openbot.zip` em **Server settings → Import** no app | validado por formato |
| 10 | WhatsApp (opcional, chip separado) | no app: **Marketplace → Apps → WhatsApp → Link WhatsApp**, escolha **A number only for OpenBot**, leia o QR code no celular do chip, escolha o modelo do **WhatsApp Orchestrator** e **Add agent**; em **Who can write**, só você (`docs/messaging.md`, "Connect WhatsApp") | validado por formato |
| 11 | Primeiro backup | `cd /opt/openbot && sudo bash backup.sh` | validado por formato (o script passou no teste com pasta falsa) |
| 12 | Backup todo dia às 4h | `sudo crontab -e` e acrescente `0 4 * * * cd /opt/openbot && bash backup.sh >> /var/log/openbot-backup.log 2>&1` | validado por formato |

**Quem responde no WhatsApp (passo 10):** é o *WhatsApp Orchestrator*, um agente que o próprio
OpenBot cria ao ligar o número, e não o Orquestrador do kit. Para o Slack, a documentação diz que
esse orquestrador "answers short requests itself, and gives other work to the one agent that fits
best"; para o WhatsApp ela diz só que "one orchestrator answers every linked number". Se o gasto
mandado pelo WhatsApp não chegar ao Financeiro, diga ao WhatsApp Orchestrator, na primeira conversa,
para passar gastos ao Financeiro e tarefas ao Organizador. **Não testado com este kit.**

O passo 6 e o 7 o OpenBot pede uma vez só; depois disso o servidor aparece no app do computador,
no app do celular e em `openbot.run/app`.

## Backup e restauração na VPS

O `docs/docker.md` diz: "To back it up, stop the container and copy the volume." O `backup.sh` faz
exatamente isso:

1. acha o container e o volume (no `/opt/openbot`, o Compose chama de `openbot-openbot-1` e
   `openbot_openbot-data`);
2. para o container (espera até 60 s), copia o `/data` inteiro para
   `/root/backups-openbot/openbot-<data>.tar.gz` usando a própria imagem do OpenBot, sem rede;
3. confere que o banco, o chaveiro e a senha do chaveiro estão no arquivo (sem eles os dados não
   abrem), grava o `.sha256` e só então dá o nome final;
4. liga o container de novo e apaga os backups mais antigos além de 7 (`OPENBOT_BACKUP_KEEP`).

O backup tem as chaves dos seus dados: ele fica com permissão 600, numa pasta 700. **Copie para
fora da VPS** (outra máquina, outro disco), por exemplo do seu computador:
`scp root@vps:/root/backups-openbot/openbot-*.tar.gz* ~/backups-openbot/`.

Para restaurar (apaga o `/data` atual e põe o backup no lugar; antes disso faz um backup do estado
atual):

```
cd /opt/openbot
sudo bash restaurar.sh /root/backups-openbot/openbot-20261124T040000Z.tar.gz --confirmo
```

Restaure com a **mesma versão da imagem ou uma mais nova**: "an older OpenBot cannot open a database
that a newer one migrated" (`docs/docker.md`, "Upgrades"). O script compara a imagem do backup com
a do container e para se forem diferentes.

## Atualizar

`docs/docker.md` ("Upgrades"): leia as notas da versão nova, compare o `compose.yaml` e o
`seccomp.json` da tag nova com os seus, faça o backup, troque `0.77.0` pela versão nova no
`compose.yaml`, baixe o `seccomp.json` da mesma tag e rode `sudo docker compose pull && sudo docker compose up -d`.
Nunca volte para uma versão mais velha.

Conferir a imagem antes (opcional, precisa do `gh`, `docs/docker.md` "Security"):

```
gh attestation verify oci://ghcr.io/nightly-labs/openbot:0.77.0 \
  --repo nightly-labs/openbot \
  --signer-workflow nightly-labs/openbot/.github/workflows/release.yml \
  --source-ref refs/tags/v0.77.0
```

## Outros comandos (de `docs/docker.md`, "Commands")

| Para | Comando |
|---|---|
| Ver o log | `sudo docker compose logs openbot` |
| Parar, ligar, reiniciar | `sudo docker compose stop`, `sudo docker compose start`, `sudo docker compose restart` |
| Sair da conta | `sudo docker compose exec openbot openbot logout` |
| Remover (os dados ficam no volume) | `sudo docker compose exec openbot openbot logout && sudo docker compose down` |
| Apagar os dados de vez | `sudo docker volume rm openbot_openbot-data` (sem volta; faça backup antes) |
