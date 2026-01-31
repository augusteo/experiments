#!/bin/bash
set -e

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')
content=$(echo "$input" | jq -r '.tool_input.content // .tool_input.new_string // ""')

# Only check files where package manager references matter
case "$file_path" in
  *Dockerfile*|*docker-compose*.yml|*.github/workflows/*.yml)
    if echo "$content" | grep -qE '\b(npm|yarn|npx|pnpm)\b'; then
      echo "BLOCKED: You're writing npm/yarn references to $file_path." >&2
      echo "This project uses Bun. Find a Bun-native solution." >&2
      exit 2
    fi
    ;;
esac

exit 0
