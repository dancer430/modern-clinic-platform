#!/usr/bin/env bash
# service-deploy — provision the Medical Booking Platform on a fresh server.
#
# Usage:
#   deploy.sh --host <ip> (--key <path> | --password <pw>) [options]
#
# Options:
#   --host <ip>          target server (required)
#   --user <name>        SSH user (default: root)
#   --port <n>           SSH port (default: 22)
#   --key <path>         private key for auth
#   --password <pw>      password for auth (use --key in CI)
#   --mode push|clone    code delivery (default: push)
#   --repo <url>         git URL, required for --mode clone
#   --force              overwrite an existing deployment (DANGEROUS)
#   --dry-run            print what would run, connect to nothing
#
# Exactly one of --key / --password is required.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$(cd "$SCRIPT_DIR/../../service-common" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
REMOTE_DIR="clinic-platform"

MODE="push"; REPO_URL=""; FORCE=0
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
    --force)    FORCE=1; shift;;
    --dry-run)  DRY_RUN=1; shift;;
    -h|--help)  grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

export HOST SSH_USER SSH_PORT SSH_KEY SSH_PASSWORD DRY_RUN
# shellcheck source=../../service-common/remote.sh
. "$COMMON_DIR/remote.sh"
# shellcheck source=../../service-common/envgen.sh
. "$COMMON_DIR/envgen.sh"

[ "$MODE" = "push" ] || [ "$MODE" = "clone" ] || c_die "--mode must be push or clone"
[ "$MODE" = "clone" ] && [ -z "$REPO_URL" ] && c_die "--mode clone requires --repo <url>"

remote_validate
remote_test_conn || c_die "cannot reach ${SSH_USER}@${HOST}:${SSH_PORT} — check IP / creds / firewall"
c_log "SSH OK."

# --- sudo sanity (root needs nothing; others need passwordless sudo) ---
if [ "$DRY_RUN" != "1" ] && [ "${SSH_USER}" != "root" ]; then
  if ! remote_run 'sudo -n true 2>/dev/null && echo SUDO_OK' | grep -q SUDO_OK; then
    c_warn "passwordless sudo not confirmed for ${SSH_USER}; init-stack.sh may stall on a sudo prompt. Prefer --user root."
  fi
fi

# --- re-run guard: never clobber an existing deployment without --force ---
if [ "$DRY_RUN" != "1" ]; then
  guard="$(remote_run "test -f ~/${REMOTE_DIR}/.env && echo HAS_ENV; (docker ps --format '{{.Names}}' 2>/dev/null; podman ps --format '{{.Names}}' 2>/dev/null) | grep -q '^booking-' && echo HAS_RUNNING; true")"
  if printf '%s' "$guard" | grep -qE 'HAS_ENV|HAS_RUNNING'; then
    if [ "$FORCE" != "1" ]; then
      c_die "existing deployment detected on ${HOST} (.env or running booking-* containers). Use service-update to update it, or pass --force to overwrite (this regenerates secrets; data volumes are preserved by compose)."
    fi
    c_warn "--force set: proceeding over existing deployment. Data volumes are preserved; secrets in .env will be regenerated."
  fi
fi

# --- deliver code ---
if [ "$MODE" = "push" ]; then
  remote_push "$REPO_ROOT" "$REMOTE_DIR" ".env"
else
  c_log "cloning $REPO_URL on server..."
  remote_run "set -e; if [ -d ~/${REMOTE_DIR}/.git ]; then cd ~/${REMOTE_DIR} && git pull --ff-only; else git clone '$REPO_URL' ~/${REMOTE_DIR}; fi"
fi

# --- generate .env locally, save creds, push to server ---
CRED_DIR="$REPO_ROOT/.deploy-credentials"
CRED_FILE="$CRED_DIR/${HOST}.env"
TMP_ENV="$(mktemp 2>/dev/null || echo /tmp/clinic-env.$$)"
mkdir -p "$CRED_DIR"

if [ "$DRY_RUN" = "1" ]; then
  c_log "DRY: would generate .env + credentials at $CRED_FILE and push to ~/${REMOTE_DIR}/.env"
else
  generate_env "$HOST" "$TMP_ENV" "$CRED_FILE"
  b64="$(base64 < "$TMP_ENV" | tr -d '\n')"
  remote_run "echo $b64 | base64 -d > ~/${REMOTE_DIR}/.env && chmod 600 ~/${REMOTE_DIR}/.env"
  rm -f "$TMP_ENV"
  c_log "credentials saved locally to $CRED_FILE"
fi

# --- bring up the stack ---
c_log "running init-stack.sh on the server (installs runtime + builds images; this can take several minutes)..."
remote_run "cd ~/${REMOTE_DIR} && sh ./init-stack.sh"

# --- verify ---
verify() {
  local url="$1" want="$2" tries="${3:-60}" code
  for _ in $(seq 1 "$tries"); do
    code="$(curl -s --noproxy '*' -o /dev/null -m 5 -w '%{http_code}' "$url" || echo 000)"
    [ "$code" = "$want" ] && { echo "  OK  $url ($code)"; return 0; }
    sleep 5
  done
  echo "  FAIL $url (last: ${code:-000})"; return 1
}

if [ "$DRY_RUN" = "1" ]; then
  c_log "DRY run complete — no server was contacted for mutations."
  exit 0
fi

c_log "verifying endpoints (allowing time for first build)..."
rc=0
verify "http://${HOST}:8000/api/schema/" 200 60 || rc=1
verify "http://${HOST}:5173/"            200 30 || rc=1

echo
if [ "$rc" = "0" ]; then
  c_log "DEPLOY OK — ${HOST}"
else
  c_warn "deploy finished but some health checks failed; run service-status for detail."
fi
cat <<EOF

  Frontend:      http://${HOST}:5173
  Backend API:   http://${HOST}:8000/api/
  Swagger:       http://${HOST}:8000/api/docs/swagger/
  MinIO console: http://${HOST}:9001

  Admin login:   admin / ${GENERATED_ADMIN_PASSWORD:-<see creds file>}
  Credentials:   ${CRED_FILE}   (gitignored — keep private)
EOF
exit "$rc"
