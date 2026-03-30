---
name: ops-domain-routing-guide
description: domain-map.ttl 기반 도메인 라우팅 공통 가이드 — 입력 텍스트에서 관련 도메인·서브모듈·쿡북 섹션을 특정하는 알고리즘
---

# Domain Routing Guide

이 문서는 입력 텍스트(이슈 제목, CS 문의, 슬랙 메시지 등)로부터 관련 도메인을 특정하는 알고리즘을 정의한다.

## 에이전트 위임 (권장)

도메인 라우팅이 필요한 스킬은 **domain-router 에이전트**를 호출하여 위임할 수 있다.
에이전트는 TTL 전체를 자신의 컨텍스트에서 처리하고 compact JSON만 반환한다.

```
Agent(
  subagent_type: "general-purpose",
  description: "TTL 파싱 및 도메인 라우팅",
  prompt: ".claude/agents/domain-router.md 의 지시를 읽고 따라라. 입력 텍스트: {입력}"
)
```

에이전트를 사용하면 호출자 컨텍스트에 TTL 원문이 올라가지 않아 후속 작업(조사, 코드 탐색 등)에 컨텍스트를 절약할 수 있다. 아래 알고리즘 상세는 에이전트 정의(`.claude/agents/domain-router.md`)와 동기화되어 있으며, 에이전트 없이 직접 수행할 때의 레퍼런스로도 사용된다.

---

## Step 1: TTL 파싱

`brain/domain-map.ttl` 을 Read로 전체 읽기. 세 종류의 블록을 추출한다.

| 블록 타입 | 접두사 | 매칭 대상 필드 |
|----------|--------|--------------|
| Domain | `:` | `d:n`(이름), `d:kw`(키워드), `d:syn`(사용자 표현 문장), `d:mod`(모듈명) |
| Note | `n:` | `d:s`(요약) |
| Glossary | `g:` | `d:q`(질문), `d:a`(답변) |

각 블록의 `d:in` 필드로 소속 도메인을 파악한다.
- Domain 블록: 블록 자체가 도메인
- Note/Glossary 블록: `d:in :도메인명` 으로 소속 도메인 결정

## Step 2: 특수 케이스 확인

입력이 티켓 ID 패턴(`[A-Z]+-\d+`, 예: CI-4145)이면:
1. `n:{ticket-id}` 블록에서 `d:in` 으로 도메인 직접 특정
2. 키워드 매칭(Step 3~4)을 건너뛰고 바로 Step 5로 이동
3. 해당 티켓 ID 블록이 없으면 → 일반 텍스트로 취급하여 Step 3 진행

## Step 3: 토큰 매칭 (2-pass)

입력 텍스트를 TTL 내 문자열 값과 매칭한다. **Pass 1(토큰)과 Pass 2(구문)** 두 단계로 수행한다.

### Pass 1: 토큰 매칭

입력 텍스트의 각 토큰(어절)을 TTL 내 문자열 값과 매칭한다.

- 토큰 T와 값 V에 대해: **T가 V의 부분 문자열**이거나, **V가 T의 부분 문자열**이면 매칭
- 길이 1자 토큰(조사 등)은 무시
- 대소문자 무시 (한글은 해당 없음)

### Pass 2: 구문 매칭 (Phrase Match)

`g:q` 값은 사용자 표현 전체 문장(예: "휴가 안 들어갔어요")이므로, 토큰 단위가 아닌 **구문 단위**로 추가 매칭한다.

1. 입력 텍스트의 토큰 집합 I와 `g:q` 값의 토큰 집합 Q를 비교
2. 겹치는 토큰 수(길이 1자 제외)를 센다 — 이때 Pass 1과 동일한 substring 규칙 적용
3. **겹치는 토큰이 2개 이상이면** 해당 `g:q`의 소속 도메인에 **구문 보너스 +3** 부여
4. 하나의 도메인에 여러 `g:q`가 구문 매칭되면 **가장 높은 1건만** 반영 (중복 보너스 방지)

> 구문 보너스는 Pass 1 가중치와 별도로 합산된다.

