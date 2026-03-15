import sys
import json


from .constants import (
    CATEGORY_PREFIX
)


class Everything(str):
    """Wildcard type marker."""
    def __ne__(self, __value: object) -> bool:
        return False


class Logger:
    """
    Logger
    ------
    Enhanced console logger with passthrough and formatted log output.

    Console output format:
        [Logger]
        Checkpoint: <name>
        Type: <type>
        Value: <value>
        [Logger]

    Outputs:
        - passthrough: input value unchanged
        - log_string: formatted log as readable string
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
                "checkpoint_name": ("STRING", {"default": "default", "multiline": False}),
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

    def execute(self, any_value=None, checkpoint_name="default", text_color="default", console=True):
        # Normalize inputs
        checkpoint_name = checkpoint_name[0] if isinstance(checkpoint_name, list) else checkpoint_name
        text_color = text_color[0] if isinstance(text_color, list) else text_color
        console = console[0] if isinstance(console, list) else console

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

        # Build clean log string (no ANSI codes)
        log_string = (
            f"[Logger]\n"
            f"Checkpoint: {checkpoint_name}\n"
            f"Type: {value_type}\n"
            f"Value:\n{value_str}\n"
            f"[Logger]\n"
        )

        # Optionally print colored version to console
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
        """Safely convert object to string without raising exceptions."""
        try:
            return str(obj)
        except Exception:
            return "<unserializable>"


class SwitchAny:
    """
    SwitchAny
    ---------
    Conditional switch with lazy evaluation.
    Only the selected input (on_true or on_false) is evaluated.
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
        """
        Tells ComfyUI which inputs are needed based on condition.
        Only the selected input will be evaluated.
        """
        if condition:
            return ["on_true"]
        else:
            return ["on_false"]

    def execute(self, condition=False, on_true=None, on_false=None):
        if condition:
            return (on_true,)
        else:
            return (on_false,)


class CalculateFrameCount:
    """
    CalculateFrameCount
    -------------------
    Computes total frame count using: frames = (duration_seconds * fps) + 1
    - duration_seconds: integer from 1 to 300
    - fps: integer from 1 to 60
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
        frame_count = duration_seconds * fps + 1
        return (frame_count,)