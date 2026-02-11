import json
import os
import traceback
from pathlib import Path
import random


from .constants import (
    CATEGORY_PREFIX
)


class Everything(str):
    """Wildcard type marker."""
    def __ne__(self, __value: object) -> bool:
        return False


class JsonFieldValueExtractor:
    """
    Node to extract a field value from a JSON string and convert it to multiple output formats:
    STRING, INT, FLOAT, JSON, VALUE_LIST, BATCH_ANY
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {
                    "multiline": False,
                    "default": "{\n"
                               "  \"name\": \"Harley\",\n"
                               "  \"age\": 25,\n"
                               "  \"power\": 9.5,\n"
                               "  \"info\": {\"city\": \"Gotham\", \"zip\": \"10001\"},\n"
                               "  \"tags\": [\"psycho\", \"funny\", \"dangerous\"],\n"
                               "  \"scores\": [1, 2.5, 3, 4]\n"
                               "}"
                }),
                "key": ("STRING", {"default": "tags", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "FLOAT", "STRING", "LIST", "BATCH_ANY")
    RETURN_NAMES = ("string", "int", "float", "json_string", "list", "batch")
    OUTPUT_IS_LIST = (False, False, False, False, False, True)
    FUNCTION = "extract_value"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = "Node to extract a field value from a JSON string and convert it to multiple output formats"

    def extract_value(self, json_string, key):
        try:
            data = json.loads(json_string)

            keys = key.split(".")
            value = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return (f"[ERROR] Field '{key}' not found", 0, 0.0, "{}", [], [])

            str_value = str(value)

            try:
                int_value = int(float(value))
            except (ValueError, TypeError):
                int_value = 0

            try:
                float_value = float(value)
            except (ValueError, TypeError):
                float_value = 0.0

            try:
                json_value = json.dumps(value, ensure_ascii=False, indent=2)
            except Exception:
                json_value = "{}"

            value_list = []
            batch_any = []
            if isinstance(value, list):
                value_list = value
                batch_any = value

            return (str_value, int_value, float_value, json_value, value_list, batch_any)

        except json.JSONDecodeError as e:
            return (f"[ERROR] Invalid JSON: {e}", 0, 0.0, "{}", [], [])
        except Exception as e:
            return (f"[ERROR] {e}", 0, 0.0, "{}", [], [])


class JsonRootListExtractor:
    """
    Attempts to parse a JSON string. If the root element is a list (array),
    it returns that list. The node first tries standard JSON parsing.
    If that fails due to quote issues (e.g., single quotes from Python's str()),
    it attempts to fix the quotes and parse again.
    Useful for extracting a root-level array from a potentially non-standard JSON string.
    """
    LOG_TAG = "[JsonRootListExtractor]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": True}),
            }
        }

    RETURN_TYPES = ("LIST",)
    RETURN_NAMES = ("list_output",)
    FUNCTION = "extract_root_list"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = """
Attempts to parse a JSON string. If the root element is a list (array),
it returns that list. The node first tries standard JSON parsing.
If that fails due to quote issues (e.g., single quotes from Python's str()),
it attempts to fix the quotes and parse again.
Useful for extracting a root-level array from a potentially non-standard JSON string.
"""

    def extract_root_list(self, json_string):

        parsed_data = None
        error_occurred = False

        try:
            parsed_data = json.loads(json_string)
            print(f"{self.LOG_TAG} Successfully parsed input as standard JSON.")
        except json.JSONDecodeError as e:
            print(f"{self.LOG_TAG} Standard JSON parsing failed: {e}. Attempting quote correction...")
            error_occurred = True

        if error_occurred:
            try:
                corrected_string = json_string.replace("'", '"')
                parsed_data = json.loads(corrected_string)
                print(f"{self.LOG_TAG} Successfully parsed input after quote correction.")
            except json.JSONDecodeError as e2:
                print(f"{self.LOG_TAG} Parsing failed even after quote correction: {e2}")
                print(f"{self.LOG_TAG} Returning empty list.")
                return ([],)
            except Exception as general_ex:
                print(f"{self.LOG_TAG} Unexpected error during quote correction: {general_ex}")
                return ([],)

        if isinstance(parsed_data, list):
            return (parsed_data,)
        else:
            print(
                f"{self.LOG_TAG} Root element is not a list (it's a {type(parsed_data).__name__}), returning empty list.")
            return ([],)


class JsonFieldRemover:
    """
    Removes fields from JSON by paths separated with '|'
    Example: "action.props | action.sequence"
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False}),
                "key": ("STRING", {
                    "default": "action.props | action.sequence",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_string",)
    FUNCTION = "clean_json"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = "Removes fields from JSON by paths separated with '|' Example: action.props | action.sequence"

    def _remove_path(self, obj, path: str):
        parts = path.split(".")
        current = obj

        for i, part in enumerate(parts):
            if not isinstance(current, dict):
                return
            if part not in current:
                return

            if i == len(parts) - 1:
                del current[part]
                return
            else:
                current = current[part]

    def clean_json(self, json_string, key):
        try:
            data = json.loads(json_string)
        except Exception:
            return (json_string,)

        field_paths = [
            f.strip()
            for f in key.split("|")
            if f.strip()
        ]

        for path in field_paths:
            self._remove_path(data, path)

        return (json.dumps(data, ensure_ascii=False, indent=2),)


class JsonFieldReplaceAdvanced:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False}),
                "key": ("STRING", {"default": ""}),   # путь: a.b.c или arr.1.name
                "value": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_string",)
    FUNCTION = "replace_field"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = "Add new field in JSON or replace exists field value"

    def cast_value(self, value: str):
        v = value.strip()
        v_low = v.lower()

        if v_low == "true":
            return True
        if v_low == "false":
            return False
        if v_low == "null":
            return None

        if (v.startswith("-") and v[1:].isdigit()) or v.isdigit():
            try:
                return int(v)
            except:
                pass

        try:
            return float(v)
        except:
            pass

        return value

    def set_by_path(self, data, path_parts, value):
        obj = data

        for i, part in enumerate(path_parts):
            is_last = i == len(path_parts) - 1

            if part.isdigit():
                idx = int(part)

                if not isinstance(obj, list):
                    raise Exception("Path error: trying to index non-array object")

                while len(obj) <= idx:
                    obj.append({})

                if is_last:
                    obj[idx] = value
                else:
                    if not isinstance(obj[idx], (dict, list)):
                        obj[idx] = {}
                    obj = obj[idx]

            else:
                if is_last:
                    obj[part] = value
                else:
                    if part not in obj or not isinstance(obj[part], (dict, list)):
                        obj[part] = {}
                    obj = obj[part]

    def replace_field(self, json_string, key, value):

        try:
            data = json.loads(json_string)
        except Exception as e:
            return (f"JSON parse error: {str(e)}",)

        if not key:
            return (json.dumps(data, ensure_ascii=False, indent=4),)

        casted = self.cast_value(value)
        path_parts = key.split(".")

        try:
            self.set_by_path(data, path_parts, casted)
        except Exception as e:
            return (f"Path set error: {str(e)}",)

        formatted = json.dumps(data, ensure_ascii=False, indent=4)

        return (formatted,)


