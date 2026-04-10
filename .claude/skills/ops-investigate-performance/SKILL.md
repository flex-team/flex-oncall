---
name: investigate-performance
description: "Use when a system performance issue needs investigation — DB load spikes, latency surges, cascade failures, timeout storms. Triggers include 'DB 부하 조사', '성능 스파이크', '레이턴시 급등', 'CPU 튐', '시스템 장애', 'cascade', 'timeout 폭증', or when metrics show abnormal infrastructure behavior. Not for domain-specific bugs (use ops-investigate-issue) or code fixes (use ops-fix-issue)."
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Agent
argument-hint: "[현상 설명] (예: DB 부하 출근시간에 튐, 레이턴시 3배 악화, prod RDS CPU 스파이크)"
---

# Investigate Performance

## Purpose

시스템/인프라 레벨의 성능 이슈를 조사하여 **데이터로 인과관계를 증명**한다.
추측이 아닌 PI/CloudWatch/OpenSearch/Grafana 데이터를 근거로 "무엇이 → 무엇을 → 왜 일으켰는지"를 밝힌다.

`ops-investigate-issue`가 도메인 기능 이슈(특정 API 버그, 데이터 불일치)를 다룬다면,
이 스킬은 **시스템 전반의 성능 저하**(DB 부하, 레이턴시 급등, cascade, timeout 폭증)를 다룬다.

## 문서 구조 원칙

`investigate-issue`와 동일한 **Progressive Disclosure** 구조를 따른다.
- L1: 한 줄 요약 (10초 파악)
- L2: 핵심 근거 테이블/차트 (1분 이해)
- L3: 상세 쿼리/데이터 (`<details>`)

mermaid를 적극 활용하여 인과 체인, 서비스 간 흐름, 타임라인을 시각화한다.

## Input
$ARGUMENTS

사용자 입력이 불충분하면 다음을 질문한다:
- **언제?** (시간대, KST)
- **어디서?** (환경: dev/prod, 클러스터/인스턴스)
- **무엇이?** (증상: DB 부하, 레이턴시, timeout 등)
- **baseline은?** (비교 대상: 어제 동일 시간, 정상 시 — 미지정 시 전일 동일 시간대 사용)

## Procedure

### Phase 1: 현상 정의 + 스코핑

1. 사용자 입력에서 시간대, 환경, 증상을 추출한다
2. baseline 시간대를 결정한다 (기본: 전일 동일 시간대)
3. `/tmp/{날짜}-perf-investigation/investigation.md` 에 조사 문서를 초기 생성한다
4. KST→UTC, KST→epoch 변환을 준비한다:
   ```bash
   python3 -c "from datetime import datetime,timezone,timedelta; kst=timezone(timedelta(hours=9)); print('UTC:', datetime(2026,4,8,9,50,tzinfo=kst).strftime('%Y-%m-%dT%H:%M:%SZ')); print('epoch:', int(datetime(2026,4,8,9,50,tzinfo=kst).timestamp()))"
   ```

### Phase 2: 인프라 메트릭 수집 (🔀 병렬 4 Agent)

**4개 Agent를 동시에 실행하여 데이터 수집 시간을 최소화한다.**

각 Agent에게 사용 가능한 도구를 안내하고, 실행할 수 없는 경우 `delegation-guide.md` 위임 포맷으로 대체하도록 지시한다.

#### 🤖 Agent A: DB 메트릭 (aws pi + aws cloudwatch)

**사전 조건:**
```bash
# AWS 인증 확인
aws sts get-caller-identity --profile {env}
# 401/403 → flex-okta-aws {env} 실행 필요

# ResourceId 조회
aws rds describe-db-instances --region ap-northeast-2 --profile {env} \
  --db-instance-identifier {instance-id} \
  --query 'DBInstances[0].{ResourceId:DbiResourceId,Class:DBInstanceClass,PI:PerformanceInsightsEnabled}' --output table
```

**PI 핵심 쿼리 7종** (모두 `aws pi get-resource-metrics`):

| # | 용도 | metric-queries |
|---|------|---------------|
| 1 | DB Load 추이 | `'[{"Metric":"db.load.avg"}]'` |
| 2 | Top SQL | `'[{"Metric":"db.load.avg","GroupBy":{"Group":"db.sql_tokenized","Limit":10}}]'` |
| 3 | 서비스별 부하 | `'[{"Metric":"db.load.avg","GroupBy":{"Group":"db.user","Limit":10}}]'` |
| 4 | 호스트별 부하 | `'[{"Metric":"db.load.avg","GroupBy":{"Group":"db.host","Limit":15}}]'` |
| 5 | Wait Event | `'[{"Metric":"db.load.avg","GroupBy":{"Group":"db.wait_event","Limit":10}}]'` |
| 6 | Wait Event 타입 | `'[{"Metric":"db.load.avg","GroupBy":{"Group":"db.wait_event_type","Limit":5}}]'` |
| 7 | OS 메트릭 | `'[{"Metric":"os.cpuUtilization.total.avg"},{"Metric":"os.memory.free.avg"}]'` |

