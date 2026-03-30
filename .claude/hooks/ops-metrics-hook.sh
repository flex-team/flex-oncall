#!/bin/bash
# ops 스킬 실행 후 메트릭스 기록을 강제하는 훅
# PostToolUse 이벤트에서 Skill 도구 사용 시 실행됨
#
# 동작: stdin JSON에서 스킬명을 읽어 ops-* 패턴이면
#       메트릭스 기록 지시를 stdout으로 출력 → Claude 컨텍스트에 주입

INPUT=$(cat)
SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty' 2>/dev/null)

if [[ "$SKILL_NAME" == "ops-investigate-issue" ]]; then
  cat <<'REMINDER'
📊 **[필수] investigation 메트릭 기록** — 조사 완료 시 Step 9-2b에서 반드시 JSONL 이벤트를 기록한다.

**기록 명령 템플릿:**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
jq -nc \
  --arg ts "$(date +%Y-%m-%dT%H:%M:%S%z)" \
  --arg user "$USER" \
  --arg model "<현재모델>" \
  --arg env "$([ -n "$GITHUB_ACTIONS" ] && echo ci || echo local)" \
  --arg ticket "<티켓ID>" \
  --arg domain "<도메인>" \
  --argjson context_loaded <true|false> \
  --argjson steps <N> \
  --argjson wrong_hypotheses <N> \
  --arg stale_found "<내용|null>" \
  --arg cookbook_verdict "<hit|ref|miss>" \
  --argjson cookbook_flows_consulted '["F1","F3"]' \
  --arg cookbook_hit_flow "<플로우ID|null>" \
  --arg session "<세션ID>" \
  '{ts:$ts, type:"investigation", user:$user, model:$model, env:$env, ticket:$ticket, domain:$domain, context_loaded:$context_loaded, steps:$steps, wrong_hypotheses:$wrong_hypotheses, stale_found:(if $stale_found == "null" then null else $stale_found end), cookbook_verdict:$cookbook_verdict, cookbook_flows_consulted:$cookbook_flows_consulted, cookbook_hit_flow:(if $cookbook_hit_flow == "null" then null else $cookbook_hit_flow end), session:$session}' \
  >> "$REPO_ROOT/metrics/$USER/$(date +%Y-%m-%d).jsonl"
```

> ⚠️ 이 기록을 건너뛰지 않는다. brain-health 리포트의 핵심 데이터이다.
> 기록 규칙 상세: `.claude/skills/ops-common/metrics-guide.md` 참조
REMINDER

elif [[ "$SKILL_NAME" == "ops-compact" ]]; then
  cat <<'REMINDER'
📊 **[필수] freshness 메트릭 기록** — Step 6 신선도 검증 후 반드시 도메인별 JSONL 이벤트를 기록한다.

**기록 명령 템플릿:**
```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
jq -nc \
  --arg ts "$(date +%Y-%m-%dT%H:%M:%S%z)" \
  --arg user "$USER" \
  --arg model "<현재모델>" \
  --arg env "$([ -n "$GITHUB_ACTIONS" ] && echo ci || echo local)" \
  --arg domain "<도메인>" \
  --argjson spec_items <N> \
  --argjson spec_review_needed <N> \
  --argjson api_refs <N> \
  --argjson api_stale <N> \
  --arg detail "<상세내용>" \
  --arg session "<세션ID>" \
  '{ts:$ts, type:"freshness", user:$user, model:$model, env:$env, domain:$domain, spec_items:$spec_items, spec_review_needed:$spec_review_needed, api_refs:$api_refs, api_stale:$api_stale, detail:$detail, session:$session}' \
  >> "$REPO_ROOT/metrics/$USER/$(date +%Y-%m-%d).jsonl"
```

> ⚠️ 이 기록을 건너뛰지 않는다. brain-health 리포트의 핵심 데이터이다.
> 기록 규칙 상세: `.claude/skills/ops-common/metrics-guide.md` 참조
REMINDER

elif [[ "$SKILL_NAME" =~ ^ops- ]]; then
  cat <<'REMINDER'
📊 **메트릭스 기록** — 이 ops 스킬 실행이 완료되면 아래를 수행한다:

1. **쿡북 히트 기록** (investigate-issue인 경우): 히트/참조/미스 판정 후 COOKBOOK.md 히트 카운트 갱신
2. **스킬 호출 로그는 자동 수집됨** — `metrics/{user}/{date}.jsonl` 에 PreToolUse hook이 기록.
3. **노트 활동 로그 작성 불필요** — JSONL 메트릭스로 대체됨.

> 기록 규칙 상세: `.claude/skills/ops-common/metrics-guide.md` 참조
REMINDER
fi

exit 0
