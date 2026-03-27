# 이지선 — Slack Knowledge Profile

> 생성일: 2026-03-27 | 분석 범위: 2021-01-01 ~ 2026-03-27
> 채널: product_qna, customer-issue, squad-tracking, squad-tracking-fe, pj-tracking-계획실근로, pj-tracking-주기연장일귀속, pj-tracking-교대근무-근무지-근무표, pj-연장근무단위, tf-휴일대체, tf-tracking-reframing, tf-보상휴가-급여-연동, tf-미사용연차수당
> 분석 메시지: ~12,010건 / 추출 카드: 552건
> 역할: Product Engineer (FE) / ep division

---

## 인물 개요

### 전문 영역

이지선은 flex Time-Tracking 프론트엔드의 핵심 엔지니어로, 2022년부터 현재까지 근무/휴가/승인/교대근무 도메인 전반을 담당한다. 주요 전문 영역은 다음과 같다:

1. **타임라인/근무입력기**: 뉴타임라인(리프레이밍), 타임블록 에디터, 근무 확정 모델, 실시간 근무 위젯. TimeBlockChunk/Bundle 네이밍 결정, overwork 그라데이션 렌더링, dimmed 처리 레이어 순서 등 FE 구현의 세밀한 스펙을 주도
2. **휴가 시스템**: 등록/취소/편집 모달, 당겨쓰기 판단 로직, 맞춤 휴가 버킷 표시, dry-run 연동. FDS/FX 전환 과정에서 승인라인 판단 불일치 버그 다수 발견/수정
3. **승인 워크플로우**: 승구개(승인 구조 개편), 뉴승인 모달, 승인 문서 컨텐츠 저장, approval-task API 구조. 참조만 있는 승인라인 처리, 빈 stage 저장 등 엣지 케이스 전문
4. **교대근무**: 2025-10부터 신 교대근무(근무지/근무표) 전면 FE 개발 리드. ag-grid 기반 테이블, 임시저장, 게시, 파견, 스케줄 템플릿 마이그레이션
5. **미사용연차수당**: 2025-Q2부터 TF 참여. 재직자/퇴직자 연차 조정 화면, 엑셀 업로드/다운로드, v3 API 전환
6. **FE 인프라**: flagsmith 피처 플래그 관리, react-query 패턴, MF(Micro-Frontend) 분리, 다국어/번역, API 스펙 업데이트 관리

**주요 협업 대상**: 김영준(Tracking BE), 전우람(FE), 안희종(PM), 권형기(디자인), 김신영(FE/디자인), 서영준(BE), 장우현(FE), 권재호(FE), 지무근(FE)

### 의사결정 원칙

1. **"이것만으로 CS 답변 가능한가" 기준**: 이슈 인입 시 access log → 재현 → 원인 분석 → 핫픽스 순서를 엄격히 따름. 단순 재현 불가면 데이터 확인으로 넘어감

2. **FE에서 할 수 있는 것은 FE에서**: 서버 변경이 크거나 일정이 빡빡할 때 FE 단에서 우회/임시 처리 후 추후 서버 이관 방향 제시
   - 사례: 교대근무 게시 시 휴무일 자동 배치 — FE에서 `autoAssignDayOffs` 함수로 빈 날에 DayOff 채번하여 전송 ([스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1766403992576599))
   - 사례: 휴가 자동 승인 — FE에서 게시 시점에 승인 문서 조회 → 내가 승인자이면 승인하는 플로우 ([스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1764727555829719))

3. **과도한 추상화 경계**: 코치마크 구현의 노력 대비 효과가 미미하다며 "최최최최후순위"로 미루기로 결정하는 등 실용적 판단 ([스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1767839415932139))

