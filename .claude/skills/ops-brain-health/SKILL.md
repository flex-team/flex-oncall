---
name: ops-brain-health
description: brain 지식 시스템의 건강 상태를 분석하여 HTML 리포트를 생성한다. metrics/ JSONL을 읽고 AI가 인사이트와 튜닝 권고를 포함한 리포트를 만든다. 트리거: 'brain health', '건강 리포트', '리포트 생성'
---

# ops-brain-health

metrics/ JSONL 파일을 분석하여 brain 지식 시스템의 건강 상태를 HTML 리포트로 생성한다.

## 전제 조건

- `metrics/` 디렉토리에 JSONL 파일이 존재해야 한다
- 데이터가 부족해도 리포트는 항상 생성한다 — 현재 가용한 데이터로 최선의 분석

## Phase 1: 데이터 수집

`metrics/` 디렉토리의 모든 JSONL 파일을 읽는다.

```bash
# 모든 JSONL 파일 목록
find metrics/ -name "*.jsonl" -type f | sort
```

각 라인을 JSON으로 파싱하고, 이벤트 타입별로 분류:

### 이벤트 타입 분류

1. **스킬 사용 이벤트** — `skill` 필드가 있고 `type` 필드가 없는 것
   ```json
   {"ts":"...","user":"yj.kim","skill":"ops-investigate-issue","args":"...","session":"..."}
   ```

2. **investigation 이벤트** — `type: "investigation"`
   ```json
   {"ts":"...","type":"investigation","user":"yj.kim","model":"claude-opus-4-6","env":"local","ticket":"CI-4240","domain":"time-tracking","context_loaded":true,"steps":5,"wrong_hypotheses":1,"stale_found":null,"session":"..."}
   ```

3. **freshness 이벤트** — `type: "freshness"`
   ```json
   {"ts":"...","type":"freshness","user":"yj.kim","model":"bedrock_claude_sonnet_4_6","env":"ci","domain":"payroll","spec_items":8,"spec_review_needed":1,"api_refs":5,"api_stale":0,"detail":"...","session":"..."}
   ```

## Phase 2: 집계

수집한 데이터를 다음 기준으로 집계:

### 스킬 사용 집계
- 스킬별 호출 수 (내림차순)
- 사용자별 분포
- 모델별 분포 (model 필드가 있는 경우)
- 일별 추이

### Investigation 집계
- 도메인별 investigation 건수
- 평균 steps (진단까지 걸린 스텝 수)
- 평균 wrong_hypotheses (소거된 가설 수)
- context_loaded true vs false 별 효율 비교
- 모델별 비교

### Freshness 집계
- 도메인별 spec_items 합, spec_review_needed 합
- 도메인별 api_refs 합, api_stale 합
- 부패율 계산: (spec_review_needed + api_stale) / (spec_items + api_refs)
- 모델별 검증 비교

## Phase 3: AI 분석

집계 결과를 바탕으로 다음을 분석하고 인사이트를 도출:

### 분석 항목

1. **스킬 사용 패턴 분석**
   - 빈도가 극단적으로 높거나 낮은 스킬 식별
   - 항상 함께 호출되는 스킬 쌍 감지 → 병합 검토 제안
   - 사용자 간 사용 패턴 차이

2. **신선도 위험 평가**
   - 부패율이 높은 도메인 식별
   - spec_review_needed 추세 분석
   - API 부패 목록

3. **조사 효율 분석**
   - context_loaded=true vs false의 steps/wrong_hypotheses 차이
   - 효율이 낮은 도메인 식별 (스텝 수가 많고 소거 가설이 많은)
   - 모델별 성능 차이 (예: CI sonnet vs 로컬 opus)

4. **구체적 튜닝 권고 생성**
   - 데이터에 근거한 액션 아이템
   - 예: "approval 도메인 컨텍스트 추가 권장", "time-tracking F3 플로우 히트율 0 — 제거 검토"
   - 예: "payroll 도메인 부패율 12.5% — 스펙 리뷰 우선 실행 권장"

## Phase 4: HTML 리포트 출력

프로젝트 루트에 `brain-health-report.html` 파일을 생성한다.

### 출력 규칙

- **단일 self-contained HTML** — 외부 CSS/JS 의존 없음, 모든 스타일 inline
- 파일명: `brain-health-report.html` (프로젝트 루트)
- 데이터가 없는 섹션은 "데이터 수집 중 — 아직 해당 타입의 이벤트가 기록되지 않았습니다" 로 표시
- 에러가 아닌 정상 상태로 처리

