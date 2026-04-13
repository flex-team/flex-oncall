"""
Unit tests for domain_router.parse_ttl()

Run with:  python3 test_domain_router.py -v
"""

import io
import os
import sys
import textwrap
import unittest

# Allow running from any working directory
sys.path.insert(0, os.path.dirname(__file__))
from domain_router import (
    parse_ttl,
    _parse_quoted_values,
    _parse_ref_values,
    tokenize,
    is_match,
    match_tokens,
    match_phrases,
    calculate_scores,
    calculate_confidence,
    determine_primary_related,
    TICKET_PATTERN,
    lookup_ticket,
    _find_note_location,
    build_result,
    route,
)


# ---------------------------------------------------------------------------
# Shared test fixture
# ---------------------------------------------------------------------------

SAMPLE_TTL = """
    @prefix d: <b:prop/> .
    @prefix : <b:domain/> .
    @prefix g: <b:gloss/> .
    @prefix n: <b:note/> .

    :notification
      d:n   "알림 (Notification)" ;
      d:kw  "알림" , "notification" , "이메일" , "SES" ;
      d:syn "알림이 안 왔어요" , "메일 못 받았어요" ;
      d:mod "notification-deliver" , "ses-feedback" ;
      d:repo "flex-pavement-backend" ;
      d:x   :time-tracking .

    :time-tracking
      d:n   "근태/휴가 (Time Tracking)" ;
      d:kw  "휴가" , "연차" , "근태" , "time-off" ;
      d:syn "휴가 신청이 안 돼요" , "연차 차감이 잘못됐어요" ;
      d:mod "timeoff-service" ;
      d:repo "flex-timetracking-backend" ;
      d:x   :notification .

    :payroll
      d:n   "급여 (Payroll)" ;
      d:kw  "급여" , "페이롤" , "payroll" , "공제" ;
      d:syn "급여 계산이 틀렸어요" ;
      d:mod "payroll-calculator" ;
      d:repo "flex-payroll-backend" .

    g:noti-01
      d:in :notification ;
      d:q  "알림이 안 왔어요" , "푸시 안 왔어요" ;
      d:a  "notification_deliver 수신자 역할 확인" .

    g:noti-02
      d:in :notification ;
      d:q  "메일 못 받았어요" ;
      d:a  "SES Delivery 확인" .

    g:tt-01
      d:in :time-tracking ;
      d:q  "연차 잔여일수 틀려요" ;
      d:a  "timeoff balance 재계산 필요" .

    n:CI-1001
      d:in :notification ;
      d:v  "bug" ;
      d:st "C" ;
      d:ca "2026-01-01" ;
      d:s  "알림 발송 실패 — SES 설정 오류" .

    n:CI-1002
      d:in :notification ;
      d:v  "spec" ;
      d:st "C" ;
      d:ca "2026-01-02" ;
      d:s  "알림 스펙 확인 — 정상 동작임" .

    n:CI-2001
      d:in :time-tracking ;
      d:v  "bug" ;
      d:st "C" ;
      d:ca "2026-02-01" ;
      d:s  "연차 잔여일수 오계산" .
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_string(ttl: str):
    """Write TTL text to a temp file and parse it."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl',
                                     delete=False, encoding='utf-8') as f:
        f.write(textwrap.dedent(ttl))
        name = f.name
    try:
        return parse_ttl(name)
    finally:
        os.unlink(name)


# ---------------------------------------------------------------------------
# Low-level helper tests
# ---------------------------------------------------------------------------

class TestParseQuotedValues(unittest.TestCase):

    def test_single_value(self):
        self.assertEqual(_parse_quoted_values('"hello"'), ['hello'])

    def test_multiple_values(self):
        self.assertEqual(
            _parse_quoted_values('"알림" , "notification" , "이메일"'),
            ['알림', 'notification', '이메일'],
        )

    def test_escaped_quote(self):
        result = _parse_quoted_values(r'"say \"hi\""')
        self.assertEqual(result, ['say \\"hi\\"'])

    def test_empty(self):
        self.assertEqual(_parse_quoted_values(''), [])

    def test_no_quotes(self):
        self.assertEqual(_parse_quoted_values(':time-tracking , :approval'), [])


class TestParseRefValues(unittest.TestCase):

    def test_single_ref(self):
        self.assertEqual(_parse_ref_values(':notification'), [':notification'])

    def test_multiple_refs(self):
        self.assertEqual(
            _parse_ref_values(':time-tracking , :approval , :annual-promotion'),
            [':time-tracking', ':approval', ':annual-promotion'],
        )

    def test_empty(self):
        self.assertEqual(_parse_ref_values(''), [])


# ---------------------------------------------------------------------------
# Domain block parsing
# ---------------------------------------------------------------------------

