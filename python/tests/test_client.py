import io
import json
import urllib.error
from datetime import date
from unittest import mock

import pytest

import marketholidays as mh
from marketholidays.cli import main as cli_main


def _resp(payload):
    class R:
        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return R()


def _http_error(status, payload):
    return urllib.error.HTTPError("u", status, "x", {}, io.BytesIO(json.dumps(payload).encode()))


ADJ = {"input": "2026-11-08", "input_is_business_day": False, "input_closed_reasons": [{"calendar": "nse", "reason": "Muhurat"}], "adjusted": "2026-11-09"}


def test_adjust_returns_date_and_builds_query():
    c = mh.Client(cache_ttl=0)
    with mock.patch("urllib.request.urlopen", return_value=_resp(ADJ)) as m:
        assert c.adjust("2026-11-08", "nse") == date(2026, 11, 9)
    url = m.call_args[0][0].full_url
    assert "/api/adjust?" in url and "calendar=nse" in url and "convention=following" in url


def test_calendar_list_and_date_objects():
    c = mh.Client(cache_ttl=0)
    with mock.patch("urllib.request.urlopen", return_value=_resp(ADJ)) as m:
        c.adjust(date(2026, 11, 8), ["nse", "bank:mumbai"])
    assert "calendar=nse%2Cbank%3Amumbai" in m.call_args[0][0].full_url


def test_is_business_day_and_reasons():
    c = mh.Client(cache_ttl=0)
    with mock.patch("urllib.request.urlopen", return_value=_resp(ADJ)):
        assert c.is_business_day("2026-11-08", "nse") is False
        assert c.closed_reasons("2026-11-08", "nse")[0]["reason"] == "Muhurat"


def test_cache_avoids_second_request():
    c = mh.Client(cache_ttl=60)
    with mock.patch("urllib.request.urlopen", return_value=_resp(ADJ)) as m:
        c.adjust("2026-11-08", "nse")
        c.adjust("2026-11-08", "nse")
    assert m.call_count == 1


def test_add_and_between():
    c = mh.Client(cache_ttl=0)
    with mock.patch("urllib.request.urlopen", return_value=_resp({"result": "2026-10-22"})):
        assert c.add_business_days("2026-10-19", 2, "nse") == date(2026, 10, 22)
    with mock.patch("urllib.request.urlopen", return_value=_resp({"business_days": 20})):
        assert c.business_days_between("2026-10-01", "2026-11-01", "nse") == 20


def test_unpublished_year_raises_specific_error():
    c = mh.Client(cache_ttl=0)
    err = _http_error(404, {"error": "not published", "error_code": "calendar_not_published"})
    with mock.patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(mh.CalendarNotPublished) as ei:
            c.adjust("2027-01-04", "nse")
    assert ei.value.status == 404 and ei.value.code == "calendar_not_published"


def test_bad_request_raises_base_error():
    c = mh.Client(cache_ttl=0)
    err = _http_error(400, {"error": "Unknown calendar 'zzz'", "error_code": "invalid_parameter"})
    with mock.patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(mh.MarketHolidaysError):
            c.adjust("2026-11-08", "zzz")


def test_network_failure_wrapped():
    c = mh.Client(cache_ttl=0)
    with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
        with pytest.raises(mh.MarketHolidaysError):
            c.adjust("2026-11-08", "nse")


def test_cli_exit_codes(capsys):
    with mock.patch("urllib.request.urlopen", return_value=_resp(ADJ)):
        assert cli_main(["check", "nse", "--date", "2026-11-08"]) == 1
    with mock.patch("urllib.request.urlopen", return_value=_resp({**ADJ, "input_is_business_day": True, "input_closed_reasons": []})):
        assert cli_main(["check", "nse", "--date", "2026-11-09"]) == 0
    with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
        assert cli_main(["check", "nse"]) == 2
