---
description: 모든 서브모듈을 최신 상태로 갱신
allowed-tools: Bash
---

# Sync Submodules

모든 git 서브모듈을 각 추적 브랜치의 최신 커밋으로 업데이트한다.

## 실행

```bash
git submodule update --remote --merge
```

위 명령어를 실행하고, 각 서브모듈별 갱신 결과를 요약해서 보고한다.

## 출력 형식

- 갱신된 서브모듈: 이전 커밋 → 새 커밋 (변경된 것만)
- 이미 최신인 서브모듈은 "이미 최신" 으로 표기
- 에러가 발생한 서브모듈이 있으면 별도 표기