4. **API 스펙 변경 커뮤니케이션 강조**: BE에서 API가 사라지거나 필드가 사라지면 사전 고지를 요청. "API가 사라지거나 필드가 사라지면 얘기를 좀 해주세요"라는 직접적 피드백 ([tf-미사용연차수당 2025-07](https://flex-cv82520.slack.com/archives/C08ECN6LF1R/p1752137810557289))

5. **배포 순서 의존성 관리**: BE/FE 배포 순서를 명확히 하고, BE 선배포 → FE 후배포 패턴을 엄수. `timeZone` → `timezone` 파라미터명 변경 시 BE 선배포 안 해서 prod 400 에러 발생한 사례를 교훈으로 공유 ([tf-reframing 2024-Q4](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1727257541629589))

6. **사이드이펙트 사전 분석**: 기능 도입 시 사이드이펙트를 구체적으로 나열. 근입개 사이드이펙트 분석 시 "이전 주기 마지막날 잠기고 이번 주기 첫날은 안 잠겼을 때", "내 근무 vs 구성원근무 vs 모바일 간 데이터 불일치 VOC 예상" 등 시나리오를 사전 제시 ([customer-issue 2022-Q3](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1661341257403079))

### 응대 패턴

1. **CS 이슈 → 즉시 원인 파악**: customer-issue 채널에서 이슈 인입 시 재현 → 코드/로그 확인 → 원인 특정 → 핫픽스 PR 작성 → 당일 배포 패턴이 반복됨. 평균 응답~해결 시간이 수 시간 이내

2. **"정상 스펙" 판단 명확**: 관리자가 구성원 휴가를 직접 등록할 경우 승인라인을 타지 않는 것이 "정상 스펙"임을 즉시 답변 ([customer-issue 2022-Q4](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1666683002871599))

3. **flagsmith 상태 우선 확인**: 특정 회사만 기능이 안 되면 flagsmith 상태부터 확인하도록 안내 ([customer-issue 2022-Q4](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1664848821670739))

4. **재현 계정 공유**: 버그 보고 시 "jiseon.lee+2@flex.team / 근무지무근 근무지 → 1월달 게시 시도" 등 구체적 재현 경로를 슬랙에 바로 공유 ([pj-교대근무 2026-01](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1767769529076679))

5. **도메인 히스토리 기반 답변**: 과거에 왜 이렇게 결정했는지, 어떤 PR에서 바뀌었는지를 기억하고 바로 연결. Notion 문서, PR 번호, 코드 위치를 함께 제시

---

## 도메인별 지식

### 1. 휴가 시스템

#### 당겨쓰기(Use in Advance) 판단 로직

**스펙/규칙**
- dry-run 응답의 `postUseInAdvanceAmount.timeOffDays > preUseInAdvanceAmount.timeOffDays`로 당겨쓰기 발생 판단
- 당겨쓰기 발생 + 승인 시 `timeOffAdvanceAgreed: true` 전송
- 한 번에 휴가 1개만 올릴 수 있으므로 응답도 1개
- FDS 휴가 Drawer에서 참조만 있는 승인라인을 "승인 없음"으로 판단하여 당겨쓰기 alert를 안 보여주는 버그 있었음 (타임라인/iOS는 정상)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1725523200000000), [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1707971264467309)

#### 맞춤 휴가 등록 모달 — 버킷 표기 규칙

**스펙/규칙**
- 버킷 2개 이상일 때부터 받은휴가/사용기한 표기 (1개면 미표기)
- 지급 방식별 분기:
  - `신청시 지급`: 받은휴가/사용기한 안 보여줌
  - `연차 소진시 지급`: 보여줌 (직접 지급 가능)
  - `근속시 지급`: 받은 날짜가 미래면 "받을"로 표기
- "소멸 시점이 다가온 휴가부터 순차차감" 안내는 버킷 2개 이상일 때만

**변경 이력**
- 2024-03: 버킷 1개일 때도 기간 표기, 미래 근속시 지급은 "받을"로 문구 변경

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1709599185575149)

#### 휴가사용내역 다운로드 기간

**스펙/규칙**
- 화면 조회: 6개월 제한
- 엑셀 다운로드: 5년까지 (2024-04 배포)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1715229491678279)

#### 휴가 부여 시 validUsageTo 검증

**스펙/규칙**
- validUsageTo가 오늘 이전이면 휴가 리스트에 안 보임
- 에러메세지 내려주기 제안됨

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1659504996958759)

#### 연속사용 휴가 소멸 안내 팝업

**스펙/규칙**
- dry run response의 `expiredTimeOffTimeAfterUse > 0`일 때 보여주면 됨
- 기존 조건문(assignMethod, partialUsage, remainingTimeOff)은 불필요
- 웹에만 들어가 있고 모바일과 싱크 안 됨 (2022-08 기준)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1661160895069699)

#### 종일휴가 interval/duration 처리

**스펙/규칙**
- 하루종일 휴가의 시간량 표시: 귀속일의 종일 휴가시간 값 사용 (interval이 아님)
- Editor Popover에서 종일휴가 블록은 양(시간)을 안 보여줘야 함
- 종일/오전반차/오후반차/시간차 전환시 이전 interval 값이 유지되어야 함

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1724834052690629)