class JsonToString:
    """
    Node: JsonToStringNode
    Converts JSON to a formatted string.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_input": ("STRING", {"multiline": False}),
                "new_line": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "process"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = "Converts JSON to a formatted string."

    def process(self, json_input, new_line=False):
        import json_process

        try:
            data = json.loads(json_input)
        except Exception as e:
            return (f"Error parsing JSON: {e}",)

        if isinstance(data, dict):
            if new_line:
                result = "\n".join(f"{k}: {v}" for k, v in data.items())
            else:
                result = ", ".join(f"{k}: {v}" for k, v in data.items())
        else:
            result = json.dumps(data, ensure_ascii=False, indent=2 if new_line else None)

        return (result,)


class JsonArraySplitter:
    """
    Expands a specified JSON array into a list of JSON objects.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_input": ("STRING", {"multiline": False}),
                "array_name": ("STRING", {"default": "prompt_list"}),
            }
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "split_json"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = "Expands a specified JSON array into a list of JSON objects."

    def _infer_and_set_return_type(self, items):
        if not items:
            self.RETURN_TYPES = (Everything("*"),)
            return

        seq = list(items)

        all_int = all(isinstance(v, int) and not isinstance(v, bool) for v in seq)
        all_float = all(isinstance(v, float) for v in seq)
        all_str = all(isinstance(v, str) for v in seq)

        if all_int:
            self.RETURN_TYPES = ("INT",)
        elif all_float:
            self.RETURN_TYPES = ("FLOAT",)
        elif all_str:
            self.RETURN_TYPES = ("STRING",)
        else:
            self.RETURN_TYPES = (Everything("*"),)

    def split_json(self, json_input, array_name):

        try:
            data = json.loads(json_input)
        except Exception as e:
            output = [f"JSON parse error: {e}"]
            self._infer_and_set_return_type(output)
            return (output,)

        arr = data.get(array_name)

        if arr is None:
            output = [f"Error: array '{array_name}' not found in JSON"]
            self._infer_and_set_return_type(output)
            return (output,)

        if not isinstance(arr, list):
            output = [f"Error: '{array_name}' must be a JSON array"]
            self._infer_and_set_return_type(output)
            return (output,)

        base_fields = {k: v for k, v in data.items() if k != array_name}

        result = []

        for item in arr:
            if not isinstance(item, dict):
                output = [f"Error: elements of '{array_name}' must be objects"]
                self._infer_and_set_return_type(output)
                return (output,)

            merged = {**base_fields, **item}
            pretty = json.dumps(merged, ensure_ascii=False, indent=4)
            result.append(pretty)

        self._infer_and_set_return_type(result)

        return (result,)


