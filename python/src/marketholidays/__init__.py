"""Indian market and bank holidays and business day adjustment, via the marketholidays.in API."""
__version__ = "0.1.0"

from .client import (  # noqa: E402
    CONVENTIONS,
    CalendarNotPublished,
    Client,
    MarketHolidaysError,
    add_business_days,
    adjust,
    adjust_detail,
    business_days_between,
    calendars,
    closed_reasons,
    holidays,
    is_business_day,
    status,
)

__all__ = [
    "CONVENTIONS",
    "CalendarNotPublished",
    "Client",
    "MarketHolidaysError",
    "add_business_days",
    "adjust",
    "adjust_detail",
    "business_days_between",
    "calendars",
    "closed_reasons",
    "holidays",
    "is_business_day",
    "status",
    "__version__",
]