#### 휴일포함 휴가 사용량(amount) 계산

**스펙/규칙**
- 휴일포함 휴가 30일 사용 시 amount는 20일로 내려옴 (정상), 그런데 remainingTimeOff에는 30일이 깎임 — 버그
- 2022-12: 핫픽스 배포

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1671671625643379)

#### 교대근무에서 맞춤휴가 처리

**스펙/규칙**
- 교대근무관리에서 맞춤휴가 등록/취소는 스펙상 미지원
- x 버튼으로 취소 불가, 휴가 문서 띄워서 취소는 가능
- 연차는 임시저장에 추가됨 (2024-09), 맞춤휴가는 미진행
- 툴바에서 스케줄 입력 시 맞춤 휴가가 제거되는 버그 (TT-16578)

**변경 이력**
- 2026-02-19: 수정 티켓 생성

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1771464130890579)

### 2. 연차 정책

#### 소멸 없음 + 스마트 연차촉진 조합

**스펙/규칙**
- 소멸 없음 정책이면 스연촉 설정 자동 off + disabled (FE)
- 서버는 소멸 없으면 스연촉을 만들지 않음
- N개 연차 정책 분리 시점(2024-05-08)부터 이 조합이 가능해짐 (놓친 케이스)
- 소멸 없으면서 연촉 on인 정책: 238개(연차만), 연월차 둘 다: 210개

**변경 이력**
- 2024-06: 소멸설정 없으면 스연촉 설정 막는 핫픽스 배포

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1719386559657829)

#### 연차 미지급 정책

**스펙/규칙**
- 모든 회사에 존재
- 초단시간 근무유형/등기 임원에게 적용
- 맵핑된 유저에게는 연차 조정 불가
- 승인 정책 관리 리스트에서 제외 (2025-01 배포)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1737070616536999)

#### 퇴직자 미사용 연차 조정 설정

**스펙/규칙**
- 연차 정책이 아닌 회사의 글로벌 설정으로 결정
- 정책별로 갖고 있을 필요 없는 속성

**출처**: [tf-미사용연차 2025-04](https://flex-cv82520.slack.com/archives/C08ECN6LF1R/p1743753029371349)

#### 연차 조정 API 구조 (v3 전환)

**스펙/규칙**
- 기존 일반 연차 조정: v2 API 2개(`by-days`, `annual-time-off-adjust-assigns`) → v3 API 1개로 교체
- 차감 시 `-days -hours -minutes`로 보내야 함
- v3 연동 후 소수점 10자리까지 보이는 이슈 발견
- 재직자는 버킷별 = adjustmentId 단위, 퇴직자는 adjustmentId 1개만 발생

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C08ECN6LF1R/p1755855435010909)

#### 퇴직자 엑셀 업로드 '확인 필요' 상태

**스펙/규칙**
- 엑셀 다운로드 가능하되, `확인 필요` 상태 행은 배경색+댓글로 disclaimer 표시
- 확인 필요 상태는 업로드 후에도 유지
- 엑셀 템플릿에 `joinDate`, `checkRequired` 컬럼 추가 (BE)

**출처**: [tf-미사용연차 2025-08](https://flex-cv82520.slack.com/archives/C08ECN6LF1R/p1754614883615619)

### 3. 근무 기록/타임라인

#### 타임블록 구조 — TimeBlockBundle 네이밍

**스펙/규칙**
- 조합형 타임블록에서 여러 블록을 묶는 컴포넌트: TimeBlockChunk → TimeBlockBundle로 변경
- BE에서 이미 bundle 사용 중
- TimeBlock → TimeBlockStandalone, TimeBlockBundleWrapper → TimeBlockBundle

**출처**: [squad-tracking-fe 2023-07](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1660870682765819)

#### 근무시간 프리필 로직

**스펙/규칙**
- 프리필: `workRule` > 해당 요일의 `usualWorkingMinutes` (없으면 일하는날 첫 번째 값)
- 휴게 타임블록: `recommendedRestTimeRanges` (교대근무면 추천휴게 안 넣음)
- 미타각 UI: `min(소정_근로_시간, remainingStatutoryMaxWorkingMinutes)`
- 버그: `Max(해당_요일_소정근로_시간, 첫_번째_근무일_소정근로_시간)` 잘못 사용

**출처**: [squad-tracking-fe 2024-04](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1668591639484599)

#### 추천휴게 자동 입력 규칙

**스펙/규칙**
- 기본값 켜짐. 근무유형에 등록된 시간이 기본, 4시간당 30분씩 자동 추가
- 최소휴게 미달 허용: 스위치 on/off 가능
- 최소휴게 미달 비허용: 강제 적용

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1658385327219409)

