#!/usr/bin/env bash
# restaurar.sh — põe de volta um backup feito pelo backup.sh, substituindo o /data inteiro.
#
# Cuidado (OpenBot v0.77.0, docs/docker.md "Upgrades"): "Do not go back to an older tag: an older
# OpenBot cannot open a database that a newer one migrated". Restaure com a MESMA imagem do
# backup ou uma mais nova. O script compara e para se forem diferentes, a menos que você
# confirme com --outra-imagem.
#
# Uso:
#   cd /opt/openbot && sudo bash restaurar.sh /root/backups-openbot/openbot-20261124T040000Z.tar.gz --confirmo
#
# Antes de apagar, ele faz um backup do estado atual (backup.sh), para dar para voltar atrás.
# Variáveis: as mesmas do backup.sh (OPENBOT_COMPOSE_DIR, OPENBOT_CONTAINER, OPENBOT_VOLUME,
# OPENBOT_BACKUP_DIR, e OPENBOT_DADOS_DIR para o modo teste, que não roda nenhum comando docker).
# Validado pelo teste com pasta falsa (tests/); não testado num OpenBot em execução.
set -euo pipefail

DADOS_FALSOS=${OPENBOT_DADOS_DIR:-}
AQUI=$(cd "$(dirname "$0")" && pwd -P)
OBRIGATORIOS=(.config/OpenBot/openbot.db .local/share/keyrings/login.keyring .config/openbot-container/keyring-password)

falha() { echo "Falhou: $*" >&2; exit 1; }

ARQ=""; CONFIRMO=0; OUTRA=0; SEM_ANTES=0
for a in "$@"; do
  case "$a" in
    --confirmo) CONFIRMO=1 ;;
    --outra-imagem) OUTRA=1 ;;
    --sem-backup-antes) SEM_ANTES=1 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    -*) falha "opção desconhecida: $a" ;;
    *) ARQ=$a ;;
  esac
done
[ -n "$ARQ" ] || falha "diga qual backup: bash restaurar.sh <arquivo.tar.gz> --confirmo"
[ -f "$ARQ" ] || falha "arquivo não encontrado: $ARQ"
ARQ=$(cd "$(dirname "$ARQ")" && pwd -P)/$(basename "$ARQ")
DIR=$(dirname "$ARQ"); NOME=$(basename "$ARQ")

if [ -f "$ARQ.sha256" ]; then
  ( cd "$DIR" && sha256sum --quiet -c "$NOME.sha256" ) || falha "o arquivo não bate com $NOME.sha256 (corrompido?)."
else
  echo "Atenção: sem $NOME.sha256, não deu para conferir o arquivo." >&2
fi

LISTA=$(tar -tzf "$ARQ") || falha "não é um .tar.gz válido."
for f in "${OBRIGATORIOS[@]}"; do
  grep -qxF "./$f" <<<"$LISTA" || falha "o backup não tem $f; restaurar deixaria os dados sem abrir."
done

IMAGEM_BACKUP=$(sed -n 's/^imagem=//p' "$ARQ.info" 2>/dev/null || true)
if [ -n "$DADOS_FALSOS" ]; then
  IMAGEM_AGORA="teste"
else
  command -v docker >/dev/null || falha "docker não encontrado."
  # shellcheck source=achar-openbot.sh
  . "$AQUI/achar-openbot.sh"
  IMAGEM_AGORA=$(docker inspect --format '{{.Config.Image}}' "$CONTAINER") || falha "container $CONTAINER não existe."
fi
if [ -n "$IMAGEM_BACKUP" ] && [ "$IMAGEM_BACKUP" != "$IMAGEM_AGORA" ] && [ "$OUTRA" -eq 0 ]; then
  falha "o backup é da imagem $IMAGEM_BACKUP e o container usa $IMAGEM_AGORA. Restaure com a mesma versão ou uma mais nova; se tiver certeza, repita com --outra-imagem."
fi

if [ "$CONFIRMO" -ne 1 ]; then
  echo "Isto APAGA o /data atual ($([ -n "$DADOS_FALSOS" ] && echo "$DADOS_FALSOS" || echo "volume $VOLUME")) e põe $NOME no lugar."
  echo "Se é isso, repita com --confirmo."
  exit 2
fi

if [ "$SEM_ANTES" -eq 0 ]; then
  echo "Backup do estado atual antes de restaurar..."
  # sem rotação aqui: a rotação poderia apagar justamente o backup que vamos restaurar
  OPENBOT_BACKUP_KEEP=100000 bash "$AQUI/backup.sh"
fi

if [ -n "$DADOS_FALSOS" ]; then
  [ -d "$DADOS_FALSOS" ] || falha "OPENBOT_DADOS_DIR não é uma pasta: $DADOS_FALSOS"
  find "$DADOS_FALSOS" -mindepth 1 -delete
  tar -xzpf "$ARQ" -C "$DADOS_FALSOS"
else
  docker stop --time 60 "$CONTAINER" >/dev/null || true
  docker run --rm --network none --user 0:0 --entrypoint sh \
    -v "$VOLUME":/data -v "$DIR":/backup:ro \
    "$IMAGEM_AGORA" -c "find /data -mindepth 1 -delete && tar -xzpf '/backup/$NOME' --numeric-owner -C /data"
  docker start "$CONTAINER" >/dev/null
fi
echo "Restaurado: $NOME"
