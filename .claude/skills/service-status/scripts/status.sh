#!/usr/bin/env bash
# service-status — read-only health check of a deployed platform.
#
# Usage:
#   status.sh --host <ip> (--key <path> | --password <pw>) [--user root] [--port 22]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMON_DIR="$(cd "$SCRIPT_DIR/../../service-common" && pwd)"
REMOTE_DIR="clinic-platform"
export DRY_RUN="${DRY_RUN:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    --host)     HOST="$2"; shift 2;;
    --user)     SSH_USER="$2"; shift 2;;
    --port)     SSH_PORT="$2"; shift 2;;
    --key)      SSH_KEY="$2"; shift 2;;
    --password) SSH_PASSWORD="$2"; shift 2;;
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

echo "=== containers on ${HOST} ==="
remote_run "
set -e
cd ~/${REMOTE_DIR} 2>/dev/null || { echo '(no ~/${REMOTE_DIR} — not deployed?)'; exit 0; }
if command -v docker >/dev/null 2>&1 && docker ps >/dev/null 2>&1; then RT=docker;
elif command -v podman >/dev/null 2>&1; then RT=podman; else echo '(no container runtime found)'; exit 0; fi
\$RT ps --filter 'name=booking-' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || true
echo
echo '--- health states ---'
for c in booking-db booking-minio booking-backend booking-frontend; do
  st=\$(\$RT inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \"\$c\" 2>/dev/null || echo 'absent')
  printf '  %-20s %s\n' \"\$c\" \"\$st\"
done
"

echo
echo "=== endpoint reachability (from this machine) ==="
for pair in "frontend|http://${HOST}:5173/" "backend|http://${HOST}:8000/api/schema/" "swagger|http://${HOST}:8000/api/docs/swagger/" "minio|http://${HOST}:9000/minio/health/live"; do
  name="${pair%%|*}"; url="${pair##*|}"
  code="$(curl -s --noproxy '*' -o /dev/null -m 5 -w '%{http_code}' "$url" || echo 000)"
  printf '  %-9s %-3s  %s\n' "$name" "$code" "$url"
done
