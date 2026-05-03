import torch
import torch.nn.functional as F
from .constants import CATEGORY_PREFIX
from .logger import LogEntry, log

class ImageRatioResizer:
    """
    ImageRatioResizer
    -----------------
    Resize image to specific aspect ratio while maintaining proportions.
    Uses center crop method to achieve the target aspect ratio.
    """

    ASPECT_CHOICES = [
        "1:1 (Square)",
        "4:3 (Standard)",
        "7:5 (Photo Landscape)",
        "16:9 (Landscape)",
        "21:9 (Ultrawide)",
        "custom"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "aspect_ratio": (cls.ASPECT_CHOICES, {"default": "16:9 (Landscape)"}),
                "custom_x": ("INT", {"default": 16, "min": 1, "max": 100}),
                "custom_y": ("INT", {"default": 9, "min": 1, "max": 100}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("resized_image", "width", "height")
    FUNCTION = "resize_to_aspect_ratio"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def resize_to_aspect_ratio(self, image, aspect_ratio, custom_x, custom_y):
        log(LogEntry(
            node_class="ImageRatioResizer",
            title="Starting aspect ratio resize",
            details={
                "Input Shape": str(image.shape),
                "Target Ratio": aspect_ratio,
                "Custom": f"{custom_x}:{custom_y}" if aspect_ratio == "custom" else "N/A"
            }
        ))

        # Handle both single image [H, W, C] and batch of images [B, H, W, C]
        if len(image.shape) == 4:
            batch_size, h, w, c = image.shape
            single_image_mode = False
        elif len(image.shape) == 3:
            h, w, c = image.shape
            batch_size = 1
            single_image_mode = True
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")

        # Determine if the image is vertical (portrait) or horizontal (landscape)
        # For batch mode, we use the first image to determine orientation
        if not single_image_mode:
            is_vertical = image[0].shape[0] > image[0].shape[1]  # h > w
        else:
            is_vertical = h > w

        # Parse the aspect ratio and adjust for vertical images
        if aspect_ratio == "custom":
            target_x, target_y = custom_x, custom_y
        else:
            # Extract ratio from string, e.g., "16:9 (Landscape)" -> 16:9
            ratio_part = aspect_ratio.split()[0]  # Gets "16:9"
            x, y = map(int, ratio_part.split(':'))

            # If image is vertical, swap the aspect ratio for certain common cases
            if is_vertical:
                # Swap common landscape ratios to portrait equivalents
                if aspect_ratio == "16:9 (Landscape)":
                    x, y = 9, 16  # 16:9 becomes 9:16
                elif aspect_ratio == "21:9 (Ultrawide)":
                    x, y = 9, 21  # 21:9 becomes 9:21
                elif aspect_ratio == "7:5 (Photo Landscape)":
                    x, y = 5, 7   # 7:5 becomes 5:7
                elif aspect_ratio == "4:3 (Standard)":
                    x, y = 3, 4   # 4:3 becomes 3:4
                # For 1:1, it stays as 1:1 (square)

        # Calculate the target dimensions based on the adjusted aspect ratio
        target_ratio = x / y
        target_x, target_y = x, y

        # Calculate target dimensions maintaining aspect ratio
        img_ratio = w / h

        if img_ratio > target_ratio:
            # Image is wider than target ratio - constraint by height
            target_height = h
            target_width = int(h * target_ratio)
        else:
            # Image is taller than target ratio - constraint by width
            target_width = w
            target_height = int(w / target_ratio)

        log(LogEntry(
            node_class="ImageRatioResizer",
            title="Target dimensions calculated",
            details={
                "Original": f"{w}x{h}",
                "Target": f"{target_width}x{target_height}",
                "Ratio": f"{target_x}:{target_y}"
            }
        ))

        # Process each image in the batch
        if single_image_mode:
            # Process single image
            resized_img = self._center_crop_resize(image, target_width, target_height)
            log(LogEntry(
                node_class="ImageRatioResizer",
                title="Resize completed",
                details={"Output Shape": str(resized_img.shape)}
            ))
            return (resized_img, target_width, target_height)
        else:
            # Process batch of images
            resized_images = []
            for i in range(batch_size):
                img = image[i]
                resized_img = self._center_crop_resize(img, target_width, target_height)
                resized_images.append(resized_img)

            batch_result = torch.stack(resized_images, dim=0)
            log(LogEntry(
                node_class="ImageRatioResizer",
                title="Batch resize completed",
                details={"Batch Size": batch_size, "Output Shape": str(batch_result.shape)}
            ))
            return (batch_result, target_width, target_height)

    def _center_crop_resize(self, img, target_width, target_height):
        """Resize image to cover the target dimensions then center crop - no padding."""
        h, w, c = img.shape

        # Calculate the scale factor to make the image cover the target dimensions
        # (scale bigger than needed so we can crop to exact size)
        scale_factor = max(target_width / w, target_height / h)

        # Calculate new dimensions after scaling
        new_width = int(w * scale_factor)
        new_height = int(h * scale_factor)

        # Resize the image
        img_tensor = img.permute(2, 0, 1).unsqueeze(0).float()  # [1, C, H, W]
        scaled_img = F.interpolate(
            img_tensor,
            size=(new_height, new_width),
            mode='bilinear',
            align_corners=False
        )
        scaled_img = scaled_img.squeeze(0).permute(1, 2, 0)  # [H, W, C]

        # Now crop to exact target dimensions from the center
        scaled_h, scaled_w, _ = scaled_img.shape
        y_start = max(0, (scaled_h - target_height) // 2)
        x_start = max(0, (scaled_w - target_width) // 2)

        # Crop to exact target dimensions (since we scaled to cover, this should work)
        cropped_img = scaled_img[y_start:y_start+target_height, x_start:x_start+target_width]

        # Ensure we return the exact target size by cropping if necessary
        final_h, final_w, _ = cropped_img.shape
        if final_h < target_height or final_w < target_width:
            # This shouldn't happen if our scale calculation is correct, but just in case
            # We won't pad, just return what we have (should be very rare with cover scaling)
            pass

        return cropped_img