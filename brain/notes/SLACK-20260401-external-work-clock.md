# SLACK-20260401: 외부출퇴근(SECOM) Operation API 호출 시 200 응답이지만 이벤트 미생성

> **상태**: 진행 중 — 2026-04-02

## 증상

- **문제 정의**: raccoon 프록시를 통한 외부출퇴근 이벤트 등록 API 호출 시 200 응답을 받지만, 실제 이벤트가 생성되지 않음
- **회사**: Customer ID 1383
- **요청자**: 김상준 (캡콤 테스트 담당)[^1]
- **대상자**: userId 124035
- **영향 범위**: dev 환경 — 캡콤 연동 테스트 차단
- **문제 시점**: 2026-04-01 11:32 KST
- 문의 내용:
  1. raccoon에서 외부출퇴근 이벤트 등록 API를 호출하면 200이 반환되지만 이벤트가 생성되지 않음[^1]

### 호출 정보

- **API**: `POST /api/operation/v2/time-tracking/external-work-clock/customers/1383/providers/SECOM/events`
- **경유**: `flex-raccoon.dev.grapeisfruit.com/proxy/time-tracking/...`[^2]
- **요청 Body**:
```json
{
  "userId": 124035,
  "eventType": "START",
  "loggedAt": "2026-04-01T02:00:00.000Z",
  "syncedAt": "2026-04-01T02:00:00.000Z",
  "eventCreatedAt": "2026-04-01T02:00:00.000Z"
}
```

---

## 현재까지 파악된 내용

### 조사 과정

> 💡 **판단 흐름**: access log 부재 확인 → 엔드포인트 배포 위치 확인 → raccoon 라우팅 불일치 특정
> → 1단계: access log에서 요청 도달 여부 확인[^3]
> → 2단계: 엔드포인트 코드 위치 특정[^4]
> → 3단계: 배포 모듈 매핑 확인[^5]
> → 결론: raccoon 프록시 라우팅 대상과 엔드포인트 배포 앱 불일치

#### 1단계: access log 확인 — 요청이 TT 백엔드에 도달했는가?

OpenSearch `flex-app.be-access-2026.04.01` 인덱스에서 2026-04-01 11:25~11:40 KST 범위를 검색했다.[^3]

| 검색 대상 | 검색 조건 | 결과 |
|-----------|----------|------|
| TT API 서버 access log | `json.path` = "external-work-clock" | **0건** |
| TT API 서버 전체 access log | app = flex-dev-dev-time-tracking-api | 803건 (정상 동작 중) |
| TT Cron 서버 access log | app = flex-dev-dev-time-tracking-cron | **0건** (전 기간 통틀어 0건) |
| TT Cron 서버 app log | external-work-clock 키워드 | **0건** |
| Raccoon 서비스 로그 | app = *raccoon* | **0건** (OpenSearch에 로그 자체 없음) |

> 💡 **핵심 발견**: TT API 서버는 해당 시간대에 803건의 access log를 정상 기록 중이었지만, `external-work-clock` 경로의 요청은 단 한 건도 없었다. Cron 서버에도 해당 요청의 흔적이 전혀 없다.[^3]

#### 2단계: 엔드포인트 코드 위치 확인

해당 API의 컨트롤러는 `external-work-clock:operation-api` 모듈에 정의되어 있다.[^4]

```
ExternalWorkClockEventOperationController
├── @RequestMapping("/api/operation/v2/time-tracking/external-work-clock")
└── registerProvider()
    └── @PostMapping("/customers/{customerId}/providers/{providerType}/events")
```

#### 3단계: 모듈 배포 매핑 확인

`applications/` 디렉토리의 `build.gradle.kts` 를 확인한 결과:[^5]

| 앱 | `external-work-clock:operation-api` 포함 | `external-work-clock:api` 포함 |
|----|:---:|:---:|
| **applications/api** (API 서버) | ❌ | ✅ |
| **applications/cron** (Cron 서버) | ✅ | ❌ |

`operation-api` 모듈은 **cron 앱에만 배포**되어 있으며, 이것은 의도된 구조이다.[^6]

---

### 원인 확정

김영준님이 cron 서버 로그에서 원인을 확인했다.[^7]

**userId 124035에 사번(employeeNumber)이 없어서 오류 발생.**

컨트롤러 코드에서 사번 검증 로직:[^4]
```kotlin
?.also { if (it.employeeNumber == null)
    throw IllegalStateException(
        "employee number doesn't exist (customerId: $customerId, userId: ${request.userId})"
    ) }
```

> 💡 **정리**:
> - raccoon → cron 서버 라우팅은 정상 동작 중 (로그 인덱스가 `flex-app.be-cron-*`)[^7]
> - 요청은 cron 서버에 도달했으나, 대상 유저에 사번이 없어 `IllegalStateException` 발생
> - cron 서버는 400/500 에러를 반환했지만, **raccoon 프록시가 모든 응답을 200으로 래핑**하여 클라이언트에 전달[^8]

#### raccoon 프록시 200 래핑 확인

`ServletRequestProxy.exchange()` 에서 백엔드 응답 상태 코드를 무시하고 항상 `ResponseEntity.ok()`로 반환한다.[^8]

