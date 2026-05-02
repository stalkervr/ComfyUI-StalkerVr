import json
import re
from .constants import CATEGORY_PREFIX
from .types import Everything
from .logger import LogEntry, log

class JsonPairInput:
    """
    JsonPairInput
    --------------
    Automatically detects and converts string inputs to appropriate types.
    Handles disconnected optional inputs by returning null for value.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "key": ("STRING", {
                    "default": "my_key",
                    "multiline": False,
                }),
            },
            "optional": {
                "value": (Everything("*"), {
                    "default": "",
                })
            }
        }

    RETURN_TYPES = ("STRING", Everything("*"))
    RETURN_NAMES = ("key", "value")
    FUNCTION = "get_pair"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    def get_pair(self, key, value=None):
        # Handle key: always convert to string
        key_str = str(key) if key is not None else ""

        # Handle value: disconnected or empty string returns None
        if value is None:
            converted_value = None
        elif isinstance(value, str) and value == "":
            converted_value = None
        else:
            # Auto-detect and convert types for connected inputs
            converted_value = self._auto_convert_type(value)

        return (key_str, converted_value)

    def _auto_convert_type(self, value):
        """Automatically convert string values to appropriate Python/JSON types."""
        if not isinstance(value, str):
            return value

        val = value.strip()
        if not val:
            return None

        # Try parsing as valid JSON (lists, dicts, numbers, booleans)
        try:
            parsed = json.loads(val)
            log(LogEntry(
                node_class="JsonPairInput",
                title="Value parsed as JSON",
                details={"Type": type(parsed).__name__}
            ))
            return parsed
        except (json.JSONDecodeError, TypeError):
            pass

        # Check for boolean literals
        if val.lower() in ('true', 'false'):
            result = val.lower() == 'true'
            log(LogEntry(
                node_class="JsonPairInput",
                title="Value converted to boolean",
                details={"Value": result}
            ))
            return result

        # Check for null/none literals
        if val.lower() in ('null', 'none'):
            log(LogEntry(
                node_class="JsonPairInput",
                title="Value converted to None",
                details={"Original": val}
            ))
            return None

        # Check for numeric literals (int or float)
        if re.match(r'^-?\d+\.?\d*$', val):
            try:
                result = int(val) if '.' not in val else float(val)
                log(LogEntry(
                    node_class="JsonPairInput",
                    title="Value converted to number",
                    details={"Type": type(result).__name__, "Value": result}
                ))
                return result
            except (ValueError, OverflowError):
                pass

        # Fallback: return as plain string
        log(LogEntry(
            node_class="JsonPairInput",
            title="Value kept as string",
            details={"Length": len(val)}
        ))
        return val