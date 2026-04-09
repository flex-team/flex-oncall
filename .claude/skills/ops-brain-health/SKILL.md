---
name: ops-brain-health
description: brain 지식 시스템의 건강 상태를 분석하여 HTML 리포트를 생성한다. metrics/ JSONL을 읽고 AI가 인사이트와 튜닝 권고를 포함한 리포트를 만든다. 트리거: 'brain health', '건강 리포트', '리포트 생성'
---

# ops-brain-health

metrics/ JSONL 파일을 분석하여 brain 지식 시스템의 건강 상태를 HTML 리포트로 생성한다.

## 전제 조건

- `metrics/` 디렉토리에 JSONL 파일이 존재해야 한다
- 데이터가 부족해도 리포트는 항상 생성한다 — 현재 가용한 데이터로 최선의 분석

## Phase 1: 데이터 수집 + 집계

### 1-1. JSONL 수집

모든 JSONL 파일을 읽어 이벤트 타입별로 분류한다:

1. **skill 이벤트** — `skill` 필드가 있고 `type` 필드가 없는 것
2. **investigation 이벤트** — `type: "investigation"`
3. **freshness 이벤트** — `type: "freshness"`

### 1-2. 시간 윈도우 집계

오늘 날짜를 기준으로 3개 윈도우를 계산한다:

| 윈도우 | 범위 | 용도 |
|--------|------|------|
| **7일** | 오늘 - 6일 ~ 오늘 | 이번 주 현황 (기본 뷰) |
| **이전 7일** | 오늘 - 13일 ~ 오늘 - 7일 | WoW 비교 대상 |
| **30일** | 오늘 - 29일 ~ 오늘 | 월간 트렌드 |

전체 데이터를 보여주지 않는다. 위 윈도우만 표시한다.

### 1-3. 집계 항목

각 윈도우에 대해 다음을 집계:

**스킬 사용:**
- 스킬별 호출 수 (내림차순)
- 사용자별 분포
- 일별 추이

**Investigation:**
- 총 건수
- 도메인별 건수
- 평균 steps, 평균 wrong_hypotheses
- context_loaded true vs false 별 효율 비교
- cookbook_verdict 분포 (hit/ref/miss)
- cookbook_hit_flow별 히트 횟수
- cookbook_flows_consulted에만 있고 hit_flow에 없는 "죽은 플로우" 목록

**Pipeline Feedback** (pipeline_feedback 필드가 있는 investigation 이벤트만):
- assess 유용도: assess_useful true vs false 비율
- 범위 추정 정확도: scope_accuracy 분포 (일치/과대/과소/미추정)
- 긴급도 적절성: urgency_accuracy 분포 (적절/과대/과소)
- 조사 방향 준수율: direction_followed true vs false 비율
- assess 생략율: skipped_assess true 비율
- impact_analyze 필요율: impact_analyze_needed true 비율
- retrospective 자유 서술 목록 (파이프라인 개선 단서)

**Freshness:**
- 도메인별 spec_items, spec_review_needed, api_refs, api_stale
- 부패율: (spec_review_needed + api_stale) / (spec_items + api_refs)

**WoW 비교:**
| 지표 | 계산 | 방향 |
|------|------|------|
| 총 스킬 호출 | 이번 주 vs 지난 주 | 참고 |
| investigation 건수 | 이번 주 vs 지난 주 | 참고 |
| 평균 steps | 이번 주 vs 지난 주 | ↓ 좋음 |
| 평균 wrong_hypotheses | 이번 주 vs 지난 주 | ↓ 좋음 |
| 쿡북 히트율 | 이번 주 vs 지난 주 | ↑ 좋음 |
| context_loaded 비율 | 이번 주 vs 지난 주 | ↑ 좋음 |
| active 노트 수 | 현재 | 참고 |
| 부패율 | 최신 | ↓ 좋음 |

### 1-4. Note Aging 집계

domain-map.ttl에서 active 노트를 추출한다:
- `n:` 프리픽스 트리플 중 `d:st "C"`가 없는 것 = active
- 각 노트의 생성일: `metrics/` JSONL에서 해당 ticket의 최초 skill 호출 시각
- aging = 오늘 - 생성일 (일 수)
- verdict 분포: `d:v` 값으로 분류

## Phase 2: AI 분석

Phase 1의 집계 결과를 바탕으로 다음을 분석:

### 분석 항목

1. **스킬 사용 패턴**
   - 빈도가 극단적으로 높거나 낮은 스킬
   - 항상 함께 호출되는 스킬 쌍
   - 사용자 간 패턴 차이

2. **쿡북 효과**
   - 히트율 추이와 의미
   - hit 시 vs miss 시의 steps/wrong_hypotheses 차이 (쿡북의 ROI)
   - 죽은 플로우 목록과 대응 방안
   - 도메인별 커버리지 갭
   - context_loaded=true + miss 조합 분석 ("지식은 있으나 절차가 없는" 도메인)

