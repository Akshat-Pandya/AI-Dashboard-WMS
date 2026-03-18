"""
param_llm.py
Extracts structured query parameters from the user's natural language query.
Runs AFTER intent classification, BEFORE tool execution.

Zone extraction is done entirely via regex — the LLM is only used for
non-zone params (limit, severity, status, sku, category, location,
hours_threshold).
This eliminates hallucination and misextraction of zone names entirely.
"""
import json
import re
import requests
from typing import Any, Dict, List

from app.core.schemas import IntentScore
from app.core.config import MODEL_NAME, OLLAMA_URL, LLM_TIMEOUT


# ── Valid values ──────────────────────────────────────────────────────────────
VALID_ORDER_STATUSES     = {"pending", "picking", "packed", "shipped", "cancelled"}
VALID_TASK_STATUSES      = {"pending", "active", "blocked", "completed"}
VALID_ASN_STATUSES       = {"expected", "in_transit", "receiving", "received", "overdue"}
VALID_SEVERITIES         = {"critical", "high", "warning", "medium", "info", "low"}
VALID_INVENTORY_STATUSES = {"available", "reserved", "damaged", "quarantine"}

# ── Severity words that must appear EXPLICITLY in the query ──────────────────
# Regex extraction — same approach as zones and categories.
# This prevents the LLM from hallucinating severity on queries like
# "show all alerts" or "what should I focus on".
_SEVERITY_WORDS = {
    "critical", "high", "warning", "medium", "info", "low"
}

# Words that look like severity but are NOT — block them from matching
# e.g. "show low stock" must not set severity="low"
_SEVERITY_BLOCKLIST_CONTEXTS = {
    # If any of these words appear nearby, don't treat it as severity
    "stock", "reorder", "replenish", "inventory", "quantity"
}

# ── Known inventory categories — used for regex extraction ───────────────────
# Extend this list as your catalogue grows
KNOWN_CATEGORIES = {
    "bearings", "conveyors", "motors", "controllers", "safety",
    "pneumatics", "hydraulics", "motion", "mechanical", "maintenance",
    "drives", "enclosures", "electrical", "sensors", "vision",
    "material handling", "packaging", "hazmat", "it equipment", "hvac",
}

# ── Intent suppression map ────────────────────────────────────────────────────
# NOTE: zone_inventory_compare + inventory_lookup is intentionally NOT suppressed.
# When user asks "show inventory of zone A and zone E", they want BOTH the
# zone comparison chart AND the tabular item list — keep both intents.
_INTENT_SUPPRESSION: Dict[str, set] = {
    "low_stock":          {"inventory_lookup"},
    "overdue_asn":          {"inbound_activity"},
    "zone_inventory_compare":          {"inventory_lookup"},
    # "warehouse_overview": {"inventory_lookup", "kpi_summary"},
}

# ── Known zones in this warehouse — used for fuzzy spelling correction ────────
# Update this list if you add/rename zones.
KNOWN_ZONES = ["Zone A", "Zone B", "Zone C", "Zone D", "Zone E"]


