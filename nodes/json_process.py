import json
import os
import traceback
import random
import re
import hashlib



from typing import Tuple
from pathlib import Path
from .constants import CATEGORY_PREFIX


class Everything(str):
    """Wildcard type marker."""
    def __ne__(self, __value: object) -> bool:
        return False


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
                "extend_value": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_string",)
    FUNCTION = "replace_field"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = (
        "Add new field in JSON or replace exists field value.\n"
        "If 'extend_value' is True and field exists, it will be extended as:\n"
        "'new_value, existing_value'.\n"
        "Skips if value is empty."
    )

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

    def get_by_path(self, data, path_parts):
        """Helper to safely get value by path."""
        obj = data
        for part in path_parts:
            if part.isdigit():
                idx = int(part)
                if not isinstance(obj, list) or idx >= len(obj):
                    return None
                obj = obj[idx]
            else:
                if not isinstance(obj, dict) or part not in obj:
                    return None
                obj = obj[part]
        return obj

    def set_by_path(self, data, path_parts, value, extend=False):
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
        # Пропускаем, если значение для записи пустое
        if not value.strip():
            return (json_string,)

        # 🔑 Обрабатываем вход: может быть строкой ИЛИ уже словарём
        if isinstance(json_string, str):
            input_str = json_string.strip()
            if not input_str:
                return ('',)  # или '{}', если хотите начинать с пустого объекта
            try:
                data = json.loads(input_str)
            except json.JSONDecodeError as e:
                # Если не JSON — возможно, это repr(dict) с одинарными кавычками
                try:
                    import ast
                    data = ast.literal_eval(input_str)
                    if not isinstance(data, dict):
                        raise ValueError("Not a dict")
                except Exception:
                    return (f"JSON parse error: {str(e)}",)
        elif isinstance(json_string, dict):
            data = json_string.copy()
        else:
            return ("Input is neither string nor dict",)

        # Далее — обычная логика
        if not key.strip():
            return (json.dumps(data, ensure_ascii=False, indent=4),)

        # Попытка парсить value как JSON, иначе cast_value
        casted = value
        try:
            parsed_val = json.loads(value)
            casted = parsed_val
        except (json.JSONDecodeError, TypeError):
            casted = self.cast_value(value)

        path_parts = key.split(".")
        try:
            self.set_by_path(data, path_parts, casted, extend=extend_value)
        except Exception as e:
            return (f"Path set error: {str(e)}",)

        return (json.dumps(data, ensure_ascii=False, indent=4),)


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


