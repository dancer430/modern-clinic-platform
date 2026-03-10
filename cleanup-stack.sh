#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PURGE_DATA=0

usage() {
  printf '%s\n' "Usage: sh ./cleanup-stack.sh [--purge-data]"
  printf '%s\n' "  --purge-data   remove postgres volume data (irreversible)"
}

for arg in "$@"; do
  case "$arg" in
    --purge-data)
      PURGE_DATA=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf '%s\n' "[cleanup] unknown argument: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

compose_down() {
  base_file="$ROOT_DIR/docker-compose.yml"
  tuned_file="$ROOT_DIR/docker-compose.2c4g.yml"

  if [ ! -f "$base_file" ]; then
    printf '%s\n' "[cleanup] docker-compose.yml not found" >&2
    exit 1
  fi

  if has_cmd podman && podman compose version >/dev/null 2>&1; then
    if [ -f "$tuned_file" ]; then
      podman compose -f "$base_file" -f "$tuned_file" down --remove-orphans || true
    else
      podman compose -f "$base_file" down --remove-orphans || true
    fi
    return
  fi

  if has_cmd docker && docker compose version >/dev/null 2>&1; then
    if [ -f "$tuned_file" ]; then
      docker compose -f "$base_file" -f "$tuned_file" down --remove-orphans || true
    else
      docker compose -f "$base_file" down --remove-orphans || true
    fi
    return
  fi

  if has_cmd docker-compose; then
    if [ -f "$tuned_file" ]; then
      docker-compose -f "$base_file" -f "$tuned_file" down --remove-orphans || true
    else
      docker-compose -f "$base_file" down --remove-orphans || true
    fi
    return
  fi

  if has_cmd podman-compose; then
    if [ -f "$tuned_file" ]; then
      podman-compose -f "$base_file" -f "$tuned_file" down --remove-orphans || true
    else
      podman-compose -f "$base_file" down --remove-orphans || true
    fi
  fi
}

remove_stale_named_containers() {
  if has_cmd docker; then
    docker rm -f booking-db booking-backend booking-frontend >/dev/null 2>&1 || true
    docker ps -a --format '{{.ID}} {{.Names}}' | while IFS=' ' read -r cid name; do
      case "$name" in
        *_booking-db|*_booking-backend|*_booking-frontend)
          docker rm -f "$cid" >/dev/null 2>&1 || true
          ;;
      esac
    done
  fi

  if has_cmd podman; then
    podman rm -f booking-db booking-backend booking-frontend >/dev/null 2>&1 || true
    podman ps -a --format '{{.ID}} {{.Names}}' | while IFS=' ' read -r cid name; do
      case "$name" in
        *_booking-db|*_booking-backend|*_booking-frontend)
          podman rm -f "$cid" >/dev/null 2>&1 || true
          ;;
      esac
    done
  fi
}

remove_project_networks() {
  if has_cmd docker; then
    docker network rm modern-clinic-platform_default >/dev/null 2>&1 || true
    docker network prune -f >/dev/null 2>&1 || true
  fi

  if has_cmd podman; then
    podman network rm modern-clinic-platform_default >/dev/null 2>&1 || true
    podman network prune -f >/dev/null 2>&1 || true
  fi
}

remove_data_volumes_if_requested() {
  if [ "$PURGE_DATA" -ne 1 ]; then
    return
  fi

  printf '%s\n' "[cleanup] --purge-data enabled: removing postgres volume data"
  if has_cmd docker; then
    docker volume rm modern-clinic-platform_postgres_data postgres_data >/dev/null 2>&1 || true
    docker volume prune -f >/dev/null 2>&1 || true
  fi

  if has_cmd podman; then
    podman volume rm modern-clinic-platform_postgres_data postgres_data >/dev/null 2>&1 || true
    podman volume prune -f >/dev/null 2>&1 || true
  fi
}

printf '%s\n' "[cleanup] project root: $ROOT_DIR"
compose_down
remove_stale_named_containers
remove_project_networks
remove_data_volumes_if_requested
printf '%s\n' "[cleanup] done"
