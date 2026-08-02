from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class AnyListLength:
    """Returns the number of items in any list object."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_list": ("*", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("count",)
    FUNCTION = "get_length"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def get_length(self, input_list):
        if not isinstance(input_list, list):
            input_list = [input_list]

        count = len(input_list)
        log(LogEntry(node_class="AnyListLength", title="Length calculated", details={"Count": count}))
        return (count,)


class AnyGetItem:
    """Retrieves a specific item from any list by index without type conversion."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_list": ("*", {"forceInput": True}),
                "index": ("INT", {"default": 0, "min": 0}),
            }
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("item",)
    FUNCTION = "get_item"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def get_item(self, input_list, index):
        if not isinstance(input_list, list):
            input_list = [input_list]

        if index < 0 or index >= len(input_list):
            log(LogEntry(
                node_class="AnyGetItem",
                title="Index out of range",
                details={"Index": index, "Max": len(input_list) - 1}
            ))
            # Возвращаем None вместо пустой строки для совместимости с любыми типами
            return (None,)

        item = input_list[index]
        log(LogEntry(node_class="AnyGetItem", title="Item retrieved", details={"Index": index}))
        return (item,)


class AnyListIndexer:
    """Splits any list into two parallel lists: original items and their indices."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_list": ("*", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("*", "*")
    RETURN_NAMES = ("items", "indices")
    FUNCTION = "index_list"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def index_list(self, input_list):
        if not isinstance(input_list, list):
            input_list = [input_list]

        # Сохраняем элементы в исходном виде, без приведения к str
        items = list(input_list)
        indices = list(range(len(input_list)))

        log(LogEntry(node_class="AnyListIndexer", title="List indexed", details={"Count": len(items)}))
        return (items, indices)



class AnyListToBatch:
    """
    Converts a list object (received via Wildcard) into a batch output.
    Enables downstream nodes with OUTPUT_IS_LIST to process each item individually.
    Works with ANY data type: STRING, IMAGE, LATENT, INT, etc.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Принимаем список как единый объект через Wildcard
                "input_list": ("*", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("output_batch",)
    FUNCTION = "convert"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"
    # КЛЮЧЕВОЙ МОМЕНТ: включаем OUTPUT_IS_LIST для выхода
    # Это заставит ComfyUI автоматически распаковать список
    # и запустить следующие ноды N раз (по одному на элемент)
    OUTPUT_IS_LIST = (True,)

    def convert(self, input_list):
        # Приводим вход к списку, если пришел одиночный элемент
        if not isinstance(input_list, list):
            input_list = [input_list]

        log(LogEntry(
            node_class="AnyListToBatch",
            title="Converted list to batch",
            details={
                "Count": len(input_list),
                "Item Type": type(input_list[0]).__name__ if input_list else "empty"
            }
        ))

        # Возвращаем список — ComfyUI сам распакует его благодаря OUTPUT_IS_LIST
        return (input_list,)