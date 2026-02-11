import sys


from .constants import (
    CATEGORY_PREFIX
)


class Everything(str):
    """Wildcard type marker."""

    def __ne__(self, __value: object) -> bool:
        return False


# class LogValue:
#     """
#     LogValue
#     ------------------
#     Logs the type, value, and an optional checkpoint name to the console based on the log_to_console flag.
#     Also outputs the formatted log message as a STRING, which can be used by other nodes (e.g., for saving to a file).
#     The console log includes the node tag and force trigger for identification if logging is enabled,
#     but the output string contains only the core information.
#     Passes the input value through unchanged to the output.
#     Uses a force_log_trigger to ensure execution even if primary output is not connected.
#     The force_log_trigger is marked with forceInput=True, so any change to it (e.g., from a connected node)
#     will cause this node to execute.
#
#     Inputs:
#         input_value (Any) - Any value to be logged and passed through
#         checkpoint_name (STRING) - Optional name for the checkpoint/log point (default: "LogPoint")
#         force_log_trigger (INT) - Optional trigger to force execution (default: 0, connect any changing value)
#         log_to_console (BOOLEAN) - Flag to enable or disable console logging (default: True)
#
#     Outputs:
#         output_value (Any) - The same value as input_value
#         log_string (STRING) - The clean log message as a string (without block start/end markers, node tags, or force trigger info)
#
#     Logs:
#         Console messages are printed based on the log_to_console flag.
#         They include [LogValue] tags and force trigger info for identification when enabled.
#         The output log_string is always clean without markers, tags, or force trigger info.
#     """
#
#     LOG_TAG = "[LogValue]"
#
#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "input_value": (Everything("*"),),
#                 "force_log_trigger": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFF, "forceInput": True}),
#                 "log_to_console": ("BOOLEAN", {"default": True}),
#             },
#             "optional": {
#                 "checkpoint_name": ("STRING", {"default": "LogPoint", "multiline": False}),
#             }
#         }
#
#     RETURN_TYPES = (Everything("*"), "STRING")
#     RETURN_NAMES = ("output_value", "log_string")
#     FUNCTION = "log_and_pass"
#     CATEGORY = "Stalkervr/Utils"
#
#     def log_and_pass(self, input_value, force_log_trigger, log_to_console, checkpoint_name="LogPoint"):
#         """
#         Logs the checkpoint name, type, and value to console based on log_to_console flag.
#         Returns the input value and a clean log message string regardless of the flag.
#         The force_log_trigger parameter ensures this function runs when its value changes.
#         """
#         value_type = type(input_value).__name__
#
#         core_log_info = f"""Checkpoint: {checkpoint_name}
# Type: {value_type}
# Value: {input_value}"""
#
#         if log_to_console:
#             console_formatted_block = f"""
# {self.LOG_TAG}
# {core_log_info}
# {self.LOG_TAG}
# """
#             print(console_formatted_block)
#
#         clean_output_string = f"\n{core_log_info}\n"
#
#         return (input_value, clean_output_string)


class LogValue:
    """
    LogValue
    --------
    Logs input value to console with checkpoint name and type.
    Passes input through unchanged and outputs clean log string.

    No trigger needed — executes on every run thanks to IS_CHANGED.
    """

    LOG_TAG = "[LogValue]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_value": (Everything("*"),),
                "log_to_console": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "checkpoint_name": ("STRING", {"default": "LogPoint", "multiline": False}),
            }
        }

    # 🔥 Отключаем кэширование — ключевое изменение
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    RETURN_TYPES = (Everything("*"), "STRING")
    RETURN_NAMES = ("output_value", "log_string")
    FUNCTION = "log_and_pass"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def log_and_pass(self, input_value, log_to_console=True, checkpoint_name="LogPoint"):
        value_type = type(input_value).__name__

        core_log_info = f"""Checkpoint: {checkpoint_name}
Type: {value_type}
Value: {input_value}"""

        if log_to_console:
            console_formatted_block = f"""
{self.LOG_TAG}
{core_log_info}
{self.LOG_TAG}
"""
            print(console_formatted_block)

        # Clean string for downstream nodes (e.g., SaveTextFile)
        clean_output_string = f"\n{core_log_info}\n"

        return (input_value, clean_output_string)


