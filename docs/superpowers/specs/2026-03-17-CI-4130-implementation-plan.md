# CI-4130: Implementation Plan

> **설계 문서**: `docs/superpowers/specs/2026-03-17-CI-4130-holiday-work-approval-availability-api.md`
> **작업 브랜치**: `feature/CI-4130-holiday-work-approval-availability`
> **대상 서브모듈**: `flex-timetracking-backend`

## 사전 조건

- `flex-timetracking-backend` 서브모듈에서 작업
- main 브랜치에서 feature 브랜치 생성

## Step 1: 응답 DTO 생성

**파일**: `time-tracking/api/src/main/kotlin/team/flex/tracking/alternativeholiday/dto/AlternativeHolidayApprovalAvailabilityResponse.kt`

```kotlin
data class AlternativeHolidayApprovalAvailabilityResponse(
    val approvalAvailable: Boolean,
)
```

- 단순 data class. 추가 의존성 없음.

## Step 2: 비즈니스 로직 서비스 생성

**파일**: `time-tracking/service/src/main/kotlin/team/flex/tracking/alternativeholiday/CustomerUserAlternativeHolidayApprovalCheckService.kt`

**의존성**:
- `CustomerWorkApprovalRuleLookUpService` — HOLIDAY_WORK 타입 승인 규칙에서 templateKey 조회
- `TrackingApprovalService` — `getApprovalRequestModelBy()` 호출로 승인라인 리졸브

**구현 로직**:
1. `CustomerWorkApprovalRuleLookUpService`로 해당 사용자의 고객사 근무 승인 규칙 조회
2. `WorkScheduleApprovalType.HOLIDAY_WORK` 타입 + `approval.enabled == true` + `approval.templateKey != null` 인 규칙 필터
3. templateKey가 없으면 `false` 반환
4. `TrackingApprovalService.getApprovalRequestModelBy(targetUser, WORK_RECORD, setOf(templateKey))` 호출
5. 결과 판정:
   - `is ResolvedApprovalProcessModel` → 승인자 목록이 비어있지 않은지 확인 → 비어있으면 `false`, 있으면 `true`
   - 그 외 (`InvalidApprovalProcessModel`, `EmptyApprovalProcess`) → `false`

**참고 코드**:
- `WorkScheduleHolidayWorkApprovalCheckerLogic.kt:164-174` — templateKey 조회 패턴
- `TrackingApprovalServiceImpl.kt:29-70` — getApprovalRequestModelBy 사용법
- `UserWorkScheduleV3RegisterMappingServiceImpl.kt` — 리졸브 결과 분기 처리 패턴

## Step 3: 비즈니스 로직 단위 테스트

**파일**: `time-tracking/service/src/test/kotlin/team/flex/tracking/alternativeholiday/CustomerUserAlternativeHolidayApprovalCheckServiceTest.kt`

**테스트 케이스**:

| # | 시나리오 | 기대값 |
|---|---------|--------|
| 1 | HOLIDAY_WORK 승인 규칙이 없음 (templateKey 없음) | `false` |
| 2 | HOLIDAY_WORK 승인 규칙 있으나 `enabled == false` | `false` |
| 3 | 리졸브 결과: `InvalidApprovalProcessModel` | `false` |
| 4 | 리졸브 결과: `EmptyApprovalProcess` | `false` |
| 5 | 리졸브 결과: `ResolvedApprovalProcessModel` (승인자 존재) | `true` |
| 6 | 리졸브 결과: `ResolvedApprovalProcessModel` (승인자 비어있음) | `false` |

**mock 대상**: `CustomerWorkApprovalRuleLookUpService`, `TrackingApprovalService`

## Step 4: Mapping Service 생성

**파일**: `time-tracking/api/src/main/kotlin/team/flex/tracking/alternativeholiday/api/UserAlternativeHolidayActionMappingService.kt`

**역할**: Controller와 Service 사이의 매핑 레이어
- actor/userIdHash에서 사용자 정보 조회
- `CustomerUserAlternativeHolidayApprovalCheckService` 호출
- 결과를 `AlternativeHolidayApprovalAvailabilityResponse`로 변환

**참고 코드**: `UserAlternativeHolidayLookUpMappingService.kt:16-49` — 동일 패턴

## Step 5: Action Controller 생성

**파일**: `time-tracking/api/src/main/kotlin/team/flex/tracking/alternativeholiday/api/UserAlternativeHolidayActionController.kt`

```kotlin
@RestController
@RequestMapping("/action/v2/time-tracking/users/{userIdHash}/alternative-holidays")
class UserAlternativeHolidayActionController(
    private val mappingService: UserAlternativeHolidayActionMappingService,
) {
    @PostMapping("/check-holiday-work-approval-availability")
    fun checkHolidayWorkApprovalAvailability(
        @AuthenticationPrincipal actor: CustomerUserIdentity,
        @PathVariable userIdHash: UserIdentity,
    ): AlternativeHolidayApprovalAvailabilityResponse {
        // 본인만 호출 가능
        if (actor.userId != userIdHash.userId) {
            throw PermissionDeniedException()
        }
        return mappingService.checkHolidayWorkApprovalAvailability(actor, userIdHash)
    }
}
```

**참고 코드**: `UserAlternativeHolidayLookUpController.kt:23-83` — 동일 권한 패턴

## Step 6: 빌드 확인

```bash
cd flex-timetracking-backend
./gradlew :time-tracking:api:compileKotlin :time-tracking:service:test --tests "*AlternativeHolidayApprovalCheck*"
```

## Step 7: operation-note 업데이트

`operation-notes/CI-4130.md`의 미결 사항에 구현 완료 체크.

## 의존성 그래프

```
Step 1 (DTO) ──────────────────────┐
Step 2 (Service) ─── Step 3 (Test) │
                                   ├── Step 4 (Mapping) ── Step 5 (Controller) ── Step 6 (Build)
                                   │
                                   └── Step 7 (Note)
```

- Step 1, 2는 병렬 가능
- Step 3은 Step 2 완료 후
- Step 4는 Step 1, 2 완료 후
- Step 5는 Step 4 완료 후
- Step 6은 Step 5 완료 후
- Step 7은 Step 6 완료 후
