---
name: cleanup-worktrees
description: 머지되었거나 취소된 브랜치의 worktree를 정리합니다. "/cleanup-worktrees", "worktree 정리", "clean up worktrees" 등으로 호출합니다.
allowed-tools:
  - Bash
---

# /cleanup-worktrees

워크스페이스 내 stale worktree를 찾아 정리합니다.

## 워크플로우

1. flex-fe 루트(현재 워크스페이스) 하위에서 `--` 패턴의 worktree 디렉토리를 탐색
2. 각 worktree의 브랜치가 remote에서 삭제되었는지 확인
3. 삭제 가능한 worktree 목록을 사용자에게 보여줌
4. 사용자 확인 후 삭제 진행

## 실행 스크립트

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "🔍 Scanning for stale worktrees..."
echo ""

STALE=()

for dir in "$WORKSPACE"/*--*/; do
  [ -d "$dir" ] || continue

  wt_name=$(basename "$dir")

  # .git 파일에서 원본 레포 경로 추출
  if [ ! -f "$dir/.git" ]; then
    continue
  fi

  gitdir=$(cat "$dir/.git" | sed 's/gitdir: //')
  # 원본 레포 경로 추출 (worktrees 상위)
  main_repo=$(dirname "$(dirname "$gitdir")")

  # 현재 브랜치 확인
  branch=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null)

  if [ -z "$branch" ]; then
    STALE+=("$wt_name|unknown|orphan")
    continue
  fi

  # remote에 브랜치가 있는지 확인
  remote_exists=$(git -C "$dir" ls-remote --heads origin "$branch" 2>/dev/null)

  if [ -z "$remote_exists" ]; then
    # remote에서 삭제됨 — develop/main에 머지되었을 가능성
    STALE+=("$wt_name|$branch|remote deleted")
  fi
done

if [ ${#STALE[@]} -eq 0 ]; then
  echo "✅ No stale worktrees found."
  exit 0
fi

echo "Found ${#STALE[@]} potentially stale worktree(s):"
echo ""
echo "| Worktree | Branch | Reason |"
echo "|----------|--------|--------|"
for item in "${STALE[@]}"; do
  IFS='|' read -r name branch reason <<< "$item"
  echo "| $name | $branch | $reason |"
done
echo ""
echo "⚠️ Review the list above. To remove a worktree:"
echo "  git -C $WORKSPACE/{main-repo} worktree remove $WORKSPACE/{worktree-name}"
```

## 사용자 확인 후 삭제

위 스크립트 실행 후 사용자에게 삭제할 worktree를 확인합니다.
확인되면 각 worktree에 대해:

```bash
# 원본 레포에서 worktree 제거
git -C $WORKSPACE/{main-repo} worktree remove $WORKSPACE/{worktree-name}

# 로컬 브랜치도 삭제
git -C $WORKSPACE/{main-repo} branch -D {branch-name}
```

## 출력 예시

```
🔍 Scanning for stale worktrees...

Found 2 potentially stale worktree(s):

| Worktree | Branch | Reason |
|----------|--------|--------|
| flex-frontend--fe-2050 | feature/fe-2050 | remote deleted |
| flex-frontend-apps-people--ppd-180 | feature/ppd-180 | remote deleted |

⚠️ Review the list above.
```