class TestDomainParsing(unittest.TestCase):

    SIMPLE_TTL = """
        @prefix d: <b:prop/> .
        @prefix : <b:domain/> .

        :notification
          d:n   "알림 (Notification)" ;
          d:cb  "알림 (Notification)" ;
          d:repo "flex-pavement-backend" , "flex-timetracking-backend" ;
          d:mod "notification-deliver" , "ses-feedback" ;
          d:api "/api/v2/notification" , "/api/v2/inbox" ;
          d:kw  "알림" , "notification" , "이메일" ;
          d:syn "알림이 안 왔어요" , "메일 못 받았어요" ;
          d:x   :time-tracking , :approval .
    """

    def setUp(self):
        self.result = _parse_string(self.SIMPLE_TTL)

    def test_domain_exists(self):
        self.assertIn(':notification', self.result['domains'])

    def test_domain_name(self):
        d = self.result['domains'][':notification']
        self.assertEqual(d['name'], '알림 (Notification)')

    def test_domain_cookbook(self):
        d = self.result['domains'][':notification']
        self.assertEqual(d['cookbook'], '알림 (Notification)')

    def test_domain_repos(self):
        d = self.result['domains'][':notification']
        self.assertIn('flex-pavement-backend', d['repos'])
        self.assertIn('flex-timetracking-backend', d['repos'])

    def test_domain_modules(self):
        d = self.result['domains'][':notification']
        self.assertIn('notification-deliver', d['modules'])

    def test_domain_apis(self):
        d = self.result['domains'][':notification']
        self.assertIn('/api/v2/notification', d['apis'])

    def test_domain_keywords(self):
        d = self.result['domains'][':notification']
        self.assertIn('알림', d['keywords'])
        self.assertIn('notification', d['keywords'])

    def test_domain_synonyms(self):
        d = self.result['domains'][':notification']
        self.assertIn('알림이 안 왔어요', d['synonyms'])

    def test_domain_cross_domains(self):
        d = self.result['domains'][':notification']
        self.assertIn(':time-tracking', d['cross_domains'])
        self.assertIn(':approval', d['cross_domains'])

    def test_template_absent_when_not_set(self):
        d = self.result['domains'][':notification']
        self.assertIsNone(d['template'])


class TestDomainWithTemplate(unittest.TestCase):

    TTL = """
        @prefix d: <b:prop/> .
        @prefix : <b:domain/> .

        :annual-promotion
          d:n   "연차촉진 (Annual Time-Off Promotion)" ;
          d:tpl "event-calculated" ;
          d:cb  "연차촉진 (Annual Time-Off Promotion)" ;
          d:repo "flex-timetracking-backend" ;
          d:kw  "연차촉진" ;
          d:x   :notification , :time-tracking .
    """

    def test_template_parsed(self):
        result = _parse_string(self.TTL)
        d = result['domains'][':annual-promotion']
        self.assertEqual(d['template'], 'event-calculated')

    def test_cross_domains(self):
        result = _parse_string(self.TTL)
        d = result['domains'][':annual-promotion']
        self.assertIn(':notification', d['cross_domains'])
        self.assertIn(':time-tracking', d['cross_domains'])


class TestMultilineContinuation(unittest.TestCase):
    """Keywords and synonyms that span multiple continuation lines."""

    TTL = """
        @prefix d: <b:prop/> .
        @prefix : <b:domain/> .

        :time-tracking
          d:n   "근태/휴가 (Time Tracking / Time Off)" ;
          d:kw  "휴가" , "연차" ,
                "time-off" , "근태" ;
          d:syn "휴일대체 기간이 안 맞아요" ,
                "보상휴가 부여 안 돼요" .
    """

    def setUp(self):
        self.result = _parse_string(self.TTL)
        self.d = self.result['domains'][':time-tracking']

    def test_multiline_keywords(self):
        self.assertIn('휴가', self.d['keywords'])
        self.assertIn('연차', self.d['keywords'])
        self.assertIn('time-off', self.d['keywords'])
        self.assertIn('근태', self.d['keywords'])

    def test_multiline_synonyms(self):
        self.assertIn('휴일대체 기간이 안 맞아요', self.d['synonyms'])
        self.assertIn('보상휴가 부여 안 돼요', self.d['synonyms'])


# ---------------------------------------------------------------------------
# Glossary block parsing
# ---------------------------------------------------------------------------

class TestGlossaryParsing(unittest.TestCase):

    TTL = """
        @prefix d: <b:prop/> .
        @prefix : <b:domain/> .
        @prefix g: <b:gloss/> .

        g:noti-01
          d:in :notification ;
          d:q  "알림이 안 왔어요" ;
          d:a  "notification_deliver 수신자 역할 확인" .

        g:noti-02
          d:in :notification ;
          d:q  "메일 못 받았어요" ;
          d:a  "SES Delivery 확인" .

        g:openapi-01
          d:q "OpenAPI 403 에러" , "OpenAPI 권한 에러" ;
          d:a "grant configuration 권한 세분화" ;
          d:in :openapi .
    """

    def setUp(self):
        self.result = _parse_string(self.TTL)
        self.glossary = self.result['glossary']

    def test_glossary_count(self):
        self.assertEqual(len(self.glossary), 3)

    def test_glossary_ids(self):
        ids = [g['id'] for g in self.glossary]
        self.assertIn('g:noti-01', ids)
        self.assertIn('g:openapi-01', ids)

    def test_glossary_domain(self):
        noti01 = next(g for g in self.glossary if g['id'] == 'g:noti-01')
        self.assertEqual(noti01['domain'], ':notification')

    def test_glossary_single_question(self):
        noti01 = next(g for g in self.glossary if g['id'] == 'g:noti-01')
        self.assertEqual(noti01['questions'], ['알림이 안 왔어요'])

    def test_glossary_multi_question(self):
        openapi01 = next(g for g in self.glossary if g['id'] == 'g:openapi-01')
        self.assertIn('OpenAPI 403 에러', openapi01['questions'])
        self.assertIn('OpenAPI 권한 에러', openapi01['questions'])

    def test_glossary_answer(self):
        noti01 = next(g for g in self.glossary if g['id'] == 'g:noti-01')
        self.assertEqual(noti01['answer'], 'notification_deliver 수신자 역할 확인')


