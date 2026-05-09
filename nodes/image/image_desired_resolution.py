import torch
import torch.nn.functional as F
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class ImageDesiredResolution:
    """Crops and resizes image for BiRefNet/WAN with correct aspect ratio preservation."""

    ASPECT_RATIOS = {
        "21:9": (21, 9),
        "16:9": (16, 9),
        "4:3": (4, 3),
        "3:2": (3, 2),
        "1:1": (1, 1),
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "image": ("IMAGE",),
            },
            "required": {
                "min_side": ("INT", {"default": 360, "min": 360, "max": 1440, "step": 16}),
                "aspect_ratio": (list(cls.ASPECT_RATIOS.keys()), {"default": "16:9"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("image", "width", "height")
    FUNCTION = "execute"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def execute(self, min_side: int, aspect_ratio: str, image: torch.Tensor = None):
        w_ratio, h_ratio = self.ASPECT_RATIOS[aspect_ratio]
        target_ratio = w_ratio / h_ratio

        log(LogEntry(
            node_class="ImageDesiredResolution",
            title="Starting resolution adjustment",
            details={
                "Min Side": min_side,
                "Aspect Ratio": aspect_ratio,
                "Target Ratio": f"{target_ratio:.3f}",
                "Image Provided": image is not None
            }
        ))

        if image is None:
            target_h = self._ceil_to_multiple(min_side, 16)
            target_w = self._ceil_to_multiple(round(min_side * target_ratio), 16)
            target_w = max(target_w, 64)
            target_h = max(target_h, 64)

            log(LogEntry(
                node_class="ImageDesiredResolution",
                title="Resolution computed (no image)",
                details={"Width": target_w, "Height": target_h}
            ))
            return (None, target_w, target_h)

        if image.ndim != 4:
            raise ValueError("Expected input tensor of shape [B, H, W, C]")

        batch_size, h, w, c = image.shape
        is_landscape = w >= h

        log(LogEntry(
            node_class="ImageDesiredResolution",
            title="Processing image batch",
            details={
                "Input Size": f"{w}x{h}",
                "Batch Size": batch_size,
                "Orientation": "landscape" if is_landscape else "portrait"
            }
        ))

        # --- Step 1: Center crop to target aspect ratio ---
        if is_landscape:
            current_ratio = w / h
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                new_h = h
                left = (w - new_w) // 2
                right = left + new_w
                top, bottom = 0, h
            else:
                new_h = int(w / target_ratio)
                new_w = w
                top = (h - new_h) // 2
                bottom = top + new_h
                left, right = 0, w
        else:
            current_ratio = h / w
            if current_ratio > target_ratio:
                new_h = int(w * target_ratio)
                new_w = w
                top = (h - new_h) // 2
                bottom = top + new_h
                left, right = 0, w
            else:
                new_w = int(h / target_ratio)
                new_h = h
                left = (w - new_w) // 2
                right = left + new_w
                top, bottom = 0, h

        cropped = image[:, top:bottom, left:right, :]

        # --- Step 2: Compute final size ---
        if is_landscape:
            target_h = self._ceil_to_multiple(min_side, 16)
            target_w = self._ceil_to_multiple(round(min_side * target_ratio), 16)
        else:
            target_w = self._ceil_to_multiple(min_side, 16)
            target_h = self._ceil_to_multiple(round(min_side * (w_ratio / h_ratio)), 16)

        target_w = max(target_w, 64)
        target_h = max(target_h, 64)

        log(LogEntry(
            node_class="ImageDesiredResolution",
            title="Crop and target size calculated",
            details={
                "Cropped Size": f"{new_w}x{new_h}",
                "Target Size": f"{target_w}x{target_h}"
            }
        ))

        # --- Step 3: Resize ---
        img_nchw = cropped.permute(0, 3, 1, 2)
        resized_nchw = F.interpolate(
            img_nchw,
            size=(target_h, target_w),
            mode="bilinear",
            align_corners=False
        )
        resized_image = resized_nchw.permute(0, 2, 3, 1)

        log(LogEntry(
            node_class="ImageDesiredResolution",
            title="Resolution adjustment completed",
            details={
                "Original": f"{w}x{h}",
                "Cropped": f"{new_w}x{new_h}",
                "Final": f"{target_w}x{target_h}"
            }
        ))

        return (resized_image, target_w, target_h)

    def _ceil_to_multiple(self, x: int, multiple: int) -> int:
        """Round up x to the nearest multiple of the given value."""
        return multiple * ((x + multiple - 1) // multiple)