2-1. **파이프라인 효과** (pipeline_feedback 데이터가 있을 때만)
   - assess 유용도와 정확도 종합 평가
   - 범위 추정이 "과소"인 케이스 패턴 분석 (어떤 도메인/타입에서 범위를 놓치는가)
   - assess 생략 케이스에서 문제가 없었는지 vs 생략하지 말았어야 했는지
   - 조사 방향 미준수 케이스 분석 (왜 안 따랐는지, 그 결과가 더 좋았는지)
   - retrospective 자유 서술에서 반복되는 피드백 패턴 추출
   - **5건 회고 트리거**: pipeline_feedback이 5건 이상이면 "파이프라인 v1 회고 시점" 알림

3. **신선도 위험**
   - 부패율이 높은 도메인
   - API 부패 목록

4. **노트 현황**
   - 7일 이상 aging된 노트 경고
   - verdict 분포 해석

5. **구체적 튜닝 권고**
   - 데이터에 근거한 액션 아이템
   - 소표본일 때 "N=5" 등 표본 크기 명시. 소표본에서의 WoW 변동은 해석에 주의 표시

## Phase 3: HTML 리포트 출력

프로젝트 루트에 `brain-health-report.html` 파일을 생성한다.

### 출력 규칙

- **단일 self-contained HTML** — 외부 CSS/JS 의존 없음
- 파일명: `brain-health-report.html` (프로젝트 루트)
- 데이터가 없는 섹션은 "데이터 수집 중 — 아직 해당 타입의 이벤트가 기록되지 않았습니다" 로 표시 (에러가 아닌 정상 상태)
- **AI 분석은 데이터에 근거** — 추측이 아닌 집계 결과를 인용

### HTML 고정 구조

