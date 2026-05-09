from ...common.constants import CATEGORY_PREFIX


class CalculateFrameCount:
    """
    CalculateFrameCount
    -------------------
    Computes total frame count for video generation: frames = (duration_seconds × fps) + 1.
    Includes the +1 offset to account for the starting frame (frame 0).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "duration_seconds": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 300,
                    "step": 1,
                    "tooltip": "Video duration in seconds (integer)"
                }),
                "fps": ("INT", {
                    "default": 16,
                    "min": 12,
                    "max": 60,
                    "step": 4,
                    "tooltip": "Frames per second"
                }),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("frame_count",)
    FUNCTION = "calculate"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"

    def calculate(self, duration_seconds: int, fps: int) -> tuple[int]:
        """Calculates frame count with +1 offset for inclusive range."""
        frame_count = duration_seconds * fps + 1
        return (frame_count,)