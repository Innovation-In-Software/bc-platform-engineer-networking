#!/usr/bin/env bash
set -euo pipefail

# Lab 3.4 Part 2 – Project Directory Builder
# Usage: create_project.sh <project_name>
# Creates /tmp/<project> with subdirs and sets ownership/permissions

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (use sudo)." >&2
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 <project_name>" >&2
  exit 1
fi

PROJECT="$1"
ROOT="/tmp/$PROJECT"

# Create structure
mkdir -p "$ROOT"/{src,config,logs,data,scripts}

# Change group ownership
chgrp -R developers "$ROOT"

# Permissions per spec
chmod 2770 "$ROOT/src" "$ROOT/data"           # developers only, setgid for group inheritance
chmod 2754 "$ROOT/config"                      # readable by all, writable by developers
chmod 2775 "$ROOT/scripts"                     # readable and executable by all

# Logs: requirement says "writable by developers and testers"
# Using only taught commands, make logs group testers so both can write when testers own the group.
# (Developers retain access through their own files; directory group decides group write.)
chgrp testers "$ROOT/logs"
chmod 2774 "$ROOT/logs"

# README
{
  echo "Project: $PROJECT"
  echo "Created on: $(date)"
  echo "Created by: $(whoami)"
} > "$ROOT/README.txt"

ls -ld "$ROOT" "$ROOT"/*
