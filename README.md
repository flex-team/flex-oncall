# oncall-worktree

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다.

## 배경

Enterprise Product Division으로 팀이 재편되면서 제품 온콜을 이 팀에서 전부 담당하게 되었다. 제품 스펙에 대한 이해가 충분하지 않은 상태라 당장 이슈를 직접 해결하기보다는, 문의 채널을 단일화하여 인입받고 적절한 담당자에게 라우팅하는 것으로 운영 중이다.

문제는 어떤 이슈가 어느 repo에 해당하는지, 어디로 라우팅해야 하는지조차 파악이 안 되는 상황이라는 것. 도메인별로 어느 repo를 봐야 하는지 알면 해당 repo로 바로 가면 되지만, 그걸 모르는 뉴비가 온콜에 바로 투입되어도 시작점을 찾을 수 있도록 한 곳에 단일화하는 것이 이 repo의 목적이다.

관련 코드베이스를 서브모듈로 모으고, 운영 과정에서 축적되는 진단 가이드(`COOKBOOK.md`)·과거 사례(`operation-notes/`)·용어집(`GLOSSARY.md`)·키워드 인덱스(`INDEX.md`) 등을 여기에 정리한다.

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

## 참고사항

### GitHub Actions에서 서브모듈 checkout 실패

서브모듈은 SSH URL(`git@github.com:...`)로 등록되어 있어 로컬에서는 SSH 키로 정상 동작하지만, GitHub Actions에서는 실패한다.

**원인**: `GITHUB_TOKEN`은 워크플로우가 실행되는 repo에만 scope이 제한되어 다른 private repo(서브모듈)에 접근 불가.

**영향 범위**: `.github/workflows/claude-ops-investigate.yml`의 `submodules: recursive` 옵션

**대응 방안**:
- **TODO**: org 레벨 PAT를 secret(`SUBMODULE_PAT` 등)에 등록하고, checkout step의 `token`에 사용
  ```yaml
  - uses: actions/checkout@v4
    with:
      token: ${{ secrets.SUBMODULE_PAT }}
      submodules: recursive
  ```
- PAT 적용 전까지는 워크플로우에서 서브모듈 코드 없이 동작 (operation-notes 등 인덱스 repo 자체 문서만 활용)