# ---------------------------------------------------------------------------
# Note block parsing
# ---------------------------------------------------------------------------

class TestNoteParsing(unittest.TestCase):

    TTL = """
        @prefix d: <b:prop/> .
        @prefix : <b:domain/> .
        @prefix n: <b:note/> .

        n:CI-4404
          d:in :review ;
          d:v  "spec" ;
          d:st "C" ;
          d:ca "2026-04-13" ;
          d:s  "평가 등급 산출 오류 — 상태 변경 경합으로 factor grade 미생성" .

        n:CI-4145
          d:in :integration ;
          d:v  "spec" ;
          d:x  :time-tracking ;
          d:st "C" ;
          d:ca "2026-03-31" ;
          d:s  "세콤/캡스/텔레캅 퇴근 정시 고정" .

        n:CI-3964
          d:in :payroll ;
          d:v  "investigating" ;
          d:s  "중도정산 시 납부할 건강보험료가 자동 계산되지 않음" .
    """

    def setUp(self):
        self.result = _parse_string(self.TTL)
        self.notes = self.result['notes']

    def test_note_keys_strip_prefix(self):
        self.assertIn('CI-4404', self.notes)
        self.assertIn('CI-4145', self.notes)
        # Should NOT have n: prefix
        self.assertNotIn('n:CI-4404', self.notes)

    def test_note_domain(self):
        self.assertEqual(self.notes['CI-4404']['domain'], ':review')

    def test_note_verdict(self):
        self.assertEqual(self.notes['CI-4404']['verdict'], 'spec')

    def test_note_status(self):
        self.assertEqual(self.notes['CI-4404']['status'], 'C')

    def test_note_consolidated_at(self):
        self.assertEqual(self.notes['CI-4404']['consolidated_at'], '2026-04-13')

    def test_note_summary(self):
        self.assertIn('평가 등급 산출 오류', self.notes['CI-4404']['summary'])

    def test_note_cross_domains(self):
        self.assertIn(':time-tracking', self.notes['CI-4145']['cross_domains'])

    def test_note_missing_optional_fields(self):
        n = self.notes['CI-3964']
        self.assertIsNone(n['status'])
        self.assertIsNone(n['consolidated_at'])
        self.assertEqual(n['cross_domains'], [])


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):

    def test_empty_file(self):
        result = _parse_string('')
        self.assertEqual(result['domains'], {})
        self.assertEqual(result['glossary'], [])
        self.assertEqual(result['notes'], {})

    def test_prefix_only_file(self):
        ttl = "@prefix d: <b:prop/> .\n@prefix : <b:domain/> .\n"
        result = _parse_string(ttl)
        self.assertEqual(result['domains'], {})

    def test_comment_lines_ignored(self):
        ttl = """
            @prefix d: <b:prop/> .
            @prefix : <b:domain/> .
            # This is a comment
            :test-domain
              d:n "Test" ;
              # inline comment
              d:kw "kw1" .
        """
        result = _parse_string(ttl)
        self.assertIn(':test-domain', result['domains'])
        self.assertIn('kw1', result['domains'][':test-domain']['keywords'])

    def test_no_optional_fields(self):
        ttl = """
            @prefix d: <b:prop/> .
            @prefix : <b:domain/> .

            :minimal
              d:n "Minimal Domain" .
        """
        result = _parse_string(ttl)
        d = result['domains'][':minimal']
        self.assertEqual(d['name'], 'Minimal Domain')
        self.assertEqual(d['keywords'], [])
        self.assertEqual(d['synonyms'], [])
        self.assertEqual(d['modules'], [])
        self.assertEqual(d['repos'], [])
        self.assertEqual(d['apis'], [])
        self.assertIsNone(d['cookbook'])
        self.assertIsNone(d['template'])
        self.assertEqual(d['cross_domains'], [])

    def test_semicolon_only_continuation(self):
        """
        Real-world pattern in account domain:
        continuation line that itself is just quoted values ending with ';'
        This must be treated as continuation of d:kw, not a new property.
        """
        ttl = """
            @prefix d: <b:prop/> .
            @prefix : <b:domain/> .

            :account
              d:kw  "이메일변경" , "관리자계정" ,
                    "퇴사자계정" , "primary_user_id" ;
              d:syn "이메일 변경해주세요" .
        """
        result = _parse_string(ttl)
        d = result['domains'][':account']
        self.assertIn('이메일변경', d['keywords'])
        self.assertIn('관리자계정', d['keywords'])
        self.assertIn('퇴사자계정', d['keywords'])
        self.assertIn('primary_user_id', d['keywords'])

    def test_multiple_domains(self):
        ttl = """
            @prefix d: <b:prop/> .
            @prefix : <b:domain/> .

            :domain-a
              d:n "Domain A" .

            :domain-b
              d:n "Domain B" .
        """
        result = _parse_string(ttl)
        self.assertIn(':domain-a', result['domains'])
        self.assertIn(':domain-b', result['domains'])

    def test_mixed_block_types(self):
        ttl = """
            @prefix d: <b:prop/> .
            @prefix : <b:domain/> .
            @prefix g: <b:gloss/> .
            @prefix n: <b:note/> .

            :dom
              d:n "Dom" .

            g:dom-01
              d:in :dom ;
              d:q  "Question?" ;
              d:a  "Answer" .

            n:CI-9999
              d:in :dom ;
              d:v  "spec" ;
              d:s  "Summary" .
        """
        result = _parse_string(ttl)
        self.assertEqual(len(result['domains']), 1)
        self.assertEqual(len(result['glossary']), 1)
        self.assertEqual(len(result['notes']), 1)
        self.assertIn('CI-9999', result['notes'])


