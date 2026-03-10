#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FORCED_RUNTIME=""

parse_args() {
  for arg in "$@"; do
    case "$arg" in
      --runtime=podman)
        FORCED_RUNTIME="podman"
        ;;
      --runtime=docker)
        FORCED_RUNTIME="docker"
        ;;
      --runtime=*)
        printf '%s\n' "[init] unsupported runtime: ${arg#--runtime=}" >&2
        exit 1
        ;;
      -h|--help)
        printf '%s\n' "Usage: sh ./init-stack.sh [--runtime=podman|docker]"
        exit 0
        ;;
      *)
        printf '%s\n' "[init] unknown argument: $arg" >&2
        exit 1
        ;;
    esac
  done
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

is_legacy_docker_compose_v1() {
  if ! has_cmd docker-compose; then
    return 1
  fi

  VERSION_TEXT=$(docker-compose version --short 2>/dev/null || true)
  if [ -z "$VERSION_TEXT" ]; then
    VERSION_TEXT=$(docker-compose version 2>/dev/null || true)
  fi

  case "$VERSION_TEXT" in
    1.*|*" version 1."*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
    return
  fi
  if has_cmd sudo; then
    sudo "$@"
    return
  fi
  printf '%s\n' "[init] need root permission to install packages: $*" >&2
  exit 1
}

detect_os() {
  uname -s | tr '[:upper:]' '[:lower:]'
}

install_docker_official_repo_debian() {
  if [ ! -f /etc/os-release ]; then
    return 1
  fi

  . /etc/os-release
  CODENAME=${VERSION_CODENAME:-}
  if [ -z "$CODENAME" ]; then
    return 1
  fi

  run_as_root apt-get update
  run_as_root apt-get install -y ca-certificates curl gnupg
  run_as_root install -m 0755 -d /etc/apt/keyrings

  if [ "$ID" = "ubuntu" ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | run_as_root gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    run_as_root chmod a+r /etc/apt/keyrings/docker.gpg
    printf '%s\n' "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $CODENAME stable" | run_as_root tee /etc/apt/sources.list.d/docker.list >/dev/null
  else
    curl -fsSL https://download.docker.com/linux/debian/gpg | run_as_root gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    run_as_root chmod a+r /etc/apt/keyrings/docker.gpg
    printf '%s\n' "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $CODENAME stable" | run_as_root tee /etc/apt/sources.list.d/docker.list >/dev/null
  fi

  run_as_root apt-get update
  run_as_root apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

install_podman_linux() {
  if [ ! -f /etc/os-release ]; then
    printf '%s\n' "[init] /etc/os-release not found, cannot auto-install podman" >&2
    return 1
  fi

  . /etc/os-release
  DIST_ID=${ID:-}
  DIST_LIKE=${ID_LIKE:-}

  case "$DIST_ID" in
    ubuntu|debian)
      run_as_root apt-get update
      run_as_root apt-get install -y podman
      ;;
    fedora)
      run_as_root dnf install -y podman
      ;;
    centos|rhel|rocky|almalinux|ol)
      if has_cmd dnf; then
        run_as_root dnf install -y podman
      else
        run_as_root yum install -y podman
      fi
      ;;
    arch|manjaro)
      run_as_root pacman -Sy --noconfirm podman
      ;;
    *)
      if printf '%s' "$DIST_LIKE" | grep -Eq 'debian|ubuntu'; then
        run_as_root apt-get update
        run_as_root apt-get install -y podman
      elif printf '%s' "$DIST_LIKE" | grep -Eq 'rhel|fedora|centos'; then
        if has_cmd dnf; then
          run_as_root dnf install -y podman
        else
          run_as_root yum install -y podman
        fi
      else
        printf '%s\n' "[init] unsupported linux distro for auto podman install: ${DIST_ID:-unknown}" >&2
        return 1
      fi
      ;;
  esac
}

install_podman_macos() {
  if ! has_cmd brew; then
    printf '%s\n' "[init] homebrew not found, cannot auto-install podman on macOS" >&2
    return 1
  fi
  brew install podman
  if brew install podman-compose; then
    return 0
  fi
  brew install docker-compose
}