def _fuzzy_correct_query(query: str) -> str:
    """
    Correct misspelled zone references before regex extraction.
    Uses character-level edit distance to snap typos like "zon a", "zoe d",
    "zone dd", "zonne c" to the correct zone name.

    Only corrects tokens that look like they're trying to be a zone reference
    (must start with 'z' and be close to "zone X" in edit distance).
    Returns the corrected query string.
    """
    def _edit_distance(a: str, b: str) -> int:
        m, n = len(a), len(b)
        dp = list(range(n + 1))
        for i in range(1, m + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, n + 1):
                temp = dp[j]
                if a[i - 1] == b[j - 1]:
                    dp[j] = prev
                else:
                    dp[j] = 1 + min(prev, dp[j], dp[j - 1])
                prev = temp
        return dp[n]

    # Build candidate patterns: ["zone a", "zone b", ..., "zone e"]
    candidates = [z.lower() for z in KNOWN_ZONES]
    # Set of valid zone suffixes for quick lookup: {"a", "b", "c", "d", "e"}
    valid_suffixes = {c.split()[-1] for c in candidates}

    tokens = query.split()
    corrected_tokens = list(tokens)

    i = 0
    while i < len(tokens):
        tok = tokens[i].lower().rstrip(".,")

        # Only attempt correction if token starts with 'z' (zone-like)
        if tok.startswith("z"):
            # Check if this token + next already forms a valid zone (no correction needed)
            if tok == "zone" and i + 1 < len(tokens):
                next_tok = tokens[i + 1].lower().rstrip(".,")
                if next_tok in valid_suffixes:
                    # Already correct — skip both tokens
                    i += 2
                    continue

            # Try single-token run-together match: e.g. "zonea" → "zone a"
            # When next token is a valid zone suffix, prefer the candidate
            # whose suffix matches that next token (resolves "zonee b" → "zone b").
            matched = False
            next_tok_lower = (
                tokens[i + 1].lower().rstrip(".,") if i + 1 < len(tokens) else ""
            )
            run_together_matches = []
            for cand in candidates:
                cand_clean = cand.replace(" ", "")
                if _edit_distance(tok, cand_clean) <= 1:
                    run_together_matches.append(cand)

            if run_together_matches:
                # If next token is a valid suffix, prefer the candidate whose
                # suffix equals that token (e.g. "zonee b" → prefer "zone b")
                chosen = None
                if next_tok_lower in valid_suffixes:
                    for cand in run_together_matches:
                        if cand.split()[-1] == next_tok_lower:
                            chosen = cand
                            break
                if chosen is None:
                    chosen = run_together_matches[0]

                parts = chosen.split()
                orig_token = tokens[i]
                corrected_tokens[i] = parts[0]
                next_is_suffix = next_tok_lower == parts[1]
                if not next_is_suffix:
                    corrected_tokens.insert(i + 1, parts[1])
                    tokens.insert(i + 1, parts[1])
                print(f"🔤 Fuzzy corrected '{orig_token}' → '{chosen}'")
                matched = True
                i += 2

            if matched:
                continue

            # Try two-token match: e.g. "zon" + "a" → "zone a"
            if i + 1 < len(tokens):
                next_tok = tokens[i + 1].lower().rstrip(".,")
                two = tok + " " + next_tok

                best_dist = 999
                best_cand = None
                for cand in candidates:
                    d = _edit_distance(two, cand)
                    if d < best_dist:
                        best_dist = d
                        best_cand = cand

                # Accept only if edit distance ≤ 2 AND the next token is not
                # a common English word — BUT always allow single-letter zone
                # suffixes (a, b, c...) even though "a" is also an article.
                _SKIP_WORDS = {"and", "or", "in", "of", "the", "at", "to",
                               "for", "with", "from", "by", "on", "an"}
                is_zone_suffix = next_tok in valid_suffixes
                if (best_dist <= 2 and best_cand
                        and (is_zone_suffix or next_tok not in _SKIP_WORDS)):
                    parts = best_cand.split()
                    print(f"🔤 Fuzzy corrected '{tokens[i]} {tokens[i+1]}' → '{best_cand}'")
                    corrected_tokens[i]     = parts[0]
                    corrected_tokens[i + 1] = parts[1]
                    i += 2
                    continue

        i += 1

    corrected = " ".join(corrected_tokens)
    if corrected != query:
        print(f"🔤 Query after fuzzy correction: {corrected!r}")
    return corrected


# ── System prompt — zones deliberately excluded (handled by regex) ────────────
SYSTEM_PROMPT = """
You are a parameter extraction engine for a Warehouse Management System.

Extract ONLY these parameters if explicitly present in the query:
- sku              : product SKU code (e.g. "SKU-A1001")
- severity         : DO NOT extract — severity is handled separately
- order_status     : ONLY for order queries. One of: pending, picking, packed,
                     shipped, cancelled.
                     "outbound", "inbound", "all" are NOT statuses.
- task_status      : ONLY for task queries. One of: pending, active, blocked,
                     completed.
- inventory_status : ONLY for inventory queries. One of: available, reserved,
                     damaged, quarantine.
- category         : inventory category name (e.g. "Mechanical", "Bearings",
                     "Motors", "Hydraulics", "Safety", "Electrical").
                     Extract even if user says "mechanical category",
                     "motors category", "show bearings", "list conveyors".
                     Return title-cased string e.g. "Mechanical", "Motors".
- location         : specific bin/location code (e.g. "A-01-03", "B-02-07").
- limit            : integer number of results (e.g. "top 10" → 10)
- hours_threshold  : integer hours for stuck/overdue detection

DO NOT extract zone or zones — those are handled separately.
Return {} if none of the above are found.
Output ONLY valid JSON. No explanation. No extra keys.

EXAMPLES:

Query: "show pending orders"
Output: {"order_status": "pending"}

Query: "show items in mechanical category"
Output: {"category": "Mechanical"}

Query: "list all motors"
Output: {"category": "Motors"}

Query: "show hydraulics inventory"
Output: {"category": "Hydraulics"}

Query: "show available items in zone A"
Output: {"inventory_status": "available"}

Query: "find items at location A-01-03"
Output: {"location": "A-01-03"}

Query: "show bearings in zone B"
Output: {"category": "Bearings"}

Query: "show low stock items in zone a and zone c"
Output: {}

Query: "which items are low on stock"
Output: {}

Query: "show inventory of zone A"
Output: {}
"""


