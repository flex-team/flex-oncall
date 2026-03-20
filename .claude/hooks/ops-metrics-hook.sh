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
📊 **메트릭스 기록 필수** — 이 ops 스킬 실행이 완료되면 반드시 아래를 수행한다:

1. **노트 활동 로그**: 대상 operation-note 하단 `## Claude 활동 로그` 테이블에 행 추가
   - subagent total_tokens, duration_ms 합산
   - 모델명, 쿡북 참조 결과 포함
2. **METRICS.md 갱신**: `operation-notes/METRICS.md` 의 활동 로그(전체) + 스킬별 사용량 + 월별 요약 테이블 갱신
3. **쿡북 히트 기록** (investigate-issue인 경우): 히트/참조/미스 판정 후 COOKBOOK.md 히트 카운트 + METRICS.md 플로우 히트 이력 갱신

> 기록 규칙 상세: `.claude/skills/ops-common/metrics-guide.md` 참조
REMINDER
fi

exit 0
