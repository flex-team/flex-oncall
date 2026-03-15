# CI-3809: 월차 2차 완료 후에도 1차 미작성으로 인한 알림 지속 발송

## 증상

### 고객 문의
- **회사**: (주)시큐리온 (Customer ID: 211769)
- **메일 수신자**: ksj7034@securion.co.kr (user_id: 835378)
- **증상**: 관리자에게 "1명 구성원의 연차 사용 계획 대리 작성이 요청되었어요" 이메일 수신

### 핵심 불일치

| 구분 | 내용 |
|------|------|
| **이메일** | "**1명** 구성원의 연차 사용 계획 대리 작성이 요청되었어요" |
| **화면 (연차 촉진 내역)** | 작성 대기 상태인 사람 **0명** (월차 2차 완료 2명만 표시) |

→ 알림은 1명이라고 보내는데, 화면에서는 작성이 필요한 사람이 없음

---

## 결론 요약

### 발견된 문제 3가지

| # | 문제 | 영향 | 근본 원인 |
|---|------|------|----------|
| **1** | **boosted_at UTC 저장 vs 조회 범위 타임존 불일치** | 1/1 촉진 건이 목록에서 누락 | 저장은 UTC, 조회는 LocalDate 기준 연도 시작으로 계산 |
| **2** | **MONTHLY/MONTHLY_FINAL 간 연동 없음** | 2차 완료 후에도 1차 미작성 알림 지속 | 1차/2차가 완전히 독립적으로 동작 |
| **3** | **searchBoostedAtFrom 파라미터 미사용** | API 파라미터를 조정해도 조회 범위가 변하지 않음 | `getAllBy`가 baseDate 연도 기준으로 자동 계산 |

### 이 이슈에서 일어난 일

```
입사일 4/1 → 소멸일 다음해 4/1 → MONTHLY 촉진 정확히 1/1
→ KST 1/1 08:00 = UTC 12/31 23:00 → DB에 전년도로 저장 (문제 1)
→ 목록 조회 시 2026년 범위에서 MONTHLY 누락, MONTHLY_FINAL만 표시
→ 한편 MONTHLY_FINAL은 완료됐지만 MONTHLY는 미작성 상태로 방치 (문제 2)
→ 알림 로직은 MONTHLY 미작성을 감지하여 매일 관리자에게 알림 발송
→ 관리자는 화면에서 작성 대기 건을 찾을 수 없음
```

---

## 데이터 확인

### 로그 확인 결과

**알림 발송 로그** (2026-02-05 08:43):
```
[스마트 연차 촉진] 연차 사용 계획 작성 필요 구성원 (customerId=211769)
inManagerWritePeriodHistoryCount: 1
taskKeys: [01kdvc2084vry4axb61z4qzxqs]
```

→ "1명"의 정체: **user 858689 (springsandy@securion.co.kr)**의 **월차 1차(MONTHLY), PENDING_WRITE**

### 촉진 목록 조회 로그

완료 상태 2명만 반환:
- `01kffp08ah8b21s8wwsgw6v3fd` → 211769, 858689, MONTHLY_FINAL, COMPLETE
- `01ke0hjk9df955hpd81745njak` → 211769, 858684, MONTHLY_FINAL, COMPLETE

### user 858689의 촉진 이력

| taskKey | boost_type | status | 비고 |
|---------|-----------|--------|------|
| `01kdvc2084vry4axb61z4qzxqs` | **MONTHLY (월차 1차)** | **PENDING_WRITE** | 미작성 → 알림의 원인 |
| `01kffp08ah8b21s8wwsgw6v3fd` | MONTHLY_FINAL (월차 2차) | COMPLETE | 이미 완료됨 |

→ **월차 2차는 완료됐지만, 월차 1차가 미작성 상태로 남아있어 알림이 계속 발송됨**

---

## 원인 분석

### 근본 원인 1: boosted_at UTC 저장 vs 조회 범위의 타임존 불일치

**목록에서 MONTHLY가 안 보이는 직접적 원인.**

#### 저장 로직 (`AnnualTimeOffPromotionRequestToWriteDocumentServiceImpl.kt:61`)

