import datetime


def fmt_duration(duration: datetime.timedelta) -> str:
    """
    Formats a `datetime.timedelta` object into a string of format `05 hrs 45 min`
    """
    hours, remainder = divmod(duration.total_seconds(), 60*60)
    minutes = remainder // 60
    return f"{int(hours):02} hrs {int(minutes):02} min"
