from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class TextWrapperBatch:
    """
    Wraps a batch of strings with a common prefix and suffix.
    Useful for adding system prompts, negative prompts, or formatting to a list of generated texts.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prefix": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text to add before each string"
                }),
                "strings": ("STRING", {
                    # "forceInput": True,
                    "default": "",
                    "multiline": True,
                    "tooltip": "List of strings to wrap. Accepts output from nodes returning LIST[STRING]."
                }),
                "suffix": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text to add after each string"
                }),
            },
            "optional": {
                "separator": ("STRING", {
                    "default": " ",
                    "tooltip": "Separator between prefix, string, and suffix. Default is space."
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("wrapped_strings",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "wrap_batch"
    CATEGORY = f"{CATEGORY_PREFIX}/Text"
    DESCRIPTION = """
    Wraps a batch of strings with a common prefix and suffix.
    Useful for adding system prompts, negative prompts, or formatting to a list of generated texts.
    """

    def wrap_batch(self, strings, prefix, suffix, separator=" "):
        """
        Wraps each string in the input list with prefix and suffix.
        Args:
            strings (list[str]): Input list of strings.
            prefix (str): Text to prepend.
            suffix (str): Text to append.
            separator (str): Separator character(s).

        Returns:
            tuple[list[str]]: List of wrapped strings.
        """

        if isinstance(strings, str):
            strings = [strings]

        if not strings:
            log(LogEntry(
                node_class="StringWrapperBatch",
                title="Empty input",
                details={"Reason": "No strings provided"}
            ))
            return ([],)

        wrapped_list = []

        for i, s in enumerate(strings):
            current_str = str(s) if s is not None else ""

            parts = []
            if prefix.strip():
                parts.append(prefix.strip())
            if current_str.strip():
                parts.append(current_str.strip())
            if suffix.strip():
                parts.append(suffix.strip())

            wrapped = separator.join(parts)
            wrapped_list.append(wrapped)

        log(LogEntry(
            node_class="StringWrapperBatch",
            title="Batch wrapped",
            details={
                "Count": len(wrapped_list),
                "Prefix Length": len(prefix),
                "Suffix Length": len(suffix)
            }
        ))

        return (wrapped_list,)