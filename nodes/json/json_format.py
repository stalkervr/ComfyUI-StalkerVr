import json
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class JsonFormat:
    """
    JsonFormat
    ----------
    Takes a JSON string (formatted or minified) and outputs a pretty-printed version.
    Useful for human-readable logging, debugging, or file saving.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False, "default": ""}),
                "ensure_ascii": ("BOOLEAN", {"default": False, "tooltip": "Escape non-ASCII characters to \\uXXXX"}),
                "sort_keys": ("BOOLEAN", {"default": False, "tooltip": "Sort dictionary keys alphabetically"}),
                "on_error_return_original": ("BOOLEAN", {"default": True, "tooltip": "Return original string on parse failure instead of error message"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("pretty_json",)
    FUNCTION = "format_json"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    def format_json(self, json_string: str, ensure_ascii=False, sort_keys=False, on_error_return_original=True):
        if not json_string or not json_string.strip():
            log(LogEntry(
                node_class="JsonFormat",
                title="Empty input",
                details={"Action": "Returning empty string"},
                footer="No formatting needed"
            ))
            return ("",)

        try:
            parsed = json.loads(json_string)
            pretty = json.dumps(
                parsed,
                indent=4,
                ensure_ascii=ensure_ascii,
                sort_keys=sort_keys,
                separators=(',', ': ')
            )
            log(LogEntry(
                node_class="JsonFormat",
                title="JSON formatted successfully",
                details={"Keys Sorted": sort_keys, "Ensure ASCII": ensure_ascii},
                footer="Pretty-printed string returned"
            ))
            return (pretty,)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {e}"
            log(LogEntry(
                node_class="JsonFormat",
                title="JSON decode failed",
                details={"Error": str(e)},
                footer=f"{'Returning original' if on_error_return_original else 'Returning error message'}"
            ))
            if on_error_return_original:
                return (json_string,)
            return (error_msg,)