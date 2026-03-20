# MEMO-20260320: 스마트 연차 촉진 크론 간헐적 타임아웃

## 증상

- `time-tracking-cron` prod에서 스마트 연차 촉진 크론 실행 중 간헐적 ERROR 발생
- 3월 내 2건 확인:
  - 2026-03-12 08:32 KST — `customerId=131240`, `SocketException: Socket closed`
  - 2026-03-20 08:35 KST — `customerId=221572`, `IOException: Canceled`
- traceId (03-20): `34fc142ccbf35c67e8e656498c6ef8a0`
- traceId (03-12): `b673f7c3481d1cf0f7adf64655d18dff`

## 원인 분석

- 크론이 전체 회사를 순회하며 원격 서비스(알림/pavement 등)를 OkHttp로 호출
- 약 35분간 156,835건 로그 발생 (03-20 기준)
- 대량 순회 중 간헐적 네트워크 타임아웃 → `FlexRemoteUnknownStateException: java.io.InterruptedIOException: timeout`
- 특정 회사 문제가 아닌 일시적 네트워크 불안정

## 영향범위

- **ERROR**: 1건/일 (해당 회사만 촉진 알림 발송 실패)
- **WARN**: 677건 — 그룹사 입사일 불일치 경고 (로직에 영향 없음)
- **INFO**: 156,157건 — 정상 처리
- 실제 촉진 알림 발송 건수가 전 회사 0건 (`NOTI_REMIND_*` 모두 0) → 실질 영향 없음
- 다음 날 크론에서 재처리되므로 누락 우려 낮음

## 해결

- 별도 조치 불필요 (간헐적 타임아웃, 실질 영향 없음)

## 비고

- 관련 클래스: `AnnualTimeOffPromotionScheduler`, `AnnualTimeOffPromotionApplicationServiceImpl`, `AnnualTimeOffPromotionSpecificationImpl`
- 로거: `t.f.t.a.c.TimeTrackingCronScheduler`, `t.f.t.p.AnnualTimeOffPromotionScheduler`
- 빈도가 증가하면 OkHttp timeout 설정 또는 재시도 로직 검토 필요

## 각주

- Slack 에러 알림 스레드 (최초 인지): https://flex-cv82520.slack.com/archives/C03DDNUEV29/p1773963481406309
  - 2026-03-20 08:38 KST, `TimeTrackingServer` 봇이 ERROR 로그 발생 알림 발송
  - cron ERROR 1건 (`AnnualTimeOffPromotionScheduler`) + API ERROR 273건 (`ServletWebExceptionHandler` 272건, `AbstractWorkScheduleRegisterService` 1건)

## Claude 활동 로그

| 시각(KST) | 활동 |
|-----------|------|
| 2026-03-20 | traceId로 prod cron 로그 조사, 에러 1건 + WARN 677건 확인, 영향범위 없음 판단 |
