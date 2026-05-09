import torch
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class ImageGetSize:
    """
    ImageGetSize
    ------------------
    Extracts width and height from an input image tensor.
    Returns either the min or max side as 'resolution' based on the boolean switch.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "use_min_side": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT")
    RETURN_NAMES = ("width", "height", "resolution")
    FUNCTION = "extract_size"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def extract_size(self, image: torch.Tensor, use_min_side: bool = False) -> tuple[int, int, int]:
        log(LogEntry(
            node_class="ImageGetSize",
            title="Extracting image dimensions",
            details={
                "Input Shape": str(image.shape),
                "Use Min Side": use_min_side
            }
        ))

        # ComfyUI image format: [B, H, W, C]
        if image.ndim != 4:
            raise ValueError("Expected 4D tensor [B, H, W, C]")

        _, height, width, _ = image.shape

        if use_min_side:
            resolution = min(width, height)
        else:
            resolution = max(width, height)

        log(LogEntry(
            node_class="ImageGetSize",
            title="Dimensions extracted",
            details={
                "Width": width,
                "Height": height,
                "Resolution": resolution
            },
            footer="Returning width, height, resolution"
        ))

        return (width, height, resolution)