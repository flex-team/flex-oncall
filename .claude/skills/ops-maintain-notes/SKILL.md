---
name: maintain-notes
description: Use when active operation-notes need batch maintenance — checks all notes against Linear status, archives completed ones, and updates COOKBOOK for each. Triggers include '노트 정리해줘', '아카이브', '일괄 유지보수'. With --rebuild, performs full COOKBOOK.md + domain-map.ttl reconstruction from all notes.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Agent
argument-hint: [--rebuild] (인자 없음: 일괄 유지보수, --rebuild: 전체 재구성)
---

# Maintain Notes

## Purpose
활성 operation-notes를 일괄 유지보수한다:
1. 아카이브 안 된 노트 전체 조회
2. Linear 이슈 상태 확인 → 노트 상태 갱신
3. 완료된 이슈의 쿡북 반영 대상 여부 판별 → 쿡북 업데이트
4. 이슈 완료 + 쿡북 반영 완료 → archive/ 로 이동

`--rebuild` 플래그를 전달하면 **COOKBOOK.md 전체 재구성 모드**로 실행한다.

## Operation Notes Directory Resolution

operation-notes 파일의 베이스 경로를 아래 우선순위로 결정한다.

| 우선순위 | 경로 | 설명 |
|---------|------|------|
| 1 | `{repo-root}/brain/notes/` | repo 루트 brain/notes 디렉토리가 존재 |
| 2 | `{repo-root}/.claude/operation-notes/` | .claude 하위에 존재 (서브모듈용) |
| 3 | `~/.claude/operation-notes/` | 글로벌 홈 디렉토리에 존재 |

- 디렉토리 **존재 여부**로 판단한다 (파일이 아닌 디렉토리).
- 셋 다 존재하지 않으면 사용자에게 `"operation-notes 디렉토리를 찾을 수 없습니다."` 로 물어본다.
- 해석된 경로를 이하 `{notes-dir}`로 표기한다.

### 아카이브 구조

```
{notes-dir}/
├── CI-3910.md          ← 활성 노트
├── CI-3914.md          ← 활성 노트
├── CLAUDE.md
└── archive/            ← 아카이브된 노트
    ├── CI-3800.md
    └── CI-3777.md
```

- 활성 = `{notes-dir}/` 루트에 있는 `.md` 파일 (CLAUDE.md 제외)
- COOKBOOK.md는 `{brain-dir}/COOKBOOK.md` (`{brain-dir}` = `{notes-dir}` 의 상위, 즉 `{repo-root}/brain/`)
- 아카이브 = `archive/` 하위 디렉토리로 이동된 노트

## Procedure

### Step 1: 활성 노트 수집
- `{notes-dir}/*.md` 목록 조회 (CLAUDE.md 제외)
- `archive/` 하위는 제외
- 노트 파일명에서 티켓 ID 추출 (예: `CI-3910.md` → `CI-3910`)
- 활성 노트가 없으면 `"아카이브 대상 노트가 없습니다."` 출력 후 종료

### Step 2: Linear 이슈 상태 일괄 조회 (🤖 subagent 병렬)
각 티켓 ID에 대해 **병렬 subagent**로 Linear 이슈 정보를 조회한다.

**각 subagent 수집 정보:**
- 이슈 상태 (Todo, In Progress, Done, Closed, Canceled 등)
- 최신 코멘트 (노트 갱신에 필요한 정보)
- 해결 방법 (코드 수정 여부 — 쿡북 반영 판별용)

**상태 분류:**
- **완료**: Done, Closed, Canceled → 아카이브 후보
- **미완료**: 그 외 → 아카이브 대상 아님, 노트 상태만 갱신

**⚠️ QNA 팀 이슈 예외:**
QNA 팀 이슈(티켓 ID가 `QNA-`로 시작)는 Linear 상태가 관리되지 않는다(항상 To-Do 등으로 남아 있음).
QNA 이슈의 완료 여부는 **코멘트 맥락**으로 판단한다:
- **완료로 판단**: 질문에 대한 답변이 완료되었고, 추가 액션이 없는 경우
- **미완료로 판단**: 답변이 아직 진행 중이거나, 후속 조치(버그 수정, 기능 개발 등)가 진행 중인 경우

### Step 3: 노트 상태 갱신
이슈 상태가 변경된 노트를 업데이트한다.

- 상태 변경 시 노트 상단 상태 표기 업데이트
  - `> **상태**: 진행 중` → `> **상태**: 해결 완료` 등
  - 진행 중 → 해결 완료 전환 시: 진행 중 템플릿 → 해결 완료 템플릿 구조로 변환 (note-issue 규칙 준수)
- 새 코멘트에서 추가 정보가 있으면 해당 섹션에 반영
- **변경 없는 노트는 스킵**

### Step 4: Brain 산출물 갱신
완료된 이슈에 대해 `ops-learn` 스킬을 per-ticket으로 실행한다.

```
Read: .claude/skills/ops-learn/SKILL.md
```

1. 각 완료 노트에 대해 `ops-learn brain/notes/{ticket-id}.md` 실행
   - ops-learn이 자동으로 쿡북 추가 대상 판별 (코드 수정 → 스킵, 운영/스펙 → 반영)
   - GLOSSARY, COOKBOOK, domain-map.ttl 갱신
2. **사용자 확인은 Step 7 리포트에서 일괄 처리** (개별 확인 생략)
3. 반영 대상이 없으면 스킵

