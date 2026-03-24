# 운영 메트릭스

> 온콜 레포의 Claude 활용 비용과 쿡북 효과를 추적한다.
> 각 ops 스킬 실행 시 자동으로 갱신된다.

## 월별 요약

| 월 | 이슈 수 | 스킬 호출 | 총 토큰 | 쿡북 히트 | 히트율 |
|----|---------|----------|---------|----------|--------|
| 2026-03 | 14 | 21 | 3,858,103 | 1/7 | 14% |

## 쿡북 플로우 히트 이력

| 플로우 | 도메인 | 총 히트 | 최근 히트 | 이슈 목록 |
|--------|--------|---------|----------|----------|
| 체크리스트#2 (휴일대체 기간 문의) | 근태/휴가 | 1 | 2026-03-23 | CI-4186 |

## 쿡북 미스 로그

| 이슈 | 도메인 | 증상 요약 | 쿡북 추가 여부 |
|------|--------|----------|-------------|
| [CI-4176](https://linear.app/flexteam/issue/CI-4176) | 계정/구성원(account/member) | 관리자 퇴사 후 OTP 락 — 신규 관리자 로그인 불가 | ✅ 추가됨 (2026-03-20 close-note) |
| [CI-4168](https://linear.app/flexteam/issue/CI-4168) | 전자계약(contract/digicon) | 전자계약 서식 반복 삭제 — 삭제자 추적 불가 (감사로그 미기록) | ✅ 추가됨 (2026-03-19 rebuild) |
| [CI-4182](https://linear.app/flexteam/issue/CI-4182) | 워크플로우/승인(workflow/approval) | 승인 완료 문서가 진행중 표시 — 이벤트 동기화 실패 | ✅ 추가됨 (2026-03-23 learn) |
| [CI-4180](https://linear.app/flexteam/issue/CI-4180) | 근태/휴가(time-tracking) | 근무유형 적용 시 500 오류 — validateBulk .first{} 방어 처리 없음 | ✅ 추가됨 (2026-03-24 close-note) |
| [CI-4188](https://linear.app/flexteam/issue/CI-4188) | 평가/리뷰(review) | 후발 추가 reviewer의 UserForm 미초기화 — lazy init 의존 | ✅ 추가됨 (2026-03-23 close-note) |
| [CI-4190](https://linear.app/flexteam/issue/CI-4190) | 외부 연동(integration) | 세콤 ODBC 연결 실패 — odbc_connection_limit=0 | ✅ 추가됨 (2026-03-23 close-note) |

## 스킬별 사용량

| 스킬 | 호출 횟수 | 총 토큰 | 평균 토큰/호출 |
|------|----------|---------|--------------|
| investigate-issue | 7 | 1,760,007 | 251,430 |
| close-note | 10 | 1,497,211 | 149,721 |
| maintain-notes | 1 | 389,509 | 389,509 |
| learn | 2 | 103,222 | 51,611 |
| note-issue | 2 | 210,376 | 105,188 |

## 활동 로그 (전체)

| 시간 (KST) | 이슈 | 스킬 | 모델 | 토큰 | 소요시간 | 쿡북 |
|------------|------|------|------|------|---------|------|
| 2026-03-23 19:10 | [CI-4188](https://linear.app/flexteam/issue/CI-4188) | close-note | opus-4-6 | 233,893 | ~5m | — |
| 2026-03-23 18:40 | [CI-4190](https://linear.app/flexteam/issue/CI-4190) | close-note | opus-4-6 | 110,659 | ~3m | — |
| 2026-03-23 18:15 | [CI-4190](https://linear.app/flexteam/issue/CI-4190) | investigate-issue | opus-4-6 | 315,387 | ~6m | 미스 |
| 2026-03-24 00:40 | [CI-4180](https://linear.app/flexteam/issue/CI-4180) | close-note | opus-4-6 | — | ~5m | — |
| 2026-03-23 17:40 | [CI-4188](https://linear.app/flexteam/issue/CI-4188) | investigate-issue | opus-4-6 | 194,524 | ~96s | 미스 |
| 2026-03-24 00:10 | [CI-4183](https://linear.app/flexteam/issue/CI-4183) | close-note | opus-4-6 | 464,608 | 7m 20s | — |
| 2026-03-23 23:30 | [CI-4182](https://linear.app/flexteam/issue/CI-4182) | investigate-issue | opus-4-6 | — | — | 미스 |
| 2026-03-23 22:55 | [CI-4186](https://linear.app/flexteam/issue/CI-4186) | close-note | opus-4-6 | — | — | — |
| 2026-03-23 22:40 | [CI-4186](https://linear.app/flexteam/issue/CI-4186) | investigate-issue | opus-4-6 | 306,419 | 1m 2s | 체크리스트#2 히트 |
| 2026-03-23 20:50 | [CI-4180](https://linear.app/flexteam/issue/CI-4180) | investigate-issue | opus-4-6 | 184,742 | 2m 49s | 미스 |
| 2026-03-23 21:25 | [CI-4179](https://linear.app/flexteam/issue/CI-4179) | close-note | opus-4-6 | 24,284 | 16s | — |
| 2026-03-23 21:15 | [CI-4169](https://linear.app/flexteam/issue/CI-4169) | close-note | opus-4-6 | 23,711 | 2m | — |
| 2026-03-23 21:00 | [CI-4174](https://linear.app/flexteam/issue/CI-4174) | close-note | opus-4-6 | 346,275 | 4m 14s | — |
| 2026-03-23 20:10 | [CI-4169](https://linear.app/flexteam/issue/CI-4169) | note-issue | opus-4-6 | 23,711 | 30s | — |
| 2026-03-23 19:35 | [CI-4179](https://linear.app/flexteam/issue/CI-4179) | learn | opus-4-6 | — | — | — |
| 2026-03-23 19:30 | [CI-4179](https://linear.app/flexteam/issue/CI-4179) | note-issue | opus-4-6 | 186,665 | 1m 31s | — |
| 2026-03-20 17:30 | [CI-4174](https://linear.app/flexteam/issue/CI-4174) | close-note | opus-4-6 | 210,272 | 3m 53s | — |
| 2026-03-20 16:50 | [CI-4176](https://linear.app/flexteam/issue/CI-4176) | close-note | opus-4-6 | 84,509 | 3m | — |
| 2026-03-20 15:53 | [CI-4176](https://linear.app/flexteam/issue/CI-4176) | investigate-issue | opus-4-6 | 332,459 | 12m | 미스 |
| 2026-03-20 16:00 | Notion 3개 | learn | opus-4-6 | 103,222 | 2m 54s | — |
| 2026-03-19 23:50 | 일괄 | maintain-notes --rebuild | opus-4-6 | 389,509 | 1m 24s | — |
| 2026-03-19 18:30 | [CI-4168](https://linear.app/flexteam/issue/CI-4168) | investigate-issue | opus-4-6 | 426,476 | 13m 13s | 미스 |
