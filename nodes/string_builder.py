from .constants import CATEGORY_PREFIX
from .logger import LogEntry, log


class StringBuilder:
    """Node to concatenate multiple STRING inputs with an optional separator and newline."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "num_inputs": ("INT", {"default": 2, "min": 0, "max": 100}),
                "separator": ("STRING", {"default": " "}),
                "newline": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    FUNCTION = "concatenate_inputs"
    CATEGORY = f"{CATEGORY_PREFIX}/String"

    def concatenate_inputs(self, num_inputs, separator="", newline=False, **kwargs):
        strings_to_concat = []

        # Collect and convert all input strings
        for i in range(1, num_inputs + 1):
            key_name = f"string_{i}"
            value = kwargs.get(key_name, "")
            str_value = str(value)
            strings_to_concat.append(str_value)

        log(LogEntry(
            node_class="StringBuilder",
            title="Collecting inputs",
            details={"Count": len(strings_to_concat), "Separator": repr(separator), "Newline": newline}
        ))

        # Build output with optional newline handling
        if newline:
            # Insert newline after the non-whitespace part of separator
            temp_separator = separator.rstrip() + "\n" + separator[len(separator.rstrip()):]
            concatenated_output = temp_separator.join(strings_to_concat)
            # Remove trailing newline if present
            if concatenated_output.endswith("\n"):
                concatenated_output = concatenated_output[:-1]
        else:
            concatenated_output = separator.join(strings_to_concat)

        log(LogEntry(
            node_class="StringBuilder",
            title="Concatenation completed",
            details={"Output length": len(concatenated_output)}
        ))

        return (concatenated_output,)