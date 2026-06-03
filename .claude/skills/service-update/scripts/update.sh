#!/usr/bin/env bash
# service-update — roll out the latest code to an already-deployed server.
# Preserves the server .env and all data volumes (postgres_data, minio_data).
#
# Usage:
#   update.sh --host <ip> (--key <path> | --password <pw>) [options]
#
# Options mirror service-deploy: --user --port --key --password
#   --mode push|clone   code delivery (default: push)
#   --repo <url>        git URL, required for --mode clone
#   --dry-run
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$(cd "$SCRIPT_DIR/../../service-common" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
REMOTE_DIR="clinic-platform"
MODE="push"; REPO_URL=""
export DRY_RUN="${DRY_RUN:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    --host)     HOST="$2"; shift 2;;
    --user)     SSH_USER="$2"; shift 2;;
    --port)     SSH_PORT="$2"; shift 2;;
    --key)      SSH_KEY="$2"; shift 2;;
    --password) SSH_PASSWORD="$2"; shift 2;;
    --mode)     MODE="$2"; shift 2;;
    --repo)     REPO_URL="$2"; shift 2;;
    --dry-run)  DRY_RUN=1; shift;;
    -h|--help)  grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

export HOST SSH_USER SSH_PORT SSH_KEY SSH_PASSWORD DRY_RUN
# shellcheck source=../../service-common/remote.sh
. "$COMMON_DIR/remote.sh"

remote_validate
remote_test_conn || c_die "cannot reach ${SSH_USER}@${HOST}:${SSH_PORT}"

# --- require an existing deployment ---
if [ "$DRY_RUN" != "1" ]; then
  if ! remote_run "test -f ~/${REMOTE_DIR}/.env && echo HAS_ENV" | grep -q HAS_ENV; then
    c_die "no existing deployment on ${HOST} (~/${REMOTE_DIR}/.env missing). Use service-deploy for a first install."
  fi
fi

# --- deliver latest code, preserving server .env ---
if [ "$MODE" = "push" ]; then
  remote_push "$REPO_ROOT" "$REMOTE_DIR" ".env"
else
  [ -n "$REPO_URL" ] || c_die "--mode clone requires --repo <url>"
  remote_run "set -e; cd ~/${REMOTE_DIR} && git pull --ff-only"
fi

# --- rebuild + restart (init-stack runs 'up -d --build', idempotent) ---
c_log "rebuilding and restarting the stack (volumes preserved)..."
remote_run "cd ~/${REMOTE_DIR} && sh ./init-stack.sh"

# --- verify ---
verify() {
  local url="$1" want="$2" tries="${3:-40}" code
  for _ in $(seq 1 "$tries"); do
    code="$(curl -s --noproxy '*' -o /dev/null -m 5 -w '%{http_code}' "$url" || echo 000)"
    [ "$code" = "$want" ] && { echo "  OK  $url ($code)"; return 0; }
    sleep 5
  done
  echo "  FAIL $url (last: ${code:-000})"; return 1
}

if [ "$DRY_RUN" = "1" ]; then c_log "DRY run complete."; exit 0; fi

c_log "verifying endpoints..."
rc=0
verify "http://${HOST}:8000/api/schema/" 200 40 || rc=1
verify "http://${HOST}:5173/"            200 20 || rc=1
[ "$rc" = "0" ] && c_log "UPDATE OK — ${HOST}" || c_warn "update finished with failing checks; run service-status."
exit "$rc"
