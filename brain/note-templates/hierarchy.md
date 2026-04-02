# 관계/계층형 추가 섹션

> **해당 도메인**: 조직 관리, 인사발령, 권한, 계정/구성원
>
> **특성**: 조직 트리, 권한 그래프 등 관계가 동작을 결정. 한 노드 변경이 하위에 전파.
>
> **핵심**: 부서 트리는 `parentDepartmentId` 기반 + 시간축(TimeSeries) 관리.
> 숨김 부서(`isVisible=false`)의 자식은 상위로 올라감.
> 발령은 별도 상태 머신 (`PRE_PROCESSING → PROCESSING → WAITING/DONE/ERROR/CANCEL`).
> 권한 캐시 6종, 일부 TTL 없음 — Kafka 이벤트 기반 갱신 + 5분 cron 보정.

## 추가 섹션 (영향 범위 ~ 해결 사이에 삽입)

```markdown
## 전파 범위

- 변경된 노드의 하위 영향 범위 (하위 조직, 소속 구성원)
- 시간축(TimeSeries) 기간 충돌 여부 — 부모-자식 간 유효기간 제약 위반
- 다른 도메인으로의 Kafka 이벤트 전파 확인:
  - 부서 변경 → `EVENT_FLEX_DEPARTMENT` → permission-backend
  - 직위 변경 → `EVENT_FLEX_USER_POSITION` → permission-backend
  - 퇴직 → `EVENT_FLEX_EMPLOYEE_STATUS_V2` → permission + checklist + offboarding
  - 발령 → `EVENT_FLEX_USER_DATA_CHANGE` → change-history + search
- 발령 상태 확인: `ERROR`/`PROCESSING`에서 멈춘 경우, 미래 발령(`WAITING`) 미적용 여부

## 겸직/복수 소속

- 겸직 사용자가 관련되어 있는가
- `isPrimary` 플래그가 어느 쪽 customer에 있는지 — 권한 체크 기준
- 계열사 연결/해제 시 workspace 통합 상태 확인
- `userFlexUsagePeriod.to` — 퇴사 예정일이 설정된 겸직자의 활성 판단

## 캐시/동기화

- 권한 캐시 6종 중 TTL 없는 캐시는 이벤트 기반으로만 갱신됨
  - Kafka consumer lag 확인 (consumer 그룹: `permission-*-event-handler`)
  - 5분 주기 cron 보정(`ResolveVerifyRunner`) — 5분 이상 미반영이면 cron 자체 실패 의심
- 발령 적용 후 다른 도메인(근태/페이롤)에 반영 안 됨 → `EVENT_FLEX_USER_DATA_CHANGE` 발행 확인
- 사용자에게 재로그인/새로고침 안내 필요 여부
```
