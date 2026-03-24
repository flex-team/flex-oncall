# 데이터 추출 (Data Export) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 과거 사례

- **근무 기록 다운로드 타임아웃**: consumer → core-api 간 OkHttp 3초 타임아웃으로 `SocketTimeoutException`. 32건 실패 — **버그 (조사 중)** [CI-4121]
