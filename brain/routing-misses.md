# Routing Feedback Log

라우팅 실패, 사용자 거부, 코드 대조 불일치를 기록한다.
`ops-learn` 실행 시 이 로그를 읽어 `d:kw`/`d:syn` 보강 및 `d:mod`/COOKBOOK 수정에 활용한다.

## 유형 정의

| 유형 | 설명 | 기록 주체 |
|------|------|----------|
| `miss` | 매칭된 도메인 없음 | ops-find-domain |
| `reject` | 매칭됐으나 사용자가 거부 | ops-find-domain |
| `correction` | 코드 확인 결과 TTL/쿡북 정보가 실제와 불일치 | ops-investigate-issue |
| `stale` | cookbook 플로우를 따랐으나 참조 아티팩트가 변경/삭제됨 | ops-investigate-issue, ops-compact |

## 로그

| 날짜 | 유형 | 입력 텍스트 / 불일치 내용 | 올바른 도메인·값 | 비고 |
|------|------|-------------------------|----------------|------|
| ~~2026-03-31~~ | ~~miss~~ | ~~"문서함", "신분증", "증명서", "서류함"~~ | ~~`:account`~~ | ~~CI-4256~~ — **처리 완료** (2026-04-02): `:account` d:kw에 "문서함", "UserDocument", "UserDocumentFile" 추가, d:syn에 "문서함 삭제 복구 가능한가요" 등 추가 |
| 2026-04-07 | correction | "감사로그" + "스케줄 삭제 이력" → `:account` 감사로그 플로우로 라우팅 | `:shift` + DB 직접 조회 | CI-4351 — 교대근무 스케줄은 raccoon audit API 대상이 아님. `v2_customer_work_plan_template` 직접 조회로 해결. `:shift` d:syn에 "스케줄 삭제 이력 확인해주세요", "스케줄이 사라졌어요" 이미 반영됨 |