### Step 5: 아카이브 실행
아카이브 조건을 **둘 다 충족**하는 노트를 `archive/`로 이동한다:
1. 이슈가 완료 상태:
   - 일반 이슈: Linear 상태가 Done/Closed/Canceled
   - QNA 이슈(`QNA-` 접두사): Step 2에서 코멘트 맥락 기반으로 완료 판단된 경우
2. 쿡북 반영 완료 (이번 실행에서 반영했거나, 반영할 내용이 없음)

**실행 순서:**
1. `mkdir -p {notes-dir}/archive/`
2. `mv {notes-dir}/{ticket-id}.md {notes-dir}/archive/`
3. COOKBOOK.md 내 노트 링크를 archive/ 경로로 업데이트
   - `[CI-XXXX](./CI-XXXX.md)` → `[CI-XXXX](./archive/CI-XXXX.md)`
4. 연관 이슈 노트의 상대 링크 업데이트
   - 활성 노트에서 아카이브된 노트 참조: `[CI-XXXX](./CI-XXXX.md)` → `[CI-XXXX](./archive/CI-XXXX.md)`
   - 아카이브된 노트에서 활성 노트 참조: `[CI-YYYY](./CI-YYYY.md)` → `[CI-YYYY](../CI-YYYY.md)`

### Step 6: 컴팩션 (자동)

아카이브 완료 후 `ops-compact` 스킬의 절차를 실행한다:

```
Read: .claude/skills/ops-compact/SKILL.md
```

1. 농축 미완료 archive 노트 일괄 농축 (`d:syn`/`d:kw` 흡수 + `d:st "C"` 설정 + 노트 정제)
2. 퇴출 기준(R1/R2/R3) 충족 시 자동 퇴출 (`n:*` 삭제 + `compact-log.md` 기록)
3. COOKBOOK Tier-1/Tier-2 계층 조정 (히트 0 + 60일 경과 → 강등, 히트 발생 → 승격)
4. 히트율 리포트 생성 (Step 7 리포트에 포함)

### Step 7: 최종 리포트
처리 결과를 테이블로 출력한다:

```
| 티켓 | 이슈 상태 | 노트 갱신 | 산출물 반영 | 아카이브 |
|------|----------|----------|-----------|---------|
| CI-XXXX | Done | ✅ 상태 업데이트 | ✅ GLOSSARY+COOKBOOK+TTL | ✅ |
| CI-YYYY | In Progress | ⏭️ 변경 없음 | — | ❌ |
```

- 각 노트별 한 줄 요약
- 아카이브된 노트 수, 활성 유지 노트 수
- 쿡북 변경 내용 요약 (변경이 있었으면)

### Step 8: 메트릭스

> 스킬 호출 로그는 PreToolUse hook이 JSONL에 자동 기록한다. 별도 METRICS.md 갱신 불필요.
> ```
> Read: .claude/skills/ops-common/metrics-guide.md
> ```

---

## `--rebuild` 모드: 전체 재구성

`$ARGUMENTS` 에 `--rebuild` 가 포함되면 **COOKBOOK.md + domain-map.ttl 을 전체 재구성**한다.
활성 노트 유지보수/아카이브는 수행하지 않는다.

### Step 1: 노트 전체 수집 (🤖 subagent)
`{notes-dir}/` 루트와 `{notes-dir}/archive/` 의 모든 `.md` 파일을 수집한다.

**제외 대상:** CLAUDE.md, COOKBOOK.md

### Step 2: domain-map.ttl 전체 재구축
각 노트에서 다음을 확인하여 domain-map.ttl을 갱신한다:
1. 모든 노트가 domain-map.ttl에 `n:{ticket-id}` 항목으로 존재하는지 확인 → 없으면 추가
2. 각 노트의 상태(진행 중/해결 완료 등)와 domain-map의 `d:v` (verdict)가 일치하는지 확인 → 불일치하면 갱신
3. domain-map에 있지만 notes/ 에 파일이 없는 항목을 제거 (orphan 정리)
4. active 노트는 "Notes — active" 섹션에, archive 노트는 "Notes — archive" 섹션에 위치하도록 정리

### Step 3: COOKBOOK.md 전체 재구성
각 노트에서 다음 섹션을 추출:
- `## 다음에 같은 문의가 오면` → 진단 체크리스트
- SQL 쿼리 블록 → 데이터 접근 템플릿
- `### 배제된 가설` / `### 확정된 원인` / `### 근본 원인` → 과거 사례
- `## 스펙/버그 판별` → 판정 결과

도메인별로 분류하여 `{brain-dir}/COOKBOOK.md` 를 전체 재작성한다.
`ops-learn` 스킬의 `references/cookbook-rules.md` 구조 및 규칙을 따른다.

### Step 4: 컴팩션 (자동)
rebuild 후에도 `ops-compact` 절차를 실행한다 (일반 모드 Step 6과 동일).

### Step 5: 사용자 확인
재구성 + 컴팩션 결과를 보여주고 확인을 받은 후 커밋한다.

---

## Rules
- 완전 자동 실행 — 최종 리포트만 출력
- 아카이브 조건: Linear 이슈 완료 AND 산출물 반영 완료
- 산출물 관련 규칙은 `ops-learn` 스킬을 따른다
- 아카이브 시 관련 링크(COOKBOOK.md, 연관 이슈 노트) 일괄 업데이트
- `archive/` 디렉토리가 없으면 자동 생성