#### 근무-휴게 합치기 로직 (CalendarTimeBlockProcessor)

**스펙/규칙**
- 근무(09:00-12:00) - 휴게(12:00-13:00) - 근무(13:00-18:00)을 09:00-18:00 하나로 표시
- 코드 위치: `flex-timetracking-backend/external-calendar/service/.../CalendarTimeBlockProcessor.kt#L86`

**출처**: [squad-tracking 2022-H1](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1662083689626059)

#### 코어타임 시간 표현

**스펙/규칙**
- 근무유형 데이터에 의존하여 요일별 표시
- "주기 내 코어타임이 모두 동일하다"는 가정 하에 FE 처리
- 추후 일별 코어타임 다르게 등록하는 기능이 생기면 블로커

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1708910856877719)

#### 일별속성 API (date-attribute) 설계

**스펙/규칙**
- 리프레이밍에서 tt-search API 대신 `/work-schedule-v3/getDateAttributes` 사용
- 조회 기준이 '근무일' 단위 → 중복 date 가능
- 최대 조회 기간 3개월 제한
- 입사전/퇴사후는 boolean, 잠금 사유(lock)는 배열(복수 가능)
- 쉬는날/공휴일 다국어: 서버는 안 함, `KoreanPublicHoliday` enum으로 클라 처리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1724901556939609)

#### adjusted-time-blocks vs recommended-rest 차이

**스펙/규칙**
- adjusted-time-blocks: 입력된 타임블록에 휴게 보정 → 완성된 결과 리턴
- recommended-rest: 추천휴게만 리턴
- 퇴근타각 후 수정 시: recommended-rest로 prefill → adjusted 사용

**출처**: [squad-tracking 2022-09](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1662083689626059)

### 4. 위젯 출퇴근

#### realTime/targetTime/onTime 설계

**스펙/규칙**
- `realTime`: 유저의 의도 (실제 출퇴근 기록)
- `targetTime`: 정책에 의한 조정 (인정 근무시간)
- `onTime`: 정시
- `canCreateWorkRecordWithWorkClock`: 계실 오픈 전 false, fallback true

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1771900781088119)

#### 확정 모델 경계 케이스

**스펙/규칙**
- realTime 수정 → targetTime 따라감 → validation 재조정 반복
- 미반영+확정스킵 시 targetDayWorkSchedule이 비어서 휴게 소실 → 파서 플래깅 수정

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1772778882376769)

#### 위젯 1차 타각 후 직접수정 → 2차 타각 충돌

**스펙/규칙**
- 위젯으로만 연속 타각하면 합쳐지지만, 중간에 직접 근무 입력하면 분리되어 충돌
- 타각 기록 시간 순서를 키바나 로그로 확인하여 재현

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1664504685088909)

#### 52시간 초과 허용인데 퇴근 막힘

**자주 오는 케이스**
- 52시간 초과 허용 설정인데 위젯에서 퇴근이 막히는 VOC
- Figma 스펙 추적하여 해결

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1764564998530319)

### 5. 승인 워크플로우

#### 참조만 있는 승인라인 처리

**스펙/규칙**
- 참조만 있어도 승인 있음으로 판단해야 함
- 타임라인(서버)/iOS는 정상, FDS Drawer(FE)에서 버그
- 참조자만 있을 때 "자동승인되었다" 알림 발송 → 고객 오해 유발

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1707971264467309), [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1658831512784609)

#### 빈 승인단계(stage) 저장

**스펙/규칙**
- 1단계만 비어 있으면 TT에서 승인 안 날림 (의도)
- 빈 stage + 비어있지 않은 stage 조합: 불가능
- 프론트에서 target이 비어있는 걸 체크하지 않아 사용자 미인지 → UI 수정
- 빈 승인단계 저장 시 휴가 등록 400 에러 원인이 되기도 함

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1659501899882349), [customer-issue 2025-03](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1659501899882349)

#### 승인 문서 before/after 모델

