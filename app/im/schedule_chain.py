import re
from datetime import datetime
from typing import List, Dict
from zoneinfo import ZoneInfo

from app.logging import logger
from app.time import unix_sleep_to_timedelta


class ScheduleChain:
    DAY_MAP = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    DEFAULT_TIMEZONE = "UTC"

    def __init__(self, name, timezone: str = DEFAULT_TIMEZONE, schedule: List[Dict] = None):
        self.name = name
        self.timezone = timezone or self.DEFAULT_TIMEZONE
        self.schedule = schedule if schedule else []
        self.tz = ZoneInfo(self.timezone)

    def __repr__(self):
        return self.name

    @property
    def steps(self) -> List[Dict]:
        """
        Get the steps for the current time.
        """
        current_time = datetime.now()
        return self._get_steps(current_time)

    def _get_steps(self, current_time: datetime) -> List[Dict]:
        """
        Get the steps based on the matchers and schedule.
        """
        current_time = current_time.astimezone(self.tz)

        for entry in self.schedule:
            if 'matchers' in entry:
                if self._match_conditions(entry['matchers'], current_time):
                    return entry['steps']
            else:
                return entry['steps']
        return []

    def _match_conditions(self, conditions: List[Dict], current_time: datetime) -> bool:
        """
        Check each condition in the list against the current date and time.
        """
        dow = (current_time.weekday() + 1) % 7
        dow_str = self.DAY_MAP[dow]
        doe = int(datetime.now().timestamp() // (24 * 60 * 60))
        date_str = current_time.strftime("%Y-%m-%d")

        for condition in conditions:
            start_time = condition.get('start_time')
            duration = condition.get('duration')
            if start_time and duration:
                if not self._within_shift_time(start_time, duration, current_time):
                    continue

            start_day = condition['start_day']
            if "=~" in start_day:
                if self._match_regex_condition(start_day, dow_str, doe, date_str):
                    return True
            elif "dow" in start_day:
                if self._match_dow_condition(start_day, dow):
                    return True
            elif "doe" in start_day:
                if self._match_doe_condition(start_day, doe):
                    return True
            elif "date" in start_day:
                if self._match_date_condition(start_day, date_str):
                    return True
            else:
                if self._evaluate_custom_expression(start_day):
                    return True
        return False

    @staticmethod
    def _within_shift_time(start_time: str, duration: str, current_time: datetime) -> bool:
        """
        Check if the current time falls within the specified shift window.
        """
        start_hour, start_minute = map(int, start_time.split(":"))
        shift_start = current_time.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        shift_end = shift_start + unix_sleep_to_timedelta(duration)

        return shift_start <= current_time < shift_end

    @staticmethod
    def _match_regex_condition(start_day: str, dow_str: str, doe: int, date_str: str) -> bool:
        """
        Evaluate regex-based conditions with "=~" operator.
        """
        left, pattern = start_day.split("=~")
        left = left.strip()
        pattern = pattern.strip().strip('"')

        if left == "dow":
            target = dow_str
        elif left == "doe":
            target = str(doe)
        elif left == "date":
            target = date_str
        else:
            try:
                target = str(eval(left, {"__builtins__": {}}, {}))
            except Exception as e:
                logger.error(f"Failed to evaluate left side of regex condition {start_day}: {e}")
                return False

        try:
            return bool(re.search(pattern, target))
        except re.error as e:
            logger.error(f"Regex error in pattern {pattern}: {e}")
            return False

    @staticmethod
    def _match_dow_condition(start_day: str, dow: int) -> bool:
        """
        Evaluate day of the week conditions.
        """
        try:
            condition = start_day.replace("dow", str(dow))
            return eval(condition, {"__builtins__": {}}, {})
        except Exception as e:
            logger.error(f"Failed to evaluate DOW condition {start_day}: {e}")
            return False

    @staticmethod
    def _match_doe_condition(start_day: str, doe: int) -> bool:
        """
        Evaluate day of epoch conditions.
        """
        try:
            condition = start_day.replace("doe", str(doe))
            return eval(condition, {"__builtins__": {}}, {})
        except Exception as e:
            logger.error(f"Failed to evaluate DOE condition {start_day}: {e}")
            return False

    @staticmethod
    def _match_date_condition(start_day: str, date_str: str) -> bool:
        """
        Evaluate specific date conditions.
        """
        try:
            condition = start_day.replace("date", f'"{date_str}"')
            return eval(condition, {"__builtins__": {}}, {})
        except Exception as e:
            logger.error(f"Failed to evaluate date condition {start_day}: {e}")
            return False

    @staticmethod
    def _evaluate_custom_expression(start_day: str) -> bool:
        """
        Evaluate any custom expression not directly tied to dow, doe, or date.
        """
        try:
            return eval(start_day, {"__builtins__": {}}, {})
        except Exception as e:
            logger.error(f"Failed to evaluate custom expression {start_day}: {e}")
            return False