# class JsonPathLoader:
#     """
#     Loads all JSON files from a folder on each execution.
#     Adds a random reload_trigger to force reloading every time.
#     Dynamically infers output type (like LoopAny).
#     """
#
#     LOG_TAG = "[JsonPathLoader]"
#
#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "folder_path": ("STRING", {"multiline": False, "default": ""}),
#                 "reload_trigger": ("INT", {"default": 0}),  # auto-generated random value
#             },
#         }
#
#     RETURN_TYPES = (Everything("*"),)
#     RETURN_NAMES = ("output",)
#     OUTPUT_IS_LIST = (True,)
#     FUNCTION = "load"
#     CATEGORY = f"{CATEGORY_PREFIX}/JSON"
#     DESCRIPTION = """
# Loads all JSON files from a folder on each execution.
# Adds a random reload_trigger to force reloading every time.
# Dynamically infers output type (like LoopAny).
# """
#
#     def _infer_and_set_return_type(self, items):
#         if not items:
#             self.RETURN_TYPES = (Everything("*"),)
#             return
#
#         all_int = all(isinstance(v, int) and not isinstance(v, bool) for v in items)
#         all_float = all(isinstance(v, float) for v in items)
#         all_str = all(isinstance(v, str) for v in items)
#
#         if all_int:
#             self.RETURN_TYPES = ("INT",)
#         elif all_float:
#             self.RETURN_TYPES = ("FLOAT",)
#         elif all_str:
#             self.RETURN_TYPES = ("STRING",)
#         else:
#             self.RETURN_TYPES = (Everything("*"),)
#
#     def load(self, folder_path, reload_trigger=None):
#
#         if reload_trigger is None:
#             reload_trigger = random.randint(0, 1_000_000)
#
#         print(f"\n")
#         print(f"{self.LOG_TAG} Generated reload_trigger: {reload_trigger}")
#
#         folder = Path(folder_path)
#         output_list = []
#
#         print(f"{self.LOG_TAG} -> Start JSON directory scan")
#         print(f"{self.LOG_TAG} Directory: {folder_path}\n")
#
#         if not folder.exists() or not folder.is_dir():
#             print(f"{self.LOG_TAG} ERROR: folder does not exist or is not a directory")
#             self.RETURN_TYPES = (Everything("*"),)
#             return ([],)
#
#         for file in folder.glob("*.json"):
#             try:
#                 file_path = str(file)
#                 size_kb = round(os.path.getsize(file) / 1024, 2)
#
#                 print(f"{self.LOG_TAG} File found: {file_path}")
#                 print(f"{self.LOG_TAG} Size: {size_kb} KB")
#
#                 raw_text = file.read_text(encoding="utf-8")
#                 json_len = len(raw_text)
#                 print(f"{self.LOG_TAG} JSON length: {json_len} chars")
#
#                 parsed = json.loads(raw_text)
#                 formatted = json.dumps(parsed, ensure_ascii=False, indent=4)
#
#                 output_list.append(formatted)
#                 print(f"{self.LOG_TAG} Loaded successfully\n")
#
#             except Exception as e:
#                 print(f"{self.LOG_TAG} ERROR reading file {file.name}: {e}")
#                 traceback.print_exc()
#
#         print(f"{self.LOG_TAG} -> Finished JSON directory scan")
#         print(f"\n")
#
#         self._infer_and_set_return_type(output_list)
#         return (output_list,)


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
                    "default": "{\n"
                               "  \"name\": \"Harley\",\n"
                               "  \"age\": 25,\n"
                               "  \"power\": 9.5,\n"
                               "  \"info\": {\"city\": \"Gotham\", \"zip\": \"10001\"},\n"
                               "  \"tags\": [\"psycho\", \"funny\", \"dangerous\"],\n"
                               "  \"scores\": [1, 2.5, 3, 4]\n"
                               "}"
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
    DESCRIPTION = """
Extracts a field value from JSON string with original type preservation.
- Supports nested keys using dot notation (e.g., 'parent.child.key')
- Returns value with its original type (string, number, boolean, list, object, null)
- Passthrough output is exact copy of input (not changed)
"""

    def extract_value(self, json_string, key):
        # Passthrough is exact copy of input - no manipulation
        json_passthrough = json_string

        try:
            # Parse JSON string
            data = json.loads(json_string)

            # Handle empty key - return the entire JSON object
            if not key or not key.strip():
                return (data, json_passthrough)

            # Navigate through nested keys using dot notation
            keys = [k for k in key.split(".") if k.strip()]

            if not keys:
                return (data, json_passthrough)

            current_value = data

            # Traverse the nested structure
            for i, current_key in enumerate(keys):
                if isinstance(current_value, dict):
                    if current_key in current_value:
                        current_value = current_value[current_key]
                    else:
                        return (None, json_passthrough)
                else:
                    return (None, json_passthrough)

            return (current_value, json_passthrough)

        except json.JSONDecodeError:
            return (None, json_passthrough)
        except Exception:
            return (None, json_passthrough)


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
        # Handle key (always convert to string)
        key_str = str(key) if key is not None else ""

        # Handle value: if not connected, value will be None
        if value is None:
            converted_value = None
        elif isinstance(value, str) and value == "":
            converted_value = None
        else:
            # Auto-detect and convert types for connected inputs
            converted_value = self._auto_convert_type(value)

        return (key_str, converted_value)

    def _auto_convert_type(self, value):
        """Automatically convert string values to appropriate types."""
        if not isinstance(value, str):
            return value

        val = value.strip()
        if not val:
            return None

        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            pass

        if val.lower() in ('true', 'false'):
            return val.lower() == 'true'

        if val.lower() in ('null', 'none'):
            return None

        if re.match(r'^-?\d+\.?\d*$', val):
            try:
                if '.' not in val:
                    return int(val)
                else:
                    return float(val)
            except (ValueError, OverflowError):
                pass

        return val