**스펙/규칙**
- 리프레이밍에서 decidedWorkRecordBlocks에 before 추가
- 계획 블록 플래그 필요

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1772604951432029)

#### deprecated 필드 제거 장애

**변경 이력**
- `approvalPolicyKeys` → `approvalPolicies` 전환 시 승인 미발생 74건 장애 발생

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1731042348907909)

#### 관리자의 내 근무 편집 시 승인

**스펙/규칙**
- "관리자인가"를 "내 근무/휴가를 등록하는지"로 판단
- 관리자가 구성원 근무 화면에서 본인 클릭 → 수정 시 승인 발생 (스펙)
- 웹에서 관리자 화면 진입 여부를 명시적으로 구분하고 있지 않음
- FE 사이즈가 작지 않아 별도 스쿼드 논의 필요

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1729662733463639)

### 6. 교대근무

#### 근무지(Workplace) 개념 — 상위 필터 계층

**스펙/규칙**
- 근무지는 조직/근무조 필터의 상위 개념
- 근무지 변경 시 조직/근무조/검색어 필터 초기화, 기타 유지
- 근무지 1개당 조직 최대 1개 매핑
- '공용' 근무지: 실제 ID가 아닌 "근무지 설정 없는 것들의 그룹핑"
- 임시저장: 전체 근무지 + 편집한 사람 단위 관리

**출처**: [pj-교대근무 2025-10~11](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1763715756587139)

#### 편집 불가 날짜/스케줄 규칙

**스펙/규칙**
- `DateUneditableReason`: 입사전, 퇴사후, 휴직중, 교대근무유형아님, 근무/휴가편집권한없음, 파견일자아님
- `ScheduleUneditableReason`: 근무편집권한없음, 휴가편집권한없음, 등록된휴가+여러날등록휴가
- 편집 불가 셀의 draft는 deferred 처리 + hover 시 툴팁
- `uneditable-dates` API: GET → POST 변경 (수백 명 조회 시 URL 길이 문제)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1764819670548289)

#### 임시저장 API 동작

**스펙/규칙**
- "변경된 날의 전체"를 보내는 방식 (화면 전체가 아님)
- FE에서 debounce 1초, 변경 시마다 누적 diff 전송
- draftShifts가 null이면 publishedShifts 유지, 빈 배열이면 제거 의미
- `timeBlockGroupId`: FE에서 채번하는 삭제 임시저장용 id
- 임시저장 평균 2~3초, 극단 8초

**출처**: [pj-교대근무 2025-12](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1766122405511589)

#### 파견(Secondment) 처리

**스펙/규칙**
- 파견 일자 수정: 생성/변경/삭제 모두 가능
- 한 유저가 동일 날짜에 동일 근무지로 파견 기록 허용
- 유저 표현: 근무지명으로 통일
- `GetUserShiftScheduleSecondmentV3Dto`에 `userWorkplaceSecondmentId` 필드 필요

**출처**: [pj-교대근무 2025-12](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1764142428071849)

#### 스케줄 템플릿 마이그레이션

**스펙/규칙**
- 기존 교대근무에서 template 이름을 key로 게시 → 다른 근무지 간 이름 중복 허용으로 key 사용 불가
- `customerWorkPlanTemplateId`가 없는 데이터(타 근무지 스케줄) 존재
- 서버 마이그레이션 불가 → FE에서 templateId 없으면 제거 + 토스트 알림

**출처**: [pj-교대근무 2025-12](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1766384513242799)

#### 교대근무 관리 메뉴 노출 조건

**스펙/규칙**
- 변경 전: 교대 근무 관리 권한 → 메뉴 노출 (최고관리자면 무조건)
- 변경 후: 교대 근무 유형 1개 이상 && 교대 근무 관리 권한 → 메뉴 노출

**변경 이력**
- 2026-02-19: prod 배포

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1770886472154359)

#### 조회 API 100명 제한

**스펙/규칙**
- `get-shift-schedules` API: 100명 넘게 호출하면 400 에러
- 608명 계정에서 100명씩 조회 시 6초 → 개선 후 3초

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1765783104060589)

#### 플래그 및 URL

**스펙/규칙**
- FE 플래그: `tt_shift_workplace_and_roster`
- URL: `/time-tracking/shift-management`
- 2026-03-09: 플래그 제거 + 온보딩 Alert(만료 2026-02-28) 동시 제거

**출처**: [pj-교대근무 2026-03](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1773039245226129)

