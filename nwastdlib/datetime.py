from datetime import datetime
import pytz


def nowtz():
    return datetime.now(tz=pytz.utc)
