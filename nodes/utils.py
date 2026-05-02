import json
import sys

from datetime import datetime

from .constants import CATEGORY_PREFIX
from .types import Everything
from .logger import LogEntry, log


class Logger:
    """
    Logger
    ------
    Enhanced console logger with passthrough, structured output, and custom colors.
    Supports wildcard inputs and force-execution for real-time pipeline debugging.
    """

    COLORS = {
        "default": "\033[0m",
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "any_value": ("*",),
                "checkpoint_name": ("STRING", {"default": "default"}),
                "text_color": (list(cls.COLORS.keys()), {"default": "default"}),
                "console": ("BOOLEAN", {"default": True}),
            }
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    RETURN_TYPES = (Everything("*"), "STRING")
    RETURN_NAMES = ("passthrough", "log_string")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"
    INPUT_IS_LIST = True

    def execute(self, any_value=None, checkpoint_name=None, text_color=None, console=None):
        checkpoint_name = checkpoint_name[0] if isinstance(checkpoint_name, list) else checkpoint_name or "default"
        text_color = text_color[0] if isinstance(text_color, list) else text_color or "default"
        console = console[0] if isinstance(console, list) else console
        console = console if console is not None else True

        actual_value = None
        value_str = "[no input]"
        value_type = "None"

        if any_value is not None:
            actual_value = any_value[0] if isinstance(any_value, list) and len(any_value) == 1 else any_value
            try:
                if isinstance(actual_value, (dict, list)):
                    value_str = json.dumps(actual_value, ensure_ascii=False, indent=2)
                    value_type = type(actual_value).__name__
                else:
                    value_str = self._safe_str(actual_value)
                    value_type = type(actual_value).__name__
            except Exception as e:
                value_str = f"<error: {e}>"
                value_type = "error"

        log_string = (
            f"[Logger]\n"
            f"Checkpoint: {checkpoint_name}\n"
            f"Type: {value_type}\n"
            f"Value:\n{value_str}\n"
            f"[Logger]\n"
        )

        if console:
            color_code = self.COLORS.get(text_color, self.COLORS["default"])
            reset_code = self.COLORS["default"]
            colored_msg = (
                f"\n{color_code}[Logger]\n"
                f"Checkpoint: {checkpoint_name}\n"
                f"Type: {value_type}\n"
                f"Value:\n{value_str}\n"
                f"[Logger]{reset_code}\n"
            )
            print(colored_msg, file=sys.stderr)

        return (actual_value, log_string)

    def _safe_str(self, obj):
        try:
            return str(obj)
        except Exception:
            return "<unserializable>"


class SwitchAny:
    """
    SwitchAny
    ---------
    Conditional switch with lazy evaluation.
    Evaluates only the branch selected by the boolean condition.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "condition": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "on_true": (Everything("*"), {"lazy": True}),
                "on_false": (Everything("*"), {"lazy": True}),
            }
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("passthrough",)
    FUNCTION = "execute"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def check_lazy_status(self, condition=False, on_true=None, on_false=None):
        """Directs ComfyUI to evaluate only the active branch."""
        return ["on_true"] if condition else ["on_false"]

    def execute(self, condition=False, on_true=None, on_false=None):
        """Returns the value from the selected branch."""
        return (on_true,) if condition else (on_false,)


class CalculateFrameCount:
    """
    CalculateFrameCount
    -------------------
    Computes total frame count for video generation: frames = (duration_seconds × fps) + 1.
    Includes the +1 offset to account for the starting frame (frame 0).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "duration_seconds": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 300,
                    "step": 1,
                    "tooltip": "Video duration in seconds (integer)"
                }),
                "fps": ("INT", {
                    "default": 16,
                    "min": 12,
                    "max": 60,
                    "step": 4,
                    "tooltip": "Frames per second"
                }),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("frame_count",)
    FUNCTION = "calculate"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def calculate(self, duration_seconds: int, fps: int) -> tuple[int]:
        """Calculates frame count with +1 offset for inclusive range."""
        frame_count = duration_seconds * fps + 1
        return (frame_count,)


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