class JsonPromptToTextPromptConverter:
    """
    Converts JSON to a string, leaving **only values** without field names,
    according to the rules:
    - empty/null values are skipped
    - strings end with a period
    - lists → comma-separated elements, ending with a period
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False}),
                "new_line": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "extract_values"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = """
Converts JSON to a string, leaving **only values** without field names,
according to the rules:
- empty/null values are skipped
- strings end with a period
- lists → comma-separated elements, ending with a period
"""

    def _is_empty(self, v):
        if v is None:
            return True
        if isinstance(v, str):
            s = v.strip()
            return s == "" or s.lower() == "null"
        return False

    def _format_string(self, s):
        s = s.strip()
        if s == "":
            return None
        if not s.endswith("."):
            s += "."
        return s

    def _format_list(self, lst):
        cleaned = []

        for item in lst:
            if self._is_empty(item):
                continue
            if isinstance(item, (dict, list)):
                temp = []
                self._collect_values(item, temp)
                cleaned.extend(temp)
            else:
                cleaned.append(str(item).strip())

        if not cleaned:
            return None

        return ", ".join(cleaned) + "."

    def _collect_values(self, obj, out_list):
        if isinstance(obj, dict):
            for v in obj.values():
                self._collect_values(v, out_list)

        elif isinstance(obj, list):
            formatted = self._format_list(obj)
            if formatted:
                out_list.append(formatted)

        else:
            if self._is_empty(obj):
                return

            formatted = self._format_string(str(obj))
            if formatted:
                out_list.append(formatted)

    def extract_values(self, json_string, new_line):

        try:
            data = json.loads(json_string)
        except Exception as e:
            return (f"JSON parse error: {e}",)

        values = []
        self._collect_values(data, values)

        if new_line:
            return ("\n".join(values),)
        else:
            return (" ".join(values),)


class JsonPathLoader:
    """
    Loads all JSON files from a folder on each execution.
    Adds a random reload_trigger to force reloading every time.
    Dynamically infers output type (like LoopAny).
    """

    LOG_TAG = "[JsonPathLoader]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"multiline": False, "default": ""}),
                "reload_trigger": ("INT", {"default": 0}),  # auto-generated random value
            },
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "load"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = """
Loads all JSON files from a folder on each execution.
Adds a random reload_trigger to force reloading every time.
Dynamically infers output type (like LoopAny).
"""

    def _infer_and_set_return_type(self, items):
        if not items:
            self.RETURN_TYPES = (Everything("*"),)
            return

        all_int = all(isinstance(v, int) and not isinstance(v, bool) for v in items)
        all_float = all(isinstance(v, float) for v in items)
        all_str = all(isinstance(v, str) for v in items)

        if all_int:
            self.RETURN_TYPES = ("INT",)
        elif all_float:
            self.RETURN_TYPES = ("FLOAT",)
        elif all_str:
            self.RETURN_TYPES = ("STRING",)
        else:
            self.RETURN_TYPES = (Everything("*"),)

    def load(self, folder_path, reload_trigger=None):

        if reload_trigger is None:
            reload_trigger = random.randint(0, 1_000_000)

        print(f"\n")
        print(f"{self.LOG_TAG} Generated reload_trigger: {reload_trigger}")

        folder = Path(folder_path)
        output_list = []

        print(f"{self.LOG_TAG} -> Start JSON directory scan")
        print(f"{self.LOG_TAG} Directory: {folder_path}\n")

        if not folder.exists() or not folder.is_dir():
            print(f"{self.LOG_TAG} ERROR: folder does not exist or is not a directory")
            self.RETURN_TYPES = (Everything("*"),)
            return ([],)

        for file in folder.glob("*.json"):
            try:
                file_path = str(file)
                size_kb = round(os.path.getsize(file) / 1024, 2)

                print(f"{self.LOG_TAG} File found: {file_path}")
                print(f"{self.LOG_TAG} Size: {size_kb} KB")

                raw_text = file.read_text(encoding="utf-8")
                json_len = len(raw_text)
                print(f"{self.LOG_TAG} JSON length: {json_len} chars")

                parsed = json.loads(raw_text)
                formatted = json.dumps(parsed, ensure_ascii=False, indent=4)

                output_list.append(formatted)
                print(f"{self.LOG_TAG} Loaded successfully\n")

            except Exception as e:
                print(f"{self.LOG_TAG} ERROR reading file {file.name}: {e}")
                traceback.print_exc()

        print(f"{self.LOG_TAG} -> Finished JSON directory scan")
        print(f"\n")

        self._infer_and_set_return_type(output_list)
        return (output_list,)


class JsonPairInput:
    """
    A simple node to input a key-value pair as strings.
    Outputs the key and value separately.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "key": ("STRING", {"default": "key", "multiline": False}),
                "value": ("STRING", {"default": "value", "multiline": False})
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("key", "value")
    FUNCTION = "get_pair"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = """
A simple node to input a key-value pair as strings.
Outputs the key and value separately."""

    def get_pair(self, key, value):
        return (key, value)


