# india-market-holidays (Python)

Indian market and bank holidays and business day adjustment in Python. A small client (standard library only) for the free [marketholidays.in API](https://marketholidays.in/api-docs): NSE, BSE, MCX, NSE settlement days, NSE currency derivatives, and RBI bank calendars for each city.

```bash
pip install india-market-holidays
```

The package installs the Python module `marketholidays` and a `marketholidays` command.

```python
import marketholidays as mh

mh.is_business_day("2026-11-10", "nse")                  # False (Diwali-Balipratipada)
mh.adjust("2026-11-08", "nse")                           # date(2026, 11, 9)
mh.adjust("2026-10-31", "nse", "modified_following")     # date(2026, 10, 30), stays in the month
mh.add_business_days("2026-10-19", 2, "nse")             # date(2026, 10, 22), skips Dussehra
mh.business_days_between("2026-10-01", "2026-11-01", "nse")  # 20
mh.is_business_day("2026-11-10", ["nse", "bank:mumbai"])  # open in every listed calendar?
mh.closed_reasons("2026-11-10", "nse,bank:mumbai")
```

Calendars: `nse`, `bse`, `mcx`, `clearing`, `currency`, `bank`, `bank:<city>` (for example `bank:mumbai`). Combine with commas or a list: a day is a business day only if it is open in all of them. `mh.calendars()` lists everything.

Conventions: `following`, `modified_following`, `preceding`, `modified_preceding`.

## Command line

```bash
marketholidays check nse && ./fetch_prices.sh     # exit 0 business day, 1 closed, 2 error
marketholidays adjust 2026-11-08 nse
marketholidays add 2026-10-19 2 nse
marketholidays between 2026-10-01 2026-11-01 nse
```

## Years and errors

Only years whose official lists are published are served (2026 today). A request whose answer would depend on an unpublished year raises `marketholidays.CalendarNotPublished` rather than guessing. Other API problems raise `marketholidays.MarketHolidaysError`.

## Notes

- Responses are cached in memory for an hour (`Client(cache_ttl=...)`). Holiday data changes a few times a year.
- This is a client for a web API, so it needs network access. Use `Client(base_url=...)` to point at another host.
- Dates come from NSE circulars and the RBI holiday matrix; confirm anything time-sensitive with your exchange or bank. See the [API docs](https://marketholidays.in/api-docs) and [terms](https://marketholidays.in/terms).

MIT licensed. Not affiliated with NSE, BSE, MCX or the RBI.
