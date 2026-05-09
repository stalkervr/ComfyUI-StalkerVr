import json
import ast
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class JsonFieldReplaceExtend:
    """
    JsonFieldReplaceExtend
    ----------------------
    Adds or replaces a field in a JSON string using dot-notation paths.
    Supports array indexing and optional value extension (prepend with comma).
    Automatically casts strings to native Python/JSON types.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False}),
                "key": ("STRING", {"default": "", "tooltip": "Dot-notation path (e.g., a.b.c or arr.1.name)"}),
                "value": ("STRING", {"default": "", "tooltip": "Value to set (auto-casts to int/float/bool/null/JSON)"}),
                "extend_value": ("BOOLEAN", {"default": False, "tooltip": "If true, prepend value to existing string: 'new, old'"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_string",)
    FUNCTION = "replace_field"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    @staticmethod
    def _cast_value(value: str):
        v = value.strip()
        v_low = v.lower()
        if v_low == "true": return True
        if v_low == "false": return False
        if v_low == "null": return None
        if v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
            try: return int(v)
            except ValueError: pass
        try: return float(v)
        except ValueError: pass
        return value

    @staticmethod
    def _set_by_path(data, path_parts, value, extend=False):
        obj = data
        for i, part in enumerate(path_parts):
            is_last = (i == len(path_parts) - 1)
            if part.isdigit():
                idx = int(part)
                if not isinstance(obj, list):
                    raise TypeError(f"Expected list at path segment '{part}'")
                while len(obj) <= idx:
                    obj.append({})
                if is_last:
                    if extend and idx < len(obj) and obj[idx] is not None:
                        existing = obj[idx]
                        if isinstance(existing, str) and isinstance(value, str):
                            obj[idx] = f"{value}, {existing}"
                        else:
                            obj[idx] = value
                    else:
                        obj[idx] = value
                else:
                    if not isinstance(obj[idx], (dict, list)):
                        obj[idx] = {}
                    obj = obj[idx]
            else:
                if is_last:
                    if extend and part in obj:
                        existing = obj[part]
                        if isinstance(existing, str) and isinstance(value, str):
                            obj[part] = f"{value}, {existing}"
                        else:
                            obj[part] = value
                    else:
                        obj[part] = value
                else:
                    if part not in obj or not isinstance(obj[part], (dict, list)):
                        obj[part] = {}
                    obj = obj[part]

    def replace_field(self, json_string, key, value, extend_value):
        if not value.strip():
            log(LogEntry(node_class="JsonFieldReplaceExtend", title="Skipped", details={"Reason": "Empty value"}, footer="Returning original JSON"))
            return (json_string,)

        # Parse input JSON
        try:
            if isinstance(json_string, str):
                data = json.loads(json_string.strip())
            elif isinstance(json_string, dict):
                data = json_string.copy()
            else:
                raise TypeError("Input must be JSON string or dict")
        except (json.JSONDecodeError, TypeError) as e:
            try:
                data = ast.literal_eval(json_string if isinstance(json_string, str) else str(json_string))
                if not isinstance(data, (dict, list)):
                    raise ValueError("Parsed result is not a dict or list")
            except Exception as fallback_err:
                log(LogEntry(node_class="JsonFieldReplaceExtend", title="Parse failed", details={"Error": str(e), "Fallback": str(fallback_err)}, footer="Returning error string"))
                return (f"JSON parse error: {e}",)

        if not key.strip():
            log(LogEntry(node_class="JsonFieldReplaceExtend", title="Empty key", details={"Action": "Returning formatted JSON"}, footer="No modification needed"))
            return (json.dumps(data, ensure_ascii=False, indent=2),)

        # Cast value
        casted = value
        try:
            casted = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            casted = self._cast_value(value)

        path_parts = [p for p in key.split(".") if p]
        if not path_parts:
            log(LogEntry(node_class="JsonFieldReplaceExtend", title="Invalid path", details={"Key": key}, footer="Returning formatted JSON"))
            return (json.dumps(data, ensure_ascii=False, indent=2),)

        try:
            self._set_by_path(data, path_parts, casted, extend=extend_value)
        except Exception as e:
            log(LogEntry(node_class="JsonFieldReplaceExtend", title="Path error", details={"Key": key, "Error": str(e)}, footer="Returning error string"))
            return (f"Path set error: {e}",)

        log(LogEntry(node_class="JsonFieldReplaceExtend", title="Field updated", details={"Key": key, "Extend": extend_value, "Path Length": len(path_parts)}, footer="Formatted JSON returned"))
        return (json.dumps(data, ensure_ascii=False, indent=2),)