공통 파라미터:
```bash
--region ap-northeast-2 --profile {env} \
--service-type RDS --identifier "{DbiResourceId}" \
--start-time "{UTC}" --end-time "{UTC}" --period-in-seconds 60
```

PI 주의사항:
- `period-in-seconds`: **1, 60, 300, 3600, 86400만 허용** (다른 값은 에러)
- 시간은 **UTC** (KST - 9시간)
- 1초 단위는 정밀 트리거 추적 시에만 (범위 2분 이내)
- **Writer와 Reader 둘 다 확인** — 부하가 이동했을 수 있음

**CloudWatch 보충 메트릭:**
```bash
aws cloudwatch get-metric-statistics --region ap-northeast-2 --profile {env} \
  --namespace "AWS/RDS" --metric-name "{MetricName}" \
  --dimensions Name=DBInstanceIdentifier,Value={instance-id} \
  --start-time "{UTC}" --end-time "{UTC}" --period 60 --statistics Average
```

주요 메트릭: `DatabaseConnections`, `BufferCacheHitRatio`, `Queries`, `DMLLatency`, `Deadlocks`, `ActiveTransactions`, `CPUUtilization`, `FreeableMemory`, `ReadIOPS`, `WriteIOPS`, `DiskQueueDepth`, `RollbackSegmentHistoryListLength`, `FreeLocalStorage`

**baseline 비교는 필수:** 비정상 시간대와 동일 쿼리로 baseline 시간대도 조회하여 수치 차이를 정량화한다.

**실행할 수 없는 경우:**
- AWS 콘솔 직접 접속 안내:
  - RDS Performance Insights: `https://ap-northeast-2.console.aws.amazon.com/rds/home?region=ap-northeast-2#performance-insights-v2`
  - CloudWatch: `https://ap-northeast-2.console.aws.amazon.com/cloudwatch/home?region=ap-northeast-2#metricsV2`
- 위 PI 핵심 쿼리 7종의 CLI 명령어를 `delegation-guide.md` 의 AWS CLI 위임 포맷으로 출력
- 수집해야 할 메트릭과 시간 범위를 체크리스트로 제공

#### 🤖 Agent B: 트래픽 분석 (opensearch:os-query-log)

`os-query-log` 스킬의 인증/실행 방법을 따른다.
인덱스: `flex-app.be-access-{날짜}` (access log)

핵심 집계 쿼리 패턴:
- **분당 요청량 추이**: `histogram` agg on `@timestamp`, interval 60
- **서비스별 분포**: `terms` agg on `kubernetes.labels.app.keyword`
- **Top API by elapsed**: `terms` agg on `json.ipath.keyword` + `sum`/`avg`/`percentiles` on `json.elapsedTime`
- **고객별/사용자별 분포**: `terms` agg on `json.authentication.customerId` 또는 `userId`
- **어제 vs 오늘**: 동일 쿼리를 어제/오늘 epoch으로 각각 실행하여 비교

**실행할 수 없는 경우:**
- Kibana 대시보드 직접 접속 안내 (시간 범위, 필터 파라미터 포함 URL 구성)
- 검색 조건을 `delegation-guide.md` 의 OpenSearch 위임 포맷으로 출력: 인덱스 패턴, 필터 필드, 시간 범위
- 결과를 받으면 Phase 3 교차 분석에 반영

#### 🤖 Agent C: RDS 이벤트 + 배포 확인

```bash
# RDS 이벤트
aws rds describe-events --region ap-northeast-2 --profile {env} \
  --source-identifier {instance-id} --source-type db-instance \
  --start-time "{ISO}" --end-time "{ISO}" --output table

# 최근 배포
cd {서브모듈} && git log --oneline --since="{날짜}" --all | head -20
```

**실행할 수 없는 경우:**
- 배포 확인(`git log`)은 도구 불필요 — 기존 경로 유지
- RDS 이벤트만 AWS 콘솔 접속 안내로 대체

#### 🤖 Agent D: LB/WAS/인프라 메트릭

