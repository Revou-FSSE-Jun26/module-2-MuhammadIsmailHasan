from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))


def now_wib():
    return datetime.now(WIB).replace(tzinfo=None)
