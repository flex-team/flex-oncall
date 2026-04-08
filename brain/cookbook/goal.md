# 목표 (Goal/OKR) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- cross-year 트리 탐지 Step 1: 올해 자식을 가진 이전 연도 root 찾기
SELECT HEX(root_o.id) AS root_id, root_o.title, root_o.formatted_cycle
FROM flex_goal.objective_v3 root_o
WHERE root_o.customer_id = ?
  AND root_o.deleted_at IS NULL
  AND root_o.cycle_year = ?  -- 이전 연도
  AND root_o.id IN (
    SELECT DISTINCT o.root_objective_id
    FROM flex_goal.objective_v3 o
    WHERE o.customer_id = ?
      AND o.deleted_at IS NULL
      AND o.cycle_year = ?  -- 올해 연도
      AND o.root_objective_id IS NOT NULL
  );

-- cross-year 트리 탐지 Step 2: 올해 자식의 정확한 위치 (직접 부모) 확인
-- ⚠️ Step 1만으로는 "어디에 있는지" 모름. 반드시 Step 2도 실행할 것.
SELECT child.title AS child_title, child.formatted_cycle AS child_cycle,
       parent.title AS parent_title, parent.formatted_cycle AS parent_cycle
FROM flex_goal.objective_v3 child
JOIN flex_goal.objective_v3 parent ON child.parent_id = parent.id
WHERE child.customer_id = ?
  AND child.deleted_at IS NULL
  AND child.cycle_year = ?  -- 올해 연도
  AND child.root_objective_id = UNHEX(?);  -- Step 1에서 찾은 root ID
```

## 과거 사례

- **cross-year 트리로 이전 연도 목표 노출**: 고객이 2025 root 하위에 2026 자식 배치 → `hit=false`로 회색 표시. FE·BE 모두 정상 동작 — **스펙** [CI-4126]
- **cross-year 트리 — 깊은 뎁스에 올해 자식**: CI-4126과 동일 패턴이나, 올해 자식이 root 바로 아래가 아니라 여러 뎁스 아래에 위치. `root_objective_id`(트리 소속)만 확인하면 "바로 하위를 펼치면 보인다"는 잘못된 안내가 나갈 수 있음. `parent_id`로 직접 부모 확인 필수 — **스펙** [CI-4358]
- **목표 엑셀 업로드 시 담당 주체 조직명 매칭 실패**: 조직은 시계열 데이터라서 목표 시작일 기준으로 해당 시점에 존재하는 조직만 매칭됨. 목표 시작일이 조직 생성일(2026-02-01)보다 이전이면 매칭 실패. 시작일을 조직 생성일 이후로 설정 후 업로드하면 해결. 업로드 후 시작일 변경 가능 — **스펙** [CI-4284]

## 도메인 컨텍스트

### 비즈니스 규칙

- **조직은 시계열 데이터**: 엑셀 업로드 시 목표 시작일을 인사기준일로 사용하여 해당 시점의 조직을 조회한다. 과거 시점에 존재하지 않았던 조직으로 목표를 만들 수 없는 제약이 있다 [CI-4284].

### 구현 특이사항

- **`root_objective_id` ≠ `parent_id`**: `root_objective_id`는 트리의 최상위 root를 가리키고, `parent_id`는 직접 부모를 가리킨다. cross-year 트리 조사 시 `root_objective_id`로 "이 트리에 속한다"만 확인하면 올해 자식이 어느 뎁스에 있는지 알 수 없다. 반드시 `parent_id` JOIN으로 정확한 위치를 특정해야 한다 [CI-4358].
- **`ancestor_id_json`**: JSON 배열로 모든 상위 계층 ID를 저장한다. 재귀 없이 뎁스를 계산할 수 있으므로 트리 시각화에 활용 가능.
- **4depth 이상 펼치기**: FE에서 4depth 이상은 안내가 나오지만, Cmd+클릭으로 하위 전체를 한번에 펼칠 수 있다. 고객 안내 시 유용 [CI-4358].