install_podman_compose_provider_linux() {
  if [ ! -f /etc/os-release ]; then
    return 1
  fi

  . /etc/os-release
  DIST_ID=${ID:-}
  DIST_LIKE=${ID_LIKE:-}

  case "$DIST_ID" in
    ubuntu|debian)
      run_as_root apt-get update
      if run_as_root apt-get install -y podman-compose; then
        return 0
      fi
      if run_as_root apt-get install -y docker-compose-plugin; then
        return 0
      fi
      if run_as_root apt-get install -y docker-compose; then
        return 0
      fi
      if run_as_root apt-get install -y python3-pip && run_as_root python3 -m pip install --break-system-packages podman-compose; then
        return 0
      fi
      if run_as_root apt-get install -y python3-pip && run_as_root python3 -m pip install podman-compose; then
        return 0
      fi
      ;;
    fedora)
      if run_as_root dnf install -y podman-compose; then
        return 0
      fi
      if run_as_root dnf install -y docker-compose-plugin; then
        return 0
      fi
      if run_as_root dnf install -y docker-compose; then
        return 0
      fi
      ;;
    centos|rhel|rocky|almalinux|ol)
      if has_cmd dnf; then
        if run_as_root dnf install -y podman-compose; then
          return 0
        fi
        if run_as_root dnf install -y docker-compose-plugin; then
          return 0
        fi
      else
        if run_as_root yum install -y podman-compose; then
          return 0
        fi
        if run_as_root yum install -y docker-compose; then
          return 0
        fi
      fi
      ;;
    arch|manjaro)
      if run_as_root pacman -Sy --noconfirm podman-compose; then
        return 0
      fi
      if run_as_root pacman -Sy --noconfirm docker-compose; then
        return 0
      fi
      ;;
    *)
      if printf '%s' "$DIST_LIKE" | grep -Eq 'debian|ubuntu'; then
        run_as_root apt-get update
        if run_as_root apt-get install -y podman-compose; then
          return 0
        fi
        if run_as_root apt-get install -y docker-compose-plugin; then
          return 0
        fi
        if run_as_root apt-get install -y docker-compose; then
          return 0
        fi
      elif printf '%s' "$DIST_LIKE" | grep -Eq 'rhel|fedora|centos'; then
        if has_cmd dnf; then
          if run_as_root dnf install -y podman-compose; then
            return 0
          fi
          if run_as_root dnf install -y docker-compose-plugin; then
            return 0
          fi
        else
          if run_as_root yum install -y podman-compose; then
            return 0
          fi
          if run_as_root yum install -y docker-compose; then
            return 0
          fi
        fi
      fi
      ;;
  esac

  return 1
}

ensure_podman_compose_available() {
  if podman compose version >/dev/null 2>&1; then
    return 0
  fi

  OS_NAME=$(detect_os)
  if [ "$OS_NAME" = "linux" ]; then
    printf '%s\n' "[init] podman compose provider missing, installing provider..."
    if install_podman_compose_provider_linux && podman compose version >/dev/null 2>&1; then
      return 0
    fi
    return 1
  fi

  if [ "$OS_NAME" = "darwin" ]; then
    if has_cmd brew; then
      if brew install podman-compose || brew install docker-compose; then
        podman compose version >/dev/null 2>&1
        return
      fi
    fi
    return 1
  fi

  return 1
}

install_docker_linux() {
  if [ ! -f /etc/os-release ]; then
    printf '%s\n' "[init] /etc/os-release not found, cannot auto-install docker" >&2
    return 1
  fi

  . /etc/os-release
  DIST_ID=${ID:-}
  DIST_LIKE=${ID_LIKE:-}

  case "$DIST_ID" in
    ubuntu|debian)
      run_as_root apt-get update
      if run_as_root apt-get install -y docker.io docker-compose-v2; then
        return 0
      fi
      if run_as_root apt-get install -y docker.io docker-compose-plugin; then
        return 0
      fi
      if run_as_root apt-get install -y docker.io; then
        if docker compose version >/dev/null 2>&1; then
          return 0
        fi
      fi
      install_docker_official_repo_debian
      ;;
    fedora)
      run_as_root dnf install -y docker docker-compose
      ;;
    centos|rhel|rocky|almalinux|ol)
      if has_cmd dnf; then
        run_as_root dnf install -y docker docker-compose-plugin || run_as_root dnf install -y moby-engine docker-compose-plugin
      else
        run_as_root yum install -y docker docker-compose
      fi
      ;;
    arch|manjaro)
      run_as_root pacman -Sy --noconfirm docker docker-compose
      ;;
    *)
      if printf '%s' "$DIST_LIKE" | grep -Eq 'debian|ubuntu'; then
        run_as_root apt-get update
        if run_as_root apt-get install -y docker.io docker-compose-v2; then
          return 0
        fi
        if run_as_root apt-get install -y docker.io docker-compose-plugin; then
          return 0
        fi
        if run_as_root apt-get install -y docker.io; then
          if docker compose version >/dev/null 2>&1; then
            return 0
          fi
        fi
        install_docker_official_repo_debian
      elif printf '%s' "$DIST_LIKE" | grep -Eq 'rhel|fedora|centos'; then
        if has_cmd dnf; then
          run_as_root dnf install -y docker docker-compose-plugin || run_as_root dnf install -y moby-engine docker-compose-plugin
        else
          run_as_root yum install -y docker docker-compose
        fi
      else
        printf '%s\n' "[init] unsupported linux distro for auto docker install: ${DIST_ID:-unknown}" >&2
        return 1
      fi
      ;;
  esac
}