### 가중치 테이블

| 매칭 대상 | 가중치 | 근거 |
|----------|--------|------|
| `d:kw` (키워드) | 3 | 도메인 전용 키워드 — 가장 강한 시그널 |
| `d:syn` (사용자 표현 문장) | 3 | `g:q`에서 추출한 도메인 직결 표현 |
| `g:q` (용어집 질문) | 3 | 사용자 표현과 직접 매칭 — `d:kw`와 동급 시그널 |
| `g:a` (용어집 답변) | 2 | 시스템 용어 매칭 (예: SES, preference=ON_TIME) |
| `d:s` (노트 요약) | 1 | 과거 이슈 참고용 — verdict=spec이면 0 |
| `d:n` (도메인 이름) | 1 | 넓은 매칭 |
| `d:mod` (모듈명) | 1 | 기술 용어 매칭 |
| 구문 보너스 (Pass 2) | +3 | `g:q` 또는 `d:syn` 전체와 2토큰 이상 겹칠 때 부여 |

> **d:s 감쇠**: verdict가 `"spec"` 인 노트의 `d:s` 가중치는 **0** (noise 방지). 해당 노트는 결과의 Related Notes에는 표시하되 스코어에는 기여하지 않는다.

## Step 4: 스코어링

```
도메인별 score = Σ (매칭된 필드의 가중치)
```

### Primary 결정

- 최고 스코어 도메인 = **primary**
- 동점 처리 (순서대로 적용):
  1. `d:kw` 히트가 더 많은 쪽이 primary
  2. `g:q`/`g:a` 히트가 더 많은 쪽이 primary
  3. 여전히 동점이면 **둘 다 primary**로 표시

### Related 결정

양방향 `d:x` 수집:
- primary의 `d:x` 에 있는 도메인
- primary를 `d:x` 로 참조하는 도메인 (역방향)

## Step 5: 결과 수집

primary + related 도메인에서 다음 정보를 수집한다:

| 수집 대상 | TTL 필드 | 용도 |
|----------|----------|------|
| 서브모듈 목록 | `d:repo` | 필요한 repo (중복 제거) |
| 모듈 경로 | `d:mod` | 코드 내 모듈 위치 |
| 쿡북 섹션 | `d:cb` | COOKBOOK.md 참조 섹션 이름 |
| 도메인 컨텍스트 | 파일 존재 여부 | `cookbook/{domain-id}.md#도메인-컨텍스트` (있으면 포함) |
| 용어집 히트 | 매칭된 `g:*` | 사용자 표현 → 시스템 용어 |
| 관련 노트 | 매칭된 `n:*` | 과거 이슈 (ID + 요약 + verdict) |

> `d:cb` 값은 COOKBOOK.md 섹션 이름의 참고용이며, 실제 COOKBOOK 구조와 다를 수 있다.

## 결과 구조

라우팅 결과는 다음 구조를 가진다:

```
primary:
  - domain: :integration
    name: "외부 연동 (Integration)"
    repos: [flex-timetracking-backend]
    modules: [external-work-clock]
    cookbook: "외부 연동 (Integration)"
    context: "cookbook/integration.md#도메인-컨텍스트"  # 존재하면 포함

related:
  - domain: :time-tracking
    name: "근태/휴가 (Time Tracking / Time Off)"
    repos: [flex-timetracking-backend]
    reason: "d:x 연결"

glossary_hits:
  - id: g:intg-03
    question: "세콤으로 퇴근했는데 정시로 찍혀요"
    answer: "퇴근 타각 자정 조정 preference=ON_TIME"

related_notes:
  - id: CI-4145
    summary: "세콤/캡스/텔레캅 퇴근 정시 고정"
    verdict: spec
    location: active | archive
```

## 매칭 없음 처리

어떤 도메인에도 매칭되지 않으면:
1. 입력 텍스트를 그대로 출력하고 "매칭된 도메인이 없습니다" 를 안내
2. CLAUDE.md의 서브모듈 맵 키워드 테이블을 fallback으로 제시
3. 사용자에게 도메인을 직접 지정하도록 요청
