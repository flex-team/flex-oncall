"""
TTL parser for brain/domain-map.ttl

Parses the Turtle (TTL) knowledge graph file and returns structured Python dicts.
No external dependencies — stdlib only.
"""

import json
import os
import re
import sys
from typing import Any


# ---------------------------------------------------------------------------
# Low-level tokeniser
# ---------------------------------------------------------------------------

def _parse_quoted_values(text: str) -> list[str]:
    """
    Extract all double-quoted string values from a fragment like:
      "val1" , "val2" , "val3"
    Handles escaped quotes inside strings.
    """
    values = []
    i = 0
    while i < len(text):
        if text[i] == '"':
            # find matching closing quote, respecting backslash escapes
            j = i + 1
            while j < len(text):
                if text[j] == '\\':
                    j += 2
                    continue
                if text[j] == '"':
                    values.append(text[i + 1:j])
                    i = j + 1
                    break
                j += 1
            else:
                # unclosed quote – take the rest as value
                values.append(text[i + 1:])
                break
        else:
            i += 1
    return values


def _parse_ref_values(text: str) -> list[str]:
    """
    Extract colon-prefixed references from a fragment like:
      :time-tracking , :approval , :annual-promotion
    """
    return re.findall(r':[A-Za-z0-9_-]+', text)


# ---------------------------------------------------------------------------
# Block accumulator
# ---------------------------------------------------------------------------

class _Block:
    """Accumulates raw lines belonging to one subject (domain/glossary/note)."""

    def __init__(self, subject: str):
        self.subject = subject
        # prop_name -> list[str of raw value fragments]
        self.props: dict[str, list[str]] = {}
        self._current_prop: str | None = None
        self._current_frags: list[str] = []

    def _flush(self):
        if self._current_prop:
            self.props.setdefault(self._current_prop, [])
            self.props[self._current_prop].append(" ".join(self._current_frags))
            self._current_prop = None
            self._current_frags = []

    def add_prop_line(self, prop: str, value_fragment: str):
        """Start a new property with its first value fragment."""
        self._flush()
        self._current_prop = prop
        if value_fragment.strip():
            self._current_frags.append(value_fragment.strip())

    def add_continuation(self, fragment: str):
        """Append a continuation line to the current property."""
        if fragment.strip():
            self._current_frags.append(fragment.strip())

    def finish(self):
        self._flush()

    def get_quoted(self, prop: str) -> list[str]:
        """Return all quoted string values for *prop* (across all fragments)."""
        result = []
        for frag in self.props.get(prop, []):
            result.extend(_parse_quoted_values(frag))
        return result

    def get_single_quoted(self, prop: str) -> str | None:
        vals = self.get_quoted(prop)
        return vals[0] if vals else None

    def get_refs(self, prop: str) -> list[str]:
        """Return all :ref values for *prop*."""
        result = []
        for frag in self.props.get(prop, []):
            result.extend(_parse_ref_values(frag))
        return result


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

# Matches lines that start a new subject block
_SUBJECT_RE = re.compile(r'^([:\w][\w:.-]*)$|^([:\w][\w:.-]*)\s')

# Matches a property declaration line (indented)
_PROP_RE = re.compile(r'^\s+(d:[a-z]+)\s+(.*?)([;.]?)\s*$')


def _subject_id(raw: str) -> str | None:
    """
    Return the subject token if *raw* is a subject-starting line, else None.

    Subject lines begin at column 0 with a non-whitespace character that looks
    like  :name  or  g:name  or  n:name  (colon-anchored IDs).
    We deliberately exclude comment lines and prefix declarations.
    """
    line = raw.strip()
    if not line or line.startswith('#') or line.startswith('@'):
        return None
    # Must be a colon-anchored token
    m = re.match(r'^([gnGN]?:[A-Za-z0-9_.-]+)\b', raw)
    if m:
        return m.group(1)
    return None


# Matches inline subject+property on the same line:
#   n:CI-4214 d:in :personnel-appointment ;
_INLINE_SUBJ_PROP_RE = re.compile(
    r'^([gnGN]?:[A-Za-z0-9_.-]+)\s+(d:[a-z]+)\s+(.*?)([;.]?)\s*$'
)


def _is_prop_line(line: str) -> tuple[str, str] | None:
    """
    Return (prop, value_fragment) if *line* is a property line, else None.
    A property line looks like:
        d:kw  "foo" , "bar" ;
        d:x   :ref1 , :ref2 .
    Must be indented.
    """
    if not line or not line[0].isspace():
        return None
    m = _PROP_RE.match(line)
    if m:
        return m.group(1), m.group(2)
    return None


