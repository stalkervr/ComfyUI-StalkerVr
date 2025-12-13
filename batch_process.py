class Everything(str):
    def __ne__(self, __value: object) -> bool:
        return False


class LoopAny:
    """
    Accepts any input (single value or list). Returns a batch (list) of items.
    If a single value is provided, wraps it into a single-item list.
    Attempts to set RETURN_TYPES to INT/FLOAT/STRING when possible.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "optional": {
                "input": (Everything("*"),),
            },
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "create_loop_any"
    CATEGORY = "Stalkervr/Control"

    def _infer_and_set_return_type(self, items):
        """
        Infer simple homogeneous type across items and set self.RETURN_TYPES accordingly.
        Prioritizes INT -> FLOAT -> STRING. If mixed or unknown, keep Everything("*").
        """
        if not items:
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

    def create_loop_any(self, input=None):
        # No input provided → empty output
        if input is None:
            self.RETURN_TYPES = (Everything("*"),)
            return ([],)

        # If input — список или кортеж → возвращаем как есть
        if isinstance(input, (list, tuple)):
            output = list(input)
            self._infer_and_set_return_type(output)
            return (output,)

        # Если передано одно значение → оборачиваем в список
        output = [input]
        self._infer_and_set_return_type(output)
        return (output,)


class ListItemExtractor:
    """
    Node to extract an item from a batch (list) by index and return the batch count.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("LIST", {}),
                "index": ("INT", {"default": 0, "min": 0}),
            }
        }

    RETURN_TYPES = ("INT", "Everything('*')")
    RETURN_NAMES = ("count", "item")
    OUTPUT_IS_LIST = (False, False)
    FUNCTION = "extract_item"
    CATEGORY = "Stalkervr/Control"

    def extract_item(self, input, index):
        if not isinstance(input, list):
            input = list(input) if input is not None else []

        count = len(input)

        if 0 <= index < count:
            item = input[index]
        else:
            item = None

        return count, item


class AnyCollector:
    """
    Collects multiple inputs of any type into a single list.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "any_input": (Everything("*"),),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }

    RETURN_TYPES = ("LIST",)
    RETURN_NAMES = ("collected_items",)
    INPUT_IS_LIST = True
    OUTPUT_NODE = True
    FUNCTION = "collect_any"
    CATEGORY = "Stalkervr/Control"

    def collect_any(self, unique_id=None, extra_pnginfo=None, **kwargs):
        collected = []

        if "any_input" in kwargs:
            for val in kwargs["any_input"]:
                try:
                    if isinstance(val, list):
                        collected.extend(val)
                    else:
                        collected.append(val)
                except Exception:
                    collected.append(val)

        if extra_pnginfo and isinstance(extra_pnginfo, list) and extra_pnginfo:
            if isinstance(extra_pnginfo[0], dict) and "workflow" in extra_pnginfo[0]:
                workflow = extra_pnginfo[0]["workflow"]
                node = next((x for x in workflow["nodes"] if str(x["id"]) == unique_id[0]), None)
                if node:
                    node["widgets_values"] = [collected]

        return {"ui": {"text": collected}, "result": (collected,)}