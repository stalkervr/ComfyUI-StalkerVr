import json
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class JsonFieldRemover:
    """
    JsonFieldRemover
    ----------------
    Removes specified fields from a JSON string using dot-notation paths.
    Supports multiple paths separated by '|' and returns a formatted JSON string.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False}),
                "key": ("STRING", {
                    "default": "action.props | action.sequence",
                    "multiline": False,
                    "tooltip": "Fields to remove, separated by '|' (e.g., 'path.to.field1 | path.to.field2')"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_string",)
    FUNCTION = "clean_json"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    @staticmethod
    def _remove_path(obj: dict, path: str) -> bool:
        """Safely removes a key from a nested dictionary using dot notation. Returns True if deleted."""
        parts = path.split(".")
        current = obj
        for i, part in enumerate(parts):
            if not isinstance(current, dict) or part not in current:
                return False
            if i == len(parts) - 1:
                del current[part]
                return True
            current = current[part]
        return False

    def clean_json(self, json_string: str, key: str) -> tuple[str]:
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            log(LogEntry(
                node_class="JsonFieldRemover",
                title="JSON decode failed",
                details={"Error": str(e)},
                footer="Returning original string"
            ))
            return (json_string,)

        field_paths = [f.strip() for f in key.split("|") if f.strip()]
        removed_paths = [path for path in field_paths if self._remove_path(data, path)]

        result = json.dumps(data, ensure_ascii=False, indent=2)

        log(LogEntry(
            node_class="JsonFieldRemover",
            title="Fields processed",
            details={
                "Attempted": len(field_paths),
                "Removed": len(removed_paths),
                "Paths": ", ".join(removed_paths) if removed_paths else "None"
            },
            footer="Formatted JSON returned"
        ))

        return (result,)