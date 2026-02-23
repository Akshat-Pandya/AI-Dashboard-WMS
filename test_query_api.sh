#!/bin/bash
 
API_URL="http://127.0.0.1:8000/query"
OUT_FILE="complex_responses_$(date +%Y%m%d_%H%M%S).json"
 
queries=(
  "How is the weather today ?"
  "What is your name?"
  "which orders are stuck and any critical alerts?"
  "show top 5 inventory KPIs"
  "warehouse performance metrics for today"
  # "list overdue inbound shipments and supplier delays"
  # "compare inventory across zones and highlight capacity issues"
  # "find inventory for Wireless Mouse and HDMI Cable"
  # "show all pending and picking orders"
  # "which tasks are active and which are blocked?"
  # "give me KPIs related to fulfillment and productivity"
  # "show alerts related to low stock and overdue ASNs"
  # "which zone is nearing capacity limits?"
  # "show inventory items below reorder level"
  # "give me operational KPIs and stuck orders together"
  # "show inbound activity and overdue shipments"
  # "what issues need immediate attention in the warehouse?"
  
  # "list critical alerts and warning alerts separately"
  # "compare zones and list top utilized ones"
  # "show warehouse dashboard summary"
  # "show KPIs and alerts for inventory health"
  # "which orders are delayed more than 24 hours?"
  # "give me a quick snapshot of warehouse risks"
  # "show tasks causing bottlenecks"
  # "what are the main warehouse problems right now?"
)
 
echo "[" > "$OUT_FILE"
 
for q in "${queries[@]}"; do
  echo "Running query: $q"
 
  response=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"$q\"}")
 
  echo "$response," >> "$OUT_FILE"
done
 
sed -i '$ s/,$//' "$OUT_FILE"
echo "]" >> "$OUT_FILE"
 
jq . "$OUT_FILE" > tmp.json && mv tmp.json "$OUT_FILE"
 
echo "✅ Complex query responses saved to $OUT_FILE"