# 연차촉진 (Annual Time-Off Promotion) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 촉진 이력 조회
SELECT id, customer_id, user_id, status, boost_type, boosted_at, dissipated_at, canceled_at
FROM annual_time_off_boost_history
WHERE customer_id = ? AND user_id = ?
ORDER BY boosted_at DESC;

-- 즉시 대응: 촉진 이력 취소 처리
UPDATE annual_time_off_boost_history
SET status = 'CANCELED',
    canceled_at = NOW(),
    canceled_user_id = 0,
    last_modified_date = NOW(),
    last_modified_by = 'operation'
WHERE id = ?;

-- 정책 변경 후 PENDING_WRITE 잔존 확인 (정책 변경 시점 vs 촉진 생성 시점 비교)
SELECT h.id, h.user_id, h.status, h.boosted_at, h.created_date,
       m.modified_at AS policy_mapped_at,
       p.enabled_annual_time_off_policy
FROM annual_time_off_boost_history h
  JOIN v2_user_customer_annual_time_off_policy_mapping m
    ON h.customer_id = m.customer_id AND h.user_id = m.user_id
  JOIN v2_customer_annual_time_off_policy p
    ON m.annual_time_off_policy_id = p.id
WHERE h.customer_id = ? AND h.user_id = ?
  AND h.status = 'PENDING_WRITE'
  AND p.enabled_annual_time_off_policy = false;
```

## 과거 사례

- **연말 촉진 → 다음 해 목록 누락**: `boosted_at` UTC 저장 vs 조회 범위 KST 연도 기준 → 연도 경계 불일치 — **버그** [CI-3907]
- **월차 2차 완료 후 1차 알림 지속**: MONTHLY/MONTHLY_FINAL 독립 동작 + UTC/KST 연도 경계 불일치 — **버그** [CI-3809]
- **히든 스펙 필터링 → 알림-화면 불일치**: 관리자 종료 시 목록에서 제외하는 히든 스펙(PR #750)이 알림에는 미적용 — **버그** [CI-3777]
- **정책 변경(미지급) 후 PENDING_WRITE 잔존**: 연차 미지급 정책으로 변경 시 기존 촉진 이력/TODO/알림 자동 정리 로직 없음 → 홈피드에 표시되나 델리에서는 버킷 매칭 숨김 처리로 미표시 — **버그** [CI-3932]