# =============================================================================
#  PUBLIC ENTRY POINT
# =============================================================================

def extract_params(query: str, intents: List[IntentScore]) -> Dict[str, Any]:
    print("\n--------------------------------------------------")
    print("🔍 Param LLM called")

    # Step 1: Fuzzy-correct spelling mistakes in zone references
    query = _fuzzy_correct_query(query)

    # Step 2: Zones via regex — zero hallucination
    zones_extracted = _extract_zones_regex(query)
    print(f"📍 Regex zone extraction: {zones_extracted}")

    # Step 3: Category via regex — reliable for known terms
    category_extracted = _extract_category_regex(query)
    if category_extracted:
        print(f"📦 Regex category extraction: {category_extracted!r}")

    # Step 3b: Severity via regex — prevents hallucination on general queries
    severity_extracted = _extract_severity_regex(query)
    if severity_extracted:
        print(f"🚨 Regex severity extraction: {severity_extracted!r}")
    else:
        print("🚨 No severity in query — will show ALL alerts")

    # Step 4: LLM for remaining params (limit, status, sku, location...)
    llm_params = _call_llm_for_non_zone_params(query, intents)

    # Step 5: Merge — regex always wins over LLM for zones, category, severity
    params: Dict[str, Any] = {**llm_params}

    # Regex category overrides LLM category (more reliable)
    if category_extracted:
        params["category"] = category_extracted

    # Regex severity overrides LLM severity — if regex found nothing, remove
    # any severity the LLM hallucinated (ensures "show all alerts" → no filter)
    if severity_extracted:
        params["severity"] = severity_extracted
    else:
        params.pop("severity", None)  # drop any hallucinated severity

    # Normalize status key — the LLM returns order_status / task_status /
    # inventory_status. Collapse whichever is present to a single "status" key
    # so tool functions don't need to know which sub-type was used.
    for status_key in ("order_status", "task_status", "inventory_status"):
        if status_key in params:
            params["status"] = params.pop(status_key)
            break

    if len(zones_extracted) == 1:
        params["zone"] = zones_extracted[0]
    elif len(zones_extracted) > 1:
        params["zones"] = zones_extracted

    print("✅ Extracted params:", params)
    return params


# =============================================================================
#  INTENT FILTERING
# =============================================================================

def filter_intents(intents: List[IntentScore]) -> List[IntentScore]:
    """
    Remove secondary intents made redundant by a stronger primary.
    Call in orchestrator AFTER classify_intent(), BEFORE extract_params().
    """
    primary_values = {s.intent.value for s in intents}
    suppressed: set = set()

    for primary, to_suppress in _INTENT_SUPPRESSION.items():
        if primary in primary_values:
            suppressed |= to_suppress

    if suppressed:
        filtered = [s for s in intents if s.intent.value not in suppressed]
        dropped  = [s.intent.value for s in intents if s.intent.value in suppressed]
        print(f"🚫 Intent suppression: dropped {dropped} (superseded)")
        return filtered

    return intents


# =============================================================================
#  ZONE EXTRACTION — PURE REGEX
# =============================================================================

def _extract_zones_regex(query: str) -> List[str]:
    """
    Extract all zone references from the query using regex only.
    Handles: "zone a", "zone a and zone c", "zone a and c", "zone a, b and c"
    """
    q = query.strip()
    found: List[str] = []

    # Pass 1: explicit "zone X" mentions
    for m in re.finditer(r'\bzone\s+([A-Za-z0-9][A-Za-z0-9\-]*)', q, re.IGNORECASE):
        normalized = _normalize_zone(m.group(1).strip())
        if normalized not in found:
            found.append(normalized)

    # Pass 2: bare single letters after connectors when at least one zone found
    # e.g. "zone a and c" — catches the trailing "c"
    if found:
        for m in re.finditer(r'\b(?:and|or|,|&)\s+([A-Za-z])\b', q, re.IGNORECASE):
            letter     = m.group(1).upper()
            normalized = f"Zone {letter}"
            if normalized not in found:
                found.append(normalized)

    return sorted(set(found))


def _normalize_zone(raw: str) -> str:
    z = raw.strip()
    if len(z) == 1 and z.isalpha():
        return f"Zone {z.upper()}"
    m = re.match(r"(?i)^zone[\s\-_]+(.+)$", z)
    if m:
        suffix = m.group(1).strip()
        if len(suffix) == 1:
            suffix = suffix.upper()
        return f"Zone {suffix}"
    return f"Zone {z.title()}"


# =============================================================================
#  CATEGORY EXTRACTION — PURE REGEX
# =============================================================================