**반드시 아래 구조를 그대로 따른다. 섹션 순서, 제목, CSS 클래스는 변경하지 않는다.**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Brain 건강 리포트</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 0 auto; padding: 2rem; line-height: 1.6; color: #1a1a1a; background: #fafafa; }
    h1 { border-bottom: 3px solid #2563eb; padding-bottom: 0.5rem; }
    h2 { color: #1e40af; margin-top: 2rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; }
    h3 { color: #374151; margin-top: 1.5rem; }
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
    .bar { display: inline-block; height: 14px; background: #3b82f6; border-radius: 2px; vertical-align: middle; }
    .bar-secondary { background: #93c5fd; }
    .wow-up { color: #059669; } .wow-up::before { content: "▲ "; }
    .wow-down { color: #dc2626; } .wow-down::before { content: "▼ "; }
    .wow-neutral { color: #6b7280; } .wow-neutral::before { content: "— "; }
    .wow-good { font-weight: 600; }
    footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 0.875rem; }
  </style>
</head>
<body>

<h1>🧠 Brain 건강 리포트</h1>
<p>분석 기간: {7d_from} ~ {7d_to} (7일) / {30d_from} ~ {30d_to} (30일) | 생성: {report_date} KST | 모델: {model}</p>

<!-- 섹션 1: 요약 -->
<section>
  <h2>📋 요약</h2>
  <div class="metric-grid">
    <!-- 메트릭 카드: 7일 스킬 호출, investigation 건수, 쿡북 히트율, active 노트 수 -->
    <!-- 각 카드에 WoW 변화 표시 -->
  </div>
  <!-- AI 요약 3-5줄 -->
</section>

<!-- 섹션 2: 주간 트렌드 -->
<section>
  <h2>📈 주간 트렌드 (WoW)</h2>
  <!-- WoW 비교 테이블: 지표, 이번 주, 지난 주, 변화, 방향 -->
  <!-- 소표본 시 N= 표시 -->
</section>

<!-- 섹션 3: 스킬 사용 분석 -->
<section>
  <h2>🔧 스킬 사용 분석</h2>
  <h3>최근 7일</h3>
  <!-- 스킬별 호출 수 테이블 -->
  <h3>최근 30일</h3>
  <!-- 스킬별 호출 수 테이블 -->
  <h3>사용자별 분포 (30일)</h3>
  <!-- 사용자별 분포 테이블 -->
  <!-- AI 인사이트 (.insight) -->
</section>

<!-- 섹션 4: 조사 효율 분석 -->
<section>
  <h2>📊 조사 효율 분석</h2>
  <h3>최근 7일</h3>
  <!-- investigation 집계 테이블 -->
  <h3>최근 30일</h3>
  <!-- investigation 집계 테이블 -->
  <h3>컨텍스트 효과 비교</h3>
  <!-- context_loaded true vs false 비교 테이블 -->
  <!-- 데이터 없으면 .no-data -->
  <!-- AI 인사이트 (.insight) -->
</section>

<!-- 섹션 4-1: 파이프라인 효과 분석 (pipeline_feedback 데이터가 있을 때만) -->
<section>
  <h2>🔄 파이프라인 효과 분석</h2>
  <h3>Assess 유용도</h3>
  <!-- assess_useful true/false 비율, scope_accuracy 분포, urgency_accuracy 분포 -->
  <h3>조사 방향 준수율</h3>
  <!-- direction_followed 비율, 미준수 시 사유 목록 -->
  <h3>Assess 생략 케이스</h3>
  <!-- skipped_assess 비율 -->
  <h3>Retrospective 목록</h3>
  <!-- retrospective 자유 서술 모아서 표시 — 패턴 추출 -->
  <!-- pipeline_feedback 5건 이상이면: .warning "파이프라인 v1 회고 시점입니다" -->
  <!-- 데이터 없으면 .no-data "파이프라인 피드백 수집 중 — 아직 새 파이프라인으로 처리된 이슈가 없습니다" -->
  <!-- AI 인사이트 (.insight) -->
</section>

<!-- 섹션 5: 쿡북 효과 분석 -->
<section>
  <h2>📖 쿡북 효과 분석</h2>
  <h3>히트율</h3>
  <!-- cookbook_verdict 분포: hit/ref/miss 수와 비율 -->
  <!-- hit 시 vs miss 시 평균 steps 비교 -->
  <h3>플로우별 히트 현황 (30일)</h3>
  <!-- 도메인, 플로우, 히트, 참조만, 히트율 테이블 -->
  <h3>도메인별 커버리지 (30일)</h3>
  <!-- 도메인, 조사 건수, hit, ref, miss, 커버리지% 테이블 -->
  <h3>죽은 플로우</h3>
  <!-- flows_consulted에만 있고 hit_flow에 없는 플로우 목록 -->
  <!-- 데이터 없으면 .no-data -->
  <!-- AI 인사이트 (.insight) -->
</section>

<!-- 섹션 6: 신선도 분석 -->
<section>
  <h2>🔍 신선도 분석</h2>
  <!-- 도메인별 부패 현황 테이블 -->
  <!-- AI 위험 평가 (.warning 또는 .danger) -->
  <!-- 데이터 없으면 .no-data -->
</section>

<!-- 섹션 7: 노트 현황 -->
<section>
  <h2>📝 노트 현황</h2>
  <h3>Active 노트</h3>
  <!-- active 노트 수, aging 분포 테이블 -->
  <h3>Aging 경고</h3>
  <!-- 7일 이상 aging된 노트 목록 (.warning) -->
  <h3>Verdict 분포</h3>
  <!-- verdict별 건수 테이블 -->
</section>

<!-- 섹션 8: 튜닝 권고 -->
<section>
  <h2>⚡ 튜닝 권고</h2>
  <!-- 우선순위별 액션 아이템 (.danger, .action-item) -->
  <!-- 각 항목에 근거 데이터 명시 -->
</section>

<!-- 섹션 9: 리뷰 필요 항목 -->
<section>
  <h2>⚠️ 리뷰 필요 항목</h2>
  <!-- 스펙 리뷰 대상, stale 시그널, API 부패 목록 -->
  <!-- 데이터 없으면 .no-data -->
</section>

<footer>
  <p>이 리포트는 ops-brain-health 스킬에 의해 자동 생성되었습니다.</p>
  <p>metrics/ JSONL 이벤트 + domain-map.ttl 을 기반으로 AI가 분석한 결과입니다.</p>
</footer>

</body>
</html>
```

### 변수 치환

- `{7d_from}`, `{7d_to}`: 7일 윈도우 시작/끝 날짜
- `{30d_from}`, `{30d_to}`: 30일 윈도우 시작/끝 날짜
- `{report_date}`: 리포트 생성 시각 (KST)
- `{model}`: 리포트 생성에 사용된 모델명

### WoW 표시 규칙

- 개선 방향으로 변화: `<span class="wow-up wow-good">+27%p</span>` 또는 `<span class="wow-down wow-good">-1.5</span>` (steps 감소는 좋음)
- 악화 방향으로 변화: `<span class="wow-down">-15%p</span>` 또는 `<span class="wow-up">+2.0</span>` (steps 증가는 나쁨)
- 변화 없음: `<span class="wow-neutral">0</span>`
- 소표본(N<10)일 때: 수치 옆에 `(N={n})` 표시

## 중요 규칙

1. **HTML 구조는 위 템플릿을 그대로 따른다** — 섹션 순서, 제목, CSS를 변경하지 않는다
2. **데이터가 없는 섹션은 에러가 아님** — "데이터 수집 중" 표시
3. **메트릭이 부족해도 리포트는 항상 생성** — 가용한 데이터로 최선의 분석
4. **전체 데이터를 보여주지 않는다** — 7일/30일 윈도우만 표시
5. **AI 분석은 데이터에 근거** — 추측 금지. 집계 수치를 인용하여 인사이트 도출
6. **튜닝 권고는 구체적으로** — "개선 필요" 같은 모호한 표현 대신 수치와 액션 명시
7. **소표본 주의** — N<10일 때 WoW 해석에 주의 표시. 30일 윈도우를 주 분석으로 사용 권장