### 7. 주기연장/초과근무

#### 주기연장 일귀속 전환

**스펙/규칙**
- 노출 화면: 근무 유형 설정, 근태 대시보드 (보상 휴가 부여는 제외)
- 근무 유형 설정 권한이 있는 사람에게만 노출
- 오픈 절차: 서버 soft open 플래그 → DB 마이그레이션(mini LEAF 1066건) → 클라이언트 플래그
- `apply_start_date_for_distribute_period_over`가 있으면 `distribute_period_over_to_day`가 false여도 일귀속으로 동작
- 일귀속 전환 시 주기가 잘리는 문제 → 안내 문구 2단계 모달

**변경 이력**
- 2025-12-02: 기본값을 가능한 가장 이른 1일로 추천 (PR #1666, 12-03 배포)
- 2026-02-11: 마이그레이션 안내 UI 전부 제거

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09S8UXL5R7/p1769391478938179)

#### 초과근무 잔여시간 계산

**스펙/규칙**
- 구/신 근무에서 남은 시간 버그: 휴가 미고려, 최대 남은시간 계산 차이

**출처**: [squad-tracking 2025-01](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1704164572006289)

### 8. 휴일대체

#### 휴일대체 버튼 노출 조건

**스펙/규칙**
- 편집 불가 날에는 아이콘 미노출
- 5개 조건 OR로 버튼 제거
- 주휴일/쉬는날만 대체 대상 (휴무일은 불가)
- 5월 1일 근로자의 날: 리스트에 뜨지만 휴일대체 불가

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1730165138735279)

#### alternativeHolidays 전송 규칙

**스펙/규칙**
- null 불가
- `targetHolidayDate: null`로 "안 보냄" 표현
- 휴일대체 취소 시 근무기록도 초기화, 승인문서 미생성

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1728262112105659)

#### date-attribute API로 교체

**스펙/규칙**
- unusual-date API는 휴일대체 대응 불가 → date-attribute로 교체
- 쉬는날 대체 시 dayOffs 미포함 버그 있었음
- 서버 targetAlternativeHoliday 중복 체크 추가 필요

**변경 이력**
- 2024-12-11 17시: `tt_members_alternative_holiday` 전체오픈

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1730165138735279)

#### 휴일대체된 날에 휴일근무 등록 허용 validation 누락

**스펙/규칙**
- 일요일을 금요일로 휴일대체 → 금요일에 휴일 등록 불가 근무가 등록됨, 일요일엔 등록 안 됨
- 휴무일 체크를 하지 않고 있음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1663302793175259)

### 9. 보상휴가

#### 보상휴가 지급 탭 필터 초기값

**스펙/규칙**
- 근무유형 필터: 기간/조직 기반 유저가 1명 이상인 근무유형 전체
  - "기본 근무 유형" 포함되면 초기값, 아니면 첫 번째
- 조직: "전체" 기본값
- 조회기간: 지난 30일

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1720147769724159)

#### 초과근무시간 유형 정렬 순서

**스펙/규칙**
- 야간 → 연장(법정근로 내) → 연장·야간(법정근로 내) → 연장 → 휴일 → 연장·야간 → 연장·휴일 → 휴일·야간 → 연장·휴일·야간
- FE에서 정렬 없이 서버 `exceededWorkTimes` 그대로 표시

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1722325394008079)

#### v2→v3 API 전환 이슈

**스펙/규칙**
- continuationToken: 첫 호출시 null 허용 필요
- excludeFixedOverTime: 2024-02 고정OT 드롭 흔적, 레거시 필드 제거 요청
- 초과근무 0인 필터링: 클라 필터로 인한 비정상 페이징
- fx-table infinity scroll: 전체 데이터 필요 (클라 필터+정렬 때문에)
- 음수 처리: 공제 > 초과근무 시 0 cap, 가산율 적용 시 올림

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1731910048968069)

### 10. FE 공통/인프라

#### flagsmith 피처 플래그 관리

**스펙/규칙**
- FE 코드 먼저 제거 → 배포 → flagsmith 키 삭제 순서 준수
- dev에만 flag 앞에 백스페이스 특수문자가 들어가 있어 flag가 안 지워지는 현상 (2024-01)
- Flagsmith segment 정리: 2024년에 19건 제거

**출처**: [squad-tracking-fe 2024-01](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1667192536337639)

#### API 스펙 업데이트 시 required 필드 변경

