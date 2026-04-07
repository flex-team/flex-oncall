#!/bin/bash

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TIMESTAMP_FILE="$REPO_ROOT/.last-submodule-sync"
SYNC_INTERVAL_HOURS=24

if [ -f "$TIMESTAMP_FILE" ]; then
  last_sync=$(cat "$TIMESTAMP_FILE")
  now=$(date +%s)
  diff=$(( (now - last_sync) / 3600 ))

  if [ "$diff" -lt "$SYNC_INTERVAL_HOURS" ]; then
    exit 0
  fi
fi

echo "[auto-sync] 서브모듈을 최신화합니다 (마지막 동기화: ${diff:-N/A}시간 전)..."
cd "$REPO_ROOT" && git submodule update --remote --merge --recursive 2>&1

date +%s > "$TIMESTAMP_FILE"
echo "[auto-sync] 완료."
