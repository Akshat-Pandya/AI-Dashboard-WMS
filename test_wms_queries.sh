#!/usr/bin/env bash
# =============================================================================
#  test_wms_queries.sh
#  Fires 50 queries at the WMS /query endpoint (sequential, with progress),
#  captures full JSON responses, timing, and HTTP status codes.
#  Output: test_results_<timestamp>.json  +  test_summary_<timestamp>.txt
#
#  Usage:
#    chmod +x test_wms_queries.sh
#    ./test_wms_queries.sh                        # default: localhost:8000
#    ./test_wms_queries.sh http://localhost:8000  # explicit base URL
#
#  Requirements: bash, curl, jq (brew install jq / apt-get install jq)
# =============================================================================

BASE_URL="${1:-http://localhost:8000}"
ENDPOINT="$BASE_URL/query"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUT_JSON="test_results_${TIMESTAMP}.json"
OUT_TXT="test_summary_${TIMESTAMP}.txt"

# ── colour helpers ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

# ── check dependencies ─────────────────────────────────────────────────────────
for dep in curl jq; do
  if ! command -v "$dep" &>/dev/null; then
    echo -e "${RED}✗ '$dep' not found. Install it and retry.${RESET}"
    exit 1
  fi
done

# =============================================================================
#  QUERY BANK  (50 queries across 7 categories)
#  Format: "CATEGORY|||query text"
# =============================================================================
declare -a QUERIES=(

  # ── 1. SIMPLE / DIRECT (should be high-confidence, fast) ───────────────────
  "SIMPLE|||show all warehouse alerts"
  "SIMPLE|||what are the current KPIs"
  "SIMPLE|||list all blocked tasks"
  "SIMPLE|||show active tasks"
  "SIMPLE|||what orders are pending"
  "SIMPLE|||show low stock items"
  "SIMPLE|||give me inbound shipment status"
  "SIMPLE|||show overdue ASNs"
  "SIMPLE|||warehouse overview"
  "SIMPLE|||show critical alerts only"

  # ── 2. ZONE / INVENTORY (single zone vs compare — key ambiguity area) ───────
  "ZONE|||show inventory in Zone A"
  "ZONE|||what items are in Zone B"
  "ZONE|||list products in Zone C"
  "ZONE|||compare Zone A and Zone B inventory"
  "ZONE|||compare all zones"
  "ZONE|||Zone A vs Zone B stock levels"
  "ZONE|||which zone has the most available stock"
  "ZONE|||show me inventory across all zones"
  "ZONE|||how many SKUs are in Zone A"
  "ZONE|||zone inventory comparison"

  # ── 3. COMPLEX / MULTI-INTENT (should trigger multiple intents) ─────────────
  "COMPLEX|||show me critical alerts and blocked tasks"
  "COMPLEX|||what are the stuck orders and low stock items right now"
  "COMPLEX|||give me a full warehouse health check"
  "COMPLEX|||show overdue shipments and pending orders"
  "COMPLEX|||which zones are nearly full and what KPIs are off target"
  "COMPLEX|||show me blocked tasks and the orders they might be affecting"
  "COMPLEX|||urgent orders and critical alerts summary"
  "COMPLEX|||inbound activity and overdue ASN report"
  "COMPLEX|||top 5 critical alerts and top 5 low stock items"
  "COMPLEX|||give me KPIs and warehouse overview together"

  # ── 4. FILTERED / PARAMETERISED (tests param extraction) ───────────────────
  "PARAM|||show top 10 low stock items"
  "PARAM|||show only warning level alerts"
  "PARAM|||orders with status shipped"
  "PARAM|||show tasks assigned to Zone B"
  "PARAM|||inbound ASNs from supplier with overdue status"
  "PARAM|||show orders with high priority"
  "PARAM|||list items with zero stock"
  "PARAM|||show urgent priority tasks"
  "PARAM|||critical and error alerts only"
  "PARAM|||show me the last 5 blocked tasks"

  # ── 5. AMBIGUOUS / EDGE CASE (intent unclear — tests fallback) ─────────────
  "AMBIGUOUS|||how is the warehouse doing"
  "AMBIGUOUS|||anything urgent I should know about"
  "AMBIGUOUS|||what needs my attention right now"
  "AMBIGUOUS|||is everything okay in the warehouse"
  "AMBIGUOUS|||summarise today's operations"

  # ── 6. FREE SQL / UNKNOWN (should trigger free-query fallback) ──────────────
  "FREE_SQL|||how many tasks were completed in Zone A"
  "FREE_SQL|||which carrier has the most shipped orders"
  "FREE_SQL|||average estimated minutes for pick tasks"
  "FREE_SQL|||count orders by priority level"
  "FREE_SQL|||which dock received the most units"

  # ── 7. IRRELEVANT (should return unknown or graceful rejection) ─────────────
  "IRRELEVANT|||what is the weather today"
  "IRRELEVANT|||tell me a joke"
  "IRRELEVANT|||who won the world cup"
  "IRRELEVANT|||write me a python script to sort a list"
  "IRRELEVANT|||what is the capital of France"
)