class JsonSerializeObject:
    """
    Takes either a single Python object or a list of Python objects
    (e.g., dictionaries, lists, primitives) and converts each to its JSON string representation.
    Returns a list (BATCH_ANY) of these JSON strings via a wildcard output marked as a list.
    """

    LOG_TAG = "[JsonSerializeObject]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_data": (Everything("*"),),
            }
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "serialize_to_json_batch"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = """
Takes either a single Python object or a list of Python objects
(e.g., dictionaries, lists, primitives) and converts each to its JSON string representation.
Returns a list (BATCH_ANY) of these JSON strings via a wildcard output marked as a list.
"""

    def serialize_to_json_batch(self, input_data):
        if isinstance(input_data, list):
            objects_to_process = input_data
            print(f"{self.LOG_TAG} Input is a list with {len(input_data)} items.")
        else:
            objects_to_process = [input_data]
            print(f"{self.LOG_TAG} Input is a single object of type {type(input_data).__name__}. Wrapped in a list.")

        json_strings = []
        for i, obj in enumerate(objects_to_process):
            try:
                json_str = json.dumps(obj, ensure_ascii=False)
                json_strings.append(json_str)
            except (TypeError, ValueError) as e:
                print(
                    f"{self.LOG_TAG} Error serializing item {i} (type {type(obj).__name__}) to JSON: {e}. Adding empty string.")
                json_strings.append("")

        print(f"{self.LOG_TAG} Serialized {len(objects_to_process)} item(s) to {len(json_strings)} JSON strings.")

        return (json_strings,)


