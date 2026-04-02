# 상태머신형 추가 섹션

> **해당 도메인**: 승인, 워크플로우, 전자계약, 체크리스트
>
> **특성**: 상태 전이(생성→대기→승인→완료)로 동작. 비정상 전이가 문제의 원인.
>
> **핵심**: 전이 구현이 도메인마다 다르다.
> - flow: 전이 규칙 레지스트리 (`IssueStatusTransitionPolicyRegistry`)
> - digicon: enum 내 인라인 가드 (`signable()`, `cancelable()` — 실패 시 silent skip)
> - TT 승인: 이벤트 소싱 (`v2_time_tracking_approval_event` — 마지막 이벤트가 핵심)
> - core 승인: 분산 락 + 단일 트랜잭션 (승인 + 데이터 반영이 한 트랜잭션)

## 추가 섹션 (영향 범위 ~ 해결 사이에 삽입)

```markdown
## 현재 상태 확인

- 대상 건의 현재 상태와 전이 이력
  - digicon: `progress_status` 컬럼 + `digicon_party_history` 테이블 (IP 주소 포함)
  - TT 승인: `v2_time_tracking_approval_event` 이벤트 체인 해석 (마지막 이벤트가 핵심)
  - core 승인: `ApprovalLineStatus` + 분산 락 상태
- 비정상 전이 여부 — 가드 로직을 우회한 DB 직접 수정 흔적
- 외부 결재 시스템 호출 실패 여부 (TT 승인: 예외 클래스 5종 구분)

## 차단 범위

- 이 건이 막혀서 진행 못하는 후속 업무/프로세스
- 영향받는 사용자 수/범위
- 우회 가능 여부 — 단, silent skip 패턴에 주의 (digicon 취소 등)

## 상태 보정 시 주의

- DB 직접 상태 변경 시 후속 트리거가 발동하지 않음:
  - digicon: Todo 상태 불일치 + 알림 누락 (afterCommit 콜백 미실행)
  - TT: Kafka 이벤트 미발행 + 외부 결재 시스템 상태 불일치
  - core: approve() 내 데이터 반영 미실행
- 이력/감사 로그 확인:
  - digicon: `digicon_party_history` (IP 포함 — 전자서명 법적 효력)
  - TT: `v2_time_tracking_approval_event` (referenceId로 체인 추적)
  - flow Issue: 별도 히스토리 없음 — updatedBy만 기록
```
