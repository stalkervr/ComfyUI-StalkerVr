import json

from .constants import CATEGORY_PREFIX


class Everything(str):
    """Wildcard type marker that accepts any input type."""

    def __ne__(self, __value: object) -> bool:
        return False


class JsonBuilder:
    """
    JsonBuilder
    ----------
    Builds JSON from key-value pairs.
    Skips fields with null or empty string values.
    Supports nested keys using dot notation.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "num_pairs": ("INT", {"default": 1, "min": 0, "max": 20}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_output",)
    FUNCTION = "build_json"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    def build_json(self, num_pairs, **kwargs):
        json_dict = {}

        for i in range(1, num_pairs + 1):
            key_name = f"key_{i}"
            value_name = f"value_{i}"

            key_val = kwargs.get(key_name)
            value_val = kwargs.get(value_name)

            # Skip if key is empty or None
            if key_val is None or key_val == "":
                continue

            # Skip if value is None or empty string
            if value_val is None or (isinstance(value_val, str) and value_val == ""):
                print(f"📝 [JsonBuilder] Skipping field '{key_val}': null or empty value")
                continue

            # Add the field to JSON
            if '.' in key_val:
                self._set_nested_value(json_dict, key_val, value_val)
            else:
                json_dict[key_val] = value_val

        try:
            json_output = json.dumps(json_dict, ensure_ascii=False, indent=2)
            print(f"✅ [JsonBuilder] Built JSON with {len(json_dict)} top-level keys/paths.")
            return (json_output,)
        except Exception as e:
            print(f"❌ [JsonBuilder] Error serializing: {e}")
            return ("{}",)

    def _set_nested_value(self, target_dict, key_path, value):
        keys = key_path.split('.')
        current = target_dict
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value