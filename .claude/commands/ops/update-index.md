---
description: 운영 노트 인덱스(INDEX.md)에 새 문서를 추가하거나 전체를 재구성
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
argument-hint: [ticket-id] (예: CI-4103) — 생략 시 전체 재구성
---

# Update Index

## Purpose
`operation-notes/INDEX.md`를 업데이트한다.
이슈 조사 시 전체 노트를 읽지 않고 키워드로 관련 문서만 찾을 수 있게 하는 것이 목적이다.

- **증분 모드**: 티켓 ID 전달 → 해당 노트를 읽고 INDEX.md에 항목 추가
- **전체 재구성 모드**: 인자 없이 호출 → 모든 노트를 스캔하여 INDEX.md 전체 재작성

## Input
$ARGUMENTS

### 모드 판별
- `$ARGUMENTS`에 티켓 ID 패턴(`[A-Z]+-\d+`)이 있으면 → **증분 모드**
- `$ARGUMENTS`가 비어있으면 → **전체 재구성 모드**

## INDEX.md 구조

```markdown
# 운영 노트 인덱스

> 이슈 조사 시 전체 문서를 읽지 말고, 이 인덱스에서 키워드로 관련 문서를 찾아 해당 문서만 읽을 것.
> COOKBOOK.md는 도메인별 진단 가이드이므로 항상 먼저 참조.

## 도메인별 문서 목록

### {도메인명}

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [{ticket-id}](./{파일명}) | {한 줄 요약} | {키워드1}, {키워드2}, ... |
```

## 도메인 분류 기준

| 키워드/영역 | 도메인 |
|------------|--------|
| 연차촉진, boost, PENDING_WRITE | 연차 촉진 (Annual Time-Off Promotion) |
| 알림, notification, 이메일, CTA, push | 알림 (Notification) |
| 휴가, 연차, time-off, 근태, 출퇴근, 휴일대체, 보상휴가, 포괄임금, 근로시간 | 근태/휴가 (Time Tracking / Time Off) |
| 스케줄, 근무표, 게시, 연장근무 | 스케줄링 (Scheduling) |
| 교대근무, shift, 배치 | 교대근무 (Shift) |
| 세콤, CAPS, 연동, external, 타각기 | 외부 연동 (Integration / SECOM) |
| 승인, approval, 승인자, 참조자 | 승인 (Approval) |
| 권한, permission, access-check | 권한 (Permission) |
| 급여, payroll, 수당, 공제 | 급여 (Payroll) |

기존 도메인에 해당하지 않으면 새 도메인 섹션을 추가한다.

## 키워드 추출 기준

노트에서 다음을 키워드로 추출한다:
- **도메인 용어**: 연차촉진, 보상휴가, 휴일대체 등
- **증상 키워드**: 알림 미수신, 부여 불가, 미표기 등
- **기능/설정명**: TrackingExperimentalDynamicConfig, forAssign 등
- **테이블/필드명**: annual_time_off_boost_history, boosted_at 등
- **시스템 용어**: UTC/KST, OpenSearch, consumer 등

키워드는 사용자가 이슈 인입 시 사용할 만한 표현 위주로 선정한다.

## Procedure

### 증분 모드

#### Step 1: 대상 노트 읽기
`operation-notes/{ticket-id}.md` (또는 `{ticket-id}-*.md` 패턴)를 읽는다.
파일이 없으면 `"해당 노트가 없습니다: {ticket-id}"` 출력 후 종료.

#### Step 2: 정보 추출
노트에서 다음을 추출:
- **제목** (H1) → 한 줄 요약
- **도메인** → 도메인 분류 기준표에 따라 판별
- **키워드** → 키워드 추출 기준에 따라 5~10개

#### Step 3: INDEX.md 업데이트
기존 INDEX.md를 읽고:
- 해당 티켓이 이미 있으면 → 요약과 키워드를 갱신
- 없으면 → 해당 도메인 섹션의 테이블에 행 추가
- 도메인 섹션이 없으면 → 새 도메인 섹션 생성

#### Step 4: 결과 보고
추가/갱신한 항목을 보여준다.

---

### 전체 재구성 모드

#### Step 1: 노트 전체 수집
`operation-notes/` 디렉토리의 모든 `.md` 파일을 수집한다.

**제외 대상:**
- `CLAUDE.md` (디렉토리 가이드)
- `COOKBOOK.md` (진단 가이드)
- `INDEX.md` (이 커맨드의 산출물)

#### Step 2: 각 노트에서 정보 추출
각 노트의 제목(H1)과 처음 20줄을 읽어 요약, 도메인, 키워드를 추출한다.

#### Step 3: INDEX.md 전체 재작성
도메인별로 그룹핑하여 INDEX.md를 재작성한다.

#### Step 4: 결과 보고
전체 문서 수와 도메인별 분포를 보여준다.

## Rules
- 키워드는 **쉼표 구분**, 한 항목당 5~10개
- 요약은 **한 줄** (50자 이내 권장)
- 도메인 분류를 **강제로 맞추지 않는다** — 해당 도메인이 없으면 새로 만든다
- 하나의 노트가 여러 도메인에 걸치면 **주 도메인 하나**에만 배치한다
- INDEX.md 외의 파일은 수정하지 않는다
- 커밋은 하지 않는다 — 호출자(note-issue, investigate-issue 등)가 함께 커밋하도록 한다
