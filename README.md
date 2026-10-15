# marketholidays

Tools for Indian market and bank business days, built on the free [marketholidays.in API](https://marketholidays.in/api-docs):

- **GitHub Action**: skip or gate workflow steps on NSE, BSE, MCX or bank holidays.
- **Python package** (`python/`): `pip install marketholidays`, plus a `marketholidays check` command for cron jobs.

Calendars: `nse`, `bse`, `mcx`, `clearing`, `currency`, `bank`, `bank:<city>`. Combine with commas; a day is a business day only if it is open in all of them.

## GitHub Action

Run a job only on days NSE is open (cron runs on every day, so gate it):

```yaml
name: Fetch prices
on:
  schedule:
    - cron: "45 4 * * 1-5"   # 10:15 IST, Monday to Friday
jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - id: day
        uses: BOZXYZ/india-market-holidays@v1
        with:
          calendar: nse
      - if: steps.day.outputs.is_business_day == 'true'
        run: ./fetch_prices.sh
```

Inputs: `calendar` (required), `date` (default: today in India), `convention` (default `following`), `fail-on-closed` (default `false`).
Outputs: `is_business_day` (`true`/`false`), `adjusted_date`, `days_shifted`, `reason`, `date`.

Move a payment date to the next working day for a city's banks:

```yaml
- id: pay
  uses: BOZXYZ/india-market-holidays@v1
  with: { calendar: "bank:mumbai", date: "2026-11-10", convention: modified_following }
- run: echo "Pay on ${{ steps.pay.outputs.adjusted_date }}"
```

The action needs `curl` and `jq` (both preinstalled on GitHub-hosted runners). If the API cannot answer, for example for a year whose holiday list is not published, the step fails instead of guessing.

## Python

See [python/README.md](python/README.md).

## Data and limits

Only years with published official holiday lists are served (2026 today). Dates come from NSE circulars and the RBI holiday matrix; confirm anything time-sensitive with your exchange or bank. [API docs](https://marketholidays.in/api-docs) · [terms](https://marketholidays.in/terms). MIT licensed; not affiliated with NSE, BSE, MCX or the RBI.