def _is_continuation(line: str) -> bool:
    """
    A continuation line is indented, does not start with d:, and is not blank/comment.
    """
    if not line or not line[0].isspace():
        return False
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        return False
    # Must not look like a property opener
    if re.match(r'd:[a-z]+\s', stripped):
        return False
    return True


def _strip_terminal(value: str) -> str:
    """Remove trailing  ;  or  .  from a value fragment."""
    return re.sub(r'\s*[;.]\s*$', '', value)


def _parse_blocks(path: str) -> list[_Block]:
    """
    Read the TTL file and split into _Block objects.
    Returns blocks in file order.
    """
    blocks: list[_Block] = []
    current: _Block | None = None

    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    for raw in lines:
        # Strip trailing newline but keep leading whitespace for indentation checks
        line = raw.rstrip('\n')

        # Check for inline subject+property on the same line first
        # e.g.  n:CI-4214 d:in :personnel-appointment ;
        inline_m = _INLINE_SUBJ_PROP_RE.match(line)
        if inline_m:
            subject, prop, value_frag = inline_m.group(1), inline_m.group(2), inline_m.group(3)
            if current:
                current.finish()
            current = _Block(subject)
            blocks.append(current)
            current.add_prop_line(prop, _strip_terminal(value_frag))
            continue

        subject = _subject_id(line)
        if subject:
            if current:
                current.finish()
            current = _Block(subject)
            blocks.append(current)
            continue

        if current is None:
            continue

        # Check for property line
        prop_match = _is_prop_line(line)
        if prop_match:
            prop, value_frag = prop_match
            current.add_prop_line(prop, _strip_terminal(value_frag))
            continue

        # Continuation line
        if _is_continuation(line):
            stripped = line.strip()
            current.add_continuation(_strip_terminal(stripped))
            continue

        # Block-ending  .  on its own indented line — flush current property
        if line.strip() == '.':
            current.finish()
            current = None

    if current:
        current.finish()

    return blocks


# ---------------------------------------------------------------------------
# Block → structured output
# ---------------------------------------------------------------------------

def _block_to_domain(b: _Block) -> dict[str, Any]:
    return {
        "name": b.get_single_quoted("d:n"),
        "keywords": b.get_quoted("d:kw"),
        "synonyms": b.get_quoted("d:syn"),
        "modules": b.get_quoted("d:mod"),
        "repos": b.get_quoted("d:repo"),
        "apis": b.get_quoted("d:api"),
        "cookbook": b.get_single_quoted("d:cb"),
        "template": b.get_single_quoted("d:tpl"),
        "cross_domains": b.get_refs("d:x"),
    }


def _block_to_glossary(b: _Block) -> dict[str, Any]:
    # domain ref: d:in holds  :domain-name
    domain_refs = b.get_refs("d:in")
    return {
        "id": b.subject,
        "domain": domain_refs[0] if domain_refs else None,
        "questions": b.get_quoted("d:q"),
        "answer": b.get_single_quoted("d:a"),
    }


