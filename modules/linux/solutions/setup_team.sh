#!/usr/bin/env bash
set -euo pipefail

# Lab 3.4 Part 1 – Team Environment Setup Script (uses only commands from labs)
# Creates users: alice, bob, charlie
# Creates groups: developers, testers, auditors
# Adds users to specified groups
# Prompts to set passwords interactively with passwd (as taught in labs)

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (use sudo)." >&2
  exit 1
fi

# Create groups if missing
for g in developers testers auditors; do
  if ! getent group "$g" >/dev/null 2>&1; then
    groupadd "$g"
  fi
done

# Create users if missing, default shell /bin/bash
for u in alice bob charlie; do
  if ! id "$u" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$u"
  fi
  echo "Set password for $u (will prompt):"
  passwd "$u"
  echo
done

# Group assignments
usermod -aG developers,auditors alice
usermod -aG developers,testers bob
usermod -aG testers,auditors charlie

# Summary
for u in alice bob charlie; do
  echo "----- $u -----"
  id "$u"
  groups "$u"
  echo
done
