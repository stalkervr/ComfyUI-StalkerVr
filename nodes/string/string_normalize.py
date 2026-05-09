import re
from ...common.constants import CATEGORY_PREFIX
from ...common.types import Everything
from ...common.logger import LogEntry, log

class StringNormalize:
    """
    StringNormalize
    ----------------
    Removes line breaks and collapses multiple whitespace characters into a single space.
    Useful for cleaning prompts, JSON strings, or any text input.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "string": (Everything("*"), {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("normalized_string",)
    FUNCTION = "normalize"
    CATEGORY = f"{CATEGORY_PREFIX}/String"

    def normalize(self, string="") -> tuple[str]:
        # Handle None or non-string inputs
        if string is None:
            string = ""
        elif not isinstance(string, str):
            string = str(string)

        log(LogEntry(
            node_class="StringNormalize",
            title="Normalizing string",
            details={"Input type": type(string).__name__, "Input length": len(string)}
        ))

        # Replace all whitespace sequences (including \n, \r, \t) with a single space
        normalized = re.sub(r'\s+', ' ', string)
        # Strip leading/trailing spaces
        normalized = normalized.strip()

        log(LogEntry(
            node_class="StringNormalize",
            title="Normalization completed",
            details={"Output length": len(normalized)}
        ))

        return (normalized,)