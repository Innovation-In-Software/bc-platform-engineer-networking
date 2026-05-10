#!/usr/bin/env bash
set -euo pipefail

# Lab 3.4 Part 4 – File Organization Script
# Usage: organize_files.sh <directory>

if [ $# -lt 1 ]; then
  echo "Usage: $0 <directory>" >&2
  exit 1
fi

dir="$1"
if [ ! -d "$dir" ]; then
  echo "Directory not found: $dir" >&2
  exit 1
fi

# Create subdirectories
for d in logs configs scripts data others; do
  mkdir -p "$dir/$d"
done

# Move by extension (case-insensitive variants could be added similarly)
find "$dir" -maxdepth 1 -type f -name "*.log" -exec mv {} "$dir/logs/" \;
find "$dir" -maxdepth 1 -type f \( -name "*.conf" -o -name "*.ini" \) -exec mv {} "$dir/configs/" \;
find "$dir" -maxdepth 1 -type f \( -name "*.sh" -o -name "*.py" \) -exec mv {} "$dir/scripts/" \;
find "$dir" -maxdepth 1 -type f \( -name "*.txt" -o -name "*.csv" -o -name "*.json" \) -exec mv {} "$dir/data/" \;
# Everything else
find "$dir" -maxdepth 1 -type f -exec mv {} "$dir/others/" \;

# Permissions
find "$dir/scripts" -type f -exec chmod 755 {} \;
find "$dir/logs" "$dir/configs" "$dir/data" "$dir/others" -type f -exec chmod 644 {} \;

# Counts
for d in logs configs scripts data others; do
  c=$(find "$dir/$d" -type f | wc -l)
  printf "%s: %s files\n" "$d" "$c"
done