**자주 오는 케이스**
- open api 버전업 시 required false → true로 바뀌는 필드 다수 발견
- `TimeOffCancelDto.timeOffEventIdToDelete`, `UserWorkScheduleAndTimeOffUseRegisterRequest.userWorkSchedule` 등
- 400 에러 발생 시 다음 배포에 실어 보내는 전략

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1696411734844609)

#### react-query enabled:false 파라미터 유효성

**스펙/규칙**
- enabled가 false여도 쿼리 파라미터 유효성 검사는 수행됨
- required 파라미터 없으면 오류 발생
- useQueryFromRemote가 원인일 수 있음

**출처**: [squad-tracking-fe 2023-08](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1692755915340589)

#### MF(Micro-Frontend) 분리

**스펙/규칙**
- global-features, settings, gnb, time-tracking 분리
- 근무/휴가는 우람/우현님, 근태관리는 지선님 담당
- `@flex-domains/time-tracking-*` 패키지 app 이동 가능 여부 분석

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1711433632062349)

#### 타임존 이슈 패턴

**자주 오는 케이스**
- 맥 크롬에서 timeZone 미전송: PR #22796에서 systemTimeZone 폴백
- TimePicker 직접 입력 시 시스템 타임존 vs 자동 조절 시 근무유형 타임존 불일치
- 9999-12-31 → 10000-01-01 타임존 변환 이슈 (TT에서 하드코딩 '마지막 날짜')
- LA 타임존 휴가 필터링 버그, Windows Etc/Unknown NaN 에러

**출처**: [squad-tracking-fe 2024-03](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1711433632062349), [customer-issue 2023-H1](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1688344560456699)

#### 배포 후 캐시 문제

**스펙/규칙**
- host QueryClient 공유로 인한 캐시 형상 불일치 → TypeError 발생

**출처**: [tf-reframing 2024-Q4](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1730354340534729)

#### 정기배포 온콜 제안

**스펙/규칙**
- 정기배포날 모니터링, 에러 체크, 스쿼드 현황판 체크를 온콜 업무에 포함 제안
- 결론: 리그레션 테스트 자동화로 크리티컬 패스(화면 접속 가능 여부) 확인 수준으로 충분

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C03780R4NHX/p1709516523421149)

---

## 의견 충돌 이력

### 1. 근입개 사이드이펙트 범위 (2022-09)
- **상대방**: 기능 도입 측
- **이지선 입장**: 이전 주기 타임블록 표시 기능 도입 시 Summary 불일치, 근무유형 변경 시 오차, 근무 잠금 충돌, 화면 간 데이터 불일치 VOC 등 사이드이펙트가 크다고 반대
- **결과**: 사이드이펙트 인지 하에 진행
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1661341257403079)

### 2. 위젯 UI 개편 비용 챌린지 (2026-02)
- **상대방**: PD/PM
- **이지선 입장**: 위젯 전체 개편은 비용이 크고, 필요 정보만 추가하면 공수 절반으로 가능하다고 챌린지
- **결과**: PD와 논의하여 범위 조정
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1770194471472749)

### 3. departmentIdHashes null 처리 — 클라 vs 서버 책임 (2026-03)
- **상대방**: 김영준(BE)
- **이지선 입장**: 클라이언트에서 null일 때 조직 넣어주려면 `departmentIdHashes`를 non-null로 바꿔달라고 요청
- **김영준 입장**: 서버가 null일 때 조직 조회해서 넣는 방식 채택 (매번 권한 조회 비용 발생)
- **결과**: 서버 측 처리로 결정 (PR `flex-timetracking-backend#11614`)
- **출처**: [pj-교대근무 2026-03](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1767676465720089)

### 4. 백로그 누적 문제 피드백 (tf-보상급여)
- **이지선 입장**: bet마다 이슈가 쌓이는데 처리 못하는 패턴을 직접적으로 지적
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1733451847529699)

### 5. API 스펙 변경 커뮤니케이션 (tf-미사용연차 2025-07)
- **상대방**: BE 개발자
- **이지선 입장**: adjustId 사라짐, deprecated 필드 제거, key 필드 누락 등이 사전 고지 없이 발생하여 "API가 사라지거나 필드가 사라지면 얘기를 좀 해주세요"라고 직접 요청
- **결과**: BE/FE 간 API 스펙 변경 커뮤니케이션 개선 합의
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/C08ECN6LF1R/p1752137810557289)
