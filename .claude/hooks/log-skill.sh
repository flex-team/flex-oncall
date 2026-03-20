#!/bin/bash

# PreToolUse hook: Skill 호출 시 자동으로 JSONL 로그 기록
# 설정 불필요 — repo clone만 하면 동작
# 저장: {repo-root}/metrics/{username}/{date}.jsonl

payload=$(cat)

skill=$(jq -r '.tool_input.skill // ""' <<< "$payload")
args=$(jq -r '.tool_input.args // ""' <<< "$payload")
session_id=$(jq -r '.session_id // ""' <<< "$payload")

[ -z "$skill" ] && exit 0

ts=$(date +"%Y-%m-%dT%H:%M:%S%z")
epoch=$(date -u +%s)
date_str=$(date +"%Y-%m-%d")

# repo root를 git으로 자동 탐색
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
  # fallback: 스크립트 위치 기준으로 역산 (.claude/hooks/ → repo root)
  REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
fi

METRICS_DIR="$REPO_ROOT/metrics/$USER"
mkdir -p "$METRICS_DIR"

jq -nc \
  --arg ts "$ts" \
  --arg epoch "$epoch" \
  --arg date "$date_str" \
  --arg user "$USER" \
  --arg skill "$skill" \
  --arg args "$args" \
  --arg session "$session_id" \
  '{ts: $ts, epoch: ($epoch | tonumber), date: $date, user: $user, skill: $skill, args: $args, session: $session}' \
  >> "$METRICS_DIR/$date_str.jsonl"
