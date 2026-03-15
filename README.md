# oncall-worktree

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다.

## 셋업

```bash
# 처음 클론할 때 (서브모듈 포함)
git clone --recurse-submodules <repo-url>

# 이미 클론한 상태에서 서브모듈 초기화
git submodule update --init --recursive

# 서브모듈을 최신으로 업데이트
git submodule update --remote
```

## 서브모듈 추가하기

```bash
git submodule add -b <branch> git@github.com:flex-team/<repo-name>.git <directory-name>
# 예: git submodule add -b develop git@github.com:flex-team/flex-timetracking-backend.git flex-timetracking-backend
```

서브모듈을 추가한 후 `CLAUDE.md`의 서브모듈 맵 테이블도 함께 업데이트할 것.
