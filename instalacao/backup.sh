#!/usr/bin/env bash
# backup.sh — copia o /data inteiro do OpenBot (volume openbot-data) para um .tar.gz, com rotação.
#
# Regras seguidas (OpenBot v0.77.0, docs/docker.md "Data" e "Backups"):
#   - "To back it up, stop the container and copy the volume": o container para durante a cópia
#     e volta a rodar no fim (se estava rodando);
#   - "Keep /data as one unit": copia o volume inteiro, com o chaveiro e a senha dele;
#   - a cópia nasce como .partial e só ganha o nome final quando está completa;
#   - um backup antigo só sai depois que o novo ficou pronto;
#   - o backup tem as chaves do OpenBot: arquivo 600, pasta 700, fora do volume.
#
# Uso (na pasta do compose.yaml, ex.: /opt/openbot):
#   sudo bash backup.sh
#   sudo OPENBOT_BACKUP_DIR=/mnt/hd/openbot OPENBOT_BACKUP_KEEP=14 bash backup.sh
#
# Variáveis:
#   OPENBOT_COMPOSE_DIR pasta do compose.yaml        (padrão: a pasta atual)
#   OPENBOT_CONTAINER   nome do container            (padrão: o do serviço openbot nesse compose;
#                                                     sem compose, "openbot")
#   OPENBOT_VOLUME      volume montado em /data      (padrão: lido do próprio container)
#   OPENBOT_BACKUP_DIR  pasta dos backups            (padrão: ~/backups-openbot)
#   OPENBOT_BACKUP_KEEP quantos backups manter       (padrão: 7)
#   OPENBOT_DADOS_DIR   MODO TESTE: uma pasta comum no lugar do volume. Nenhum comando docker roda.
#
# Validado por formato e pelo teste com pasta falsa (tests/); não testado num OpenBot em execução.
set -euo pipefail

DESTINO=${OPENBOT_BACKUP_DIR:-$HOME/backups-openbot}
MANTER=${OPENBOT_BACKUP_KEEP:-7}
DADOS_FALSOS=${OPENBOT_DADOS_DIR:-}

# Arquivos sem os quais o /data não abre (docker/instances/openbot-instance, REQUIRED_FILES).
OBRIGATORIOS=(.config/OpenBot/openbot.db .local/share/keyrings/login.keyring .config/openbot-container/keyring-password)

falha() { echo "Falhou: $*" >&2; exit 1; }

[[ $MANTER =~ ^[1-9][0-9]*$ ]] || falha "OPENBOT_BACKUP_KEEP tem que ser um número de 1 para cima."

umask 077
mkdir -p "$DESTINO"
chmod 700 "$DESTINO"
DESTINO=$(cd "$DESTINO" && pwd -P)

if [ -n "$DADOS_FALSOS" ]; then
  [ -d "$DADOS_FALSOS" ] || falha "OPENBOT_DADOS_DIR não é uma pasta: $DADOS_FALSOS"
  DADOS_FALSOS=$(cd "$DADOS_FALSOS" && pwd -P)
  case "$DESTINO/" in
    "$DADOS_FALSOS"/*) falha "a pasta dos backups não pode ficar dentro dos dados." ;;
  esac
fi

while :; do
  CARIMBO=$(date -u +%Y%m%dT%H%M%SZ)
  NOME="openbot-$CARIMBO.tar.gz"
  [ -e "$DESTINO/$NOME" ] || break
  sleep 1   # já existe um backup deste segundo: espera o próximo
done
PARCIAL="$DESTINO/$NOME.partial"
FINAL="$DESTINO/$NOME"
rm -f -- "$DESTINO"/*.partial

limpar() { rm -f -- "$PARCIAL"; }
trap limpar ERR

if [ -n "$DADOS_FALSOS" ]; then
  tar -czf "$PARCIAL" -C "$DADOS_FALSOS" .
  IMAGEM="teste"
else
  command -v docker >/dev/null || falha "docker não encontrado."
  # shellcheck source=achar-openbot.sh
  . "$(dirname "$0")/achar-openbot.sh"
  IMAGEM=$(docker inspect --format '{{.Config.Image}}' "$CONTAINER") || falha "container $CONTAINER não existe."
  ESTAVA=$(docker inspect --format '{{.State.Running}}' "$CONTAINER")
  voltar() { if [ "$ESTAVA" = true ]; then docker start "$CONTAINER" >/dev/null || echo "Atenção: $CONTAINER não voltou a rodar." >&2; fi; }
  trap 'limpar; voltar' ERR
  trap voltar EXIT
  if [ "$ESTAVA" = true ]; then
    echo "Parando $CONTAINER para copiar (até 60 s)..."
    docker stop -t 60 "$CONTAINER" >/dev/null
  fi
  # Usa a própria imagem do OpenBot (já baixada) só para rodar o tar, sem rede, lendo o volume.
  docker run --rm --network none --user 0:0 --entrypoint sh \
    -v "$VOLUME":/data:ro -v "$DESTINO":/backup \
    "$IMAGEM" -c "tar -czf '/backup/$NOME.partial' -C /data . && chown $(id -u):$(id -g) '/backup/$NOME.partial' && chmod 600 '/backup/$NOME.partial'"
fi

LISTA=$(tar -tzf "$PARCIAL")
for f in "${OBRIGATORIOS[@]}"; do
  grep -qxF "./$f" <<<"$LISTA" || { limpar; falha "o backup não tem $f; os dados não abririam sem ele. Os backups antigos ficaram."; }
done

chmod 600 "$PARCIAL"
( cd "$DESTINO" && sha256sum "$NOME.partial" | sed "s/\.partial\$//" >"$NOME.sha256" )
printf 'imagem=%s\ncriado=%s\n' "$IMAGEM" "$CARIMBO" >"$DESTINO/$NOME.info"
mv -- "$PARCIAL" "$FINAL"
trap - ERR

# Rotação: só depois do novo estar pronto, apaga os mais antigos além de MANTER.
mapfile -t TODOS < <(cd "$DESTINO" && ls -1 openbot-*.tar.gz 2>/dev/null | sort)
APAGAR=$(( ${#TODOS[@]} - MANTER ))
for (( i = 0; i < APAGAR; i++ )); do
  rm -f -- "$DESTINO/${TODOS[i]}" "$DESTINO/${TODOS[i]}.sha256" "$DESTINO/${TODOS[i]}.info"
done

echo "Backup pronto: $FINAL ($(du -h "$FINAL" | cut -f1)); mantidos: $(( ${#TODOS[@]} < MANTER ? ${#TODOS[@]} : MANTER ))"
