# domain-map.ttl 작성 규칙

Claude Code가 `domain-map.ttl` 을 일관성 있게 읽고/쓰도록 하는 규칙 문서.

## Turtle 형식 기본

Turtle(Terse RDF Triple Language)은 RDF 그래프를 사람이 읽기 쉽게 표현하는 직렬화 형식이다.
기본 구조는 `주어 술어 목적어 .` 트리플이며, 같은 주어의 술어를 `;` 로 이어 쓸 수 있다.

```turtle
:time-off
    d:n  "연차/맞춤휴가" ;
    d:repo "flex-timetracking-backend" ;
    d:mod "/time-off" ;
    d:kw "연차", "맞춤휴가", "time-off" .
```

- 문자열 값은 `"쌍따옴표"` 로 감싼다.
- 다중 값은 `,` 로 구분한다.
- 트리플 그룹의 마지막은 `.` 으로 닫는다.

## Prefix 정의

파일 상단에 반드시 아래 4개 prefix를 선언한다. 순서도 고정.

```turtle
@prefix d: <b:prop/> .     # 속성 (property)
@prefix : <b:domain/> .    # 도메인 (domain)
@prefix n: <b:note/> .     # 노트 (note)
@prefix g: <b:gloss/> .    # 용어 (glossary term)
```

| prefix | IRI | 용도 |
|--------|-----|------|
| `d:` | `<b:prop/>` | 속성(술어)을 정의 |
| `:` | `<b:domain/>` | 도메인 엔티티를 식별 |
| `n:` | `<b:note/>` | 노트 엔티티를 식별 |
| `g:` | `<b:gloss/>` | 용어집 엔티티를 식별 |

## 속성 약어 테이블

| 약어 | 의미 | 값 타입 | 사용 대상 |
|------|------|---------|-----------|
| `d:n` | name (도메인명) | string | domain |
| `d:cb` | cookbook section명 | string | domain |
| `d:repo` | 서브모듈 repo | string | domain |
| `d:mod` | 모듈 경로 | string | domain |
| `d:kw` | keyword | string (다중) | domain |
| `d:syn` | synonym (사용자 표현 문장) | string (다중) | domain |
| `d:x` | cross-domain 관계 | domain ref | domain |
| `d:in` | 소속 도메인 | domain ref | note, glossary |
| `d:v` | verdict | enum string | note |
| `d:s` | summary | string | note |
| `d:q` | user query (사용자 표현) | string (다중) | glossary |
| `d:a` | answer (시스템 용어) | string | glossary |

## 도메인 추가/수정/삭제 규칙

### 추가
```turtle
:new-domain
    d:n  "도메인 한글명" ;
    d:repo "서브모듈명" ;
    d:mod "/모듈경로" ;
    d:kw "키워드1", "키워드2" .
```
- `d:n` 은 필수. 나머지는 해당하는 것만 기록.
- 도메인 ID(`:` 뒤)는 영문 kebab-case. 예: `:compensatory-time-off`

### 수정
- 기존 트리플 블록을 직접 편집한다.
- 속성 추가 시 기존 블록에 `;` 로 이어 쓴다.
- 키워드 추가 시 `d:kw` 값 목록에 `,` 로 추가한다.

### 삭제
- 도메인 블록 전체를 제거한다.
- 해당 도메인을 참조하는 `d:x`, `d:in` 도 함께 제거한다.

## 노트 추가 규칙

```turtle
n:CI-1234
    d:in :time-off ;
    d:v  "investigating" ;
    d:s  "연차 차감이 안 되는 이슈" .
```

### verdict 값 (열거형)
| 값 | 의미 |
|----|------|
| `"spec"` | 스펙대로 동작 (버그 아님) |
| `"bug"` | 버그 확인, 수정 필요/완료 |
| `"investigating"` | 조사 중 |
| `"operational"` | 운영 조치로 해결 (데이터 패치 등) |

- 새 노트 생성 시 verdict는 `"investigating"` 으로 시작한다.
- close-note 시 verdict를 확정 값으로 변경한다.
- `d:in` 은 도메인 ref 하나. 여러 도메인에 걸치면 주 도메인만 기록한다.

## 용어집 추가 규칙

```turtle
g:annual-leave
    d:q "연차", "연차휴가", "유급휴가" ;
    d:a "time-off (annual)" ;
    d:in :time-off .
```

- `d:q` 는 사용자/CS가 쓰는 표현. 다중 값 가능.
- `d:a` 는 시스템에서 쓰는 정확한 용어.
- `d:in` 은 소속 도메인.
- GLOSSARY.md와 동기화한다. domain-map.ttl이 source of truth.

## Cross-domain 관계 추가 규칙

```turtle
:notification
    d:n  "알림" ;
    d:x  :time-off, :work-record .
```

### 양방향 관계 주의사항

**한쪽만 기록한다.** 반대 방향은 추론으로 처리한다.

규칙:
- 의존하는 쪽(caller)에서 의존되는 쪽(callee)으로 `d:x` 를 기록한다.
- 예: notification이 time-tracking을 호출하므로 `:notification d:x :time-off` 만 기록.
- `:time-off d:x :notification` 은 기록하지 않는다.
- 조회 시 역방향 관계가 필요하면 `d:x` 의 object로 등장하는 모든 트리플을 검색한다.

## 파일 구조 권장 순서

```turtle
# 1. Prefix 선언
@prefix d: <b:prop/> .
@prefix : <b:domain/> .
@prefix n: <b:note/> .
@prefix g: <b:gloss/> .

# 2. 도메인 정의 (알파벳순)
:approval ...
:compensatory-time-off ...

# 3. Cross-domain 관계 (해당 도메인 블록에 d:x로 포함)

# 4. 노트 (티켓 번호순)
n:CI-1234 ...

# 5. 용어집 (알파벳순)
g:annual-leave ...
```

## 주의사항

- 속성 약어는 이 문서에 정의된 것만 사용한다. 새 속성이 필요하면 이 문서를 먼저 갱신한다.
- domain-map.ttl은 RDF 파서로 검증 가능한 유효한 Turtle이어야 한다.
- 주석은 `#` 으로 시작. 섹션 구분용으로만 사용한다.
- 빈 줄로 트리플 블록을 구분한다.