```kotlin
fun exchange(httpMethod: HttpMethod? = null): ResponseEntity<Any> {
    return exchangeOnly(httpMethod = httpMethod)
        .let {
            ResponseEntity.ok()  // ← 항상 200 OK로 반환
                .headers(...)
                .body(it.body)   // body만 전달, 상태 코드는 버림
        }
}
```

따라서 김상준님이 본 200 응답은 정확하다. response body 안에 에러 정보가 담겨 있었을 것이다.

#### 부수 버그: `@ExceptionHandler` 파라미터 타입 불일치

```kotlin
@ExceptionHandler(IllegalArgumentException::class, IllegalStateException::class)
fun illegalArgumentExceptionMapping(e: IllegalArgumentException): ResponseEntity<Any?>
//                                     ^^^^^^^^^^^^^^^^^^^^^^^^
// IllegalStateException도 처리 대상이지만 파라미터가 IllegalArgumentException만 받음
```

`IllegalStateException` 발생 시 이 핸들러가 매칭되지만 파라미터 주입에 실패하여, Spring 기본 에러 핸들러(500)로 넘어갈 수 있다.[^9]

### 초기 조사 경로 (수정)

초기 조사에서 access log/app log에서 요청 흔적을 찾지 못해 "raccoon 라우팅 불일치"로 추정했으나, 실제로는:
- raccoon은 **cron 서버로 정상 라우팅**하고 있었음[^7]
- OpenSearch에서 cron 서버 access log가 0건이었던 것은 **cron 서버가 access log를 OpenSearch에 적재하지 않기 때문**으로 추정[^3]
- 김영준님이 찾은 로그 인덱스가 `flex-app.be-cron-2026.03.30`으로, 검색 범위(`2026.04.01`)와 날짜가 달라 누락된 것일 수도 있음[^7]

---

## 발견한 버그

1. **`@ExceptionHandler` 파라미터 타입 불일치** — `IllegalStateException`을 처리하도록 등록했지만 파라미터가 `IllegalArgumentException`만 받음[^9]

---

## 미결 사항

- [ ] userId 124035에 사번을 등록하면 정상 동작하는지 검증

## 참고 자료

- Slack 스레드: [#C09RSJM1S9K](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1775010721560539)
- cron 서버 에러 로그: [OpenSearch](https://log-dashboard.dev.grapeisfruit.com/_dashboards/app/discover#/doc/654ffbb0-fad6-11ee-bebc-fb15a8772b5b/flex-app.be-cron-2026.03.30?id=69258337-bdb8-43e8-88ee-820a7f1cd13d)
- 컨트롤러: `flex-timetracking-backend` > external-work-clock/operation-api/src/main/kotlin/team/flex/externalworkclock/ExternalWorkClockEventOperationController.kt:140
- raccoon 프록시: `flex-raccoon` > commons/utils/proxy/src/main/kotlin/team/flex/commons/utils/proxy/ServletRequestProxy.kt:98-109
- API 서버 의존성: `flex-timetracking-backend` > applications/api/build.gradle.kts:18-20
- Cron 서버 의존성: `flex-timetracking-backend` > applications/cron/build.gradle.kts:19

## 각주

[^1]: Slack: #C09RSJM1S9K [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1775010721560539) — 김상준, 2026-04-01
[^2]: Slack: #C09RSJM1S9K [Reply 1](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1775010744388789) — curl 요청 원문
[^3]: OpenSearch `flex-app.be-access-2026.04.01`, `flex-app.be-api-2026.04.01`, `flex-app.be-cron-2026.04.01` 검색 — 2026-04-02 조사
[^4]: 코드: `flex-timetracking-backend` > external-work-clock/operation-api/src/.../ExternalWorkClockEventOperationController.kt:155-159
[^5]: 코드: `flex-timetracking-backend` > applications/api/build.gradle.kts (operation-api 미포함), applications/cron/build.gradle.kts:19 (operation-api 포함)
[^6]: 사용자 확인, 2026-04-02 — "applications/cron 여기있는게 맞아. operation api는 api모듈이 아닌 cron"
[^7]: Slack: #C09RSJM1S9K [Reply 6](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1775113795839699) — 김영준, 2026-04-02 — "해당 유저의 사번으로 이벤트를 만드는데, 124035에 사번이 없어서 오류 발생" + [cron 로그 링크](https://log-dashboard.dev.grapeisfruit.com/_dashboards/app/discover#/doc/654ffbb0-fad6-11ee-bebc-fb15a8772b5b/flex-app.be-cron-2026.03.30?id=69258337-bdb8-43e8-88ee-820a7f1cd13d)
[^8]: 코드: `flex-raccoon` > commons/utils/proxy/src/main/kotlin/team/flex/commons/utils/proxy/ServletRequestProxy.kt:98-109 — `ResponseEntity.ok()`로 항상 200 반환
[^9]: 코드: `flex-timetracking-backend` > external-work-clock/operation-api/src/.../ExternalWorkClockEventOperationController.kt:64-73 — `@ExceptionHandler` 파라미터 타입 불일치