install_runtime() {
  OS_NAME=$(detect_os)

  if [ "$OS_NAME" = "linux" ]; then
    printf '%s\n' "[init] podman not found, trying to install podman..."
    if install_podman_linux; then
      return 0
    fi
    printf '%s\n' "[init] podman install failed, trying docker..."
    install_docker_linux
    return
  fi

  if [ "$OS_NAME" = "darwin" ]; then
    printf '%s\n' "[init] podman not found, trying to install podman via brew..."
    if install_podman_macos; then
      return 0
    fi
    printf '%s\n' "[init] podman install failed; please install docker desktop manually" >&2
    return 1
  fi

  printf '%s\n' "[init] unsupported OS: $OS_NAME" >&2
  return 1
}

install_runtime_by_force() {
  if [ "$FORCED_RUNTIME" = "podman" ]; then
    OS_NAME=$(detect_os)
    if [ "$OS_NAME" = "linux" ]; then
      install_podman_linux
      return
    fi
    if [ "$OS_NAME" = "darwin" ]; then
      install_podman_macos
      return
    fi
    printf '%s\n' "[init] unsupported OS for forced podman install: $OS_NAME" >&2
    exit 1
  fi

  if [ "$FORCED_RUNTIME" = "docker" ]; then
    OS_NAME=$(detect_os)
    if [ "$OS_NAME" = "linux" ]; then
      install_docker_linux
      return
    fi
    printf '%s\n' "[init] forced docker install is supported on linux only in this script" >&2
    exit 1
  fi
}

ensure_env_file() {
  if [ -f "$ROOT_DIR/.env" ]; then
    return
  fi

  if [ -f "$ROOT_DIR/.env.example" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    printf '%s\n' "[init] .env created from .env.example"
    return
  fi

  printf '%s\n' "[init] .env missing and .env.example not found" >&2
  exit 1
}

load_env_vars() {
  if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    . "$ROOT_DIR/.env"
    set +a
  fi
}

detect_access_host() {
  ACCESS_HOST="localhost"
  if has_cmd hostname; then
    HOST_IPS=$(hostname -I 2>/dev/null || true)
    if [ -n "$HOST_IPS" ]; then
      for ip in $HOST_IPS; do
        case "$ip" in
          127.*|169.254.*)
            ;;
          *)
            ACCESS_HOST="$ip"
            return
            ;;
        esac
      done
    fi
  fi
}

ensure_docker_ready() {
  OS_NAME=$(detect_os)
  if [ "$OS_NAME" != "linux" ]; then
    return
  fi

  if docker info >/dev/null 2>&1; then
    return
  fi

  if has_cmd systemctl; then
    run_as_root systemctl enable --now docker
  fi

  if ! docker info >/dev/null 2>&1; then
    printf '%s\n' "[init] docker daemon not ready" >&2
    exit 1
  fi
}

ensure_podman_ready() {
  OS_NAME=$(detect_os)
  if [ "$OS_NAME" != "darwin" ]; then
    return
  fi

  if ! has_cmd podman; then
    return
  fi

  if ! podman machine inspect >/dev/null 2>&1; then
    podman machine init
  fi

  podman machine start >/dev/null 2>&1 || true
}

RUNTIME_KIND=""
COMPOSE_KIND=""

