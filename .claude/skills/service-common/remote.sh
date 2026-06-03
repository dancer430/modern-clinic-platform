#!/usr/bin/env bash
# service-common/remote.sh — shared SSH / transport helpers for the
# service-deploy, service-status, and service-update skills.
#
# SOURCE this file; do not execute it directly.
#
# Inputs (environment variables set by the calling operation script):
#   HOST          target server IP / hostname        (required)
#   SSH_USER      login user                          (default: root)
#   SSH_PORT      ssh port                            (default: 22)
#   exactly one of:
#     SSH_KEY       path to a private key
#     SSH_PASSWORD  login password
#   DRY_RUN=1     print the remote command instead of running it (optional)
#
# Public functions:
#   remote_validate           — validate inputs, fail fast
#   remote_test_conn          — prove connectivity (returns non-zero on failure)
#   remote_run "<script>"     — run a shell script on the server (stdin-safe via base64)
#   remote_capture "<script>" — like remote_run but echoes stdout to our stdout
#   remote_push <localdir> <remotedir> [extra rsync excludes...]
#
# Password auth uses `sshpass` when available, otherwise falls back to an
# `expect` wrapper (preinstalled on macOS). First connect uses
# StrictHostKeyChecking=accept-new.

SSH_USER="${SSH_USER:-root}"
SSH_PORT="${SSH_PORT:-22}"
DRY_RUN="${DRY_RUN:-0}"

_have() { command -v "$1" >/dev/null 2>&1; }

