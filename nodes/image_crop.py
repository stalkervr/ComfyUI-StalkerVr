import os
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
from .constants import CATEGORY_PREFIX
from .logger import LogEntry, log

class ImageCropper:
    """
    ImageCropper
    ---------
    Crops images from a batch using explicit margin offsets.
    Supports optional size restoration via bilinear interpolation and disk export.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "left": ("INT", {"default": 0, "min": 0}),
                "right": ("INT", {"default": 0, "min": 0}),
                "top": ("INT", {"default": 0, "min": 0}),
                "bottom": ("INT", {"default": 0, "min": 0}),
                "restore_size": ("BOOLEAN", {"default": False}),
                "save_path": ("STRING", {"default": ""}),
                "filename": ("STRING", {"default": "crop"}),
                "save_to_folder": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("cropped_images",)
    FUNCTION = "crop_batch"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def crop_batch(
            self,
            images: torch.Tensor,
            left: int,
            right: int,
            top: int,
            bottom: int,
            restore_size: bool,
            save_path: str,
            filename: str,
            save_to_folder: bool,
    ):
        log(LogEntry(
            node_class="ImageCropper",
            title="Starting batch crop",
            details={
                "Input Shape": str(images.shape),
                "Margins": f"L:{left}, R:{right}, T:{top}, B:{bottom}",
                "Restore Size": restore_size
            }
        ))

        if images.ndim != 4:
            raise ValueError("Input must be a batch of images with shape [B, H, W, C]")

        batch_size, h, w, c = images.shape
        x1 = left
        x2 = w - right
        y1 = top
        y2 = h - bottom

        if x1 >= x2 or y1 >= y2:
            raise ValueError("Invalid crop dimensions: resulting width or height is non-positive")

        cropped_images = images[:, y1:y2, x1:x2, :]

        if restore_size:
            # Permute to [B, C, H, W] for interpolation
            cropped_images = cropped_images.permute(0, 3, 1, 2)
            resized_images = F.interpolate(cropped_images, size=(h, w), mode='bilinear', align_corners=False)
            # Permute back to [B, H, W, C]
            cropped_images = resized_images.permute(0, 2, 3, 1)

        # Save images to disk if required
        if save_to_folder and save_path:
            os.makedirs(save_path, exist_ok=True)
            for idx in range(batch_size):
                img = cropped_images[idx].cpu()  # Move to CPU for numpy conversion
                np_img = (img.numpy() * 255).astype(np.uint8)
                if c == 1:
                    np_img = np_img[:, :, 0]
                    mode = "L"
                elif c == 3:
                    mode = "RGB"
                else:
                    mode = "RGBA"
                pil_img = Image.fromarray(np_img, mode=mode)
                pil_img.save(os.path.join(save_path, f"{filename}_{idx}.png"))

        log(LogEntry(
            node_class="ImageCropper",
            title="Batch crop completed",
            details={"Output Shape": str(cropped_images.shape)},
            footer="Returning cropped images"
        ))

        return (cropped_images,)