```kotlin
val fixedBoostedAt = requestTime
    .withZoneSameInstant(TimeZoneConstants.ZONE_UTC)  // KST 08:00 → UTC 23:00 (전날)
    .toLocalDateTime()                                 // 타임존 정보 손실
```

```
Cron 실행: 2026-01-01 08:00:00 KST
→ UTC 변환: 2025-12-31 23:00:00
→ DB 저장: 2025-12-31 23:00:00 (의도적 UTC 저장, 코드 주석에 명시)
```

#### 조회 로직 (`AnnualTimeOffPromotionHistoryServiceImpl.kt:getAllBy`)

```kotlin
val boostedAtFrom = DateUtil.firstDayOfYear(baseDate).atStartOfDay()  // 2026-01-01 00:00:00
val boostedAtTo = boostedAtFrom.plusYears(1)                           // 2027-01-01 00:00:00
```

#### 불일치

저장은 UTC로, 조회 범위는 LocalDate 기준(타임존 불명확)으로 계산 → **KST 1/1 08:00 촉진이 UTC 기준 전년도(12/31 23:00)로 저장되어 연도 범위에서 제외**

#### 재현 조건

**입사일이 4/1인 구성원**에서 반드시 재현:
```
입사일: 2025-04-01
→ 월차 소멸일: 2026-04-01 (입사일 + 1년)
→ MONTHLY(1차) 촉진일: 2026-01-01 (소멸 3개월 전)
→ Cron: 2026-01-01 08:00 KST = 2025-12-31 23:00 UTC
→ DB: 2025-12-31 23:00:00
→ 조회 범위: >= 2026-01-01 00:00:00
→ 범위 밖 → 누락
```

**정확히 1/1에 촉진이 실행되는 경우만 발생** (KST 1/1 08:00 = UTC 12/31 23:00으로 연도가 바뀜). 1/2 이후 촉진은 UTC로도 같은 연도이므로 문제 없음.

### 근본 원인 2: MONTHLY/MONTHLY_FINAL이 독립적으로 동작

**알림이 계속 발송되는 원인.**

코드 분석 결과, 세 곳 모두에서 **1차/2차 간 연동 로직이 없음**:

| 영역 | 로직 유무 | 설명 |
|------|----------|------|
| **알림 발송** (`managerWritePeriod`) | ❌ | 해당 이력의 `written`, 기한만 체크. 같은 유저의 다른 타입 완료 여부 미확인 |
| **화면 필터링** (`getUserAnnualTimeOffBucketWithBoostHistories`) | ❌ | MONTHLY_FINAL 완료 시 MONTHLY 제외 로직 없음 |
| **촉진 완료 처리** (`complete`) | ❌ | MONTHLY_FINAL 완료 시 MONTHLY 자동 취소 로직 없음 |

### 왜 알림에서는 MONTHLY가 포함되는가?

알림과 목록이 **서로 다른 DB 쿼리**를 사용:

| | 알림 발송 | 목록 조회 |
|---|---|---|
| 메서드 | `getAllOfNotWrittenStatusBy()` | `getAllBy()` |
| DB 쿼리 | `findAllByCustomerIdAndStatusIn` | `findAllByCustomerIdAndUserIdAnd`**`BoostedAt`** |
| boosted_at 필터 | **없음** | **있음** (연도 범위) |
| 필터링 | 메모리에서 `written.not()` | DB에서 `boosted_at >= 2026-01-01` |

알림은 customerId + status로만 전체 조회 → UTC `2025-12-31 23:00:00` MONTHLY도 포함됨.
목록은 boosted_at 연도 범위 필터 적용 → MONTHLY 제외됨.

### 알림 발송 조건 (`managerWritePeriod`)

```kotlin
// AnnualTimeOffPromotionNotificationServiceImpl.kt:192-201
fun managerWritePeriod(history, baseDate): Boolean {
    val notWritten = history.written.not()                                 // ← 미작성
    val passedMandatorySubmission = baseDate >= history.shouldUserWriteBy  // ← 사용자 기한 경과
    val notPassedManagerWritePeriod = baseDate < history.shouldManagerWriteBy // ← 관리자 기한 미경과
    return notWritten && passedMandatorySubmission && notPassedManagerWritePeriod
}
```

