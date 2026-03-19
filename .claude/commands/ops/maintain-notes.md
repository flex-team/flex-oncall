---
description: 활성 노트 일괄 유지보수 + 아카이브. --rebuild 로 COOKBOOK 전체 재구성
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

### Step 4: 산출물 갱신 (COOKBOOK)
완료된 이슈에 대해 `update-artifacts.md` 를 읽고 **증분 모드**를 per-ticket으로 실행한다.

```
Read: .claude/commands/ops/update-artifacts.md
```

1. 각 완료 노트에 대해 쿡북 반영 대상 판별 (`update-artifacts` 규칙 따름):
   - 코드 수정으로 해결 → 쿡북 스킵
   - 운영 대응 / 스펙 확인 → COOKBOOK 반영
2. 반영 대상 노트가 있으면:
   - `update-artifacts` 증분 모드 (Phase 1~2)를 각 대상 티켓에 대해 수행
   - **사용자 확인은 Step 6 리포트에서 일괄 처리** (개별 확인 생략)
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

### Step 6: 최종 리포트
처리 결과를 테이블로 출력한다:

```
| 티켓 | 이슈 상태 | 노트 갱신 | 쿡북 반영 | 아카이브 |
|------|----------|----------|----------|---------|
| CI-XXXX | Done | ✅ 상태 업데이트 | ✅ 진단 가이드 추가 | ✅ |
| CI-YYYY | In Progress | ⏭️ 변경 없음 | — | ❌ |
```

- 각 노트별 한 줄 요약
- 아카이브된 노트 수, 활성 유지 노트 수
- 쿡북 변경 내용 요약 (변경이 있었으면)

### Step 7: 메트릭스 기록

> 이 스텝은 PostToolUse 훅이 자동으로 리마인드한다. 기록 규칙 상세는 아래 가이드를 참조.
> ```
> Read: .claude/commands/ops/metrics-guide.md
> ```

1. **`.claude/METRICS.md` 갱신**: 활동 로그(전체)에 행 추가 (이슈 = `일괄`) + 스킬별 사용량 + 월별 요약 갱신
   - subagent total_tokens/duration_ms 합산
   - 월별 요약의 이슈 수, 스킬 호출, 총 토큰, 쿡북 히트 수치를 활동 로그 기반으로 재계산

---

## `--rebuild` 모드: 전체 재구성

`$ARGUMENTS` 에 `--rebuild` 가 포함되면 **COOKBOOK.md 를 전체 재구성**한다.
활성 노트 유지보수/아카이브는 수행하지 않는다.

### Step 1: 노트 전체 수집 (🤖 subagent)
`{notes-dir}/` 루트와 `{notes-dir}/archive/` 의 모든 `.md` 파일을 수집한다.

**제외 대상:** CLAUDE.md, COOKBOOK.md

### Step 2: COOKBOOK.md 전체 재구성
각 노트에서 다음 섹션을 추출:
- `## 다음에 같은 문의가 오면` → 진단 체크리스트
- SQL 쿼리 블록 → 데이터 접근 템플릿
- `### 배제된 가설` / `### 확정된 원인` / `### 근본 원인` → 과거 사례
- `## 스펙/버그 판별` → 판정 결과

도메인별로 분류하여 `{brain-dir}/COOKBOOK.md` 를 전체 재작성한다.
`update-artifacts.md` 의 COOKBOOK 구조 및 규칙을 따른다.

### Step 3: 사용자 확인
재구성 결과를 보여주고 확인을 받은 후 커밋한다.

---

## Rules
- 완전 자동 실행 — 최종 리포트만 출력
- 아카이브 조건: Linear 이슈 완료 AND 쿡북 반영 완료
- 산출물 관련 규칙은 `update-artifacts` 를 따른다 (코드 진입점 미포함, SQL 파라미터화, 도메인 분류 등)
- 아카이브 시 관련 링크(COOKBOOK.md, 연관 이슈 노트) 일괄 업데이트
- `archive/` 디렉토리가 없으면 자동 생성
