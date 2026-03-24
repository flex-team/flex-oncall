---
name: ops-metrics-guide
description: 메트릭스 기록 가이드
---

# 메트릭스 기록 가이드

> ops 스킬이 참조하는 공통 가이드. PostToolUse 훅이 ops 스킬 실행 시 자동 리마인드한다.

## 메트릭스 수집 구조

| 수집처 | 형식 | 방식 | 용도 |
|--------|------|------|------|
| `metrics/{user}/{date}.jsonl` | JSONL | **자동** (PreToolUse hook) | 단일 소스 — 모든 스킬 호출 기록 |
| `brain/routing-misses.md` | Markdown | 반자동 (ops-find-domain 기록, ops-learn 소비) | 라우팅 miss/reject/correction |
| `brain/COOKBOOK.md` 히트 카운트 | Markdown 인라인 | investigate-issue가 갱신 | 플로우별 히트 실적 |

> ~~`.claude/METRICS.md`~~, ~~노트 활동 로그 테이블~~은 폐기됨. JSONL이 단일 소스이며, `ops-compact` 실행 시 on-demand 집계한다.

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