class JsonDeserializeObject:
    """
    Takes either a single JSON string or a list of JSON strings and deserializes each string
    back into its original Python object (e.g., dictionaries, lists, primitives).
    Returns a list (BATCH_ANY) of these Python objects.
    If input is a single string, it's treated as a list with one item.
    If input is a list, each item is processed individually.
    """

    LOG_TAG = "[JsonDeserializeObject]"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_data": (Everything("*"),),
            },
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "deserialize_from_json_batch"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = """
Takes either a single JSON string or a list of JSON strings and deserializes each string
back into its original Python object (e.g., dictionaries, lists, primitives).
Returns a list (BATCH_ANY) of these Python objects.
If input is a single string, it's treated as a list with one item.
If input is a list, each item is processed individually.
"""

    def deserialize_from_json_batch(self, input_data):
        if isinstance(input_data, list):
            json_strings_to_process = input_data
            print(f"{self.LOG_TAG} Input is a list with {len(input_data)} items.")
        elif isinstance(input_data, str):
            json_strings_to_process = [input_data]
            print(f"{self.LOG_TAG} Input is a single JSON string. Wrapped in a list for processing.")
        else:
            print(
                f"{self.LOG_TAG} Input is neither a list nor a string (it's a {type(input_data).__name__}). Returning empty list.")
            return ([],)

        python_objects = []
        for i, json_str in enumerate(json_strings_to_process):
            if not isinstance(json_str, str):
                print(f"{self.LOG_TAG} Item {i} is not a string (it's a {type(json_str).__name__}). Adding None.")
                python_objects.append(None)
                continue

            try:
                obj = json.loads(json_str)
                python_objects.append(obj)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"{self.LOG_TAG} Error deserializing item {i} ('{json_str[:50]}...'): {e}. Adding None.")
                python_objects.append(None)

        print(
            f"{self.LOG_TAG} Deserialized {len(json_strings_to_process)} item(s) to {len(python_objects)} Python object(s).")

        return (python_objects,)


class JsonFormat:
    """
    JsonFormat
    ----------
    Takes a JSON string (formatted or minified) and outputs a pretty-printed version.
    Useful for human-readable logging or file saving.

    If input is not valid JSON, returns the original string (or error message if strict mode enabled).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False, "default": ""}),
                "ensure_ascii": ("BOOLEAN", {"default": False}),
                "sort_keys": ("BOOLEAN", {"default": False}),
                "on_error_return_original": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("pretty_json",)
    FUNCTION = "format_json"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = "Formats JSON string with indentation for readability."

    def format_json(self, json_string: str, ensure_ascii=False, sort_keys=False, on_error_return_original=True):
        try:
            # Parse JSON
            parsed = json.loads(json_string)
            # Pretty-print
            pretty = json.dumps(
                parsed,
                indent=4,
                ensure_ascii=ensure_ascii,
                sort_keys=sort_keys,
                separators=(',', ': ')  # standard spacing
            )
            return (pretty,)
        except json.JSONDecodeError as e:
            error_msg = f"[JsonFormat ERROR] Invalid JSON: {e}"
            print(error_msg, file=__import__('sys').stderr)
            if on_error_return_original:
                return (json_string,)
            else:
                return (error_msg,)


class JsonMinify:
    """
    JsonMinify
    ----------
    Takes a pretty-printed JSON string and outputs a minified (compact) version.
    Removes all unnecessary whitespace, newlines, and indentation.

    If input is not valid JSON, returns the original string (or error message if strict mode enabled).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": False, "default": ""}),
                "ensure_ascii": ("BOOLEAN", {"default": False}),
                "sort_keys": ("BOOLEAN", {"default": False}),
                "on_error_return_original": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("minified_json",)
    FUNCTION = "minify_json"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = "Minifies JSON string by removing whitespace and newlines."

    def minify_json(self, json_string: str, ensure_ascii=False, sort_keys=False, on_error_return_original=True):
        try:
            # Parse to validate and normalize
            parsed = json.loads(json_string)
            # Dump in compact form
            minified = json.dumps(
                parsed,
                separators=(',', ':'),  # no extra spaces
                ensure_ascii=ensure_ascii,
                sort_keys=sort_keys
            )
            return (minified,)
        except json.JSONDecodeError as e:
            error_msg = f"[JsonMinify ERROR] Invalid JSON: {e}"
            print(error_msg, file=__import__('sys').stderr)
            if on_error_return_original:
                return (json_string,)
            else:
                return (error_msg,)