import torch
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class ImageGetSize:
    """
    ImageGetSize
    ------------------
    Extracts width and height from an input image tensor.
    Returns either the min or max side as 'resolution' based on the boolean switch.
    Passes through the original image unchanged for chaining.
    Image input is optional to support dynamic workflows.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "use_min_side": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "If True, resolution is min(W,H). If False, resolution is max(W,H)."
                }),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "Optional input image tensor [B, H, W, C]. If not provided, returns 0 for dimensions."
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT")
    RETURN_NAMES = ("image_passthrough", "width", "height", "resolution")
    FUNCTION = "extract_size"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def extract_size(self, use_min_side: bool = True, image: torch.Tensor = None) -> tuple[
        torch.Tensor | None, int, int, int]:

        if image is None:
            log(LogEntry(
                node_class="ImageGetSize",
                title="No image provided",
                details={
                    "Reason": "Optional image input is empty",
                    "Use Min Side": use_min_side
                }
            ))
            return (None, 0, 0, 0)

        log(LogEntry(
            node_class="ImageGetSize",
            title="Extracting image dimensions",
            details={
                "Input Shape": str(image.shape),
                "Use Min Side": use_min_side
            }
        ))

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
            }
        ))

        return (image, width, height, resolution)