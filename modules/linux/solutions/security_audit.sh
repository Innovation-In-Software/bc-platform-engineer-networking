#!/usr/bin/env bash
set -euo pipefail

# Lab 3.4 Part 3 – Security Audit Script
# Usage: security_audit.sh [directory]
# Defaults to /tmp

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (use sudo)." >&2
  exit 1
fi

dir="${1:-/tmp}"
if [ ! -d "$dir" ]; then
  echo "Directory not found: $dir" >&2
  exit 1
fi

ts="$(date +%Y%m%d_%H%M%S)"
report="security_report_${ts}.txt"

# Counts using GNU find predicates
c_777=$(find "$dir" -type f -perm 777 2>/dev/null | wc -l)
c_world_writable=$(find "$dir" -type f -perm -0002 2>/dev/null | wc -l)
c_over_10m=$(find "$dir" -type f -size +10M 2>/dev/null | wc -l)
c_mtime_day=$(find "$dir" -type f -mtime -1 2>/dev/null | wc -l)
c_setids=$(find "$dir" -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | wc -l)

{
  echo "=== Security Audit Report ==="
  echo "Target: $dir"
  echo "Generated: $(date) by $(whoami)"
  echo
  echo "Files with 777 perms: $c_777"
  find "$dir" -type f -perm 777 2>/dev/null | head -n 20
  echo
  echo "World-writable files: $c_world_writable"
  find "$dir" -type f -perm -0002 2>/dev/null | head -n 20
  echo
  echo ">10MB files: $c_over_10m"
  find "$dir" -type f -size +10M 2>/dev/null | head -n 20
  echo
  echo "Modified in last 24h: $c_mtime_day"
  find "$dir" -type f -mtime -1 2>/dev/null | head -n 20
  echo
  echo "setuid/setgid files: $c_setids"
  find "$dir" -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | head -n 20
} > "$report"

echo "Summary:"
echo "777=$c_777 world_writable=$c_world_writable >10MB=$c_over_10m mtime<1d=$c_mtime_day setid=$c_setids"
echo "Report written to: $report"