# ---------------------------------------------------------------------------
# Real file integration tests
# ---------------------------------------------------------------------------

REAL_TTL_PATH = os.path.join(os.path.dirname(__file__), '..', 'domain-map.ttl')


@unittest.skipUnless(os.path.exists(REAL_TTL_PATH), "domain-map.ttl not found")
class TestRealFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = parse_ttl(REAL_TTL_PATH)

    def test_domain_count(self):
        self.assertGreaterEqual(len(self.result['domains']), 20,
                                f"Expected >=20 domains, got {len(self.result['domains'])}")

    def test_glossary_count(self):
        self.assertGreaterEqual(len(self.result['glossary']), 100,
                                f"Expected >=100 glossary entries, got {len(self.result['glossary'])}")

    def test_note_count(self):
        self.assertGreaterEqual(len(self.result['notes']), 200,
                                f"Expected >=200 notes, got {len(self.result['notes'])}")

    def test_known_domain_notification(self):
        self.assertIn(':notification', self.result['domains'])

    def test_known_domain_time_tracking(self):
        self.assertIn(':time-tracking', self.result['domains'])

    def test_notification_keywords_populated(self):
        d = self.result['domains'][':notification']
        self.assertTrue(len(d['keywords']) > 5,
                        f"notification should have many keywords, got {len(d['keywords'])}")

    def test_notification_repos(self):
        d = self.result['domains'][':notification']
        self.assertIn('flex-pavement-backend', d['repos'])

    def test_time_tracking_multiline_keywords(self):
        """
        time-tracking has a very long keyword list spanning many lines.
        Verify that keywords from different continuation lines are all captured.
        """
        d = self.result['domains'][':time-tracking']
        self.assertIn('휴가', d['keywords'])
        self.assertIn('근태', d['keywords'])
        # These are from later continuation lines
        self.assertIn('캘린더', d['keywords'])
        self.assertIn('cleansing', d['keywords'])

    def test_account_domain_kw_continuation(self):
        """
        account domain has continuation lines ending with ';' that look like
        a new property opener — they must still be treated as d:kw continuation.
        """
        d = self.result['domains'][':account']
        self.assertIn('이메일변경', d['keywords'])
        self.assertIn('TOTP', d['keywords'])

    def test_notes_have_domain(self):
        for note_id, note in self.result['notes'].items():
            self.assertIsNotNone(note['domain'],
                                 f"Note {note_id} has no domain")

    def test_glossary_all_have_id(self):
        for entry in self.result['glossary']:
            self.assertTrue(entry['id'].startswith('g:'),
                            f"Glossary entry has bad id: {entry['id']}")

    def test_cross_domains_are_refs(self):
        """All cross_domain values must start with ':'."""
        for domain_id, d in self.result['domains'].items():
            for ref in d['cross_domains']:
                self.assertTrue(ref.startswith(':'),
                                f"Bad cross_domain ref '{ref}' in domain {domain_id}")

    def test_note_ci_4145_cross_domain(self):
        """CI-4145 has d:x :time-tracking — verify it's parsed."""
        self.assertIn('CI-4145', self.result['notes'])
        self.assertIn(':time-tracking', self.result['notes']['CI-4145']['cross_domains'])

    def test_note_ci_4404_exists(self):
        self.assertIn('CI-4404', self.result['notes'])
        n = self.result['notes']['CI-4404']
        self.assertEqual(n['verdict'], 'spec')
        self.assertEqual(n['status'], 'C')

    def test_known_glossary_entries(self):
        ids = {g['id'] for g in self.result['glossary']}
        self.assertIn('g:noti-01', ids)
        self.assertIn('g:tt-01', ids)

    def test_annual_promotion_template(self):
        d = self.result['domains'][':annual-promotion']
        self.assertEqual(d['template'], 'event-calculated')

    def test_checklist_no_template_with_template(self):
        """checklist has d:tpl "state-machine"."""
        d = self.result['domains'][':checklist']
        self.assertEqual(d['template'], 'state-machine')

    def test_work_event_transmitter_domain(self):
        self.assertIn(':work-event-transmitter', self.result['domains'])


# ---------------------------------------------------------------------------
# Tokenizer tests
# ---------------------------------------------------------------------------

class TestTokenize(unittest.TestCase):

    def test_basic_split(self):
        # "안"은 1자 한국어 토큰이므로 제거됨
        result = tokenize("알림이 안 왔어요")
        self.assertIn("알림이", result)
        self.assertIn("왔어요", result)
        self.assertNotIn("안", result)

    def test_single_char_removed(self):
        # 1자 토큰(예: "이", "가") 제거
        result = tokenize("알림이 이 안 왔어요")
        self.assertNotIn("이", result)
        self.assertIn("알림이", result)

    def test_lowercase(self):
        result = tokenize("SES Notification")
        self.assertIn("ses", result)
        self.assertIn("notification", result)

    def test_empty_input(self):
        self.assertEqual(tokenize(""), [])

    def test_whitespace_only(self):
        self.assertEqual(tokenize("   "), [])

    def test_single_char_only(self):
        self.assertEqual(tokenize("a b c"), [])

    def test_mixed(self):
        result = tokenize("SES 알림 이 안 왔어요")
        self.assertIn("ses", result)
        self.assertIn("알림", result)
        self.assertNotIn("이", result)


