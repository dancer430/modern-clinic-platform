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
      run_as_root apt-get install -y podman podman-compose
      ;;
    fedora)
      run_as_root dnf install -y podman podman-compose
      ;;
    centos|rhel|rocky|almalinux|ol)
      if has_cmd dnf; then
        run_as_root dnf install -y podman podman-compose
      else
        run_as_root yum install -y podman podman-compose
      fi
      ;;
    arch|manjaro)
      run_as_root pacman -Sy --noconfirm podman podman-compose
      ;;
    *)
      if printf '%s' "$DIST_LIKE" | grep -Eq 'debian|ubuntu'; then
        run_as_root apt-get update
        run_as_root apt-get install -y podman podman-compose
      elif printf '%s' "$DIST_LIKE" | grep -Eq 'rhel|fedora|centos'; then
        if has_cmd dnf; then
          run_as_root dnf install -y podman podman-compose
        else
          run_as_root yum install -y podman podman-compose
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
  brew install podman podman-compose
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
      run_as_root apt-get install -y docker.io docker-compose-v2 || run_as_root apt-get install -y docker.io docker-compose-plugin
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
        run_as_root apt-get install -y docker.io docker-compose-v2 || run_as_root apt-get install -y docker.io docker-compose-plugin
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
    if podman compose version >/dev/null 2>&1; then
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
    if has_cmd docker-compose; then
      RUNTIME_KIND="docker"
      COMPOSE_KIND="docker-compose"
      return
    fi
    printf '%s\n' "[init] forced runtime docker, but no compose command found" >&2
    exit 1
  fi

  if has_cmd podman; then
    ensure_podman_ready
    if podman compose version >/dev/null 2>&1; then
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

  if has_cmd docker-compose; then
    RUNTIME_KIND="docker"
    COMPOSE_KIND="docker-compose"
    return
  fi

  if [ -n "${RUNTIME_KIND}" ]; then
    return
  fi

  install_runtime

  if has_cmd podman; then
    ensure_podman_ready
    if podman compose version >/dev/null 2>&1; then
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

  if has_cmd docker-compose; then
    RUNTIME_KIND="docker"
    COMPOSE_KIND="docker-compose"
    return
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

printf '%s\n' "[init] project root: $ROOT_DIR"
parse_args "$@"
ensure_env_file
select_runtime_and_compose
printf '%s\n' "[init] runtime: $RUNTIME_KIND, compose: $COMPOSE_KIND"
run_compose_up
printf '%s\n' "[init] done"