class ConsoleLog:
    """
    ConsoleLog
    ----------
    Console logger for debugging.

    Console output format:
        [ConsoleLog]
        Checkpoint: <name>
        Type: <type>
        Value: <value>
        [ConsoleLog]

    (followed by an empty line)
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

    # 🔥 КЛЮЧЕВАЯ СТРОКА: отключает кэширование
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = f"{CATEGORY_PREFIX}/Debug"
    INPUT_IS_LIST = True

    def execute(self, any_value=None, checkpoint_name="default", text_color="default", console=True):

        checkpoint_name = checkpoint_name[0] if isinstance(checkpoint_name, list) else checkpoint_name
        text_color = text_color[0] if isinstance(text_color, list) else text_color
        console = console[0] if isinstance(console, list) else console

        if not console:
            return {"ui": {}}

        value_str = "[no input]"
        value_type = "None"

        if any_value is not None:
            try:
                if isinstance(any_value, list):
                    if len(any_value) == 1:
                        item = any_value[0]
                        value_str = self._safe_str(item)
                        value_type = type(item).__name__
                    else:
                        value_str = f"<list of {len(any_value)} items>"
                        value_type = "list"
                else:
                    value_str = self._safe_str(any_value)
                    value_type = type(any_value).__name__
            except Exception as e:
                value_str = f"<error: {e}>"
                value_type = "error"

        color_code = self.COLORS.get(text_color, self.COLORS["default"])
        reset_code = self.COLORS["default"]
        msg = (
            f"\n{color_code}[ConsoleLog]\n"
            f"Checkpoint: {checkpoint_name}\n"
            f"Type: {value_type}\n"
            f"Value: {value_str}\n"
            f"[ConsoleLog]{reset_code}\n"
        )
        print(msg, file=sys.stderr)

        return {"ui": {}}

    def _safe_str(self, obj):
        """Safely convert object to string without raising exceptions."""
        try:
            return str(obj)
        except Exception:
            return "<unserializable>"


class DebugConditioningStructure:
    """
    DebugConditioningStructure
    -------------------------
    Analyzes and prints the full structure of conditioning with tensor shapes.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "debug_structure"
    CATEGORY = f"{CATEGORY_PREFIX}/Debug"

    def _get_tensor_info(self, tensor):
        if hasattr(tensor, 'shape'):
            shape_str = "x".join(str(s) for s in tensor.shape)
            device_str = str(getattr(tensor, 'device', 'N/A'))
            return f"[{shape_str} on {device_str}]"
        return f"[{type(tensor).__name__}]"

    def debug_structure(self, conditioning):
        print("\n" + "=" * 60)
        print("[DebugConditioningStructure] CONDITIONING STRUCTURE ANALYSIS")
        print("=" * 60)

        if not isinstance(conditioning, list):
            print(f"❌ NOT A LIST: {type(conditioning)}")
            print(f"   Value: {conditioning}")
            return (conditioning,)

        print(f"✅ List with {len(conditioning)} item(s)")

        for i, item in enumerate(conditioning):
            print(f"\n--- Item {i} ---")

            if not isinstance(item, tuple):
                print(f"❌ Not a tuple: {type(item)}")
                continue

            if len(item) < 2:
                print(f"❌ Tuple too short: length {len(item)}")
                continue

            tensor_part, params_part = item[0], item[1]

            # Analyze tensor part
            print(f"Tensor: {self._get_tensor_info(tensor_part)}")

            # Analyze params part
            if not isinstance(params_part, dict):
                print(f"Params: ❌ Not a dict ({type(params_part)})")
                continue

            print(f"Params dict with {len(params_part)} key(s):")
            for key, value in params_part.items():
                if hasattr(value, 'shape'):
                    print(f"  • {key}: {self._get_tensor_info(value)}")
                elif isinstance(value, list):
                    if value and hasattr(value[0], 'shape'):
                        print(f"  • {key}: LIST of {len(value)} tensors")
                        for j, v in enumerate(value[:3]):  # Show first 3
                            print(f"    [{j}]: {self._get_tensor_info(v)}")
                        if len(value) > 3:
                            print(f"    ... and {len(value) - 3} more")
                    else:
                        print(f"  • {key}: LIST of {len(value)} items (non-tensor)")
                else:
                    print(
                        f"  • {key}: {type(value).__name__} = {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")

        print("\n" + "=" * 60)
        return (conditioning,)