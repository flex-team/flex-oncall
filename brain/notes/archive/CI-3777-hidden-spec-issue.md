# CI-3777: 연차촉진 히든 스펙으로 인한 알림/화면 불일치

## 문제 상황

**Customer ID**: 60425
**User ID**: 294613
**발생 시점**: 2026-01-16 ~ 현재

### 증상
- 알림: "구성원 연차사용계획서 작성 필요" 매일 수신
- 화면: 기본 화면에서 해당 구성원 미노출
- 회피책: '관리작성 기간' 필터 선택 시 보임

## 원인 분석

### 시간 흐름
1. **2026-01-05**: 자동 촉진 (id: 399100)
   - 관리자(902341)가 대신 작성 (written_by_manager=true)
   - 반려됨 (REJECTED)

2. **2026-01-16**: 재촉진 (id: 400590)
   - PENDING_WRITE 상태
   - 미작성

3. **2026-01-26**: 별도 촉진 (id: 401842)
   - 본인(294613)이 작성
   - 승인됨 (APPROVED)

### 히든 스펙 적용

**PR**: https://github.com/flex-team/flex-timetracking-backend/pull/750
**적용 시점**: 2025-07-09 (CI-1892 대응)
**파일**: `time-off/service/.../AnnualTimeOffPromotionApplicationServiceImpl.kt:215-225, 302-305`

**로직**:
```kotlin
// 관리자에 의해 종료된 내역이 있는 경우,
// 작성 기한이 지난 내역은 목록에 포함하지 않습니다.
val writtenByManagerHistories = boostHistories.filter {
    it.written && (it.completeActorId != user.userId)
}

if (writtenByManagerHistories.any {
    it.dissipateType === boostHistory.boostType.dissipateType &&
    it.expirationDate == boostHistory.dissipatedAt &&
    contextStatus !== AnnualTimeOffPromotionHistoryContextStatus.NONE
}) {
    null  // 화면에서 제외
}
```

**적용 결과**:
- id: 399100 (관리자 작성)이 `writtenByManagerHistories`에 포함
- id: 400590과 같은 소멸일(2026-07-05)이므로 필터링
- displayStatus 필터 적용 시만 보임

### 알림 발송 로직

**파일**: `time-off/service/.../AnnualTimeOffPromotionNotificationServiceImpl.kt:127-194`

**조건** (Line 145-148):
```kotlin
val inManagerWritePeriodHistory = histories
    .filter { history ->
        !history.canceled &&  // 취소되지 않음
        managerWritePeriod(history, evaluationDate)  // 관리자 작성 기간
    }
```

**불일치 원인**: 알림 발송 로직은 히든 스펙 필터링 미적용

## 해결 방법

### 단기 (고객 대응)
```sql
-- id: 400590 취소 처리
UPDATE annual_time_off_boost_history
SET status = 'CANCELED',
    canceled_at = NOW(),
    canceled_user_id = 0,
    last_modified_date = NOW(),
    last_modified_by = 'operation'
WHERE id = 400590;

-- (선택) id: 399100 취소 처리
UPDATE annual_time_off_boost_history
SET status = 'CANCELED',
    canceled_at = NOW(),
    canceled_user_id = 0,
    last_modified_date = NOW(),
    last_modified_by = 'operation'
WHERE id = 399100;
```

### 장기 (근본 원인)
1. **재촉진 시 이전 미작성 문서 자동 취소**
2. **알림 발송 로직에 히든 스펙 필터링 적용**
3. **화면에 히든 스펙 적용 여부 표시** (경고 메시지)

## 관련 이슈

- CI-1892: 히든 스펙 핫픽스 원본 이슈
- CI-2487, CI-3497, CI-1942, CI-1977: 유사 패턴
- [CI-3932](./CI-3932.md): 등기임원(연차 미지급 대상)에게 연차 사용 계획서 작성 요청 표시 — 촉진 대상 아닌 구성원에게 촉진 알림 표시
