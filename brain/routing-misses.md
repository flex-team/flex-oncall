# Routing Feedback Log

라우팅 실패, 사용자 거부, 코드 대조 불일치를 기록한다.
`ops-learn` 실행 시 이 로그를 읽어 `d:kw`/`d:syn` 보강 및 `d:mod`/COOKBOOK 수정에 활용한다.

## 유형 정의

| 유형 | 설명 | 기록 주체 |
|------|------|----------|
| `miss` | 매칭된 도메인 없음 | ops-find-domain |
| `reject` | 매칭됐으나 사용자가 거부 | ops-find-domain |
| `correction` | 코드 확인 결과 TTL/쿡북 정보가 실제와 불일치 | ops-investigate-issue |

## 로그

| 날짜 | 유형 | 입력 텍스트 / 불일치 내용 | 올바른 도메인·값 | 비고 |
|------|------|-------------------------|----------------|------|
| 2026-03-25 | miss | 원천징수확인서 발급번호 관리번호 자동채번 — COOKBOOK에 전용 플로우 없음 | :payroll (flex-payroll-backend > work-income) | CI-4208 — 미구현 기능 확인. 증명서/문서 라벨이지만 실제 도메인은 급여 |
| 2026-03-25 | miss | 휴일대체 취소 불가 — COOKBOOK에 취소 오류 진단 플로우 없음 | :time-tracking (flex-timetracking-backend > time-tracking) | CI-4217 — FE가 구 이벤트 ID 전송. 수정(cancel+re-register) 후 갱신 누락 |