**ALB (Application Load Balancer):**
```bash
# 5xx 발생 시점 — DB CPU 전인지 후인지 (원인 vs 결과 구분)
aws cloudwatch get-metric-statistics ... --namespace "AWS/ApplicationELB" \
  --metric-name "HTTPCode_Target_5XX_Count" --period 60
# RequestCount — 외부 유입 RPS
# TargetResponseTime — LB→서버 레이턴시 (p99)
# HealthyHostCount — Healthy Host 수 변화
```

**DB 엔진 내부 (CloudWatch):**
- `DatabaseConnections` + `ActiveTransactions` — 커넥션 풀 포화 확인
- `Deadlocks` + `RowLockTime` — Lock 경합
- `RollbackSegmentHistoryListLength` — long transaction
- `ReadIOPS` + `WriteIOPS` + `DiskQueueDepth` — Storage IOPS 병목

**WAS 메트릭 (grafana:grafana-dashboard — Spring Actuator/Prometheus):**

`grafana_query_prometheus` 로 PromQL 직접 실행. datasource_uid는 환경별로 다름 (모르면 uid 없이 호출하면 목록 반환).

| 카테고리 | PromQL | 조사 용도 |
|---------|--------|----------|
| HikariCP Active | `hikaricp_connections_active{app="{app}"}` | 커넥션 풀 포화 — active가 max에 도달하면 cascade |
| HikariCP Timeout | `irate(hikaricp_connections_timeout_total{app="{app}"}[5m])` | 커넥션 획득 실패 — timeout 원인 특정 |
| HikariCP Pending | `hikaricp_connections_pending{app="{app}"}` | 커넥션 대기 요청 수 |
| JVM GC 횟수 | `irate(jvm_gc_pause_seconds_count{app="{app}"}[5m])` | GC STW가 DB 커넥션을 물고 있었는지 |
| JVM GC 시간 | `irate(jvm_gc_pause_seconds_sum{app="{app}"}[5m])` | GC pause 총 시간 |
| Tomcat 스레드 | `tomcat_threads_current_threads{app="{app}"}` | 워커 스레드 포화 — 모든 스레드가 DB 대기인지 |
| HTTP RPS | `sum by(uri) (irate(http_server_requests_seconds_count{app="{app}"}[5m]))` | API별 요청 수 — access log 대비 검증 |
| HTTP 응답시간 | `http_server_requests_seconds_max{app="{app}"}` | API별 최대 응답시간 |
| ERROR 로그율 | `irate(logback_events_total{app="{app}",level="error"}[5m])` | 에러 발생 추이 |
| CPU | `system_cpu_usage{app="{app}"}` | 앱 레벨 CPU |
| Heap 메모리 | `jvm_memory_used_bytes{app="{app}",area="heap"}` | 메모리 부족/GC 압박 |

app 라벨 예시: prod = `flex-prod-prod-time-tracking-api`, dev = `flex-dev-dev-time-tracking-api`

**전체 스냅샷이 필요하면:**
```
grafana_dashboard_snapshot(env="prod", dashboard_uid="0BjSzaB7z",
  variables='{"application":"{app}"}',
  time_from="{KST ISO}", time_to="{KST ISO}")
```

**실행할 수 없는 경우:**
- Grafana 대시보드 직접 접속 URL 안내 (시간 범위 파라미터 포함)
- 확인해야 할 패널 목록(HikariCP, JVM GC, HTTP 응답시간, 에러율)과 정상 baseline을 체크리스트로 제공

### Phase 3: 원인 좁히기 (소거법)

Phase 2 결과를 교차 분석하여 가설을 세우고, 데이터로 소거한다.
**한 번에 1-2개 가설만 조사. 소거 후 다음 가설을 추가.**

#### Smoking Gun 패턴 (교차 분석 시 참고)

이 패턴들로 원인의 방향을 빠르게 좁힐 수 있다:

| 관측 | 가능성 높은 원인 |
|------|---------------|
| LB Latency↑ + DB CPU 정상 | 네트워크 또는 WAS 내부 로직 (외부 API 대기 등) |
| DB CPU 100% + 쿼리 로그 깨끗 | N+1 (작은 쿼리 수만 번) 또는 DB 엔진 설정 |
| 모든 지표 동시에 튐 | DB Lock으로 모든 요청이 줄 서서 시스템 정체 |
| DB CPU↑ → 이후 LB 5xx | DB가 원인, LB는 결과 |
| LB 5xx → 이후 DB CPU↑ | 재시도 폭풍이 DB를 압도 |
| 전체 API 균일하게 느려짐 | DB 레벨 자원 경합 (특정 쿼리 아닌 전체 CPU 포화) |
| 특정 서비스만 느려짐 | 해당 서비스의 쿼리 또는 외부 의존성 문제 |
| HikariCP active = max + timeout 증가 | DB 응답 지연 → 커넥션 풀 고갈 → cascade 증폭 |
| Tomcat 스레드 포화 + HikariCP pending 증가 | 모든 워커가 DB 대기 → 신규 요청 처리 불가 |
| GC pause 급증 + DB 커넥션 hold | GC STW가 커넥션 반환을 지연 → 풀 고갈 |

