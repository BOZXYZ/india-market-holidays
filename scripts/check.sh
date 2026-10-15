#!/usr/bin/env bash
# Calls the marketholidays.in business day API and writes step outputs.
# Inputs come from environment variables (never interpolated into the script text):
#   MH_CALENDAR, MH_DATE (optional), MH_CONVENTION, MH_FAIL_ON_CLOSED, MH_BASE_URL
set -euo pipefail

BASE_URL="${MH_BASE_URL:-https://marketholidays.in}"
CALENDAR="${MH_CALENDAR:?calendar input is required}"
CONVENTION="${MH_CONVENTION:-following}"
DATE="${MH_DATE:-$(TZ=Asia/Kolkata date +%F)}"
FAIL_ON_CLOSED="${MH_FAIL_ON_CLOSED:-false}"
OUT="${GITHUB_OUTPUT:-/dev/stdout}"

command -v jq >/dev/null 2>&1 || { echo "::error::jq is required (preinstalled on GitHub-hosted runners)"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "::error::curl is required"; exit 1; }

BODY="$(mktemp)"
trap 'rm -f "$BODY"' EXIT

STATUS="$(curl -sS -G -o "$BODY" -w '%{http_code}' --max-time 20 --retry 2 --retry-delay 2 \
  -A "marketholidays-action/1.0 (+https://marketholidays.in/api-docs)" \
  --data-urlencode "date=$DATE" \
  --data-urlencode "calendar=$CALENDAR" \
  --data-urlencode "convention=$CONVENTION" \
  "$BASE_URL/api/adjust")" || { echo "::error::Could not reach $BASE_URL"; exit 1; }

if [ "$STATUS" != "200" ]; then
  MSG="$(jq -r '.error // "unexpected response"' "$BODY" 2>/dev/null || echo "unexpected response")"
  echo "::error::marketholidays API returned HTTP $STATUS: $MSG"
  exit 1
fi

IS_BD="$(jq -r '.input_is_business_day' "$BODY")"
ADJUSTED="$(jq -r '.adjusted' "$BODY")"
SHIFTED="$(jq -r '.days_shifted' "$BODY")"
REASON="$(jq -r '[.input_closed_reasons[] | "\(.calendar): \(.reason)"] | join("; ")' "$BODY")"
REASON="${REASON//$'\n'/ }"; REASON="${REASON//$'\r'/ }"

{
  echo "is_business_day=$IS_BD"
  echo "adjusted_date=$ADJUSTED"
  echo "days_shifted=$SHIFTED"
  echo "reason=$REASON"
  echo "date=$DATE"
} >> "$OUT"

if [ "$IS_BD" = "true" ]; then
  echo "$DATE is a business day for $CALENDAR."
else
  echo "$DATE is NOT a business day for $CALENDAR ($REASON). $CONVENTION -> $ADJUSTED."
  if [ "$FAIL_ON_CLOSED" = "true" ]; then
    echo "::error::$DATE is not a business day for $CALENDAR"
    exit 1
  fi
fi
