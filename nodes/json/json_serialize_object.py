import json
from ...common.constants import CATEGORY_PREFIX
from ...common.types import Everything
from ...common.logger import LogEntry, log

class JsonSerializeObject:
    """
    JsonSerializeObject
    -------------------
    Serializes single objects or lists of objects into JSON strings.
    Supports batch processing via ComfyUI's list output mechanism.
    """

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

    def serialize_to_json_batch(self, input_data):
        objects_to_process = input_data if isinstance(input_data, list) else [input_data]

        log(LogEntry(
            node_class="JsonSerializeObject",
            title="Serialization started",
            details={
                "Input Type": "List" if isinstance(input_data, list) else type(input_data).__name__,
                "Items": len(objects_to_process)
            }
        ))

        json_strings = []
        for i, obj in enumerate(objects_to_process):
            try:
                json_str = json.dumps(obj, ensure_ascii=False)
                json_strings.append(json_str)
            except (TypeError, ValueError) as e:
                log(LogEntry(
                    node_class="JsonSerializeObject",
                    title=f"Item {i} serialization failed",
                    details={"Type": type(obj).__name__, "Error": str(e)},
                    footer="Fallback to empty string"
                ))
                json_strings.append("")

        log(LogEntry(
            node_class="JsonSerializeObject",
            title="Serialization completed",
            details={"Processed": len(objects_to_process), "Output Items": len(json_strings)},
            footer="Batch output ready"
        ))

        return (json_strings,)