#### 소거 가설 체크리스트

| 가설 | 확인 방법 | 소거 기준 |
|------|---------|---------|
| 트래픽 증가 | access log 어제 vs 오늘 총 요청수 | 동일하면 소거 |
| 코드 배포 | git log + 배포 시점 비교 | 스파이크 이후 배포면 소거 |
| Cron/배치 | cron 로그 조회 | 0건이면 소거 |
| 인덱스 미사용 | `db:db-query`로 EXPLAIN | 인덱스 사용 중이면 소거 |
| 메모리/IO | FreeableMemory, ReadIOPS | 안정이면 소거 |
| 특정 고객 집중 | access log 고객별 집계 | 분산이면 소거 |
| 특정 서비스 | PI db.user 분석 | 여러 서비스면 소거 |
| 발령/권한변경 | access log WRITE 요청 + consumer recordKey | 없으면 소거 |
| LB Target 장애 | ALB HealthyHostCount | 변화 없으면 소거 |
| 커넥션 풀 포화 (DB) | DatabaseConnections + ActiveTransactions | Max 미도달이면 소거 |
| Lock 경합 | PI wait_event + Deadlocks | 0이면 소거 |
| Storage IOPS 초과 | ReadIOPS/WriteIOPS + DiskQueueDepth | 정상이면 소거 |
| CPU Credit 소진 | CPUCreditBalance (T계열만) | 해당 없거나 잔여 있으면 소거 |
| JVM GC STW | Grafana `jvm_gc_pause_seconds_sum` | GC pause 없으면 소거 |
| HikariCP 커넥션 풀 포화 | Grafana `hikaricp_connections_active` vs max | max 미도달이면 소거 |
| HikariCP timeout | Grafana `hikaricp_connections_timeout_total` | 0이면 소거 |
| Tomcat 스레드 포화 | Grafana `tomcat_threads_current_threads` vs max | 여유 있으면 소거 |
| 네트워크 대역폭 | NetworkThroughput | 임계치 미도달이면 소거 |
| Aurora failover/restart | RDS Events | 이벤트 없으면 소거 |

**소거된 가설도 반드시 문서에 기록한다** — 제3자가 "이건 확인했고, 아니었다"를 알 수 있도록.

### Phase 4: 인과관계 추적 + 비교 검증

Phase 3에서 원인 후보를 좁혔으면, 인과 체인을 **데이터로 증명**한다.
추측이 아닌 "A 데이터가 B를 가리키고, B 데이터가 C를 가리킨다"의 연쇄.

#### 인과관계 추적 패턴

**패턴 1: PI db.user → 서비스 식별**

PI에서 특정 `db.user`가 갑자기 부하 증가하면, 해당 서비스의 로그를 집중 분석한다.
- 예: `flex_openfga`가 0→9 AAS → OpenFGA 관련 로그 심층 분석

**패턴 2: PI 1초 단위 → 정밀 트리거 추적**

PI를 `period-in-seconds 1`로 조회하면 정확한 초 단위로 어떤 서비스/호스트가 먼저 뛰었는지 볼 수 있다.
- `db.user`로: 어떤 서비스가 먼저 부하를 줬는지
- `db.host`로: 어떤 pod가 트리거인지
- 어제 동일 시각과 1초 단위 비교: 어제는 회복했는데 오늘은 왜 cascade했는지

**패턴 3: consumer recordKey 파싱 → 이벤트 소스**

Kafka consumer 로그의 `json.recordKey`를 파싱하여 어떤 고객/사용자/오브젝트에 이벤트가 집중되었는지 확인한다.
- recordKey 구조: `{entity} {relation} {object_type}:{id}`
- entity/relation/object별 `Counter`로 집계하면 "누가 무엇을 했는지" 패턴이 보인다

**패턴 4: Kafka 토픽 역추적 → 서비스 간 연결**

특정 consumer의 이벤트 폭주가 확인되면, Kafka 토픽을 역추적하여 **어떤 서비스가 이벤트를 발행했는지** 찾는다.
- consumer log의 `json.topic`으로 토픽 확인
- 해당 토픽을 구독하는 consumer의 코드에서 처리 로직 추적
- 이벤트를 발행하는 서비스의 access log에서 원인 API 특정