select_runtime_and_compose() {
  if [ "$FORCED_RUNTIME" = "podman" ]; then
    if ! has_cmd podman; then
      printf '%s\n' "[init] forced runtime podman; installing podman..."
      install_runtime_by_force
    fi
    ensure_podman_ready
    if ensure_podman_compose_available; then
      RUNTIME_KIND="podman"
      COMPOSE_KIND="podman_compose"
      return
    fi
    if has_cmd podman-compose; then
      RUNTIME_KIND="podman"
      COMPOSE_KIND="podman-compose"
      return
    fi
    printf '%s\n' "[init] forced runtime podman, but no compose command found" >&2
    exit 1
  fi

  if [ "$FORCED_RUNTIME" = "docker" ]; then
    if ! has_cmd docker && ! has_cmd docker-compose; then
      printf '%s\n' "[init] forced runtime docker; installing docker..."
      install_runtime_by_force
    fi
    if has_cmd docker; then
      ensure_docker_ready
      if docker compose version >/dev/null 2>&1; then
        RUNTIME_KIND="docker"
        COMPOSE_KIND="docker_compose"
        return
      fi
    fi
    if has_cmd docker-compose && is_legacy_docker_compose_v1; then
      printf '%s\n' "[init] detected legacy docker-compose v1, trying to install docker compose v2 plugin..."
      install_docker_linux
      if has_cmd docker; then
        ensure_docker_ready
        if docker compose version >/dev/null 2>&1; then
          RUNTIME_KIND="docker"
          COMPOSE_KIND="docker_compose"
          return
        fi
      fi
    fi
    if has_cmd docker-compose && ! is_legacy_docker_compose_v1; then
      RUNTIME_KIND="docker"
      COMPOSE_KIND="docker-compose"
      return
    fi
    if has_cmd docker-compose && is_legacy_docker_compose_v1; then
      printf '%s\n' "[init] detected legacy docker-compose v1, please install docker compose v2 plugin" >&2
      exit 1
    fi
    printf '%s\n' "[init] forced runtime docker, but no compose command found" >&2
    exit 1
  fi

  if has_cmd podman; then
    ensure_podman_ready
    if ensure_podman_compose_available; then
      RUNTIME_KIND="podman"
      COMPOSE_KIND="podman_compose"
      return
    fi
    if has_cmd podman-compose; then
      RUNTIME_KIND="podman"
      COMPOSE_KIND="podman-compose"
      return
    fi
  fi

  if has_cmd docker; then
    ensure_docker_ready
    if docker compose version >/dev/null 2>&1; then
      RUNTIME_KIND="docker"
      COMPOSE_KIND="docker_compose"
      return
    fi
  fi

  if has_cmd docker-compose && ! is_legacy_docker_compose_v1; then
    RUNTIME_KIND="docker"
    COMPOSE_KIND="docker-compose"
    return
  fi
  if has_cmd docker-compose && is_legacy_docker_compose_v1; then
    printf '%s\n' "[init] detected legacy docker-compose v1, skipping it and expecting docker compose v2" >&2
  fi

  if [ -n "${RUNTIME_KIND}" ]; then
    return
  fi

  install_runtime

  if has_cmd podman; then
    ensure_podman_ready
    if ensure_podman_compose_available; then
      RUNTIME_KIND="podman"
      COMPOSE_KIND="podman_compose"
      return
    fi
    if has_cmd podman-compose; then
      RUNTIME_KIND="podman"
      COMPOSE_KIND="podman-compose"
      return
    fi
  fi

  if has_cmd docker; then
    ensure_docker_ready
    if docker compose version >/dev/null 2>&1; then
      RUNTIME_KIND="docker"
      COMPOSE_KIND="docker_compose"
      return
    fi
  fi

  if has_cmd docker-compose && ! is_legacy_docker_compose_v1; then
    RUNTIME_KIND="docker"
    COMPOSE_KIND="docker-compose"
    return
  fi
  if has_cmd docker-compose && is_legacy_docker_compose_v1; then
    printf '%s\n' "[init] detected legacy docker-compose v1, please install docker compose v2 plugin" >&2
  fi

  printf '%s\n' "[init] no usable compose command found after installation" >&2
  exit 1
}

