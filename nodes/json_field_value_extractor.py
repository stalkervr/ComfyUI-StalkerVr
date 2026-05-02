import json
from .constants import CATEGORY_PREFIX
from .types import Everything
from .logger import LogEntry, log

class JsonFieldValueExtractor:
    """
    JsonFieldValueExtractor
    ------------------------
    Extracts a field value from a JSON string and returns it with its original type.
    Supports nested keys using dot notation (e.g., 'parent.child.key').
    Includes passthrough output for chaining multiple extractions in pipeline.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {
                    "multiline": False,
                    "default": '{"name": "Harley", "age": 25, "info": {"city": "Gotham", "zip": "10001"}, "tags": ["psycho", "funny"]}'
                }),
                "key": ("STRING", {
                    "default": "info.city",
                    "multiline": False,
                    "tooltip": "Field key to extract (supports dot notation: parent.child.key)"
                }),
            }
        }

    RETURN_TYPES = (Everything("*"), "STRING")
    RETURN_NAMES = ("value", "json_passthrough")
    FUNCTION = "extract_value"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    def extract_value(self, json_string, key):
        json_passthrough = json_string

        try:
            data = json.loads(json_string)

            if not key or not key.strip():
                log(LogEntry(
                    node_class="JsonFieldValueExtractor",
                    title="Empty key provided",
                    details={"Action": "Returning full JSON object"},
                    footer="Key validation complete"
                ))
                return (data, json_passthrough)

            keys = [k.strip() for k in key.split(".") if k.strip()]
            current_value = data

            for k in keys:
                if isinstance(current_value, dict) and k in current_value:
                    current_value = current_value[k]
                else:
                    log(LogEntry(
                        node_class="JsonFieldValueExtractor",
                        title="Key not found",
                        details={"Requested": key, "Failed at": k},
                        footer="Returning None"
                    ))
                    return (None, json_passthrough)

            log(LogEntry(
                node_class="JsonFieldValueExtractor",
                title="Value extracted successfully",
                details={"Key": key, "Type": type(current_value).__name__},
                footer="Ready for downstream nodes"
            ))
            return (current_value, json_passthrough)

        except json.JSONDecodeError as e:
            log(LogEntry(
                node_class="JsonFieldValueExtractor",
                title="JSON decode failed",
                details={"Error": str(e)},
                footer="Returning None"
            ))
            return (None, json_passthrough)
        except Exception as e:
            log(LogEntry(
                node_class="JsonFieldValueExtractor",
                title="Unexpected error",
                details={"Error": str(e)},
                footer="Returning None"
            ))
            return (None, json_passthrough)