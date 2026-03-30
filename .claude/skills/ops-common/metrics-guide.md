---
name: ops-metrics-guide
description: 메트릭스 기록 가이드
---

# 메트릭스 기록 가이드

> ops 스킬이 참조하는 공통 가이드. PostToolUse 훅이 ops 스킬 실행 시 자동 리마인드한다.

## 메트릭스 수집 구조

| 수집처 | 형식 | 방식 | 용도 |
|--------|------|------|------|
| `metrics/{user}/{date}.jsonl` | JSONL | **자동** (PreToolUse hook) | 단일 소스 — skill/investigation/freshness 전체 이벤트 기록 |
| `brain/routing-misses.md` | Markdown | 반자동 (ops-find-domain 기록, ops-learn 소비) | 라우팅 miss/reject/correction |
| `brain/COOKBOOK.md` 히트 카운트 | Markdown 인라인 | investigate-issue가 갱신 | 플로우별 히트 실적 |

## 쿡북 히트 판정 (investigate-issue 전용)

`investigate-issue` 실행 시 쿡북 참조 결과를 판정한다.

### 판정 기준

| 판정 | 조건 | 동작 |
|------|------|------|
| **히트(Hit)** | 쿡북 플로우의 단계를 따라가서 가설 확정 또는 원인 발견에 기여 | COOKBOOK.md 해당 플로우 `히트: N` +1 |
| **참조(Ref)** | 플로우를 읽었지만 이번 이슈와 무관 | 기록만 (히트 증가 안 함) |
| **미스(Miss)** | 해당 도메인에 플로우가 없어서 처음부터 조사 | routing-misses.md에 기록 |
| **해당 없음** | investigate-issue가 아닌 스킬 | 동작 없음 |

### 히트 시 추가 동작

1. **COOKBOOK.md 갱신**: 해당 플로우의 `히트: N` 을 +1 하고, 출처 이슈 ID를 추가
2. Tier-2(`cookbook/{domain}.md`)의 플로우가 히트한 경우 → `ops-compact` 실행 시 Tier-1 승격 대상

### 미스 시 추가 동작

조사 완료 후 `ops-learn` 또는 `ops-close-note` 에서 새 플로우를 COOKBOOK에 등록한다.

## JSONL 이벤트 타입별 수집 규칙

### skill (자동 수집)

- **수집 방식**: PreToolUse hook (`log-skill.sh`)이 자동 기록 — 수동 동작 불필요
- **트리거**: 모든 Skill 도구 호출 시
- **스키마**:
  ```json
  {"ts":"...","epoch":1234,"date":"2026-03-30","user":"yj.kim","skill":"ops-investigate-issue","args":"CI-4240","session":"..."}
  ```

### investigation (수동 기록 필수)

- **수집 방식**: `ops-investigate-issue` Step 9-2b에서 Claude가 Bash로 기록
- **트리거**: ops-investigate-issue 스킬의 조사 완료 시
- **스키마**:
  ```json
  {"ts":"...","type":"investigation","user":"...","model":"...","env":"local|ci","ticket":"CI-4240","domain":"time-tracking","context_loaded":true,"steps":5,"wrong_hypotheses":1,"stale_found":null,"cookbook_verdict":"hit","cookbook_flows_consulted":["F1","F3"],"cookbook_hit_flow":"F3","session":"..."}
  ```
- **필드 설명**:

| 필드 | 설명 | 수집 시점 |
|------|------|----------|
| `ticket` | 조사한 티켓 ID | Argument Resolution 시 |
| `domain` | 라우팅된 도메인 ID | 도메인 라우팅 완료 시 |
| `context_loaded` | 쿡북 도메인 컨텍스트 로딩 여부 | 쿡북 참조 시 |
| `steps` | 가설 검증 사이클 반복 횟수 | 가설 검증 루프 종료 시 |
| `wrong_hypotheses` | 소거된 가설 수 | 가설 검증 루프 종료 시 |
| `stale_found` | 부패 발견 내용 (없으면 `null`) | 코드-TTL 대조 시 |
| `cookbook_verdict` | 쿡북 히트 판정 (`hit`/`ref`/`miss`) | 쿡북 히트/미스 확정 시 |
| `cookbook_flows_consulted` | 참조한 플로우 ID 배열 | 쿡북 참조 시 |
| `cookbook_hit_flow` | 히트 플로우 ID (없으면 `null`) | 히트/미스 확정 시 |

### freshness (수동 기록 필수)

- **수집 방식**: `ops-compact` Step 6-3에서 Claude가 Bash로 기록
- **트리거**: ops-compact 스킬의 신선도 검증 완료 시 (도메인별 1건씩)
- **스키마**:
  ```json
  {"ts":"...","type":"freshness","user":"...","model":"...","env":"local|ci","domain":"payroll","spec_items":8,"spec_review_needed":1,"api_refs":5,"api_stale":0,"detail":"CI-4131 올림 설정 스펙 — 관련 코드 변경 감지","session":"..."}
  ```
- **필드 설명**:

| 필드 | 설명 |
|------|------|
| `domain` | 검증 대상 도메인 |
| `spec_items` | 스펙 항목 총 수 |
| `spec_review_needed` | 코드 변경 감지된 스펙 수 |
| `api_refs` | 쿡북에서 참조하는 API 수 |
| `api_stale` | 코드에서 사라진 API 수 |
| `detail` | 리뷰 필요 항목 요약 |

## 공통 필드 수집 규칙

모든 JSONL 이벤트 타입에 공통으로 포함되는 필드:

| 필드 | 수집 방법 |
|------|----------|
| `ts` | `date +%Y-%m-%dT%H:%M:%S%z` (KST) |
| `user` | `$USER` 환경변수 |
| `model` | 현재 세션의 Claude 모델 ID (예: `claude-opus-4-6`) |
| `env` | `$GITHUB_ACTIONS` 존재 시 `ci`, 아니면 `local` |
| `session` | Claude Code 세션 ID |
