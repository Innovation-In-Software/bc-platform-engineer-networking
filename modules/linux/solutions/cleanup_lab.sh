#!/usr/bin/env bash
set -euo pipefail

# Lab 3.4 Part 6 – Cleanup Script
# Prompts before deleting users, groups, and lab directories

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (use sudo)." >&2
  exit 1
fi

# Targets
USERS=(alice bob charlie)
GROUPS=(developers testers auditors)
PROJECTS=(/tmp/webapp)

# Also allow team-based patterns passed as arguments (e.g., platform)
if [ $# -gt 0 ]; then
  TEAM="$1"
  USERS+=("${TEAM}_dev1" "${TEAM}_dev2" "${TEAM}_tester")
  GROUPS+=("${TEAM}_developers" "${TEAM}_testers")
  PROJECTS+=("/tmp/${TEAM}_project")
fi

echo "Users to remove: ${USERS[*]}"
echo "Groups to remove: ${GROUPS[*]}"
echo "Project directories to remove: ${PROJECTS[*]}"

read -r -p "Proceed with deletion? (yes/no): " ans
if [ "$ans" != "yes" ]; then
  echo "Aborted."; exit 0
fi

for u in "${USERS[@]}"; do
  if id "$u" >/dev/null 2>&1; then
    userdel -r "$u" || true
  fi
done

for g in "${GROUPS[@]}"; do
  if getent group "$g" >/dev/null 2>&1; then
    groupdel "$g" || true
  fi
done

for p in "${PROJECTS[@]}"; do
  if [ -d "$p" ]; then
    rm -rf "$p" || true
  fi
done

# Remove reports in CWD
find . -maxdepth 1 -type f -name 'security_report_*.txt' -exec rm -f {} \; || true
find /tmp -maxdepth 2 -type f -name 'setup_audit_*.txt' -exec rm -f {} \; || true

echo "Cleanup completed."