858689의 MONTHLY 이력: written=false, 기한 조건 충족 → **알림 대상으로 판정**

### 스펙 관점에서의 문제

법적 촉진 프로세스:
```
MONTHLY (1차): 소멸 3개월 전 → 구성원에게 사용 계획 작성 요청
MONTHLY_FINAL (2차): 소멸 1개월 전 → 1차 미응답분에 대해 관리자가 사용 시기 지정
```

**MONTHLY_FINAL은 MONTHLY의 후속 단계**. 2차에서 관리자가 사용 시기를 지정 완료했으면 법적 촉진 절차는 이미 이행된 것.
따라서 1차가 미작성이어도 2차가 완료됐으면 1차에 대한 알림은 **불필요하며 스펙에 맞지 않음**.

### 화면에서 1차가 안 보이는 이유

**원인: targetBuckets에 MONTHLY 버킷이 없어서 "소멸일 변경된 문서" 필터에 걸림** (`ApplicationServiceImpl.kt:243-256`)

```kotlin
if (targetBuckets.none {
    it.expirationDate == boostHistory.dissipatedAt &&       // 2026-04-01
    it.dissipateType === boostHistory.boostType.dissipateType  // MONTHLY
}) {
    logger.info { "[연촉][...] 소멸일 변경된 문서 숨김" }
    return@mapNotNull null  // ← 목록에서 제외
}
```

#### targetBuckets 구성 과정

```
1. getBoostableBuckets(calculationBaseDate=2026-02-05) 호출
2. getUserAnnualTimeOffBuckets로 월차 부여 이력 조회
3. toBucketsWithDissipateType으로 dissipateType 결정:
   - timeRound가 lastMonthlyTimeRound ± 1 범위 → MONTHLY_FINAL
   - 그 외 → MONTHLY
4. 필터링 후 targetBuckets 구성
```

**결과**: targetBuckets = `[{MONTHLY_FINAL, 2026-04-01}]` (MONTHLY 버킷 없음)

→ MONTHLY 촉진 이력(`dissipateType=MONTHLY, dissipatedAt=2026-04-01`)이 매치 실패 → 제외

#### dissipateType은 시간에 따라 변하지 않음

- dissipateType은 `timeRound`(월차 부여 차수)에 의해 **배정 시점에 고정**
- MONTHLY(timeRound 1~10)와 MONTHLY_FINAL(timeRound 11~12)은 독립적
- 시간 경과나 calculationBaseDate 변경으로 전환되지 않음

#### MONTHLY 버킷이 없는 가능성

- 정책 변경으로 해당 timeRound의 월차 부여가 변경/소멸
- 입사일 변경으로 버킷 재계산 시 누락
- `getUserAnnualTimeOffBuckets` 조회에서 해당 버킷이 제외

→ **858689의 월차 부여 이력(버킷) DB 데이터 확인 필요**

#### 히든 스펙(관리자 작성 필터)은 해당 안 됨

- MONTHLY_FINAL 완료가 writtenByManagerHistories에 들어가더라도
- `MONTHLY_FINAL === MONTHLY` 비교가 false이므로 매치되지 않음

#### 확정된 원인: boosted_at UTC 저장으로 인한 연도 경계 문제

MONTHLY의 DB 데이터:
```
boosted_at = 2025-12-31 23:00:00 (UTC) = 2026-01-01 08:00:00 (KST)
```

`getAllBy` 쿼리 범위 계산 (`AnnualTimeOffPromotionHistoryServiceImpl.kt`):
```kotlin
val boostedAtFrom = DateUtil.firstDayOfYear(baseDate).atStartOfDay()  // 2026-01-01 00:00:00
val boostedAtTo = boostedAtFrom.plusYears(1)                           // 2027-01-01 00:00:00
```

```
DB 쿼리: boosted_at >= '2026-01-01 00:00:00' AND boosted_at < '2027-01-01 00:00:00'
MONTHLY:       2025-12-31 23:00:00 → 범위 밖! (DB 조회에서 제외)
MONTHLY_FINAL: 2026-01-21 07:06:18 → 범위 안 (조회됨)
```