class JsonPathLoader:
    """
    Loads all JSON files from a folder.
    Cache is disabled - folder is rescanned on every execution.
    Supports file sorting and quantity limits.
    Dynamically infers output type.
    """

    LOG_TAG = "[JsonPathLoader]"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        Always return random value to force re-execution.
        This ensures folder contents are always fresh.
        """
        return random.random()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                "sort_by": (
                ["name", "name_desc", "created", "created_desc", "modified", "modified_desc", "size", "size_desc"], {
                    "default": "name",
                    "label": "Sort By",
                    "tooltip": "Sort files by: name, created date, modified date, or size (ascending or descending)"
                }),
                "limit": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 1,
                    "label": "File Limit",
                    "tooltip": "Max number of files to load (0 = unlimited)"
                }),
            },
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "load"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"
    DESCRIPTION = """
🎯 Loads all JSON files from a folder.

Features:
- Cache disabled by default (always rescans folder)
- Sort files by: name, created, modified, size (asc/desc)
- Limit number of loaded files (0 = unlimited)
- Dynamically infers output type (INT, FLOAT, STRING, or *)
- Detailed logging for debugging

Usage:
- Files are always read fresh on every execution
- Use for dynamic file collections that change during workflow
- Set limit to control how many files to process
"""

    def _sort_files(self, files, sort_by):
        """
        Sort files based on criteria.
        Args:
            files: List of Path objects
            sort_by: Sort criteria string
        Returns:
            Sorted list of Path objects
        """
        if sort_by == "name":
            return sorted(files, key=lambda f: f.name.lower())
        elif sort_by == "name_desc":
            return sorted(files, key=lambda f: f.name.lower(), reverse=True)
        elif sort_by == "created":
            return sorted(files, key=lambda f: f.stat().st_ctime)
        elif sort_by == "created_desc":
            return sorted(files, key=lambda f: f.stat().st_ctime, reverse=True)
        elif sort_by == "modified":
            return sorted(files, key=lambda f: f.stat().st_mtime)
        elif sort_by == "modified_desc":
            return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
        elif sort_by == "size":
            return sorted(files, key=lambda f: f.stat().st_size)
        elif sort_by == "size_desc":
            return sorted(files, key=lambda f: f.stat().st_size, reverse=True)
        else:
            return sorted(files, key=lambda f: f.name.lower())

    def _infer_return_type(self, items):
        """
        Infer return type from loaded items.
        Args:
            items: List of loaded JSON content strings
        Returns:
            Tuple with appropriate ComfyUI type
        """
        if not items:
            return (Everything("*"),)

        all_int = all(isinstance(v, int) and not isinstance(v, bool) for v in items)
        all_float = all(isinstance(v, float) for v in items)
        all_str = all(isinstance(v, str) for v in items)

        if all_int:
            return ("INT",)
        elif all_float:
            return ("FLOAT",)
        elif all_str:
            return ("STRING",)
        else:
            return (Everything("*"),)

    def load(self, folder_path, sort_by="name", limit=0):
        """
        Load all JSON files from the specified folder.
        Args:
            folder_path: Path to folder containing JSON files
            sort_by: Sort criteria (name, created, modified, size + _desc)
            limit: Max number of files to load (0 = unlimited)
        Returns:
            Tuple with list of JSON content strings
        """
        print(f"\n{self.LOG_TAG} -> Start JSON directory scan")
        print(f"{self.LOG_TAG} Directory: {folder_path}")
        print(f"{self.LOG_TAG} Sort By: {sort_by}")
        print(f"{self.LOG_TAG} Limit: {'unlimited' if limit == 0 else limit}\n")

        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            print(f"{self.LOG_TAG} ERROR: folder does not exist or is not a directory")
            self.RETURN_TYPES = (Everything("*"),)
            return ([],)

        json_files = list(folder.glob("*.json"))
        total_files = len(json_files)
        print(f"{self.LOG_TAG} Total JSON files found: {total_files}")

        sorted_files = self._sort_files(json_files, sort_by)
        print(f"{self.LOG_TAG} Files sorted by: {sort_by}")

        if limit > 0:
            sorted_files = sorted_files[:limit]
            print(f"{self.LOG_TAG} Limited to: {len(sorted_files)} files")

        output_list = []

        for file in sorted_files:
            try:
                file_path = str(file)
                size_kb = round(os.path.getsize(file) / 1024, 2)

                print(f"{self.LOG_TAG} File found: {file.name}")
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
        print(f"{self.LOG_TAG} Total files loaded: {len(output_list)}\n")

        self.RETURN_TYPES = self._infer_return_type(output_list)

        return (output_list,)