# ---------------------------------------------------------------------------
# is_match tests
# ---------------------------------------------------------------------------

class TestIsMatch(unittest.TestCase):

    def test_token_in_value(self):
        # token이 value의 부분문자열
        self.assertTrue(is_match("noti", "notification"))

    def test_value_in_token(self):
        # value가 token의 부분문자열
        self.assertTrue(is_match("notification_deliver", "notification"))

    def test_exact_match(self):
        self.assertTrue(is_match("ses", "ses"))

    def test_case_insensitive(self):
        self.assertTrue(is_match("ses", "SES"))
        self.assertTrue(is_match("SES", "ses"))

    def test_no_match(self):
        self.assertFalse(is_match("payroll", "notification"))

    def test_bidirectional_real(self):
        # 명세 예시: is_match("ses", "SES") → True
        self.assertTrue(is_match("ses", "SES"))
        # is_match("notification_deliver", "notification") → True
        self.assertTrue(is_match("notification_deliver", "notification"))


# ---------------------------------------------------------------------------
# match_tokens tests
# ---------------------------------------------------------------------------

def _sample_data():
    """SAMPLE_TTL을 파싱한 data dict 반환."""
    import tempfile, textwrap
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl',
                                     delete=False, encoding='utf-8') as f:
        f.write(textwrap.dedent(SAMPLE_TTL))
        name = f.name
    try:
        return parse_ttl(name)
    finally:
        os.unlink(name)