**`searchBoostedAtFrom` 파라미터를 변경해도 소용없음** - 이 값은 실제 DB 쿼리에 사용되지 않고, `searchBoostedAtTo`의 연도 기준으로 범위가 자동 결정됨.

**결과**: 같은 유저의 MONTHLY와 MONTHLY_FINAL이 UTC 저장으로 인해 서로 다른 연도 범위에 분리되어, 한 번의 조회로 둘 다 볼 수 없음.

#### Operation API로 확인

```
POST /api/operation/v2/time-off/annual-time-off-promotion/customers/211769/search
```

```json
{
  "actorUserId": 835378,
  "searchBoostedAtFrom": "2025-01-01",
  "searchBoostedAtTo": "2026-03-01",
  "targetUsers": [858689]
}
```

→ MONTHLY_FINAL만 반환되고 MONTHLY는 빠짐 (확인 완료)

---

## 해결 방안

### 단기: 해당 촉진 이력 취소

```sql
-- 858689의 MONTHLY(1차) 미작성 이력 취소
UPDATE annual_time_off_boost_history
SET status = 'CANCELED',
    updated_at = NOW()
WHERE customer_id = 211769
  AND task_key = '01kdvc2084vry4axb61z4qzxqs';
```

### 장기: 3가지 문제에 대한 해결

#### 문제 A: boosted_at 저장/조회 타임존 불일치

`getAllBy`에서 조회 범위를 UTC 기준으로 보정하거나, 저장 시 KST 기준으로 변경:

```kotlin
// Option A-1: 조회 범위를 UTC 기준으로 보정
val boostedAtFrom = DateUtil.firstDayOfYear(baseDate)
    .atStartOfDay()
    .atZone(TimeZoneConstants.ZONE_SEOUL)
    .withZoneSameInstant(TimeZoneConstants.ZONE_UTC)
    .toLocalDateTime()
```

#### 문제 B: MONTHLY_FINAL 완료 시 MONTHLY 자동 처리

**Option B-1: MONTHLY_FINAL 완료 시 미작성 MONTHLY 자동 취소**
- `complete()` 메서드에서 같은 유저/소멸일의 MONTHLY PENDING_WRITE를 CANCELED로 변경
- 장점: 깔끔한 데이터 정리
- 단점: 기존 데이터 마이그레이션 필요

**Option B-2: 알림 발송 로직에서 필터링 추가**
- `sendManagerRemindSubmissionDueDateMessage`에서 같은 유저의 MONTHLY_FINAL COMPLETE 여부 확인 후 MONTHLY 제외
- 장점: 기존 데이터 영향 없음
- 단점: 근본적 해결이 아님

#### 문제 C: searchBoostedAtFrom이 실제로 사용되지 않음

`getAllBy`에서 `baseDate`의 연도 시작으로 자동 계산하므로, API 파라미터 `searchBoostedAtFrom`이 무시됨. 이 파라미터를 실제 쿼리에 반영하거나, API 명세에서 제거 필요.

**권장: 단기 취소 + 장기 Option B-1 + 문제 A 수정**

---

## 관련 코드 위치

| 항목 | 위치 |
|------|------|
| 알림 대상 판정 | `AnnualTimeOffPromotionNotificationServiceImpl.kt:145-147, 192-201` |
| 알림 로그 | `AnnualTimeOffPromotionNotificationServiceImpl.kt:149-155` |
| 화면 필터링 | `AnnualTimeOffPromotionApplicationServiceImpl.kt:167-173, 236-333` |
| 촉진 완료 처리 | `AnnualTimeOffPromotionHistoryServiceImpl.kt:271-307` |
| 촉진 타입 정의 | `AnnualTimeOffPromotionType.kt:7-15` |

## 유사 이슈

- **CI-3777**: 히든 스펙으로 인한 알림/화면 불일치
- **CI-1892, CI-2487, CI-3497**: 무효된 촉진 잔존으로 알림 발송
- [CI-3932](./CI-3932.md): 등기임원(연차 미지급 대상)에게 연차 사용 계획서 작성 요청 표시 — 촉진 알림 대상 필터링 관련

---

## 작성 정보

- **작성일**: 2026-02-06
- **상태**: 원인 파악 완료, 해결 방안 결정 필요
