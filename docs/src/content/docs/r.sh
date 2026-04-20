#!/usr/bin/env bash

# Replace em dash with hyphen in all files recursively
find . -type f -print0 | while IFS= read -r -d '' file; do
  # Only process text-like files (skip binaries)
  if file "$file" | grep -q text; then
    sed -i 's/-/-/g' "$file"
  fi
done
