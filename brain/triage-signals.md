# 이슈 분류 신호 사전

온콜 이슈 인입 시 문의 내용에서 타입을 판별하기 위한 키워드·판단 기준.
분류 결과에 따라 첫 번째 조사 액션이 결정된다.

## 오류형 (Error)

- 키워드: 오류, 에러, 실패, 안 돼요, 500, 400, 예상치 못한, 서버 오류, 다시 시도
- 첫 번째 액션: access log (HTTP 상태코드 + 에러 응답)
- OpenSearch 인덱스: `flex-app.be-*`, 검색 필드: `status_code`, `request_uri`, `response_body`

## 데이터형 (Data)

- 키워드: 이상해요, 안 보여요, 누락, 값이 다르다, 사라졌어요, 중복, 데이터 추출, 확인해주세요
- 첫 번째 액션: DB 쿼리 (데이터 상태 확인), `ops-db-query-builder` 활용

## 성능형 (Perf)

- 키워드: 느려요, 로딩, 타임아웃, 오래 걸려요, 무한 로딩, 멈춰요, timeout
- 첫 번째 액션: access log (응답시간 분포), 검색 필드: `duration_ms`, `request_uri`

## 인프라 성능형 (InfraPerf)

- 키워드: DB 부하, CPU 스파이크, AAS, 레이턴시 급등, cascade, 커넥션 풀, HikariCP timeout, 전체 API 느려짐, Writer 포화, RDS, Performance Insights
- 판별 기준: 사용자 문의가 아닌 **모니터링 메트릭에서 발견**되는 시스템 전반 성능 저하. 특정 API/고객이 아닌 전체 서비스에 영향.
- 첫 번째 액션: `ops-investigate-performance` 스킬로 조사 (AWS PI, CloudWatch, Grafana, OpenSearch 병렬 수집)
- Perf와의 구분: Perf는 "사용자가 느리다고 문의" → access log부터. InfraPerf는 "모니터링에서 DB/CPU/메모리 이상 감지" → PI/CloudWatch부터.

## 권한형 (Auth)

- 키워드: 접근이 안 돼요, 권한, 403, Forbidden, 볼 수 없어요, 메뉴가 없어요, 비활성화
- 첫 번째 액션: access log (403 확인) + 권한 테이블

## 스펙질문형 (Spec)

- 키워드: 원래 이런 건가요, 정상인가요, 스펙이, 의도된, 기획, 어떻게 동작, 사양, 왜 이렇게 되는 거예요, 이게 맞나요
- 첫 번째 액션: 도메인 스펙 문서 확인 (서브모듈 CLAUDE.md, Notion, 과거 노트)
- 게이트웨이 역할: 의도된 동작 여부 판별 → 아니면 타입 재분류

## 화면형 (Render)

- 키워드: 안 보여요, 깨져요, 레이아웃, 빈 화면, 흰 화면, 렌더링, 컴포넌트, 버튼이 없어요, UI, 화면, 새로고침하면 됨, 콘솔 에러, 프론트
- 첫 번째 액션: access log (API 응답 정상 여부 확인) + FE 코드 (컴포넌트/페이지 탐색)
- 판별 기준: API 응답이 정상(200 + 데이터 존재)인데 화면에 안 보이면 FE 이슈 확정
- FE 서브모듈: flex-timetracking-frontend, flex-frontend-apps-performance-management, flex-frontend-apps-people

## 복합 신호

명확한 장애 신호(500, 타임아웃)가 있으면 해당 타입 우선.
모호하면 스펙질문형으로 시작하여 의도된 동작인지 먼저 확인.
"안 보여요" 등 데이터형과 겹치는 키워드는 access log에서 API 응답이 정상이면 화면형(Render)으로 재분류.
Perf와 InfraPerf 구분: 특정 사용자/API의 느림 문의 → Perf. DB 부하/CPU 급등 등 시스템 전반 모니터링 이상 → InfraPerf.
어느 쪽이든 아니다 싶으면 재진입 — 이전에 확인한 사실은 재사용하고 미확인 경로만 탐색.
