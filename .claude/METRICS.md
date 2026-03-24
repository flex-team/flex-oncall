# 운영 메트릭스

> ⚠️ **이 파일은 더 이상 갱신하지 않는다.** 메트릭스는 `metrics/{user}/{date}.jsonl` 에서 자동 수집되며, `ops-compact` 실행 시 on-demand 집계된다. (2026-03-24~)
>
> 아래 데이터는 폐기 시점까지의 누적 기록이다.

## 월별 요약

| 월 | 이슈 수 | 스킬 호출 | 총 토큰 | 쿡북 히트 | 히트율 |
|----|---------|----------|---------|----------|--------|
| 2026-03 | 23 | 40 | 6,070,113 | 2/11 | 18% |

## 쿡북 플로우 히트 이력

| 플로우 | 도메인 | 총 히트 | 최근 히트 | 이슈 목록 |
|--------|--------|---------|----------|----------|
| 체크리스트#2 (휴일대체 기간 문의) | 근태/휴가 | 2 | 2026-03-24 | CI-4186, CI-4199 |

## 쿡북 미스 로그

| 이슈 | 도메인 | 증상 요약 | 쿡북 추가 여부 |
|------|--------|----------|-------------|
| [CI-4176](https://linear.app/flexteam/issue/CI-4176) | 계정/구성원(account/member) | 관리자 퇴사 후 OTP 락 — 신규 관리자 로그인 불가 | ✅ 추가됨 (2026-03-20 close-note) |
| [CI-4168](https://linear.app/flexteam/issue/CI-4168) | 전자계약(contract/digicon) | 전자계약 서식 반복 삭제 — 삭제자 추적 불가 (감사로그 미기록) | ✅ 추가됨 (2026-03-19 rebuild) |
| [CI-4182](https://linear.app/flexteam/issue/CI-4182) | 워크플로우/승인(workflow/approval) | 승인 완료 문서가 진행중 표시 — 이벤트 동기화 실패 | ✅ 추가됨 (2026-03-23 learn) |
| [CI-4180](https://linear.app/flexteam/issue/CI-4180) | 근태/휴가(time-tracking) | 근무유형 적용 시 500 오류 — validateBulk .first{} 방어 처리 없음 | ✅ 추가됨 (2026-03-24 close-note) |
| [CI-4188](https://linear.app/flexteam/issue/CI-4188) | 평가/리뷰(review) | 후발 추가 reviewer의 UserForm 미초기화 — lazy init 의존 | ✅ 추가됨 (2026-03-23 close-note) |
| [CI-4190](https://linear.app/flexteam/issue/CI-4190) | 외부 연동(integration) | 세콤 ODBC 연결 실패 — odbc_connection_limit=0 | ✅ 추가됨 (2026-03-23 close-note) |
| [CI-4203](https://linear.app/flexteam/issue/CI-4203) | 승인/알림(approval/notification) | 승인 리마인드 발송자 추적 — access log 조회로 확인 | ✅ 추가됨 (2026-03-24 close-note) |
| [CI-4193](https://linear.app/flexteam/issue/CI-4193) | 승인(approval) | 경력 변경 댓글 누락/중복 — FE size=1 버그 | ✅ 추가됨 (2026-03-24 close-note) |

## 스킬별 사용량

| 스킬 | 호출 횟수 | 총 토큰 | 평균 토큰/호출 |
|------|----------|---------|--------------|
| investigate-issue | 11 | 2,292,783 | 208,435 |
| close-note | 19 | 2,259,341 | 118,913 |
| maintain-notes | 1 | 389,509 | 389,509 |
| learn | 2 | 103,222 | 51,611 |
| note-issue | 6 | 1,007,480 | 167,913 |

## 활동 로그 (전체)

| 시간 (KST) | 이슈 | 스킬 | 모델 | 토큰 | 소요시간 | 쿡북 |
|------------|------|------|------|------|---------|------|
| 2026-03-24 22:30 | [CI-4193](https://linear.app/flexteam/issue/CI-4193) | close-note | opus-4-6 | 163,708 | 4m 30s | — |
| 2026-03-24 22:00 | [CI-4193](https://linear.app/flexteam/issue/CI-4193) | investigate-issue | opus-4-6 | — | — | 미스 |
| 2026-03-24 21:30 | [CI-4197](https://linear.app/flexteam/issue/CI-4197) | close-note | opus-4-6 | 101,144 | 1m 12s | — |
| 2026-03-24 20:15 | [CI-4197](https://linear.app/flexteam/issue/CI-4197) | close-note | opus-4-6 | 24,141 | 32s | — |
| 2026-03-24 20:00 | [CI-4204](https://linear.app/flexteam/issue/CI-4204) | note-issue | opus-4-6 | 101,416 | 8s | — |
| 2026-03-24 19:30 | [CI-4203](https://linear.app/flexteam/issue/CI-4203) | close-note | opus-4-6 | — | 2m 0s | — |
| 2026-03-24 19:15 | [CI-4203](https://linear.app/flexteam/issue/CI-4203) | investigate-issue | opus-4-6 | 231,875 | 3m 6s | 미스 |
| 2026-03-24 18:30 | [CI-4201](https://linear.app/flexteam/issue/CI-4201) | close-note | opus-4-6 | 120,000 | 3m 0s | — |
| 2026-03-24 18:00 | [CI-4200](https://linear.app/flexteam/issue/CI-4200) | close-note | opus-4-6 | 285,506 | 1m 32s | — |
| 2026-03-24 17:30 | [CI-4179](https://linear.app/flexteam/issue/CI-4179) | close-note | opus-4-6 | 28,086 | 51s | — |
| 2026-03-24 17:15 | [CI-4202](https://linear.app/flexteam/issue/CI-4202) | close-note | opus-4-6 | 27,904 | 37s | — |
| 2026-03-24 17:00 | [CI-4201](https://linear.app/flexteam/issue/CI-4201) | investigate-issue | opus-4-6 | 300,901 | 5m 10s | 체크리스트#4 참조 |
| 2026-03-24 16:00 | [CI-4202](https://linear.app/flexteam/issue/CI-4202) | note-issue | opus-4-6 | 222,003 | 2m 13s | — |
| 2026-03-24 14:30 | [CI-4195](https://linear.app/flexteam/issue/CI-4195) | close-note | opus-4-6 | 175,349 | 2m 41s | — |
| 2026-03-24 14:15 | [CI-4199](https://linear.app/flexteam/issue/CI-4199) | close-note | opus-4-6 | — | — | — |
| 2026-03-24 14:00 | [CI-4199](https://linear.app/flexteam/issue/CI-4199) | investigate-issue | opus-4-6 | — | — | 체크리스트#2 히트 |
| 2026-03-24 12:15 | [CI-4197](https://linear.app/flexteam/issue/CI-4197) | note-issue | opus-4-6 | 210,896 | 2m 0s | — |
| 2026-03-24 10:45 | [CI-4195](https://linear.app/flexteam/issue/CI-4195) | note-issue | opus-4-6 | 262,789 | 2m 29s | — |
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