c_log()  { printf '\033[1;34m[remote]\033[0m %s\n'        "$*" >&2; }
c_warn() { printf '\033[1;33m[remote] WARN:\033[0m %s\n'  "$*" >&2; }
c_die()  { printf '\033[1;31m[remote] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# Shell-quote each argument into a single string (for `sh -c` / rsync -e).
_shq() {
  local a out=''
  for a in "$@"; do
    out="$out '${a//\'/\'\\\'\'}'"
  done
  printf '%s' "${out# }"
}

# Populated by remote_validate.
_TARGET=''
_SSH_OPTS=()

remote_validate() {
  [ -n "${HOST:-}" ] || c_die "HOST not set (target server IP is required)"

  if [ -n "${SSH_KEY:-}" ] && [ -n "${SSH_PASSWORD:-}" ]; then
    c_die "provide either SSH_KEY or SSH_PASSWORD, not both"
  fi
  if [ -z "${SSH_KEY:-}" ] && [ -z "${SSH_PASSWORD:-}" ]; then
    c_die "provide one of SSH_KEY (key path) or SSH_PASSWORD"
  fi
  if [ -n "${SSH_KEY:-}" ]; then
    [ -f "$SSH_KEY" ] || c_die "SSH_KEY not found: $SSH_KEY"
  fi
  if [ -n "${SSH_PASSWORD:-}" ] && ! _have sshpass && ! _have expect; then
    c_die "password auth requires 'sshpass' or 'expect' installed locally"
  fi

  _TARGET="${SSH_USER}@${HOST}"
  _SSH_OPTS=(
    -p "$SSH_PORT"
    -o StrictHostKeyChecking=accept-new
    -o ConnectTimeout=15
    -o ServerAliveInterval=15
  )
  if [ -n "${SSH_KEY:-}" ]; then
    _SSH_OPTS+=( -i "$SSH_KEY" -o IdentitiesOnly=yes )
  else
    _SSH_OPTS+=( -o PubkeyAuthentication=no -o PreferredAuthentications=password )
  fi
}

# Spawn an arbitrary command line (string) under `expect`, answering the
# password / passphrase / host-key prompts. Exit status mirrors the child.
_expect_spawn() {
  EXPECT_CMD="$1" EXPECT_PW="${SSH_PASSWORD:-}" expect <<'EXP'
set timeout 180
set cmd $env(EXPECT_CMD)
set pw  $env(EXPECT_PW)
spawn -noecho sh -c $cmd
expect {
  -nocase -re {are you sure you want to continue connecting} { send "yes\r"; exp_continue }
  -nocase -re {password:}  { send "$pw\r"; exp_continue }
  -nocase -re {passphrase} { send "$pw\r"; exp_continue }
  eof
}
catch wait result
exit [lindex $result 3]
EXP
}

# Run ssh with the given single remote-command string, honoring auth mode.
_ssh_exec() {
  local rcmd="$1"
  if [ -z "${SSH_PASSWORD:-}" ]; then
    ssh "${_SSH_OPTS[@]}" "$_TARGET" "$rcmd"
  elif _have sshpass; then
    sshpass -p "$SSH_PASSWORD" ssh "${_SSH_OPTS[@]}" "$_TARGET" "$rcmd"
  else
    _expect_spawn "$(_shq ssh "${_SSH_OPTS[@]}" "$_TARGET" "$rcmd")"
  fi
}

remote_test_conn() {
  c_log "testing SSH connectivity to ${_TARGET} (port ${SSH_PORT})..."
  if [ "$DRY_RUN" = "1" ]; then c_log "DRY: skip connectivity test"; return 0; fi
  _ssh_exec 'echo connection-ok' | grep -q connection-ok
}

# Encode the script as base64 so quoting never bites, regardless of auth mode.
_encode_remote() {
  local script="$1"
  local b64
  b64=$(printf '%s' "$script" | base64 | tr -d '\n')
  printf 'echo %s | base64 -d | bash' "$b64"
}

remote_run() {
  local script="$1"
  if [ "$DRY_RUN" = "1" ]; then
    c_log "DRY remote_run:"; printf '%s\n' "----" "$script" "----" >&2; return 0
  fi
  _ssh_exec "$(_encode_remote "$script")"
}

# Same as remote_run but does not suppress stdout (caller captures it).
remote_capture() { remote_run "$@"; }

# rsync a local directory to the server. Trailing slash semantics: contents
# of <localdir> land inside <remotedir>.
remote_push() {
  local src="$1" dst="$2"; shift 2
  local excludes=(
    --exclude '.git' --exclude 'node_modules' --exclude '.venv'
    --exclude '__pycache__' --exclude '*.pyc' --exclude 'db.sqlite3'
    --exclude 'backend/media' --exclude 'frontend/dist'
    --exclude '.deploy-credentials' --exclude '.pytest_cache' --exclude '.ruff_cache'
  )
  local e
  for e in "$@"; do excludes+=( --exclude "$e" ); done

  local ssh_e
  ssh_e="ssh $(_shq "${_SSH_OPTS[@]}")"

  if [ "$DRY_RUN" = "1" ]; then
    c_log "DRY remote_push: $src -> ${_TARGET}:$dst"
    return 0
  fi

  c_log "pushing $src -> ${_TARGET}:$dst ..."
  remote_run "mkdir -p '$dst'"

  if _have rsync; then
    if [ -z "${SSH_PASSWORD:-}" ] || _have sshpass; then
      local pre=()
      [ -n "${SSH_PASSWORD:-}" ] && pre=( sshpass -p "$SSH_PASSWORD" )
      "${pre[@]}" rsync -az --delete-after "${excludes[@]}" \
        -e "$ssh_e" "$src/" "${_TARGET}:$dst/"
    else
      local full
      full=$(_shq rsync -az --delete-after "${excludes[@]}" -e "$ssh_e" "$src/" "${_TARGET}:$dst/")
      _expect_spawn "$full"
    fi
  else
    c_warn "rsync not found locally; falling back to scp (no excludes, slower)"
    if [ -z "${SSH_PASSWORD:-}" ]; then
      scp "${_SSH_OPTS[@]}" -r "$src/." "${_TARGET}:$dst/"
    elif _have sshpass; then
      sshpass -p "$SSH_PASSWORD" scp "${_SSH_OPTS[@]}" -r "$src/." "${_TARGET}:$dst/"
    else
      _expect_spawn "$(_shq scp "${_SSH_OPTS[@]}" -r "$src/." "${_TARGET}:$dst/")"
    fi
  fi
}