run_compose_up() {
  BASE_FILE="$ROOT_DIR/docker-compose.yml"
  TUNED_FILE="$ROOT_DIR/docker-compose.2c4g.yml"

  if [ ! -f "$BASE_FILE" ]; then
    printf '%s\n' "[init] docker-compose.yml not found in project root" >&2
    exit 1
  fi

  case "$COMPOSE_KIND" in
    podman_compose)
      if [ -f "$TUNED_FILE" ]; then
        podman compose -f "$BASE_FILE" -f "$TUNED_FILE" up -d --build
      else
        podman compose -f "$BASE_FILE" up -d --build
      fi
      ;;
    podman-compose)
      if [ -f "$TUNED_FILE" ]; then
        podman-compose -f "$BASE_FILE" -f "$TUNED_FILE" up -d --build
      else
        podman-compose -f "$BASE_FILE" up -d --build
      fi
      ;;
    docker_compose)
      if [ -f "$TUNED_FILE" ]; then
        docker compose -f "$BASE_FILE" -f "$TUNED_FILE" up -d --build
      else
        docker compose -f "$BASE_FILE" up -d --build
      fi
      ;;
    docker-compose)
      if [ -f "$TUNED_FILE" ]; then
        docker-compose -f "$BASE_FILE" -f "$TUNED_FILE" up -d --build
      else
        docker-compose -f "$BASE_FILE" up -d --build
      fi
      ;;
    *)
      printf '%s\n' "[init] unsupported compose kind: $COMPOSE_KIND" >&2
      exit 1
      ;;
  esac
}

show_compose_status() {
  BASE_FILE="$ROOT_DIR/docker-compose.yml"
  TUNED_FILE="$ROOT_DIR/docker-compose.2c4g.yml"

  case "$COMPOSE_KIND" in
    podman_compose)
      if [ -f "$TUNED_FILE" ]; then
        podman compose -f "$BASE_FILE" -f "$TUNED_FILE" ps || true
      else
        podman compose -f "$BASE_FILE" ps || true
      fi
      ;;
    podman-compose)
      if [ -f "$TUNED_FILE" ]; then
        podman-compose -f "$BASE_FILE" -f "$TUNED_FILE" ps || true
      else
        podman-compose -f "$BASE_FILE" ps || true
      fi
      ;;
    docker_compose)
      if [ -f "$TUNED_FILE" ]; then
        docker compose -f "$BASE_FILE" -f "$TUNED_FILE" ps || true
      else
        docker compose -f "$BASE_FILE" ps || true
      fi
      ;;
    docker-compose)
      if [ -f "$TUNED_FILE" ]; then
        docker-compose -f "$BASE_FILE" -f "$TUNED_FILE" ps || true
      else
        docker-compose -f "$BASE_FILE" ps || true
      fi
      ;;
  esac
}

print_post_init_summary() {
  detect_access_host
  BACKEND_PORT="${BACKEND_PORT:-8000}"
  FRONTEND_PORT="${FRONTEND_PORT:-5173}"
  POSTGRES_HOST_VALUE="${POSTGRES_HOST:-db}"
  POSTGRES_PORT_VALUE="${POSTGRES_PORT:-5432}"
  ADMIN_USER_VALUE="${DJANGO_SUPERUSER_USERNAME:-admin}"
  ADMIN_EMAIL_VALUE="${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
  ADMIN_PASSWORD_VALUE="${DJANGO_SUPERUSER_PASSWORD:-<set-in-.env>}"

  printf '%s\n' "[init] stack status:"
  show_compose_status

  printf '%s\n' "[init] access information:"
  printf '%s\n' "  - Frontend: http://$ACCESS_HOST:$FRONTEND_PORT"
  printf '%s\n' "  - Backend API: http://$ACCESS_HOST:$BACKEND_PORT"
  printf '%s\n' "  - Database (internal): $POSTGRES_HOST_VALUE:$POSTGRES_PORT_VALUE"
  printf '%s\n' "[init] default admin credentials:"
  printf '%s\n' "  - Username: $ADMIN_USER_VALUE"
  printf '%s\n' "  - Email: $ADMIN_EMAIL_VALUE"
  printf '%s\n' "  - Password: $ADMIN_PASSWORD_VALUE"
}

printf '%s\n' "[init] project root: $ROOT_DIR"
parse_args "$@"
ensure_env_file
load_env_vars
select_runtime_and_compose
printf '%s\n' "[init] runtime: $RUNTIME_KIND, compose: $COMPOSE_KIND"
run_compose_up
print_post_init_summary
printf '%s\n' "[init] done"
