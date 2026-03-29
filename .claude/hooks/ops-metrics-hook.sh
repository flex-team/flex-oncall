#!/bin/bash
# ops 스킬 실행 후 메트릭스 기록을 강제하는 훅
# PostToolUse 이벤트에서 Skill 도구 사용 시 실행됨
#
# 동작: stdin JSON에서 스킬명을 읽어 ops-* 패턴이면
#       메트릭스 기록 지시를 stdout으로 출력 → Claude 컨텍스트에 주입

INPUT=$(cat)
SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty' 2>/dev/null)

# ops-* 스킬만 대상
if [[ "$SKILL_NAME" =~ ^ops- ]]; then
  cat <<'REMINDER'
📊 **메트릭스 기록** — 이 ops 스킬 실행이 완료되면 아래를 수행한다:

1. **쿡북 히트 기록** (investigate-issue인 경우): 히트/참조/미스 판정 후 COOKBOOK.md 히트 카운트 갱신
2. **스킬 호출 로그는 자동 수집됨** — `metrics/{user}/{date}.jsonl` 에 PreToolUse hook이 기록.
3. **노트 활동 로그 작성 불필요** — JSONL 메트릭스로 대체됨.

> 기록 규칙 상세: `.claude/skills/ops-common/metrics-guide.md` 참조
REMINDER
fi

exit 0