class TestMatchTokens(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = _sample_data()

    def test_keyword_weight_3(self):
        # "알림" → :notification d:kw, weight=3
        bd = match_tokens(["알림"], self.data)
        self.assertIn(":notification", bd)
        self.assertEqual(bd[":notification"]["d:kw"], 3)

    def test_glossary_question_weight_3(self):
        # "알림이" → g:noti-01 d:q "알림이 안 왔어요" 에 부분 매칭, weight=3
        bd = match_tokens(["알림이"], self.data)
        self.assertIn(":notification", bd)
        self.assertGreaterEqual(bd[":notification"]["g:q"], 3)

    def test_glossary_answer_weight_2(self):
        # "확인" → g:noti-01 answer "notification_deliver 수신자 역할 확인" 에 매칭, weight=2
        bd = match_tokens(["확인"], self.data)
        self.assertIn(":notification", bd)
        self.assertGreaterEqual(bd[":notification"]["g:a"], 2)

    def test_note_summary_spec_weight_0(self):
        # CI-1002 (verdict=spec)의 summary "알림 스펙 확인"에서 "스펙"이 매칭되어도 점수 없어야
        bd = match_tokens(["스펙"], self.data)
        # :notification이 아예 없거나 있어도 d:s=0
        if ":notification" in bd:
            self.assertEqual(bd[":notification"]["d:s"], 0)

    def test_note_summary_bug_weight_1(self):
        # CI-1001 (verdict=bug)의 summary "알림 발송 실패" 에서 "발송" 매칭 → d:s += 1
        bd = match_tokens(["발송"], self.data)
        self.assertIn(":notification", bd)
        self.assertEqual(bd[":notification"]["d:s"], 1)

    def test_domain_name_weight_1(self):
        # "payroll" → :payroll d:n "급여 (Payroll)" 에 매칭, weight=1
        bd = match_tokens(["payroll"], self.data)
        self.assertIn(":payroll", bd)
        self.assertGreaterEqual(bd[":payroll"]["d:n"], 1)

    def test_module_weight_1(self):
        # "ses-feedback" → :notification d:mod에 매칭, weight=1
        bd = match_tokens(["ses-feedback"], self.data)
        self.assertIn(":notification", bd)
        self.assertGreaterEqual(bd[":notification"]["d:mod"], 1)

    def test_no_match_empty(self):
        # 매칭 없는 토큰
        bd = match_tokens(["xyzabcdef12345"], self.data)
        self.assertEqual(bd, {})

    def test_phrase_bonus_initialized_zero(self):
        # match_tokens 결과에 phrase_bonus 키가 있고 0이어야 함
        bd = match_tokens(["알림"], self.data)
        self.assertIn("phrase_bonus", bd[":notification"])
        self.assertEqual(bd[":notification"]["phrase_bonus"], 0)


# ---------------------------------------------------------------------------
# match_phrases tests
# ---------------------------------------------------------------------------

class TestMatchPhrases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = _sample_data()

    def test_two_overlapping_tokens_give_bonus(self):
        # "알림이 안 왔어요" → tokens: ["알림이", "안", "왔어요"]
        # g:noti-01 d:q "알림이 안 왔어요" → overlap >= 2
        tokens = tokenize("알림이 안 왔어요")
        bd = match_tokens(tokens, self.data)
        match_phrases(tokens, self.data, bd)
        self.assertEqual(bd[":notification"]["phrase_bonus"], 3)

    def test_one_token_overlap_no_bonus(self):
        # "알림" 한 단어만 → overlap < 2, 보너스 없음
        tokens = ["알림"]
        bd = match_tokens(tokens, self.data)
        initial_bonus = bd.get(":notification", {}).get("phrase_bonus", 0)
        match_phrases(tokens, self.data, bd)
        self.assertEqual(bd.get(":notification", {}).get("phrase_bonus", 0), initial_bonus)

    def test_max_one_bonus_per_domain(self):
        # 두 개의 synonyms/questions 모두 2+ 겹쳐도 domain당 최대 1회 (+3)
        # "알림이 안 왔어요 메일 못 받았어요" → :notification에 두 구문 모두 매칭될 수 있음
        tokens = tokenize("알림이 안 왔어요 메일 못 받았어요")
        bd = match_tokens(tokens, self.data)
        match_phrases(tokens, self.data, bd)
        self.assertEqual(bd[":notification"]["phrase_bonus"], 3)  # not 6

    def test_bonus_only_on_matched_domain(self):
        # :notification 관련 토큰만 있을 때 :payroll에 보너스 없어야
        tokens = tokenize("알림이 안 왔어요")
        bd = match_tokens(tokens, self.data)
        match_phrases(tokens, self.data, bd)
        payroll_bonus = bd.get(":payroll", {}).get("phrase_bonus", 0)
        self.assertEqual(payroll_bonus, 0)


# ---------------------------------------------------------------------------
# calculate_scores tests
# ---------------------------------------------------------------------------

class TestCalculateScores(unittest.TestCase):

    def test_sum_all_fields(self):
        breakdowns = {
            ":notification": {
                "d:kw": 6,
                "d:syn": 3,
                "g:q": 3,
                "g:a": 2,
                "d:s": 1,
                "d:n": 1,
                "d:mod": 1,
                "phrase_bonus": 3,
            }
        }
        scores = calculate_scores(breakdowns)
        self.assertEqual(scores[":notification"], 20)

    def test_multiple_domains(self):
        breakdowns = {
            ":a": {"d:kw": 3, "d:syn": 0, "g:q": 0, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
            ":b": {"d:kw": 6, "d:syn": 3, "g:q": 0, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 3},
        }
        scores = calculate_scores(breakdowns)
        self.assertEqual(scores[":a"], 3)
        self.assertEqual(scores[":b"], 12)

    def test_empty_breakdowns(self):
        self.assertEqual(calculate_scores({}), {})


# ---------------------------------------------------------------------------
# calculate_confidence tests
# ---------------------------------------------------------------------------

class TestCalculateConfidence(unittest.TestCase):

    def test_high_top_gte6_gap_gte3(self):
        scores = {":notification": 10, ":time-tracking": 3}
        self.assertEqual(calculate_confidence(scores), "high")

    def test_low_close_scores(self):
        scores = {":notification": 10, ":time-tracking": 9}
        self.assertEqual(calculate_confidence(scores), "low")

    def test_low_top_lt6(self):
        scores = {":notification": 5, ":time-tracking": 1}
        self.assertEqual(calculate_confidence(scores), "low")

    def test_none_empty(self):
        self.assertEqual(calculate_confidence({}), "none")

    def test_none_all_zero(self):
        scores = {":notification": 0, ":time-tracking": 0}
        self.assertEqual(calculate_confidence(scores), "none")

    def test_single_domain_high(self):
        # 2nd=0이므로 gap=top >= 6이면 high
        scores = {":notification": 9}
        self.assertEqual(calculate_confidence(scores), "high")

    def test_single_domain_low_score(self):
        scores = {":notification": 4}
        self.assertEqual(calculate_confidence(scores), "low")

    def test_exact_boundary_high(self):
        # top=6, gap=3 (second=3)
        scores = {":a": 6, ":b": 3}
        self.assertEqual(calculate_confidence(scores), "high")

    def test_exact_boundary_low_gap(self):
        # top=6, gap=2 (second=4)
        scores = {":a": 6, ":b": 4}
        self.assertEqual(calculate_confidence(scores), "low")


# ---------------------------------------------------------------------------
# determine_primary_related tests
# ---------------------------------------------------------------------------

class TestDeterminePrimaryRelated(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = _sample_data()

    def test_highest_score_is_primary(self):
        scores = {":notification": 15, ":time-tracking": 5, ":payroll": 2}
        breakdowns = {
            ":notification": {"d:kw": 9, "d:syn": 3, "g:q": 3, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
            ":time-tracking": {"d:kw": 3, "d:syn": 0, "g:q": 2, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
            ":payroll": {"d:kw": 2, "d:syn": 0, "g:q": 0, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
        }
        primary, related = determine_primary_related(scores, breakdowns, self.data)
        self.assertIn(":notification", primary)
        self.assertNotIn(":notification", related)

    def test_related_from_cross_domains(self):
        # :notification has d:x :time-tracking
        scores = {":notification": 15, ":time-tracking": 2}
        breakdowns = {
            ":notification": {"d:kw": 9, "d:syn": 3, "g:q": 3, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
            ":time-tracking": {"d:kw": 2, "d:syn": 0, "g:q": 0, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
        }
        primary, related = determine_primary_related(scores, breakdowns, self.data)
        self.assertIn(":notification", primary)
        # :time-tracking은 :notification의 d:x에 있으므로 related
        self.assertIn(":time-tracking", related)

    def test_tiebreak_by_keyword_hits(self):
        # 동점이지만 d:kw가 더 높은 쪽이 primary
        scores = {":notification": 6, ":time-tracking": 6}
        breakdowns = {
            ":notification": {"d:kw": 6, "d:syn": 0, "g:q": 0, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
            ":time-tracking": {"d:kw": 3, "d:syn": 3, "g:q": 0, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
        }
        primary, _ = determine_primary_related(scores, breakdowns, self.data)
        self.assertIn(":notification", primary)
        self.assertNotIn(":time-tracking", primary)

    def test_empty_scores(self):
        primary, related = determine_primary_related({}, {}, self.data)
        self.assertEqual(primary, [])
        self.assertEqual(related, [])

    def test_bidirectional_related(self):
        # :time-tracking도 d:x :notification을 가지므로 양방향
        # :time-tracking이 primary면 :notification이 related에 포함
        scores = {":time-tracking": 10, ":notification": 2}
        breakdowns = {
            ":time-tracking": {"d:kw": 9, "d:syn": 0, "g:q": 1, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
            ":notification": {"d:kw": 2, "d:syn": 0, "g:q": 0, "g:a": 0, "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0},
        }
        primary, related = determine_primary_related(scores, breakdowns, self.data)
        self.assertIn(":time-tracking", primary)
        self.assertIn(":notification", related)


# ---------------------------------------------------------------------------
# TestTicketLookup
# ---------------------------------------------------------------------------

class TestTicketLookup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = _sample_data()

    def test_lookup_success(self):
        note = lookup_ticket("CI-1001", self.data)
        self.assertIsNotNone(note)
        self.assertEqual(note["domain"], ":notification")
        self.assertEqual(note["verdict"], "bug")

    def test_lookup_not_found_returns_none(self):
        note = lookup_ticket("CI-9999", self.data)
        self.assertIsNone(note)

    def test_ticket_pattern_matches_valid(self):
        self.assertIsNotNone(TICKET_PATTERN.match("CI-4404"))
        self.assertIsNotNone(TICKET_PATTERN.match("TT-123"))
        self.assertIsNotNone(TICKET_PATTERN.match("QNA-9999"))

    def test_ticket_pattern_rejects_invalid(self):
        self.assertIsNone(TICKET_PATTERN.match("알림이 안 왔어요"))
        self.assertIsNone(TICKET_PATTERN.match("ci-1234"))   # lowercase
        self.assertIsNone(TICKET_PATTERN.match("CI-"))       # no digits
        self.assertIsNone(TICKET_PATTERN.match("1234"))      # no prefix

    def test_find_note_location_empty_brain_dir(self):
        location = _find_note_location("CI-1001", "")
        self.assertEqual(location, "unknown")

    def test_find_note_location_active(self):
        # Use the real brain/notes directory
        brain_dir = os.path.join(os.path.dirname(__file__), "..")
        # CI-3964 is an active note (present in notes/ root in real file)
        location = _find_note_location("CI-3964", brain_dir)
        self.assertIn(location, ["active", "unknown"])

    def test_find_note_location_archive(self):
        brain_dir = os.path.join(os.path.dirname(__file__), "..")
        # CI-3568 is an archived note
        location = _find_note_location("CI-3568", brain_dir)
        self.assertIn(location, ["archive", "unknown"])


# ---------------------------------------------------------------------------
# TestRoute (end-to-end with SAMPLE_TTL)
# ---------------------------------------------------------------------------

def _make_sample_ttl_file():
    """Write SAMPLE_TTL to a temp file, return path."""
    import tempfile, textwrap
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl',
                                     delete=False, encoding='utf-8') as f:
        f.write(textwrap.dedent(SAMPLE_TTL))
        return f.name


class TestRoute(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ttl_path = _make_sample_ttl_file()

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.ttl_path)

    def test_returns_required_keys(self):
        result = route("알림이 안 왔어요", self.ttl_path)
        required = {"input", "confidence", "primary", "related",
                    "glossary_hits", "related_notes", "score_breakdown", "no_match"}
        self.assertEqual(required, required & set(result.keys()))

    def test_notification_query_primary(self):
        result = route("알림이 안 왔어요", self.ttl_path)
        primary_domains = [p["domain"] for p in result["primary"]]
        self.assertIn(":notification", primary_domains)

    def test_notification_confidence_high(self):
        result = route("알림이 안 왔어요", self.ttl_path)
        self.assertEqual(result["confidence"], "high")

    def test_ticket_id_lookup_ci_1001(self):
        result = route("CI-1001", self.ttl_path)
        self.assertEqual(result["confidence"], "high")
        primary_domains = [p["domain"] for p in result["primary"]]
        self.assertIn(":notification", primary_domains)
        self.assertFalse(result["no_match"])

    def test_ticket_id_not_found_falls_through(self):
        # "CI-9999" is a valid ticket pattern but not in notes → tokenizes normally
        result = route("CI-9999", self.ttl_path)
        # Should still return a valid structure (no_match may be True)
        self.assertIn("no_match", result)
        self.assertIn("primary", result)

    def test_unrelated_text_no_match(self):
        result = route("완전히무관한내용입니다xyzfoo바bar", self.ttl_path)
        self.assertTrue(result["no_match"])
        self.assertEqual(result["primary"], [])

    def test_glossary_hits_included(self):
        result = route("알림이 안 왔어요", self.ttl_path)
        # g:noti-01 has d:q "알림이 안 왔어요" matching ":notification" (primary)
        hit_ids = [h["id"] for h in result["glossary_hits"]]
        self.assertIn("g:noti-01", hit_ids)

    def test_no_match_flag_false_for_match(self):
        result = route("알림이 안 왔어요", self.ttl_path)
        self.assertFalse(result["no_match"])

    def test_score_breakdown_only_positive(self):
        result = route("알림이 안 왔어요", self.ttl_path)
        for domain_id, bd in result["score_breakdown"].items():
            self.assertGreater(bd["total"], 0)
            for k, v in bd.items():
                if k != "total":
                    self.assertGreater(v, 0, f"field {k} in {domain_id} should be > 0")

    def test_primary_has_domain_fields(self):
        result = route("알림이 안 왔어요", self.ttl_path)
        for p in result["primary"]:
            self.assertIn("domain", p)
            self.assertIn("score", p)
            self.assertIn("repos", p)
            self.assertIn("modules", p)
            self.assertIn("apis", p)


# ---------------------------------------------------------------------------
# TestIntegrationWithRealTTL — 실제 domain-map.ttl 기반 end-to-end 검증
# ---------------------------------------------------------------------------

class TestIntegrationWithRealTTL(unittest.TestCase):
    """실제 domain-map.ttl로 end-to-end 검증."""

    TTL_PATH = os.path.join(os.path.dirname(__file__), '..', 'domain-map.ttl')

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(cls.TTL_PATH):
            raise unittest.SkipTest('domain-map.ttl not found')
        cls.data = parse_ttl(cls.TTL_PATH)

    # ------------------------------------------------------------------
    # 1. Parsing counts
    # ------------------------------------------------------------------

    def test_parsing_domains_gte_20(self):
        self.assertGreaterEqual(
            len(self.data['domains']),
            20,
            f"domains={len(self.data['domains'])}, expected >= 20",
        )

    def test_parsing_glossary_gte_100(self):
        self.assertGreaterEqual(
            len(self.data['glossary']),
            100,
            f"glossary={len(self.data['glossary'])}, expected >= 100",
        )

    def test_parsing_notes_gte_200(self):
        self.assertGreaterEqual(
            len(self.data['notes']),
            200,
            f"notes={len(self.data['notes'])}, expected >= 200",
        )

    # ------------------------------------------------------------------
    # 2. Known routing cases
    # ------------------------------------------------------------------

    def test_route_notification(self):
        result = route('알림이 안 왔어요', self.TTL_PATH)
        primary = [p['domain'] for p in result['primary']]
        self.assertIn(':notification', primary)

    def test_route_time_tracking_attendance(self):
        result = route('출퇴근 기록이 이상해요', self.TTL_PATH)
        primary = [p['domain'] for p in result['primary']]
        self.assertIn(':time-tracking', primary)

    def test_route_annual_promotion(self):
        result = route('연차촉진 문서가 안 보여요', self.TTL_PATH)
        primary = [p['domain'] for p in result['primary']]
        self.assertIn(':annual-promotion', primary)

    def test_route_approval(self):
        result = route('승인 요청이 안 돼요', self.TTL_PATH)
        primary = [p['domain'] for p in result['primary']]
        self.assertIn(':approval', primary)

    def test_route_payroll(self):
        result = route('급여 명세서가 안 보여요', self.TTL_PATH)
        primary = [p['domain'] for p in result['primary']]
        self.assertIn(':payroll', primary)

    def test_route_time_tracking_vacation(self):
        result = route('휴가가 안 들어갔어요', self.TTL_PATH)
        primary = [p['domain'] for p in result['primary']]
        self.assertIn(':time-tracking', primary)

    # ------------------------------------------------------------------
    # 3. Ticket ID lookup
    # ------------------------------------------------------------------

    def test_ticket_id_ci_4404_no_match_false(self):
        result = route('CI-4404', self.TTL_PATH)
        self.assertFalse(result['no_match'], "CI-4404 is a known ticket, no_match should be False")

    # ------------------------------------------------------------------
    # 4. Ambiguous input — confidence should be low or none
    # ------------------------------------------------------------------

    def test_ambiguous_input_low_confidence(self):
        # '처리'는 여러 도메인에 걸쳐 약하게 분산되어 낮은 confidence를 반환한다
        result = route('처리', self.TTL_PATH)
        self.assertIn(
            result['confidence'],
            ['low', 'none'],
            f"'처리' is ambiguous, expected low/none but got: {result['confidence']}",
        )

    # ------------------------------------------------------------------
    # 5. Benchmark — 100 calls, avg latency < 200ms
    # ------------------------------------------------------------------

    def test_benchmark_latency(self):
        """100회 반복, 평균 latency < 200ms."""
        import time
        inputs = [
            '알림이 안 왔어요',
            '출퇴근 기록이 이상해요',
            '연차촉진 문서가 안 보여요',
            'CI-4404',
            '승인 요청이 안 돼요',
        ]
        start = time.perf_counter()
        for _ in range(20):
            for inp in inputs:
                route(inp, self.TTL_PATH)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000
        print(f'\n  Benchmark: 100 calls, avg={avg_ms:.1f}ms, total={elapsed:.2f}s')
        self.assertLess(avg_ms, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
