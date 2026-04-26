from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def now_jst() -> datetime:
    return datetime.now(JST)


def today_jst():
    return now_jst().date()
