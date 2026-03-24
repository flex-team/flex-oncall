# 출퇴근 (Work Clock) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

- 서비스: `time-tracking-api` (K8s label: `flex-prod-prod-time-tracking-api`)
- 근무 위젯 편집기 요청 시 사용된 IP → Kibana access log에서 확인
