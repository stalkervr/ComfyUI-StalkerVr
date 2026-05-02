import json
from .constants import CATEGORY_PREFIX
from .logger import LogEntry, log

class JsonPromptToTextPromptConverter:
    """
    JsonPromptToTextPromptConverter
    --------------------------------
    Converts JSON to a plain text prompt by extracting only values.
    Skips empty/null fields, auto-appends punctuation, and supports line breaks.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False, "default": "{}"}),
                "new_line": ("BOOLEAN", {"default": False, "tooltip": "Join values with newlines instead of spaces."}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "extract_values"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    @staticmethod
    def _is_empty(v):
        if v is None:
            return True
        if isinstance(v, str):
            s = v.strip()
            return s == "" or s.lower() == "null"
        return False

    @staticmethod
    def _format_string(s: str) -> str | None:
        s = s.strip()
        if not s or s.lower() == "null":
            return None
        if not s.endswith("."):
            s += "."
        return s

    @staticmethod
    def _format_list(lst: list) -> str | None:
        cleaned = []
        for item in lst:
            if JsonPromptToTextPromptConverter._is_empty(item):
                continue
            if isinstance(item, (dict, list)):
                temp = []
                JsonPromptToTextPromptConverter._collect_values(item, temp)
                cleaned.extend(temp)
            else:
                val = str(item).strip()
                if val:
                    cleaned.append(val)

        if not cleaned:
            return None
        return ", ".join(cleaned) + "."

    @staticmethod
    def _collect_values(obj, out_list: list):
        if isinstance(obj, dict):
            for v in obj.values():
                JsonPromptToTextPromptConverter._collect_values(v, out_list)
        elif isinstance(obj, list):
            formatted = JsonPromptToTextPromptConverter._format_list(obj)
            if formatted:
                out_list.append(formatted)
        else:
            if JsonPromptToTextPromptConverter._is_empty(obj):
                return
            formatted = JsonPromptToTextPromptConverter._format_string(str(obj))
            if formatted:
                out_list.append(formatted)

    def extract_values(self, json_string: str, new_line: bool) -> tuple[str]:
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            log(LogEntry(
                node_class="JsonPromptToTextPromptConverter",
                title="JSON parse failed",
                details={"Error": str(e)},
                footer="Returning error string"
            ))
            return (f"JSON parse error: {e}",)

        values = []
        self._collect_values(data, values)

        separator = "\n" if new_line else " "
        result = separator.join(values)

        log(LogEntry(
            node_class="JsonPromptToTextPromptConverter",
            title="Prompt generated",
            details={"Format": "Newline" if new_line else "Single line", "Segments": len(values)},
            footer="Ready for text prompt input"
        ))
        return (result,)