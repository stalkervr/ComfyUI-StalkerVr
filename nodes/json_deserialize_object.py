import json
from .constants import CATEGORY_PREFIX
from .types import Everything
from .logger import LogEntry, log

class JsonDeserializeObject:
    """
    JsonDeserializeObject
    ---------------------
    Deserializes single JSON strings or lists of strings into Python objects.
    Supports batch processing via ComfyUI's list output mechanism.
    """

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

    def deserialize_from_json_batch(self, input_data):
        # Normalize input to list
        if isinstance(input_data, list):
            items = input_data
        elif isinstance(input_data, str):
            items = [input_data]
        else:
            log(LogEntry(
                node_class="JsonDeserializeObject",
                title="Invalid input type",
                details={"Got": type(input_data).__name__},
                footer="Returning empty list"
            ))
            return ([],)

        log(LogEntry(
            node_class="JsonDeserializeObject",
            title="Deserialization started",
            details={"Items": len(items)}
        ))

        results = []
        for i, item in enumerate(items):
            if not isinstance(item, str):
                log(LogEntry(
                    node_class="JsonDeserializeObject",
                    title=f"Item {i} skipped",
                    details={"Type": type(item).__name__, "Reason": "Not a string"},
                    footer="Appending None"
                ))
                results.append(None)
                continue

            try:
                results.append(json.loads(item))
            except (json.JSONDecodeError, TypeError) as e:
                log(LogEntry(
                    node_class="JsonDeserializeObject",
                    title=f"Item {i} deserialization failed",
                    details={
                        "Preview": item[:50] + "..." if len(item) > 50 else item,
                        "Error": str(e)
                    },
                    footer="Appending None"
                ))
                results.append(None)

        log(LogEntry(
            node_class="JsonDeserializeObject",
            title="Deserialization completed",
            details={"Processed": len(items), "Output Items": len(results)},
            footer="Batch output ready"
        ))
        return (results,)