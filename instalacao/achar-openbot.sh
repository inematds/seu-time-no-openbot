# achar-openbot.sh — usado por backup.sh e restaurar.sh (não rode sozinho).
# Descobre o container do OpenBot e o volume montado em /data.
#   1. OPENBOT_CONTAINER, se você definiu;
#   2. senão, o container do serviço "openbot" do compose.yaml da pasta OPENBOT_COMPOSE_DIR
#      (padrão: a pasta atual), ex.: openbot-openbot-1 em /opt/openbot;
#   3. senão, um container chamado "openbot" (o nome do "docker run" de docs/docker.md).
# O volume sai do próprio container (o que está montado em /data), salvo OPENBOT_VOLUME.

CONTAINER=${OPENBOT_CONTAINER:-}
if [ -z "$CONTAINER" ]; then
  _dir=${OPENBOT_COMPOSE_DIR:-$PWD}
  if [ -f "$_dir/compose.yaml" ] || [ -f "$_dir/docker-compose.yml" ]; then
    CONTAINER=$(docker compose --project-directory "$_dir" ps --all --quiet openbot 2>/dev/null | head -n 1)
  fi
  CONTAINER=${CONTAINER:-openbot}
fi
VOLUME=${OPENBOT_VOLUME:-$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$CONTAINER" 2>/dev/null || true)}
[ -n "$VOLUME" ] || falha "não achei o volume de /data no container $CONTAINER (rode na pasta do compose.yaml ou defina OPENBOT_CONTAINER / OPENBOT_VOLUME)."
echo "Container: $CONTAINER · volume: $VOLUME"