### HTML 구조

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Brain 건강 리포트</title>
  <style>
    /* 깔끔한 리포트 스타일 — 다크/라이트 모두 가독성 확보 */
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 0 auto; padding: 2rem; line-height: 1.6; color: #1a1a1a; background: #fafafa; }
    h1 { border-bottom: 3px solid #2563eb; padding-bottom: 0.5rem; }
    h2 { color: #1e40af; margin-top: 2rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; }
    table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
    th, td { border: 1px solid #d1d5db; padding: 0.5rem 0.75rem; text-align: left; }
    th { background: #f3f4f6; font-weight: 600; }
    tr:nth-child(even) { background: #f9fafb; }
    .insight { background: #eff6ff; border-left: 4px solid #2563eb; padding: 1rem; margin: 1rem 0; border-radius: 0 4px 4px 0; }
    .warning { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1rem 0; border-radius: 0 4px 4px 0; }
    .danger { background: #fee2e2; border-left: 4px solid #ef4444; padding: 1rem; margin: 1rem 0; border-radius: 0 4px 4px 0; }
    .action-item { background: #ecfdf5; border-left: 4px solid #10b981; padding: 0.75rem 1rem; margin: 0.5rem 0; border-radius: 0 4px 4px 0; }
    .no-data { color: #6b7280; font-style: italic; padding: 1rem; text-align: center; }
    .metric { font-size: 2rem; font-weight: 700; color: #2563eb; }
    .metric-label { font-size: 0.875rem; color: #6b7280; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 1rem 0; }
    .metric-card { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; text-align: center; }
    footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 0.875rem; }
  </style>
</head>
<body>
  <h1>🧠 Brain 건강 리포트</h1>
  <p>분석 기간: {from} ~ {to} | 생성: {date} | 모델: {model}</p>

  <section>
    <h2>📋 요약</h2>
    <!-- AI가 작성한 3-5줄 핵심 요약 -->
    <!-- 총 이벤트 수, 활성 사용자 수, 주요 발견 사항 -->
  </section>

  <section>
    <h2>🔧 스킬 사용 분석</h2>
    <!-- 핵심 메트릭 카드: 총 호출 수, 고유 스킬 수, 활성 사용자 수 -->
    <!-- 스킬별 호출 수 테이블 (스킬명, 호출 수, 비율) -->
    <!-- 사용자별 분포 테이블 -->
    <!-- 모델별 분포 테이블 (데이터 있는 경우) -->
    <!-- AI 해석: 사용 패턴 인사이트 (.insight 클래스) -->
  </section>

  <section>
    <h2>🔍 신선도 분석</h2>
    <!-- 도메인별 부패 현황 테이블 (도메인, spec 항목 수, 리뷰 필요, API 참조, API 부패, 부패율) -->
    <!-- AI 위험 평가 (.warning 또는 .danger 클래스) -->
    <!-- 모델별 검증 비교 -->
    <!-- 데이터 없으면 .no-data 표시 -->
  </section>

  <section>
    <h2>📊 조사 효율 분석</h2>
    <!-- 컨텍스트 효과 비교 테이블 (context_loaded, 건수, 평균 스텝, 평균 소거 가설) -->
    <!-- 도메인별 이슈 빈도 -->
    <!-- 모델별 비교 -->
    <!-- AI 해석 -->
    <!-- 데이터 없으면 .no-data 표시 -->
  </section>

  <section>
    <h2>⚡ 튜닝 권고</h2>
    <!-- AI가 데이터 기반으로 생성한 구체적 액션 아이템 목록 -->
    <!-- 각 항목은 .action-item 클래스 -->
    <!-- 근거 데이터를 함께 표시 -->
  </section>

  <section>
    <h2>⚠️ 리뷰 필요 항목</h2>
    <!-- 스펙 리뷰 대상 목록 -->
    <!-- stale 시그널 목록 -->
    <!-- API 부패 목록 -->
    <!-- 데이터 없으면 .no-data 표시 -->
  </section>

  <footer>
    <p>이 리포트는 ops-brain-health 스킬에 의해 자동 생성되었습니다.</p>
    <p>metrics/ 디렉토리의 JSONL 이벤트를 기반으로 AI가 분석한 결과입니다.</p>
  </footer>
</body>
</html>
```

### 변수 치환

- `{from}`: 가장 오래된 이벤트의 날짜
- `{to}`: 가장 최근 이벤트의 날짜
- `{date}`: 리포트 생성 시각 (KST)
- `{model}`: 리포트 생성에 사용된 모델명

## 중요 규칙

1. **데이터가 없는 섹션은 에러가 아님** — "데이터 수집 중" 으로 표시
2. **메트릭이 부족해도 리포트는 항상 생성** — 현재 가용한 데이터로 최선의 분석
3. **HTML은 self-contained** — 외부 CSS/JS 의존 없음
4. **리포트 파일명은 `brain-health-report.html`** — 프로젝트 루트에 생성
5. **AI 분석은 데이터에 근거** — 추측이 아닌 집계 결과를 인용하여 인사이트 도출
6. **튜닝 권고는 구체적으로** — "개선 필요" 같은 모호한 표현 대신 "payroll 도메인 부패율 12.5%, 스펙 리뷰 우선 실행" 같이 수치와 액션을 명시