def _block_to_note(b: _Block) -> tuple[str, dict[str, Any]]:
    # Strip "n:" prefix for the key
    note_id = b.subject[2:] if b.subject.startswith("n:") else b.subject
    domain_refs = b.get_refs("d:in")
    return note_id, {
        "domain": domain_refs[0] if domain_refs else None,
        "verdict": b.get_single_quoted("d:v"),
        "status": b.get_single_quoted("d:st"),
        "consolidated_at": b.get_single_quoted("d:ca"),
        "summary": b.get_single_quoted("d:s"),
        "cross_domains": b.get_refs("d:x"),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_ttl(path: str) -> dict[str, Any]:
    """
    Parse a TTL file and return:
        {
            "domains":  { ":domain-id": {...}, ... },
            "glossary": [ {"id": "g:xx", "domain": ":x", ...}, ... ],
            "notes":    { "CI-1234": {...}, ... },
        }
    """
    blocks = _parse_blocks(path)

    domains: dict[str, Any] = {}
    glossary: list[dict[str, Any]] = []
    notes: dict[str, Any] = {}

    for b in blocks:
        subj = b.subject
        if subj.startswith("g:"):
            glossary.append(_block_to_glossary(b))
        elif subj.startswith("n:"):
            note_id, note_data = _block_to_note(b)
            notes[note_id] = note_data
        elif subj.startswith(":"):
            domains[subj] = _block_to_domain(b)

    return {"domains": domains, "glossary": glossary, "notes": notes}


# ---------------------------------------------------------------------------
# Matching engine
# ---------------------------------------------------------------------------

def tokenize(text: str) -> list[str]:
    """공백 기준 분리, 1자 토큰 제거, 소문자 변환."""
    return [t.lower() for t in text.split() if len(t) > 1]


def is_match(token: str, value: str) -> bool:
    """양방향 substring 매칭 (대소문자 무시).
    token이 value의 부분문자열이거나, value가 token의 부분문자열이면 True."""
    token_lower = token.lower()
    value_lower = value.lower()
    return token_lower in value_lower or value_lower in token_lower


def match_tokens(tokens: list[str], data: dict) -> dict[str, dict]:
    """각 토큰을 도메인 필드와 매칭, 가중치 합산.

    Returns: {':domain-id': {'d:kw': N, 'd:syn': N, 'g:q': N, 'g:a': N,
                              'd:s': N, 'd:n': N, 'd:mod': N, 'phrase_bonus': 0}, ...}
    """
    WEIGHTS = {
        "d:kw": 3,
        "d:syn": 3,
        "g:q": 3,
        "g:a": 2,
        "d:n": 1,
        "d:mod": 1,
    }

    def _empty_breakdown() -> dict:
        return {k: 0 for k in WEIGHTS} | {"d:s": 0, "phrase_bonus": 0}

    breakdowns: dict[str, dict] = {}

    for token in tokens:
        # --- Domain-level fields ---
        for domain_id, domain in data["domains"].items():
            for kw in domain.get("keywords", []):
                if is_match(token, kw):
                    bd = breakdowns.setdefault(domain_id, _empty_breakdown())
                    bd["d:kw"] += WEIGHTS["d:kw"]

            for syn in domain.get("synonyms", []):
                if is_match(token, syn):
                    bd = breakdowns.setdefault(domain_id, _empty_breakdown())
                    bd["d:syn"] += WEIGHTS["d:syn"]

            if domain.get("name") and is_match(token, domain["name"]):
                bd = breakdowns.setdefault(domain_id, _empty_breakdown())
                bd["d:n"] += WEIGHTS["d:n"]

            for mod in domain.get("modules", []):
                if is_match(token, mod):
                    bd = breakdowns.setdefault(domain_id, _empty_breakdown())
                    bd["d:mod"] += WEIGHTS["d:mod"]

        # --- Glossary fields ---
        for entry in data["glossary"]:
            domain_id = entry.get("domain")
            if not domain_id:
                continue

            for q in entry.get("questions", []):
                if is_match(token, q):
                    bd = breakdowns.setdefault(domain_id, _empty_breakdown())
                    bd["g:q"] += WEIGHTS["g:q"]

            answer = entry.get("answer")
            if answer and is_match(token, answer):
                bd = breakdowns.setdefault(domain_id, _empty_breakdown())
                bd["g:a"] += WEIGHTS["g:a"]

        # --- Note summaries ---
        for note in data["notes"].values():
            domain_id = note.get("domain")
            if not domain_id:
                continue
            # verdict == "spec" → weight 0, 나머지 → weight 1
            if note.get("verdict") == "spec":
                continue
            summary = note.get("summary")
            if summary and is_match(token, summary):
                bd = breakdowns.setdefault(domain_id, _empty_breakdown())
                bd["d:s"] += 1

    return breakdowns


def match_phrases(tokens: list[str], data: dict, breakdowns: dict[str, dict]) -> None:
    """구문 매칭 보너스를 breakdowns에 in-place 적용.

    d:syn 및 g:q 값의 토큰 집합과 입력 토큰 집합의 겹침이 2개 이상이면,
    해당 도메인에 phrase_bonus = 3 적용 (도메인당 최대 1회).
    """
    token_set = set(tokens)
    given_bonus: set[str] = set()

    def _check(domain_id: str, phrase: str) -> None:
        if domain_id in given_bonus:
            return
        phrase_tokens = set(tokenize(phrase))
        overlap = token_set & phrase_tokens
        if len(overlap) >= 2:
            if domain_id not in breakdowns:
                breakdowns[domain_id] = {
                    "d:kw": 0, "d:syn": 0, "g:q": 0, "g:a": 0,
                    "d:s": 0, "d:n": 0, "d:mod": 0, "phrase_bonus": 0
                }
            breakdowns[domain_id]["phrase_bonus"] = 3
            given_bonus.add(domain_id)

    for domain_id, domain in data["domains"].items():
        for syn in domain.get("synonyms", []):
            _check(domain_id, syn)

    for entry in data["glossary"]:
        domain_id = entry.get("domain")
        if not domain_id:
            continue
        for q in entry.get("questions", []):
            _check(domain_id, q)


def apply_unique_kw_bonus(tokens: list[str], data: dict, breakdowns: dict[str, dict]) -> None:
    """도메인 전용 키워드에 보너스 부여.

    입력 토큰이 정확히 하나의 도메인 d:kw에만 exact-match되면
    해당 도메인에 보너스를 준다. 범용 키워드(여러 도메인에서 공유)는 보너스 없음.
    기존 점수를 변경하지 않고 순수 가산만 한다.
    """
    BONUS = 8

    for token in tokens:
        token_lower = token.lower()
        # 이 토큰이 exact-match하는 도메인의 d:kw를 가진 도메인 목록
        exact_domains: list[str] = []
        for domain_id, domain in data["domains"].items():
            for kw in domain.get("keywords", []):
                if token_lower == kw.lower():
                    exact_domains.append(domain_id)
                    break  # 도메인당 1회만

        if len(exact_domains) == 1 and exact_domains[0] in breakdowns:
            breakdowns[exact_domains[0]].setdefault("unique_kw", 0)
            breakdowns[exact_domains[0]]["unique_kw"] += BONUS


def calculate_scores(breakdowns: dict[str, dict]) -> dict[str, int]:
    """도메인별 총점 (모든 필드 가중치 + phrase_bonus 합산)."""
    return {
        domain_id: sum(bd.values())
        for domain_id, bd in breakdowns.items()
    }


def calculate_confidence(scores: dict[str, int]) -> str:
    """'high' if top >= 6 AND gap to 2nd >= 3. 'low' otherwise. 'none' if no matches."""
    if not scores:
        return "none"

    sorted_scores = sorted(scores.values(), reverse=True)
    top = sorted_scores[0]

    if top == 0:
        return "none"

    second = sorted_scores[1] if len(sorted_scores) > 1 else 0
    gap = top - second

    if top >= 6 and gap >= 3:
        return "high"
    return "low"


def determine_primary_related(
    scores: dict[str, int],
    breakdowns: dict[str, dict],
    data: dict,
) -> tuple[list[str], list[str]]:
    """Primary: highest score. Tiebreak: d:kw hits > g:q+g:a hits > both primary.
    Related: primary's d:x + domains referencing primary via d:x (bidirectional)."""
    if not scores:
        return [], []

    max_score = max(scores.values())
    candidates = [d for d, s in scores.items() if s == max_score]

    if len(candidates) == 1:
        primary_list = candidates
    else:
        # Tiebreak 1: d:kw hits
        def kw_hits(d: str) -> int:
            return breakdowns.get(d, {}).get("d:kw", 0)

        max_kw = max(kw_hits(d) for d in candidates)
        kw_winners = [d for d in candidates if kw_hits(d) == max_kw]

        if len(kw_winners) == 1:
            primary_list = kw_winners
        else:
            # Tiebreak 2: g:q + g:a hits
            def gqa_hits(d: str) -> int:
                bd = breakdowns.get(d, {})
                return bd.get("g:q", 0) + bd.get("g:a", 0)

            max_gqa = max(gqa_hits(d) for d in kw_winners)
            gqa_winners = [d for d in kw_winners if gqa_hits(d) == max_gqa]
            primary_list = gqa_winners  # all remaining are primary

    # Related: bidirectional d:x
    related: set[str] = set()
    primary_set = set(primary_list)

    for primary_id in primary_list:
        domain = data["domains"].get(primary_id, {})
        for ref in domain.get("cross_domains", []):
            if ref not in primary_set:
                related.add(ref)

    # Domains that reference any primary via d:x
    for domain_id, domain in data["domains"].items():
        if domain_id in primary_set:
            continue
        for ref in domain.get("cross_domains", []):
            if ref in primary_set:
                related.add(domain_id)
                break

    return primary_list, sorted(related)


# ---------------------------------------------------------------------------
# Ticket ID lookup
# ---------------------------------------------------------------------------

TICKET_PATTERN = re.compile(r'^[A-Z]+-\d+$')


def lookup_ticket(ticket_id: str, data: dict) -> dict | None:
    """Lookup ticket ID in notes. Returns note dict or None."""
    return data["notes"].get(ticket_id)


def _find_note_location(ticket_id: str, brain_dir: str) -> str:
    """Check if note file exists in brain/notes/ (active) or brain/notes/archive/ (archive).
    Returns 'active', 'archive', or 'unknown'."""
    if not brain_dir:
        return "unknown"
    active_path = os.path.join(brain_dir, "notes", f"{ticket_id}.md")
    archive_path = os.path.join(brain_dir, "notes", "archive", f"{ticket_id}.md")
    if os.path.exists(active_path):
        return "active"
    if os.path.exists(archive_path):
        return "archive"
    return "unknown"


# ---------------------------------------------------------------------------
# Result builder
# ---------------------------------------------------------------------------

def build_result(
    input_text: str,
    primary_ids: list[str],
    related_ids: list[str],
    breakdowns: dict[str, dict],
    scores: dict[str, int],
    confidence: str,
    data: dict,
    brain_dir: str = "",
) -> dict:
    """Build the final routing result dict."""
    primary_set = set(primary_ids)
    related_set = set(related_ids)
    all_domains = set(primary_ids) | set(related_ids)

    # --- Primary domain objects ---
    primary_out = []
    for domain_id in primary_ids:
        domain = data["domains"].get(domain_id, {})
        entry: dict[str, Any] = {
            "domain": domain_id,
            "name": domain.get("name"),
            "score": scores.get(domain_id, 0),
            "repos": domain.get("repos", []),
            "modules": domain.get("modules", []),
            "apis": domain.get("apis", []),
            "cookbook": domain.get("cookbook"),
        }
        primary_out.append(entry)

    # --- Related domain objects ---
    related_out = []
    for domain_id in related_ids:
        domain = data["domains"].get(domain_id, {})
        # Determine reason: whether primary references this domain or this domain references primary
        reason_parts = []
        for pid in primary_ids:
            pdomain = data["domains"].get(pid, {})
            if domain_id in pdomain.get("cross_domains", []):
                reason_parts.append(f"d:x 연결")
                break
        if not reason_parts:
            reason_parts.append("d:x 연결")
        entry = {
            "domain": domain_id,
            "name": domain.get("name"),
            "repos": domain.get("repos", []),
            "reason": reason_parts[0],
        }
        related_out.append(entry)

    # --- Glossary hits ---
    # Entries whose domain is in primary/related AND any question matches any input token
    input_tokens = tokenize(input_text)
    glossary_hits = []
    for g in data["glossary"]:
        if g.get("domain") not in all_domains:
            continue
        matched = False
        for q in g.get("questions", []):
            for token in input_tokens:
                if is_match(token, q):
                    matched = True
                    break
            if matched:
                break
        if matched:
            glossary_hits.append({
                "id": g["id"],
                "question": g["questions"][0] if g["questions"] else None,
                "answer": g.get("answer"),
            })

    # --- Related notes ---
    # Notes whose domain is in primary OR any input token matches note.summary
    related_notes = []
    for note_id, note in data["notes"].items():
        note_domain = note.get("domain")
        summary = note.get("summary", "") or ""
        in_primary_domain = note_domain in primary_set
        summary_match = any(is_match(token, summary) for token in input_tokens) if summary else False
        if not (in_primary_domain or summary_match):
            continue
        location = _find_note_location(note_id, brain_dir)
        related_notes.append({
            "id": note_id,
            "summary": note.get("summary"),
            "verdict": note.get("verdict"),
            "location": location,
        })

    # --- Score breakdown (only domains with total > 0, only fields with value > 0) ---
    score_breakdown: dict[str, dict] = {}
    for domain_id, bd in breakdowns.items():
        total = scores.get(domain_id, 0)
        if total <= 0:
            continue
        filtered = {k: v for k, v in bd.items() if v > 0}
        filtered["total"] = total
        score_breakdown[domain_id] = filtered

    no_match = len(primary_ids) == 0

    return {
        "input": input_text,
        "confidence": confidence,
        "primary": primary_out,
        "related": related_out,
        "glossary_hits": glossary_hits,
        "related_notes": related_notes,
        "score_breakdown": score_breakdown,
        "no_match": no_match,
    }


# ---------------------------------------------------------------------------
# Triage classification
# ---------------------------------------------------------------------------

def parse_triage_signals(path: str) -> list[dict[str, Any]]:
    """Parse triage-signals.md and return list of signal definitions.
    Each entry: {'korean': str, 'english': str, 'keywords': [str], 'first_action': str}
    """
    signals: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            m = re.match(r'^## (.+?) \((\w+)\)', line)
            if m:
                current = {
                    'korean': m.group(1),
                    'english': m.group(2),
                    'keywords': [],
                    'first_action': '',
                }
                signals.append(current)
                continue

            if current is None:
                continue

            if line.startswith('- 키워드:'):
                kw_text = line[len('- 키워드:'):].strip()
                current['keywords'] = [k.strip() for k in kw_text.split(',')]
            elif line.startswith('- 첫 번째 액션:'):
                current['first_action'] = line[len('- 첫 번째 액션:'):].strip()

    return signals


_SPEC_FALLBACK: dict[str, Any] = {
    'korean': '스펙질문형',
    'english': 'Spec',
    'keywords': [],
    'first_action': '도메인 스펙 문서 확인 (서브모듈 CLAUDE.md, Notion, 과거 노트)',
}


def classify_triage(text: str, signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify input text against triage signals. Returns best matching signal.
    Falls back to Spec if no keywords match."""
    text_lower = text.lower()
    best: dict[str, Any] | None = None
    best_count = 0

    for signal in signals:
        count = sum(1 for kw in signal['keywords'] if kw.lower() in text_lower)
        if count > best_count:
            best_count = count
            best = signal

    if best is None:
        for signal in signals:
            if signal['english'] == 'Spec':
                return signal
        return _SPEC_FALLBACK

    return best


# ---------------------------------------------------------------------------
# Main route function
# ---------------------------------------------------------------------------

def route(input_text: str, ttl_path: str, brain_dir: str = "") -> dict:
    """Main routing function.
    1. If input matches TICKET_PATTERN, try direct lookup → if found, skip matching
    2. Otherwise: tokenize → match_tokens → match_phrases → scores → confidence → primary/related → build_result
    """
    data = parse_ttl(ttl_path)

    # Ticket ID path
    if TICKET_PATTERN.match(input_text.strip()):
        ticket_id = input_text.strip()
        note = lookup_ticket(ticket_id, data)
        if note is not None:
            domain_id = note.get("domain")
            primary_ids = [domain_id] if domain_id else []
            # Related from that domain's cross_domains
            related_ids: list[str] = []
            if domain_id and domain_id in data["domains"]:
                related_ids = data["domains"][domain_id].get("cross_domains", [])
            # Build minimal breakdowns/scores for the result
            breakdowns: dict[str, dict] = {}
            scores: dict[str, int] = {}
            result = build_result(
                input_text=input_text,
                primary_ids=primary_ids,
                related_ids=related_ids,
                breakdowns=breakdowns,
                scores=scores,
                confidence="high",
                data=data,
                brain_dir=brain_dir,
            )
            result["triage"] = _classify_triage(input_text, brain_dir)
            return result

    # Normal matching path
    tokens = tokenize(input_text)
    breakdowns = match_tokens(tokens, data)
    match_phrases(tokens, data, breakdowns)
    apply_unique_kw_bonus(tokens, data, breakdowns)
    scores = calculate_scores(breakdowns)
    confidence = calculate_confidence(scores)
    primary_ids, related_ids = determine_primary_related(scores, breakdowns, data)

    result = build_result(
        input_text=input_text,
        primary_ids=primary_ids,
        related_ids=related_ids,
        breakdowns=breakdowns,
        scores=scores,
        confidence=confidence,
        data=data,
        brain_dir=brain_dir,
    )
    result["triage"] = _classify_triage(input_text, brain_dir)
    return result


def _classify_triage(text: str, brain_dir: str) -> dict[str, Any]:
    """Classify input text against triage-signals.md and return the result."""
    signals_path = os.path.join(brain_dir, "triage-signals.md") if brain_dir else ""
    if signals_path and os.path.exists(signals_path):
        signals = parse_triage_signals(signals_path)
        return classify_triage(text, signals)
    return _SPEC_FALLBACK


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """CLI: python domain_router.py [--ticket=ID] "input text"
    Reads brain/domain-map.ttl relative to script location (brain/scripts/ → brain/).
    Outputs JSON to stdout."""
    import argparse

    parser = argparse.ArgumentParser(description="Domain router for oncall triage")
    parser.add_argument("input", help="Input text for routing")
    parser.add_argument("--ticket", default="", help="Ticket ID (included in output for reference)")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    brain_dir = os.path.dirname(script_dir)  # brain/scripts → brain
    ttl_path = os.path.join(brain_dir, "domain-map.ttl")

    result = route(args.input, ttl_path, brain_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
