class StringConcatenation:
    """Node to concatenate two inputs of type ANY with an optional separator and newline."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "any_1": ("STRING", {"default": ""}),
                "any_2": ("STRING", {"default": ""}),
                "separator": ("STRING", {"default": ", "}),
                "newline": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "concatenate_inputs"
    CATEGORY = "Stalkervr/Text"

    def concatenate_inputs(self, any_1="", any_2="", separator="", newline=False):
        # Преобразуем входы в строки для конкатенации
        str_input1 = str(any_1)
        str_input2 = str(any_2)

        if newline:
            concatenated_output = f"{str_input1}{separator}\n{str_input2}"
        else:
            concatenated_output = f"{str_input1}{separator}{str_input2}"

        return (concatenated_output,)


class StringWrapper:
    """
    Node to wrap input text with a prefix and suffix.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prefix": ("STRING", {"multiline": False, "default": ""}),
                "input_text": ("STRING", {"multiline": False, "default": ""}),
                "suffix": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "wrap_text"
    CATEGORY = "Stalkervr/Text"

    def wrap_text(self, prefix, input_text, suffix):
        prefix = prefix.strip()
        input_text = input_text.strip()
        suffix = suffix.strip()
        parts = [prefix, input_text, suffix]
        combined = " ".join([p for p in parts if p])

        return (combined,)

class StringListToString:
    """
    Node to join a list of strings into a single string using a specified separator.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string_list": ("LIST", {"default": []}),
                "separator": ("STRING", {"default": ", "}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("OUTPUT",)
    FUNCTION = "join_list"
    CATEGORY = "Stalkervr/Text"

    def join_list(self, string_list, separator):
        safe_list = [str(item) for item in string_list]
        combined = separator.join(safe_list)
        return (combined,)


class StringCollector:
    """
    Accumulates STRING inputs into a single list.
    Uses INPUT_IS_LIST=True so it can collect multiple inputs over time.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {},
            "optional": {
                "text_input": ("STRING", {}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }

    RETURN_TYPES = ("LIST",)
    RETURN_NAMES = ("collected_texts",)
    INPUT_IS_LIST = True
    OUTPUT_NODE = True
    FUNCTION = "collect_texts"
    CATEGORY = "Stalkervr/Text"

    def collect_texts(self, unique_id=None, extra_pnginfo=None, **kwargs):
        values = []
        if "text_input" in kwargs:
            for val in kwargs["text_input"]:
                try:
                    if isinstance(val, str):
                        values.append(val.strip())
                    elif isinstance(val, list):
                        values.extend([str(v).strip() for v in val])
                    else:
                        values.append(str(val).strip())
                except Exception:
                    values.append(str(val).strip())
                    pass

        if extra_pnginfo and isinstance(extra_pnginfo, list) and extra_pnginfo:
            if isinstance(extra_pnginfo[0], dict) and "workflow" in extra_pnginfo[0]:
                workflow = extra_pnginfo[0]["workflow"]
                node = next((x for x in workflow["nodes"] if str(x["id"]) == unique_id[0]), None)
                if node:
                    node["widgets_values"] = [values]

        return {"ui": {"text": values}, "result": (values,)}

class StringBuilder:
    """Node to concatenate multiple STRING inputs with an optional separator and newline."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "num_inputs": ("INT", {"default": 2, "min": 0, "max": 20}),
                "separator": ("STRING", {"default": " "}),
                "newline": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "concatenate_inputs"
    CATEGORY = "Stalkervr/Text"

    def concatenate_inputs(self, num_inputs, separator="", newline=False, **kwargs):
        strings_to_concat = []
        for i in range(1, num_inputs + 1):
            key_name = f"string_{i}"
            value = kwargs.get(key_name, "")
            str_value = str(value)
            strings_to_concat.append(str_value)

        if newline:
            temp_separator = separator.rstrip() + "\n" + separator[len(separator.rstrip()):] # separator с \n после
            concatenated_output = temp_separator.join(strings_to_concat)
            if concatenated_output.endswith("\n"):
                concatenated_output = concatenated_output[:-1]
        else:
            concatenated_output = separator.join(strings_to_concat)

        return (concatenated_output,)