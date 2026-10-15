"""Small client for the marketholidays.in API (standard library only)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from typing import Any, Iterable, Union

from . import __version__

DateLike = Union[date, datetime, str]
CalendarLike = Union[str, Iterable[str]]

DEFAULT_BASE_URL = "https://marketholidays.in"
CONVENTIONS = ("following", "modified_following", "preceding", "modified_preceding")


class MarketHolidaysError(Exception):
    """The API refused the request or could not be reached."""

    def __init__(self, message: str, code: str = "error", status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class CalendarNotPublished(MarketHolidaysError):
    """The answer would depend on a year whose holiday list is not published yet (never guessed)."""


def _iso(d: DateLike) -> str:
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


def _cal(calendar: CalendarLike) -> str:
    return calendar if isinstance(calendar, str) else ",".join(calendar)


def _to_date(iso: str) -> date:
    return date.fromisoformat(iso)


class Client:
    """Talks to the API. Responses are cached in memory for ``cache_ttl`` seconds."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 15.0, cache_ttl: float = 3600.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, Any]] = {}

    # -- transport -------------------------------------------------------
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
        url = f"{self.base_url}{path}" + (f"?{query}" if query else "")
        hit = self._cache.get(url)
        if hit and time.monotonic() - hit[0] < self.cache_ttl:
            return hit[1]
        req = urllib.request.Request(url, headers={"User-Agent": f"marketholidays-python/{__version__}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 - fixed https base URL
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                body = {}
            message = body.get("error") or f"HTTP {exc.code}"
            code = body.get("error_code", "error")
            cls = CalendarNotPublished if code == "calendar_not_published" else MarketHolidaysError
            raise cls(message, code=code, status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise MarketHolidaysError(f"Could not reach {self.base_url}: {exc}") from exc
        self._cache[url] = (time.monotonic(), data)
        return data

    # -- business days ---------------------------------------------------
    def adjust_detail(self, on: DateLike, calendar: CalendarLike, convention: str = "following") -> dict:
        """Full API response for /api/adjust (reasons, skipped days, rule applied)."""
        return self._get("/api/adjust", {"date": _iso(on), "calendar": _cal(calendar), "convention": convention})

    def adjust(self, on: DateLike, calendar: CalendarLike, convention: str = "following") -> date:
        """Move ``on`` to a business day. Returns ``on`` itself when it already is one."""
        return _to_date(self.adjust_detail(on, calendar, convention)["adjusted"])

    def is_business_day(self, on: DateLike, calendar: CalendarLike) -> bool:
        return bool(self.adjust_detail(on, calendar)["input_is_business_day"])

    def closed_reasons(self, on: DateLike, calendar: CalendarLike) -> list[dict]:
        """Why ``on`` is closed, per calendar (empty list when it is a business day)."""
        return list(self.adjust_detail(on, calendar)["input_closed_reasons"])

    def add_business_days(self, on: DateLike, days: int, calendar: CalendarLike) -> date:
        """Add (or, if negative, subtract) business days."""
        data = self._get("/api/business-days/add", {"date": _iso(on), "days": days, "calendar": _cal(calendar)})
        return _to_date(data["result"])

    def business_days_between(self, start: DateLike, end: DateLike, calendar: CalendarLike) -> int:
        """Business days in [start, end): start included, end excluded."""
        data = self._get("/api/business-days/between", {"start": _iso(start), "end": _iso(end), "calendar": _cal(calendar)})
        return int(data["business_days"])

    # -- reference data --------------------------------------------------
    def calendars(self) -> dict:
        return self._get("/api/calendars")

    def holidays(self, year: int = 2026, city: str | None = None) -> dict:
        return self._get("/api/holidays", {"year": year, "city": city})

    def status(self, on: DateLike | None = None) -> dict:
        return self._get("/api/status", {"date": _iso(on) if on is not None else None})


_default = Client()


def adjust(on: DateLike, calendar: CalendarLike, convention: str = "following") -> date:
    return _default.adjust(on, calendar, convention)


def adjust_detail(on: DateLike, calendar: CalendarLike, convention: str = "following") -> dict:
    return _default.adjust_detail(on, calendar, convention)


def is_business_day(on: DateLike, calendar: CalendarLike) -> bool:
    return _default.is_business_day(on, calendar)


def closed_reasons(on: DateLike, calendar: CalendarLike) -> list[dict]:
    return _default.closed_reasons(on, calendar)


def add_business_days(on: DateLike, days: int, calendar: CalendarLike) -> date:
    return _default.add_business_days(on, days, calendar)


def business_days_between(start: DateLike, end: DateLike, calendar: CalendarLike) -> int:
    return _default.business_days_between(start, end, calendar)


def calendars() -> dict:
    return _default.calendars()


def holidays(year: int = 2026, city: str | None = None) -> dict:
    return _default.holidays(year, city)


def status(on: DateLike | None = None) -> dict:
    return _default.status(on)
