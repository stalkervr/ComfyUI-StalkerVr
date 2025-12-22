import json


class JsonBuilder:
    """
    Node to dynamically add key-value input pairs based on the 'num_pairs' value.
    Supports nested keys using dot notation (e.g., 'parent.child.key').
    Attempts to infer the type of values (int, float, bool, null, list, dict) from their string representation.
    Combines these pairs into a JSON string output.
    """

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "num_pairs": ("INT", {"default": 1, "min": 0, "max": 20}),
            },
        }

        return inputs

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_output",)
    FUNCTION = "build_json"
    CATEGORY = "Stalkervr/JSON"
    DESCRIPTION = """
Node to dynamically add key-value input pairs based on the 'num_pairs' value.
Supports nested keys using dot notation (e.g., 'parent.child.key').
Attempts to infer the type of values (int, float, bool, null, list, dict) from their string representation.
Combines these pairs into a JSON string output.
"""

    def build_json(self, num_pairs, **kwargs):
        """
        Builds a JSON string from the provided key-value pairs up to num_pairs.
        Supports nested keys using dot notation.
        Attempts to infer the type of values from their string representation.
        Uses **kwargs to capture values from the dynamically added inputs.
        Only uses the first 'num_pairs' pairs of inputs (key_1/value_1, key_2/value_2, ..., key_{num_pairs}/value_{num_pairs}).
        """
        json_dict = {}

        for i in range(1, num_pairs + 1):
            key_name = f"key_{i}"
            value_name = f"value_{i}"

            key_val = kwargs.get(key_name)
            value_val = kwargs.get(value_name)

            if key_val is not None and key_val != "":
                typed_value = self._convert_value(value_val)

                if '.' in key_val:
                    self._set_nested_value(json_dict, key_val, typed_value)
                else:
                    json_dict[key_val] = typed_value

        try:
            json_output = json.dumps(json_dict, ensure_ascii=False, indent=2)
            print(f"[JsonBuilder] Built JSON with {len(json_dict)} top-level keys/paths.")
        except (TypeError, ValueError) as e:
            print(f"[JsonBuilder] Error serializing to JSON: {e}")
            json_output = "{}"

        return (json_output,)

    def _set_nested_value(self, target_dict, key_path, value):
        """
        Helper function to set a value in a nested dictionary based on a dot-separated key path.
        e.g., key_path='parent.child.key', value='val' sets target_dict['parent']['child']['key'] = 'val'
        Creates intermediate dictionaries if they don't exist.
        """
        keys = key_path.split('.')
        current = target_dict

        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def _convert_value(self, value_str):
        """
        Attempts to convert a string value to its most appropriate Python type
        (int, float, bool, None, list, dict).
        If conversion fails, returns the original string.
        """
        if not isinstance(value_str, str):
            return value_str

        try:
            parsed_json = json.loads(value_str)
            return parsed_json
        except (json.JSONDecodeError, TypeError):
            pass

        if value_str.lower() in ('none', 'null'):
            return None

        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'

        try:
            f_val = float(value_str)
            if f_val.is_integer():
                return int(f_val)
            else:
                return f_val
        except ValueError:
            pass

        return value_str