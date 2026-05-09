from datetime import datetime
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class CurrentDateTime:
    """
    CurrentDateTime
    ---------------
    Returns the current date/time as a formatted string.
    Supports cascading precision: seconds auto-enables minutes & hours.
    Forces execution on every queue for real-time timestamps.
    """

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "include_hours": ("BOOLEAN", {"default": False, "label": "Include Hours", "tooltip": "Add hours (HH). Required for minutes/seconds."}),
                "include_minutes": ("BOOLEAN", {"default": False, "label": "Include Minutes", "tooltip": "Add minutes (MM). Auto-enables hours."}),
                "include_seconds": ("BOOLEAN", {"default": False, "label": "Include Seconds", "tooltip": "Add seconds (SS). Auto-enables hours & minutes."}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("date_time",)
    FUNCTION = "get_date"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def get_date(self, include_hours=False, include_minutes=False, include_seconds=False):
        try:
            now = datetime.now()

            # Cascading precision logic
            if include_seconds:
                include_hours = True
                include_minutes = True
            elif include_minutes:
                include_hours = True

            # Build timestamp
            result = now.strftime("%Y%m%d")
            if include_hours:
                result += now.strftime("%H")
            if include_minutes:
                result += now.strftime("%M")
            if include_seconds:
                result += now.strftime("%S")

            # Centralized logging
            log(LogEntry(
                node_class="CurrentDateTime",
                title="Timestamp Generated",
                details={
                    "Value": result,
                    "Precision": f"H:{include_hours}, M:{include_minutes}, S:{include_seconds}"
                },
                footer="CurrentDateTime execution complete"
            ))

            return (result,)
        except Exception as e:
            log(LogEntry(
                node_class="CurrentDateTime",
                title="Timestamp Generation Failed",
                details={"Error": str(e)},
                footer="Fallback to error string"
            ))
            return (f"Error: {e}",)