TOTAL=${#QUERIES[@]}

# =============================================================================
#  COUNTERS
# =============================================================================
pass=0; fail=0; warn=0
declare -A cat_counts   # category → total
declare -A cat_pass     # category → pass
declare -a results_arr  # will hold JSON objects

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║       WMS AI Query Test Suite — $TOTAL queries              ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${RESET}"
echo -e "  Endpoint : ${CYAN}$ENDPOINT${RESET}"
echo -e "  Output   : ${CYAN}$OUT_JSON${RESET}"
echo ""

# =============================================================================
#  MAIN LOOP
# =============================================================================
idx=0
for entry in "${QUERIES[@]}"; do
  idx=$((idx + 1))
  CATEGORY="${entry%%|||*}"
  QUERY="${entry##*|||}"

  # track category totals
  cat_counts[$CATEGORY]=$(( ${cat_counts[$CATEGORY]:-0} + 1 ))

  # ── build request payload ──────────────────────────────────────────────────
  PAYLOAD=$(jq -n --arg q "$QUERY" '{"query": $q}')

  # ── fire request, capture response + timing + HTTP status ─────────────────
  START_NS=$(date +%s%N 2>/dev/null || date +%s)  # ns on Linux, s on macOS

  HTTP_RESPONSE=$(curl -s -w "\n__HTTP_STATUS__%{http_code}__END__" \
    -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    --max-time 90 \
    --connect-timeout 5 \
    2>&1)

  END_NS=$(date +%s%N 2>/dev/null || date +%s)

  # compute elapsed ms (handle macOS date which has only second precision)
  if [[ ${#START_NS} -gt 10 ]]; then
    ELAPSED_MS=$(( (END_NS - START_NS) / 1000000 ))
  else
    ELAPSED_MS=$(( (END_NS - START_NS) * 1000 ))
  fi

  # split body and status code
  HTTP_STATUS=$(echo "$HTTP_RESPONSE" | grep -o '__HTTP_STATUS__[0-9]*__END__' | grep -o '[0-9]*')
  BODY=$(echo "$HTTP_RESPONSE" | sed 's/__HTTP_STATUS__[0-9]*__END__//')

  # ── parse response fields ──────────────────────────────────────────────────
  if echo "$BODY" | jq -e . >/dev/null 2>&1; then
    IS_VALID_JSON=true
    SUMMARY=$(echo "$BODY"    | jq -r '.summary // "N/A"')
    WIDGET_COUNT=$(echo "$BODY" | jq '.widgets | length // 0')
    INTENT_COUNT=$(echo "$BODY" | jq '.intents | length // 0')
    INTENTS_DETECTED=$(echo "$BODY" | jq -r '[.intents[]?.intent] | join(", ") // "none"')
    TOP_CONFIDENCE=$(echo "$BODY"   | jq '[.intents[]?.confidence] | max // 0')
    HAS_DATA=$(echo "$BODY"         | jq 'if (.data | keys | length) > 0 then true else false end')
    DATA_KEYS=$(echo "$BODY"        | jq -r '.data | keys | join(", ")')
    HAS_ERROR=$(echo "$BODY"        | jq -r '
      if .summary | test("error|failed|could not|unable"; "i") then "true"
      elif (.data | to_entries[] | .value | type == "object" and has("error")) then "true"
      else "false"
      end' 2>/dev/null || echo "false")
  else
    IS_VALID_JSON=false
    SUMMARY="INVALID JSON OR TIMEOUT"
    WIDGET_COUNT=0; INTENT_COUNT=0; INTENTS_DETECTED="parse_error"
    TOP_CONFIDENCE=0; HAS_DATA=false; DATA_KEYS=""; HAS_ERROR=true
  fi

  # ── classify result ────────────────────────────────────────────────────────
  STATUS_ICON=""; STATUS_LABEL=""
  if [[ "$IS_VALID_JSON" == "false" || "$HTTP_STATUS" != "200" ]]; then
    STATUS_ICON="${RED}✗${RESET}"; STATUS_LABEL="FAIL"
    fail=$((fail + 1))
  elif [[ "$HAS_ERROR" == "true" || "$WIDGET_COUNT" -eq 0 ]]; then
    STATUS_ICON="${YELLOW}⚠${RESET}"; STATUS_LABEL="WARN"
    warn=$((warn + 1))
    cat_pass[$CATEGORY]=$(( ${cat_pass[$CATEGORY]:-0} + 1 ))  # partial pass
  else
    STATUS_ICON="${GREEN}✓${RESET}"; STATUS_LABEL="PASS"
    pass=$((pass + 1))
    cat_pass[$CATEGORY]=$(( ${cat_pass[$CATEGORY]:-0} + 1 ))
  fi

  # ── console output ─────────────────────────────────────────────────────────
  printf "%s [%02d/%d] %-12s %s\n" \
    "$(echo -e "$STATUS_ICON")" "$idx" "$TOTAL" "[$CATEGORY]" "$QUERY"
  printf "          HTTP:%-4s  Time:%-6s  Intents:%-30s  Widgets:%d\n" \
    "${HTTP_STATUS:-ERR}" "${ELAPSED_MS}ms" "$INTENTS_DETECTED" "$WIDGET_COUNT"

  # ── build JSON result object ───────────────────────────────────────────────
  RESULT_OBJ=$(jq -n \
    --argjson  idx          "$idx" \
    --arg      category     "$CATEGORY" \
    --arg      query        "$QUERY" \
    --arg      status_label "$STATUS_LABEL" \
    --argjson  http_status  "${HTTP_STATUS:-0}" \
    --argjson  elapsed_ms   "$ELAPSED_MS" \
    --arg      intents      "$INTENTS_DETECTED" \
    --argjson  intent_count "$INTENT_COUNT" \
    --argjson  top_conf     "${TOP_CONFIDENCE:-0}" \
    --argjson  widget_count "$WIDGET_COUNT" \
    --argjson  has_data     "$HAS_DATA" \
    --arg      data_keys    "$DATA_KEYS" \
    --arg      has_error    "$HAS_ERROR" \
    --arg      summary      "$SUMMARY" \
    '{
      idx:          $idx,
      category:     $category,
      query:        $query,
      status:       $status_label,
      http_status:  $http_status,
      elapsed_ms:   $elapsed_ms,
      intents:      $intents,
      intent_count: $intent_count,
      top_confidence: $top_conf,
      widget_count: $widget_count,
      has_data:     $has_data,
      data_keys:    $data_keys,
      has_error:    $has_error,
      summary_preview: ($summary | if length > 200 then .[:200] + "…" else . end)
    }')

  results_arr+=("$RESULT_OBJ")
done

echo ""
echo -e "${BOLD}──────────────────────────────────────────────────────────${RESET}"

# =============================================================================
#  BUILD FINAL JSON
# =============================================================================
# join result objects into a JSON array
RESULTS_JSON_ARRAY=$(printf '%s\n' "${results_arr[@]}" | jq -s '.')

# category breakdown
CAT_BREAKDOWN="{}"
for cat in "${!cat_counts[@]}"; do
  total_c=${cat_counts[$cat]}
  pass_c=${cat_pass[$cat]:-0}
  CAT_BREAKDOWN=$(echo "$CAT_BREAKDOWN" | jq \
    --arg cat "$cat" \
    --argjson t "$total_c" \
    --argjson p "$pass_c" \
    '. + {($cat): {"total": $t, "pass_or_warn": $p, "fail": ($t - $p)}}')
done

FINAL_JSON=$(jq -n \
  --arg      endpoint      "$ENDPOINT" \
  --arg      timestamp      "$TIMESTAMP" \
  --argjson  total          "$TOTAL" \
  --argjson  pass           "$pass" \
  --argjson  warn           "$warn" \
  --argjson  fail           "$fail" \
  --argjson  categories     "$CAT_BREAKDOWN" \
  --argjson  results        "$RESULTS_JSON_ARRAY" \
  '{
    meta: {
      endpoint:   $endpoint,
      timestamp:  $timestamp,
      total:      $total,
      pass:       $pass,
      warn:       $warn,
      fail:       $fail,
      pass_rate:  (($pass + $warn) / $total * 100 | round | tostring + "%")
    },
    category_breakdown: $categories,
    results: $results
  }')

echo "$FINAL_JSON" > "$OUT_JSON"
echo -e "${GREEN}✓ JSON results saved → $OUT_JSON${RESET}"

# =============================================================================
#  PLAIN-TEXT SUMMARY
# =============================================================================
{
  echo "WMS AI QUERY TEST SUMMARY"
  echo "========================="
  echo "Timestamp  : $TIMESTAMP"
  echo "Endpoint   : $ENDPOINT"
  echo "Total      : $TOTAL"
  echo "PASS       : $pass"
  echo "WARN       : $warn  (responded but no widgets / summary had error-words)"
  echo "FAIL       : $fail"
  echo ""

  echo "CATEGORY BREAKDOWN"
  echo "------------------"
  for cat in SIMPLE ZONE COMPLEX PARAM AMBIGUOUS FREE_SQL IRRELEVANT; do
    t=${cat_counts[$cat]:-0}
    p=${cat_pass[$cat]:-0}
    f=$((t - p))
    printf "  %-15s  total=%-3d  pass/warn=%-3d  fail=%d\n" "$cat" "$t" "$p" "$f"
  done
  echo ""

  echo "FAILURES & WARNINGS"
  echo "-------------------"
  echo "$FINAL_JSON" | jq -r '
    .results[]
    | select(.status != "PASS")
    | "[\(.status)] [\(.category)] \(.query)\n  HTTP:\(.http_status) Intents:\(.intents) Widgets:\(.widget_count)\n  Summary: \(.summary_preview)\n"
  '

  echo ""
  echo "SLOWEST QUERIES (top 10)"
  echo "------------------------"
  echo "$FINAL_JSON" | jq -r '
    [.results[] | {query, elapsed_ms, category, intents}]
    | sort_by(-.elapsed_ms)
    | .[:10][]
    | "\(.elapsed_ms)ms  [\(.category)]  \(.query)  → \(.intents)"
  '

  echo ""
  echo "LOW CONFIDENCE RESULTS (top_confidence < 0.7)"
  echo "----------------------------------------------"
  echo "$FINAL_JSON" | jq -r '
    .results[]
    | select(.top_confidence < 0.7 and .category != "IRRELEVANT")
    | "conf=\(.top_confidence)  [\(.category)]  \(.query)  → \(.intents)"
  '

  echo ""
  echo "INTENT DISTRIBUTION"
  echo "-------------------"
  echo "$FINAL_JSON" | jq -r '
    [.results[].intents]
    | map(split(", ")[])
    | group_by(.)
    | map({intent: .[0], count: length})
    | sort_by(-.count)[]
    | "\(.count)x  \(.intent)"
  '

} > "$OUT_TXT"

echo -e "${GREEN}✓ Text summary saved  → $OUT_TXT${RESET}"
echo ""

# =============================================================================
#  CONSOLE SUMMARY
# =============================================================================
echo -e "${BOLD}RESULTS SUMMARY${RESET}"
echo -e "  ${GREEN}PASS : $pass${RESET}"
echo -e "  ${YELLOW}WARN : $warn${RESET}"
echo -e "  ${RED}FAIL : $fail${RESET}"
echo ""

PASS_RATE=$(( (pass + warn) * 100 / TOTAL ))
echo -e "  Overall pass rate: ${BOLD}${PASS_RATE}%${RESET} (pass + warn / total)"
echo ""

echo -e "${BOLD}Category breakdown:${RESET}"
for cat in SIMPLE ZONE COMPLEX PARAM AMBIGUOUS FREE_SQL IRRELEVANT; do
  t=${cat_counts[$cat]:-0}
  p=${cat_pass[$cat]:-0}
  f=$((t - p))
  if [[ $f -gt 0 ]]; then
    echo -e "  $(printf '%-15s' $cat)  ${RED}$f fail${RESET}  /  $t total"
  else
    echo -e "  $(printf '%-15s' $cat)  ${GREEN}all pass${RESET}  /  $t total"
  fi
done

echo ""
echo -e "Run ${CYAN}cat $OUT_TXT${RESET} for the full diagnostic report."
echo -e "Run ${CYAN}jq '.results[] | select(.status!=\"PASS\")' $OUT_JSON${RESET} for failed query details."
echo ""