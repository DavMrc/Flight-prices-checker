import datetime
import pathlib


def fmt_duration(duration: datetime.timedelta) -> str:
    """
    Formats a `datetime.timedelta` object into a string of format `05 hrs 45 min`
    """
    hours, remainder = divmod(duration.total_seconds(), 60*60)
    minutes = remainder // 60
    return f"{int(hours):02} hrs {int(minutes):02} min"


def gantt_chart_height_proportion(df) -> int:
    """80 + `len(df)` * 18"""
    return 80 + len(df) * 18


def get_project_root() -> pathlib.Path:
    """Returns the project root directory as a `pathlib.Path` object."""
    CURR_PATH = pathlib.Path(__file__)
    PRJ_ROOT = CURR_PATH.parent.parent.parent
    return PRJ_ROOT
