import datetime
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class GenerateCreationTime:
    """Generates ISO-formatted creation timestamp for video metadata."""

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "use_current_time": ("BOOLEAN", {"default": True}),
                "custom_datetime": ("STRING", {"default": "2026-03-11 15:30:00"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("creation_time",)
    FUNCTION = "generate"
    CATEGORY = f"{CATEGORY_PREFIX}/Production"
    OUTPUT_NODE = True

    def generate(self, use_current_time=True, custom_datetime=""):
        if use_current_time:
            creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(LogEntry(node_class="GenerateCreationTime", title="Generated current time", details={"Timestamp": creation_time}))
        else:
            creation_time = custom_datetime.strip()
            if creation_time:
                try:
                    datetime.datetime.strptime(creation_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError("Custom datetime must be in format: YYYY-MM-DD HH:MM:SS")
            log(LogEntry(node_class="GenerateCreationTime", title="Using custom time", details={"Timestamp": creation_time}))

        return (creation_time,)