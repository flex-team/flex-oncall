# 채용 (Recruitment) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 이 도메인이 하는 일

채용 공고 관리, 채용사이트 운영, 지원자 파이프라인(접수/서류심사/면접/합격) 관리를 담당한다. `flex-recruiting-backend` 에서 별도 서비스로 운영되며, 별도 데이터베이스(`flex_recruiting`)를 사용한다.

### 핵심 개념

- **채용사이트(`site`)**: 회사별 채용 페이지. 고유 subdomain을 가지며, subdomain 변경은 운영팀 수동 승인이 필요하다.
- **subdomain 변경 요청(`site_subdomain_change`)**: 고객이 신청 → 검토중 상태 → 운영팀 승인/반려. `#alarm-recruiting-operation` 슬랙 채널로 알림이 발송된다.

### 주요 흐름

1. **subdomain 변경**: 고객 신청 → 슬랙 알림 발송(`#alarm-recruiting-operation`) → 온콜 담당자가 적절성 확인 → Operation API로 승인/반려

### 비즈니스 규칙

- **subdomain 승인은 수동**: 자동 승인이 아니라 운영팀이 도메인명 적절성을 확인한 후 수동 처리한다. 알림 채널 모니터링을 놓치면 방치되는 구조.
- **승인/반려 API**: raccoon Operation API를 통해 처리. Swagger에서 `recruiting` 태그로 확인 가능.

### 자주 혼동되는 것들

- **domain-map.ttl에서의 위치**: 채용 도메인은 별도 도메인 블록이 없고, 과거 이슈(CI-4170)는 `:account`에 매핑되어 있다. 채용 관련 이슈가 인입되면 `flex-recruiting-backend` 서브모듈을 확인해야 한다.
- **채용 vs 계정**: subdomain 변경 요청은 채용 도메인이지만, 로그인/SSO 관련은 계정 도메인이다.

### 구현 특이사항

- **알림 채널 의존**: `#alarm-recruiting-operation` 슬랙 채널 알림에 의존하는 운영 프로세스. 알림이 발송되지 않으면 요청을 인지할 수 없다.
- **독립 서비스**: 다른 flex 백엔드와 달리 별도 서비스 + 별도 DB 구조. 코어 인프라(인증, 회사 설정 등)만 공유.

---

## 데이터 접근

```sql
-- 채용사이트 subdomain 변경 요청 조회
SELECT * FROM flex_recruiting.site_subdomain_change
WHERE customer_id = ?
ORDER BY created_at DESC;
```

## 과거 사례

- **subdomain 변경 검토중 방치**: 온콜 담당자가 `#alarm-recruiting-operation` 알림을 모니터링하지 않아 9일간 방치. operation API로 즉시 승인 처리 — **운영 요청** [CI-4170]
