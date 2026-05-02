from .constants import CATEGORY_PREFIX
from .logger import LogEntry, log

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
    CATEGORY = f"{CATEGORY_PREFIX}/String"

    def wrap_text(self, prefix, input_text, suffix):
        # Strip whitespace from all parts
        prefix = prefix.strip()
        input_text = input_text.strip()
        suffix = suffix.strip()

        log(LogEntry(
            node_class="StringWrapper",
            title="Processing text wrap",
            details={
                "Prefix": repr(prefix),
                "Input length": len(input_text),
                "Suffix": repr(suffix)
            }
        ))

        # Build parts list and filter out empty strings
        parts = [prefix, input_text, suffix]
        combined = " ".join([p for p in parts if p])

        log(LogEntry(
            node_class="StringWrapper",
            title="Text wrapped successfully",
            details={"Output length": len(combined)}
        ))

        return (combined,)