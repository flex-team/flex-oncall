---
name: compact
description: Use when active operation-notes need compaction — consolidates knowledge signals into domain-map.ttl, retires old note references, adjusts COOKBOOK tiers, and reports hit rates. Triggers include '정리해줘', '컴팩션', '토큰 줄이자', or called automatically from ops-maintain-notes.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task
argument-hint: (인자 없음)
---

# Compact

## Purpose
brain 산출물의 지식 라이프사이클을 관리한다:
- **농축**: archive 노트의 유효 신호를 domain-map.ttl keyword/synonym에 흡수
- **퇴출**: 농축 완료 + 조건 충족한 노트 참조(n:*)를 domain-map.ttl에서 제거
- **COOKBOOK 계층 조정**: Tier-1/Tier-2 간 승격/강등
- **히트율 리포트**: JSONL 메트릭스 집계

## Procedure

### Step 1: 현황 스캔

1. `brain/notes/archive/` 의 모든 노트를 스캔
2. `brain/domain-map.ttl` 에서 모든 `n:*` 트리플을 파싱
3. 각 노트의 상태를 분류:
   - `d:st "C"` 없음 → **농축 미완료**
   - `d:st "C"` 있음 → 퇴출 기준 평가 대상

### Step 2: 농축 (d:st "C" 없는 archive 노트)

각 농축 미완료 노트에 대해:
1. 노트의 "증상" 섹션에서 사용자 표현 추출 → domain-map.ttl `d:syn` 에 없는 것 추가
2. 노트에서 유효한 진단 키워드 추출 → domain-map.ttl `d:kw` 에 도메인 고유 키워드 추가
3. domain-map.ttl에서 해당 노트에 `d:st "C"` + `d:ca "YYYY-MM-DD"` (오늘 날짜) 설정
4. 노트 정제: Claude 활동 로그, 소거된 가설, DB 원시 데이터 제거

### Step 3: 퇴출 (d:st "C" + 조건 충족)

퇴출 기준 (OR):
- **R1**: `d:v = "bug"` + COOKBOOK에 해당 이슈의 진단 플로우가 없음 (코드 수정으로 해결, 재현 불가)
- **R2**: `d:ca` 날짜 + 90일 경과 (오늘: $TODAY 기준). `d:ca` 없으면 퇴출 제외
- **R3**: 동일 도메인의 다른 노트가 같은 원인/코드 위치를 기술 (중복)

퇴출 실행:
1. 해당 `n:{ticket-id}` 트리플을 domain-map.ttl에서 삭제
2. `brain/compact-log.md` 에 퇴출 이력 추가:
   ```
   | {날짜} | {ticket-id} | {기준 R1/R2/R3} | {흡수한 d:syn/d:kw} | {사유 한 줄} |
   ```

**절대 퇴출하지 않는 것**: glossary(g:*) 항목, active 노트(notes/ 루트)

### Step 4: COOKBOOK 계층 조정

1. `brain/COOKBOOK.md` 의 조사 플로우에서 히트 카운트 확인
2. **강등 대상**: Tier-1에 있고, 히트 0, 추가일로부터 60일 경과 → `cookbook/{domain}.md` 로 이동
   - 강등 시 플로우의 트리거 표현을 domain-map.ttl `d:syn` 에 흡수
3. **승격 대상**: Tier-2(`cookbook/{domain}.md`)에 있고, 히트 1 이상 → `brain/COOKBOOK.md` 로 이동

### Step 5: 히트율 리포트

`metrics/` 디렉토리의 JSONL 파일과 COOKBOOK.md의 히트 카운트를 읽어 리포트 생성:

```
## 🔧 컴팩션 리포트

### 실행 결과
- 농축: {N}건 (d:syn +{N}, d:kw +{N})
- 퇴출: {N}건 (R1: {N}, R2: {N}, R3: {N})
- COOKBOOK 강등: {N}건, 승격: {N}건

### 히트율
- COOKBOOK 플로우 히트율: {N}/{M} ({P}%)
- 라우팅 미스: {N}건 (routing-misses.md 기준)

### domain-map.ttl 현황
- 도메인: {N}개
- 노트 참조: {N}개 (퇴출 전 {M}개)
- 용어: {N}개

### COOKBOOK 현황
- Tier-1: {N}줄
- Tier-2 파일: {N}개
```

### Step 6: 커밋

compact-log.md + domain-map.ttl + COOKBOOK 변경을 하나의 커밋으로:
```
🗜️ brain compact: 농축 {N}건, 퇴출 {N}건, 계층 조정 {N}건
```

## Rules
- 퇴출 전 반드시 농축 완료 확인 (`d:st "C"`)
- glossary(g:*) 는 절대 퇴출하지 않는다
- active 노트(notes/ 루트)는 건드리지 않는다
- 서브모듈 변경은 커밋하지 않는다
- R2 기준의 90일은 `d:ca` 날짜 기준. `d:ca` 가 없으면 퇴출 대상에서 제외
