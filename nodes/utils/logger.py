import json
import sys

from ...common.constants import CATEGORY_PREFIX
from ...common.types import Everything


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