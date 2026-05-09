import re
from datetime import datetime
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class FormatDatePath:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {
                    "multiline": False,
                    "default": "WAN/%date:yyyy-MM-dd%/%date:hhmmss%"
                }),
            }
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("formatted_path",)
    FUNCTION = "format_path"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def format_path(self, template: str):
        now = datetime.now()

        def replace_match(match):
            fmt = match.group(1)
            py_fmt = (
                fmt.replace("yyyy", "%Y")
                   .replace("MM", "%m")
                   .replace("dd", "%d")
                   .replace("HH", "%H")
                   .replace("hh", "%H")
                   .replace("mm", "%M")
                   .replace("ss", "%S")
            )
            return now.strftime(py_fmt)

        try:
            formatted = re.sub(r"%date:([^%]+)%", replace_match, template)
            log(LogEntry(
                node_class="FormatDatePath",
                title="Path formatted",
                details={"Time": now.strftime("%H:%M:%S"), "Result": formatted}
            ))
            return (formatted,)
        except Exception as e:
            log(LogEntry(
                node_class="FormatDatePath",
                title="Formatting failed",
                details={"Error": str(e)}
            ))
            return (f"Formatting error: {e}",)