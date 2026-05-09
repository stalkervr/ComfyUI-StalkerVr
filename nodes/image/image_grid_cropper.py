import os
import torch
import numpy as np
from PIL import Image
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class ImageGridCropper:
    """
    ImageGridCropper
    ----------------
    Slices images into a grid of fixed-size crops.
    Supports batch processing, automatic padding, and optional disk saving.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "rows": ("INT", {"default": 2, "min": 1}),
                "cols": ("INT", {"default": 2, "min": 1}),
                "block_width": ("INT", {"default": 256, "min": 1}),
                "block_height": ("INT", {"default": 256, "min": 1}),
                "save_path": ("STRING", {"default": ""}),
                "filename": ("STRING", {"default": "crop"}),
                "save_to_folder": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "crop_grid"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def crop_grid(
            self,
            image: torch.Tensor,
            rows: int,
            cols: int,
            block_width: int,
            block_height: int,
            save_path: str,
            filename: str,
            save_to_folder: bool,
    ):
        log(LogEntry(
            node_class="ImageGridCropper",
            title="Starting grid crop",
            details={
                "Grid": f"{rows}x{cols}",
                "Block Size": f"{block_width}x{block_height}",
                "Input Shape": str(image.shape)
            }
        ))

        # Determine input format (batch or single image)
        if image.ndim == 4:
            batch_size, h, w, c = image.shape
            single_image_mode = False
        elif image.ndim == 3:
            h, w, c = image.shape
            batch_size = 1
            single_image_mode = True
        else:
            raise ValueError(f"Unsupported image shape {image.shape}")

        if c not in [1, 3, 4]:
            raise ValueError(f"Unsupported channel count: expected 1, 3 or 4 but got {c}")

        all_crops = []

        # Process each image in the batch
        for img_idx in range(batch_size):
            img = image[img_idx] if not single_image_mode else image
            crops = []

            for row in range(rows):
                for col in range(cols):
                    x1 = col * block_width
                    y1 = row * block_height
                    x2 = min(x1 + block_width, w)
                    y2 = min(y1 + block_height, h)

                    # Extract crop region
                    crop = img[y1:y2, x1:x2, :]

                    # Pad if crop is smaller than target block size
                    pad_w = block_width - (x2 - x1)
                    pad_h = block_height - (y2 - y1)
                    if pad_w > 0 or pad_h > 0:
                        crop = torch.nn.functional.pad(
                            crop.permute(2, 0, 1),
                            (0, pad_w, 0, pad_h),
                            mode='constant', value=0
                        ).permute(1, 2, 0)

                    crops.append(crop)

                    # Optional: Save crop to disk
                    if save_to_folder and save_path:
                        os.makedirs(save_path, exist_ok=True)
                        np_img = (crop.cpu().numpy() * 255).astype(np.uint8)

                        if c == 1:
                            np_img = np_img[:, :, 0]
                            mode = "L"
                        elif c == 3:
                            mode = "RGB"
                        else:
                            mode = "RGBA"

                        pil_img = Image.fromarray(np_img, mode=mode)
                        save_name = f"{filename}_{img_idx}_{row}_{col}.png" if not single_image_mode else f"{filename}_{row}_{col}.png"
                        pil_img.save(os.path.join(save_path, save_name))

            batch_crops = torch.stack(crops, dim=0)
            all_crops.append(batch_crops)

        # Combine all crops from all images
        final_batch = all_crops[0] if single_image_mode else torch.cat(all_crops, dim=0)

        log(LogEntry(
            node_class="ImageGridCropper",
            title="Grid cropping completed",
            details={"Output Batch Size": final_batch.shape[0]},
            footer="Returning cropped image batch"
        ))

        return (final_batch,)