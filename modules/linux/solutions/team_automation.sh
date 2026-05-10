#!/usr/bin/env bash
set -euo pipefail

# Lab 3.4 Part 5 – Team Automation Script
# Usage: team_automation.sh <teamname>
# Creates users {team}_dev1, {team}_dev2, {team}_tester
# Creates groups {team}_developers, {team}_testers
# Sets up project in /tmp/<team>_project
# Generates a setup report

require_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root (use sudo)." >&2
    exit 1
  fi
}

ensure_group() {
  local g="$1"
  if ! getent group "$g" >/dev/null 2>&1; then
    groupadd "$g"
  fi
}

ensure_user() {
  local u="$1"
  if ! id "$u" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$u"
    echo "Set password for $u (will prompt):"
    passwd "$u"
  fi
}

create_project() {
  local name="$1"
  local root="/tmp/${name}_project"
  mkdir -p "$root"/{src,config,logs,data,scripts}
  chgrp -R "${TEAM_DEVS}" "$root"
  chmod 2770 "$root/src" "$root/data"
  chmod 2754 "$root/config"
  chmod 2775 "$root/scripts"
  chgrp "${TEAM_TESTERS}" "$root/logs"
  chmod 2774 "$root/logs"
  {
    echo "Project: ${name}_project"
    echo "Created on: $(date)"
    echo "Created by: $(whoami)"
  } > "$root/README.txt"
  echo "$root"
}

run_audit() {
  local target="$1"
  local ts="$(date +%Y%m%d_%H%M%S)"
  local report="${target}/setup_audit_${ts}.txt"
  {
    echo "Team: $TEAM"
    echo "Project: $target"
    echo "Generated: $(date)"
    echo
    echo "Users:"; id "${TEAM}_dev1"; id "${TEAM}_dev2"; id "${TEAM}_tester"; echo
    echo "Groups:"; getent group "$TEAM_DEVS"; getent group "$TEAM_TESTERS"; echo
    echo "Directory listing:"; ls -l "$target"; echo
    echo "Security scan summary:"
    echo -n "777: "; find "$target" -type f -perm 777 | wc -l
    echo -n "world-writable: "; find "$target" -type f -perm -0002 | wc -l
    echo -n ">10M: "; find "$target" -type f -size +10M | wc -l
    echo -n "mtime<1d: "; find "$target" -type f -mtime -1 | wc -l
    echo -n "setid: "; find "$target" -type f \( -perm -4000 -o -perm -2000 \) | wc -l
  } > "$report"
  echo "$report"
}

if [ $# -lt 1 ]; then
  echo "Usage: $0 <teamname>" >&2
  exit 1
fi

require_root
TEAM="$1"
TEAM_DEVS="${TEAM}_developers"
TEAM_TESTERS="${TEAM}_testers"

ensure_group "$TEAM_DEVS"
ensure_group "$TEAM_TESTERS"

ensure_user "${TEAM}_dev1"
ensure_user "${TEAM}_dev2"
ensure_user "${TEAM}_tester"

# Assign group memberships
usermod -aG "$TEAM_DEVS" "${TEAM}_dev1"
usermod -aG "$TEAM_DEVS" "${TEAM}_dev2"
usermod -aG "$TEAM_TESTERS" "${TEAM}_tester"

PROJECT_ROOT=$(create_project "$TEAM")
REPORT_PATH=$(run_audit "$PROJECT_ROOT")

echo "Setup complete. Project: $PROJECT_ROOT"
echo "Report: $REPORT_PATH"
