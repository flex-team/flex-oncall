---
name: sync-repos
description: 워크스페이스 내 모든 flex 레포를 동기화합니다. git fetch --all --prune 후 develop(없으면 main) 브랜치로 checkout합니다. "/sync-repos", "레포 동기화", "sync all repos" 등으로 호출합니다.
allowed-tools:
  - Bash
---

# /sync-repos

워크스페이스 내 모든 flex-* 레포를 최신 상태로 동기화합니다.

## 워크플로우

1. flex-fe 루트(현재 워크스페이스) 하위의 모든 git 레포를 탐색 (worktree 제외: `--` 패턴 제외)
2. 각 레포에 대해 순차적으로:
   - `git fetch --all --prune`
   - develop 브랜치가 있으면 `git checkout develop && git pull origin develop`
   - 없으면 `git checkout main && git pull origin main`
3. 실패한 레포는 목록으로 출력

## 실행 스크립트

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "🔄 Syncing all repos in $WORKSPACE..."
echo ""

FAILED=()
SUCCESS=0

for dir in "$WORKSPACE"/flex-*/; do
  repo=$(basename "$dir")

  # worktree 디렉토리 제외 (-- 패턴)
  if [[ "$repo" == *"--"* ]]; then
    continue
  fi

  # git 레포인지 확인
  if [ ! -d "$dir/.git" ]; then
    continue
  fi

  echo "--- $repo ---"

  cd "$dir" || continue

  # fetch
  if ! git fetch --all --prune 2>&1; then
    FAILED+=("$repo (fetch failed)")
    continue
  fi

  # checkout develop or main
  if git rev-parse --verify develop >/dev/null 2>&1; then
    git checkout develop 2>&1 && git pull origin develop 2>&1
  elif git rev-parse --verify main >/dev/null 2>&1; then
    git checkout main 2>&1 && git pull origin main 2>&1
  fi

  SUCCESS=$((SUCCESS + 1))
  echo ""
done

echo "✅ Synced $SUCCESS repos"
if [ ${#FAILED[@]} -gt 0 ]; then
  echo "❌ Failed: ${FAILED[*]}"
fi
```

## 출력 예시

```
🔄 Syncing all repos...

--- flex-frontend ---
Already on 'develop'
Already up to date.

--- flex-frontend-apps-host ---
Already on 'develop'
Already up to date.

...

✅ Synced 22 repos
```
