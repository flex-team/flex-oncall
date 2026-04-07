---
name: oncall
description: 온콜 이슈 분석 및 디버깅 스킬. CS팀이 슬랙에 올린 이슈나 QA가 보고한 버그의 원인을 체계적으로 분석하고, 슬랙 공유용 한글 요약을 생성한다. "온콜", "QA 이슈", "버그 분석", "이슈 분석", "원인 파악", "왜 안 되는지", "에러가 난다", "안 된다고 해", "CS 이슈" 등의 표현을 사용하거나, 특정 기능의 오류/장애 상황을 설명할 때 이 스킬을 사용한다. Linear 티켓이나 슬랙 메시지 URL을 공유하며 분석을 요청하는 경우에도 사용한다.
argument-hint: <Slack URL 또는 Linear 티켓 ID> (예: https://flex-team.slack.com/archives/... 또는 CI-4500)
---

# 온콜 이슈 분석 (Orchestrator)

## 역할

이슈 접수부터 슬랙 공유까지 전체 온콜 워크플로우를 자동 진행하는 오케스트레이터.
내부적으로 3개 서브 스킬을 순서대로 실행하며, 중간 결과에 따라 early-exit한다.

## 워크플로우

```
/oncall (이 스킬)
  ├─ Phase 1: /oncall-triage
  │    → [분류] + [판정] + [대상 레포]
  │
  ├─ 분기 판단
  │    ├─ BE 이슈 → Phase 3으로 건너뜀 (triage 결과만으로 BE 제보 작성)
  │    ├─ 스펙 이슈 / Not a bug → Phase 3으로 건너뜀
  │    └─ FE 이슈 / 판단 불가 → Phase 2 진행
  │
  ├─ Phase 2: /oncall-investigate
  │    → [결론] + [원인] + [근거] + [관련 파일]
  │
  └─ Phase 3: /oncall-summarize
       → 슬랙 공유용 메시지 생성
```

## 실행 규칙

### Phase 1: Triage

`/oncall-triage` 스킬의 전체 지침을 따라 실행한다.

**Input**: $ARGUMENTS (Slack URL, Linear 티켓 ID, 또는 이슈 설명)
**Output**: 이슈 요약, 유형 분류, FE/BE 판정, 대상 레포

### 분기 판단

Triage 결과의 **[판정]** 에 따라 다음 단계를 결정한다:

| 판정 | 다음 단계 | 이유 |
|------|-----------|------|
| **BE 이슈** | → Phase 3 (summarize) | FE에서 심층 조사할 수 없음. BE 확인 요청 포맷으로 바로 작성 |
| **스펙 이슈** | → Phase 3 (summarize) | 조사 불필요. 스펙 이슈 포맷으로 바로 작성 |
| **Not a bug** | → Phase 3 (summarize) | 이미 해결됨 등. 확인 결과 포맷으로 바로 작성 |
| **FE 이슈** | → Phase 2 (investigate) | FE 코드 조사 필요 |
| **FE-BE 교차** | → Phase 2 (investigate) | FE 코드 추적 후 BE 교차 조사 |
| **판단 불가** | → Phase 2 (investigate) | 코드를 봐야 판단 가능 |

분기 시 사용자에게 표시:
```
● Triage 완료. {판정 근거 한 줄}
  [다음] {Phase 2 진행 / Phase 3으로 건너뜀} — {이유}
```

### Phase 2: Investigate

`/oncall-investigate` 스킬의 전체 지침을 따라 실행한다.

**Input**: Phase 1의 triage 결과 (이슈 유형, FE/BE 판정, 대상 레포, 회사 ID, 증상)
**Output**: 원인 분류, 근거, 관련 파일, 가설 테이블

### Phase 3: Summarize

`/oncall-summarize` 스킬의 전체 지침을 따라 실행한다.

**Input**: 원인 분류 + 조사 결과 (Phase 2에서 온 경우), 또는 triage 결과만 (early-exit인 경우)
**Output**: 슬랙 공유용 메시지

## 주의사항

- 각 Phase의 세부 지침은 해당 서브 스킬의 SKILL.md를 따른다. 이 스킬은 흐름 제어만 담당한다.
- Phase 전환 시 반드시 사용자에게 현재 단계와 다음 단계를 표시한다.
- 긴급(rotating_light) + 광범위 영향 이슈는 Phase 1에서 escalation을 먼저 제안하고, 조사는 병행한다.
