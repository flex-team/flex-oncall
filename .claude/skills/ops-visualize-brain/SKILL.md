---
name: visualize-brain
description: brain/domain-map.ttl을 파싱하여 인터랙티브 도메인 그래프(brain/graph.html)를 생성하고 브라우저에서 연다
---

# Brain 도메인 그래프 시각화

## Purpose

`brain/domain-map.ttl` 을 파싱하여 `brain/graph-template.html` 의 데이터 마커를 교체하고, `brain/graph.html` 을 생성한다.

## Execution

### Step 1: 소스 파일 읽기

두 파일을 Read:
1. `brain/domain-map.ttl` — 도메인/노트/용어 데이터
2. `brain/graph-template.html` — HTML 템플릿 (데이터 마커 포함)

### Step 2: TTL 파싱 → JavaScript 객체 생성

domain-map.ttl을 텍스트로 읽어 3개 JavaScript 객체를 생성한다.

#### 도메인 파싱

`:` prefix로 시작하는 블록에서 추출:
```
:{id}
  d:n   "..." ;     → name
  d:cb  "..." ;     → cookbook section
  d:repo "..." ;    → repos (쉼표 구분 시 배열)
  d:mod "..." ;     → modules
  d:kw  "..." ;     → keywords
  d:x   :{id} ;     → cross-domain 관계
```

결과 형식:
```javascript
const domains = {
  '{id}': { n: '{name}', cb: '{cb}', repos: [...], mods: [...], kw: [...], x: [...] },
};
```

#### 노트 파싱

`n:` prefix로 시작하는 블록에서 추출:
```
n:{id}
  d:in :{domain} ;  → 소속 도메인
  d:v  "..." ;      → verdict
  d:s  "..." ;      → summary
```

active/archive 구분: `# Notes — active` 주석 아래는 `active:true`, `# Notes — archive` 주석 아래는 `active:false`.

결과 형식:
```javascript
const notes = [
  { id: '{id}', domain: '{domain}', v: '{verdict}', s: '{summary}', active: true/false },
];
```

#### 용어 파싱

`g:` prefix로 시작하는 블록에서 추출:
```
g:{id}
  d:in :{domain} ;  → 소속 도메인
  d:q  "..." ;      → 사용자 표현
  d:a  "..." ;      → 시스템 용어
```

결과 형식:
```javascript
const glossary = [
  { id: '{id}', domain: '{domain}', q: '{user query}', a: '{system term}' },
];
```

### Step 3: 템플릿에 데이터 주입

`graph-template.html` 에서 `// __BRAIN_DATA_START__` 와 `// __BRAIN_DATA_END__` 사이를 파싱된 데이터로 교체한다.

교체 내용:
```javascript
// __BRAIN_DATA_START__
const domains = { ...파싱 결과... };
const notes = [ ...파싱 결과... ];
const glossary = [ ...파싱 결과... ];
// __BRAIN_DATA_END__
```

**주의**: JavaScript 문자열 내 작은따옴표(')는 이스케이프(`\'`)해야 한다.

### Step 4: graph.html 작성

Edit이 아닌 Write로 `brain/graph.html` 을 생성한다 (전체 교체).

### Step 5: 브라우저 열기

```bash
open brain/graph.html
```

> CDN이 `file://` 에서 안 되면:
> ```bash
> cd brain && python3 -m http.server 8847 &
> open http://localhost:8847/graph.html
> ```

### Step 6: 통계 출력

```
생성 완료:
- 도메인: {N}개
- 노트: {active}개 active / {archive}개 archive
- cross-domain 엣지: {N}개
- 용어: {N}개
```

## Template 수정 시 주의

`brain/graph-template.html` 이 시각화의 원본 템플릿이다. UI/스타일/레이아웃을 변경하려면 이 파일을 수정하고, 이 스킬을 다시 실행하면 된다. `brain/graph.html` 은 생성물이므로 직접 수정하지 않는다.

데이터 마커: `// __BRAIN_DATA_START__` ~ `// __BRAIN_DATA_END__` 사이만 교체된다.