def _extract_category_regex(query: str) -> str:
    """
    Extract inventory category from the query using the known categories list.
    Returns title-cased category string or empty string if not found.

    Handles:
      "show items in mechanical category" → "Mechanical"
      "list all motors"                   → "Motors"
      "hydraulics inventory"              → "Hydraulics"
      "show bearings in zone B"           → "Bearings"
      "material handling items"           → "Material Handling"
    """
    q_lower = query.lower()

    # Sort by length descending so multi-word categories match first
    for cat in sorted(KNOWN_CATEGORIES, key=len, reverse=True):
        # Use word-boundary matching
        pattern = r'\b' + re.escape(cat) + r'\b'
        if re.search(pattern, q_lower):
            return cat.title()

    return ""


# =============================================================================
#  SEVERITY EXTRACTION — PURE REGEX
# =============================================================================

def _extract_severity_regex(query: str) -> str:
    """
    Extract severity only if explicitly mentioned as an alert filter.
    Returns lowercase severity string or empty string.

    Handles:
      "show critical alerts"     → "critical"
      "show high severity alerts"→ "high"
      "show all alerts"          → ""   (no severity — return ALL)
      "what should I focus on"   → ""   (no severity mentioned)
      "show low stock items"      → ""   (low = stock context, not severity)
    """
    q_lower = query.lower()

    for sev in _SEVERITY_WORDS:
        pattern = r'\b' + re.escape(sev) + r'\b'
        if re.search(pattern, q_lower):
            # Check if any blocklist context word appears within 4 words of severity
            words = q_lower.split()
            for idx, w in enumerate(words):
                if w == sev or w.startswith(sev):
                    window_start = max(0, idx - 4)
                    window_end   = min(len(words), idx + 5)
                    window       = set(words[window_start:window_end])
                    if window & _SEVERITY_BLOCKLIST_CONTEXTS:
                        # Severity word is in a stock/inventory context — ignore it
                        break
            else:
                return sev

    return ""


# =============================================================================
#  LLM CALL — NON-ZONE, NON-CATEGORY PARAMS
# =============================================================================

def _call_llm_for_non_zone_params(query: str, intents: List[IntentScore]) -> Dict[str, Any]:
    """Call LLM only for: limit, severity, status variants, sku, location, hours_threshold."""
    intent_list = ", ".join(s.intent.value for s in intents)

    prompt = f"""{SYSTEM_PROMPT}

Query: "{query}"
Detected intents: {intent_list}

Return ONLY JSON.
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_predict": 80,
            "top_p": 0.9,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=LLM_TIMEOUT)
        response.raise_for_status()
        raw = response.json().get("response", "").strip()
        print("📝 Raw LLM (non-zone) output:", raw)

        params = _extract_json(raw)
        params = _validate_and_clean(params)

        # Hard-remove zone keys — never let LLM override regex
        params.pop("zone", None)
        params.pop("zones", None)

        return params

    except Exception as e:
        print("⚠️ Param LLM error:", e)
        return {}


# =============================================================================
#  HELPERS
# =============================================================================

def _validate_and_clean(params: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(params)

    # Strip null / empty / zero padding
    for key in list(cleaned.keys()):
        v = cleaned[key]
        if v is None:
            del cleaned[key]
        elif isinstance(v, str) and v.strip() == "":
            del cleaned[key]
        elif isinstance(v, (int, float)) and v == 0 and key in ("limit", "hours_threshold"):
            del cleaned[key]
        elif isinstance(v, list) and len(v) == 0:
            del cleaned[key]

    if "order_status" in cleaned:
        s = str(cleaned["order_status"]).strip().lower()
        if s not in VALID_ORDER_STATUSES:
            print(f"⚠️ Dropping invalid order_status={s!r}")
            del cleaned["order_status"]

    if "task_status" in cleaned:
        s = str(cleaned["task_status"]).strip().lower()
        if s not in VALID_TASK_STATUSES:
            print(f"⚠️ Dropping invalid task_status={s!r}")
            del cleaned["task_status"]

    if "inventory_status" in cleaned:
        s = str(cleaned["inventory_status"]).strip().lower()
        if s not in VALID_INVENTORY_STATUSES:
            print(f"⚠️ Dropping invalid inventory_status={s!r}")
            del cleaned["inventory_status"]

    # Legacy "status" key — validate against all valid sets
    if "status" in cleaned:
        s = str(cleaned["status"]).strip().lower()
        all_valid = (VALID_ORDER_STATUSES | VALID_TASK_STATUSES |
                     VALID_ASN_STATUSES | VALID_INVENTORY_STATUSES)
        if s not in all_valid:
            print(f"⚠️ Dropping invalid status={s!r}")
            del cleaned["status"]

    if "severity" in cleaned:
        sv = str(cleaned["severity"]).strip().lower()
        if sv not in VALID_SEVERITIES:
            print(f"⚠️ Dropping invalid severity={sv!r}")
            del cleaned["severity"]

    return cleaned


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {}