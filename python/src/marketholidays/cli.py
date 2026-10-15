"""Command line: ``marketholidays check nse`` exits 0 on a business day, 1 when closed, 2 on error."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from .client import CONVENTIONS, Client, MarketHolidaysError


def _today_ist() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="marketholidays", description="Indian market and bank business days (marketholidays.in)")
    p.add_argument("--base-url", default=None, help="API base URL (default https://marketholidays.in)")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="exit 0 if the date is a business day, 1 if closed")
    c.add_argument("calendar", help="e.g. nse, mcx, bank:mumbai, nse,bank:mumbai")
    c.add_argument("--date", default=None, help="YYYY-MM-DD (default: today in India)")

    a = sub.add_parser("adjust", help="print the adjusted date")
    a.add_argument("date")
    a.add_argument("calendar")
    a.add_argument("--convention", default="following", choices=CONVENTIONS)

    d = sub.add_parser("add", help="add business days (negative goes back)")
    d.add_argument("date")
    d.add_argument("days", type=int)
    d.add_argument("calendar")

    b = sub.add_parser("between", help="count business days in [start, end)")
    b.add_argument("start")
    b.add_argument("end")
    b.add_argument("calendar")

    args = p.parse_args(argv)
    client = Client(base_url=args.base_url) if args.base_url else Client()
    try:
        if args.cmd == "check":
            on = args.date or _today_ist()
            detail = client.adjust_detail(on, args.calendar)
            if detail["input_is_business_day"]:
                print(f"{on} is a business day for {args.calendar}")
                return 0
            why = "; ".join(f"{r['calendar']}: {r['reason']}" for r in detail["input_closed_reasons"])
            print(f"{on} is NOT a business day for {args.calendar} ({why}); next: {detail['adjusted']}")
            return 1
        if args.cmd == "adjust":
            print(client.adjust(args.date, args.calendar, args.convention).isoformat())
        elif args.cmd == "add":
            print(client.add_business_days(args.date, args.days, args.calendar).isoformat())
        else:
            print(client.business_days_between(args.start, args.end, args.calendar))
    except MarketHolidaysError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
