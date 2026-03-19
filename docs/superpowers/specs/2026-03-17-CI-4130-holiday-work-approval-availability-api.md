# CI-4130: 휴일대체 사후신청 승인 가능 여부 확인 API

> **Linear**: [CI-4130](https://linear.app/flexteam/issue/CI-4130)
> **상태**: 설계 확정
> **날짜**: 2026-03-17

## 배경

휴일대체 사후신청 버튼이 `original-holiday-info` API 응답 기반으로 노출되는데, 이 API는 승인라인 유효성을 체크하지 않는다. 1차 조직장이 없는 구성원 등 승인라인이 깨진 경우에도 버튼이 노출되어, 신청이 된 것처럼 보이지만 실제로는 처리되지 않는 문제가 발생한다.

`original-holiday-info`는 날짜 범위 기반 API로 화면 전환마다 호출되므로, 승인 가능 여부(범위 무관, 1회 호출이면 충분)를 여기에 추가하면 불필요한 리졸브가 반복된다. 따라서 별도 Action API로 분리한다.

## API 스펙

### 엔드포인트

```
POST /action/v2/time-tracking/users/{userIdHash}/alternative-holidays/check-holiday-work-approval-availability
```

### 파라미터

| 구분 | 이름 | 타입 | 설명 |
|------|------|------|------|
| Path | `userIdHash` | `UserIdentity` | 대상 구성원 (본인만 호출 가능) |
| Body | 없음 | - | - |

### 응답

```json
{
  "approvalAvailable": boolean
}
```

### 판단 로직

| 리졸브 결과 | `approvalAvailable` | 의미 |
|---|---|---|
| `ResolvedApprovalProcessModel` (승인자 있음) | `true` | 승인라인 정상 → 사후신청 가능 |
| `ResolvedApprovalProcessModel` (승인자 비어있음) | `false` | 방어 로직 |
| `InvalidApprovalProcessModel` | `false` | 승인라인 깨짐 (1차 조직장 없음 등) |
| `EmptyApprovalProcess` | `false` | 승인 불필요 = 휴일대체 승인 설정 없음 |
| templateKey 없음 | `false` | 휴일근무 승인 설정 자체가 없음 |

> 휴일대체는 반드시 승인이 필요한 프로세스이므로, `ResolvedApprovalProcessModel`에 실제 승인자가 존재하는 경우**만** `true`.

### 권한

- `@AuthenticationPrincipal actor`와 `@PathVariable userIdHash`가 일치할 때만 응답
- 불일치 시 `PermissionDeniedException`

## 내부 흐름

```
ActionController
  → MappingService
    → CustomerUserAlternativeHolidayApprovalCheckService
      1. CustomerWorkApprovalRuleLookUpService로 HOLIDAY_WORK 타입 승인 규칙 조회
      2. templateKey 추출 (없으면 false 반환)
      3. TrackingApprovalService.getApprovalRequestModelBy(user, WORK_RECORD, {templateKey}) 호출
      4. 결과 판정:
         - ResolvedApprovalProcessModel + 승인자 존재 → true
         - 그 외 → false
```

## 파일 구조

### 신규 파일

```
time-tracking/api/src/main/kotlin/team/flex/tracking/alternativeholiday/
├── api/
│   ├── UserAlternativeHolidayActionController.kt         — Controller
│   └── UserAlternativeHolidayActionMappingService.kt     — DTO 변환
└── dto/
    └── AlternativeHolidayApprovalAvailabilityResponse.kt — 응답 DTO

time-tracking/service/src/main/kotlin/team/flex/tracking/alternativeholiday/
└── CustomerUserAlternativeHolidayApprovalCheckService.kt — 비즈니스 로직
```

### 참조하는 기존 코드

| 파일 | 용도 |
|------|------|
| `TrackingApprovalService.getApprovalRequestModelBy()` | 승인라인 리졸브 |
| `CustomerWorkApprovalRuleLookUpService` | HOLIDAY_WORK templateKey 조회 |
| `TrackingApprovalCategoryType.WORK_RECORD` | 승인 카테고리 |
| `WorkScheduleApprovalType.HOLIDAY_WORK` | 승인 규칙 타입 필터 |

## 테스트 전략

- `CustomerUserAlternativeHolidayApprovalCheckService` 단위 테스트:
  - templateKey 없음 → false
  - `InvalidApprovalProcessModel` 반환 → false
  - `EmptyApprovalProcess` 반환 → false
  - `ResolvedApprovalProcessModel` (승인자 있음) → true
  - `ResolvedApprovalProcessModel` (승인자 비어있음) → false