**패턴 5: platform 로그 — 캐시 히트율 분석**

OpenFGA 등 platform 서비스의 로그에서 캐시 히트율 변화를 추적한다.
- `json.datastore_query_count >= 1` 필터 = 실제 DB를 친 요청만 집계
- 어제 vs 오늘 분당 DB 히트 비교 → 캐시 무효화 시점 특정
- `json.grpc_method`별 분류, `json.query_duration_ms` 추이

**패턴 6: access log → 특정 사용자의 전체 API 이력**

의심 사용자/고객을 특정한 후:
- 해당 `userId`/`customerId`의 전체 API 호출 목록 조회
- `POST`/`PUT`/`DELETE`만 필터 → 무엇을 "했는지"
- 다른 사용자도 동일 고객에서 WRITE 했는지 → **유일한 트리거인지 확인**

**패턴 7: 코드 경로 추적 → 이벤트 흐름 교차 검증**

로그에서 특정 API가 트리거로 의심되면:
- 해당 API의 코드에서 이벤트 발행 경로 추적 (Explore agent 활용)
- Kafka 토픽 → Consumer → DB/OpenFGA Write까지 코드 레벨 확인
- **코드 경로와 로그 데이터가 일치하는지 교차 검증**하여 추론이 아닌 증명으로 만든다

**패턴 8: Grafana WAS 메트릭 → cascade 증폭 경로**

DB 부하가 원인으로 특정된 후, WAS 레벨에서 cascade가 어떻게 증폭되었는지 추적한다.
- `hikaricp_connections_active` → max 도달 시점 = 커넥션 풀 고갈 시점
- `hikaricp_connections_timeout_total` 증가 시점 = 앱 레벨 timeout 시작 시점
- `tomcat_threads_current_threads` 포화 시점 = 신규 요청 처리 불가 시점
- 이 3개의 시점을 DB AAS 피크와 비교하면 cascade 전파 경로가 보인다

#### 비교 검증 원칙

- **모든 수치는 baseline(어제/정상 시)과 비교**한다. 절대값만으로 판단하지 않는다.
- 비교 결과를 테이블로 정량화한다: `| 지표 | 오늘 | 어제 | 차이 |`
- 3일 이상 비교하면 "오늘만의 현상"인지 "추세"인지 구분할 수 있다.

### Phase 5: 결론 + 보고

조사 문서를 최종 정리한다.

#### 문서 구조

1. **용어 설명** — 비개발자도 읽을 수 있도록 (AAS, PI, cascade 등)
2. **요약** — 1줄 원인 + 영향 + 시간대
3. **원인 — 인과 체인** (mermaid diagram)
4. **왜 이런 일이 일어나는지** — 기술적 메커니즘 설명
5. **상세 증거** — 각 단계별 데이터 (테이블, 차트)
6. **소거된 가설** — 확인했지만 아닌 것들 (테이블)
7. **근본 원인 분해** — 아래 프레임워크 사용
8. **권장 조치** — 단기/중기/장기

#### 근본 원인 분해 프레임워크

단일 원인이 아니라 여러 요인의 조합일 수 있다:

| 요인 유형 | 설명 | 예시 |
|----------|------|------|
| **직접 트리거** | cascade를 시작시킨 특정 이벤트 | 대량 PDF export → tuple Write 폭주 |
| **증폭 요인** | 트리거의 영향을 키운 구조 | 캐시 무효화 → DB 직접 조회 전환 |
| **용량 한계** | tipping point가 낮은 이유 | Writer 여유분 부족, request-scoped cache |
| **cascade 메커니즘** | 자기 강화 루프 | CPU 포화 → 쿼리 지연 → 세션 증가 → 더 포화 |

"트리거만 해결하면 내일은 괜찮지만, 다른 곳에서 같은 패턴이 발생하면 재발"
→ 4가지 요인 모두에 대한 조치를 권장한다.

## 주의사항

- **추측하지 않는다.** 모든 결론은 데이터 근거가 있어야 한다. 근거 없는 판단은 "추정"으로 명시한다.
- **확인하지 않은 것을 확인한 것처럼 말하지 않는다.**
- **할루시네이션 자가 점검**: 중간 결론이 나오면 "이게 정말 맞나? 다른 해석은?" 자문한다.
- **소거된 가설에도 가치가 있다.** 읽는 사람이 "왜 이건 아닌지"를 이해할 수 있다.
- **DB 조회 규칙**: `db:db-query` 또는 `ops-db-query-builder`를 통해 수행. `db_query`를 직접 호출하지 않는다.
- **시간은 KST 기준으로 표시**하되, AWS API 호출 시에만 UTC로 변환한다.
