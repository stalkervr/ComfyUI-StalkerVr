import os
import torch
import numpy as np
import torch.nn.functional as F

class ImageGridCropper:
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
    CATEGORY = "Stalkervr/Images"

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
        if image.ndim == 4:
            img = image[0]
        elif image.ndim == 3:
            img = image
        else:
            raise ValueError(f"Unsupported image shape {image.shape}")

        h, w, c = img.shape
        if c not in [1, 3, 4]:
            raise ValueError(f"Unsupported channel count: expected 1, 3 or 4 but got {c}")

        crops = []
        for row in range(rows):
            for col in range(cols):
                x1 = col * block_width
                y1 = row * block_height
                x2 = min(x1 + block_width, w)
                y2 = min(y1 + block_height, h)

                crop = img[y1:y2, x1:x2, :]
                pad_w = block_width - (x2 - x1)
                pad_h = block_height - (y2 - y1)
                if pad_w > 0 or pad_h > 0:
                    crop = torch.nn.functional.pad(
                        crop.permute(2, 0, 1),
                        (0, pad_w, 0, pad_h),
                        mode='constant', value=0
                    ).permute(1, 2, 0)

                crops.append(crop)

                if save_to_folder and save_path:
                    os.makedirs(save_path, exist_ok=True)
                    from PIL import Image
                    np_img = (crop.numpy() * 255).astype(np.uint8)
                    if c == 1:
                        np_img = np_img[:, :, 0]
                        mode = "L"
                    elif c == 3:
                        mode = "RGB"
                    else:
                        mode = "RGBA"
                    pil_img = Image.fromarray(np_img, mode=mode)
                    pil_img.save(f"{save_path}/{filename}_{row}_{col}.png")

        batch = torch.stack(crops, dim=0)

        return (batch,)

class ImageBatchCrop:
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
    CATEGORY = "Stalkervr/Images"

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
            cropped_images = cropped_images.permute(0, 3, 1, 2)  # [B, C, H, W]
            resized_images = F.interpolate(cropped_images, size=(h, w), mode='bilinear', align_corners=False)
            cropped_images = resized_images.permute(0, 2, 3, 1)  # обратно [B, H, W, C]

        # Сохраняем, если требуется
        if save_to_folder and save_path:
            os.makedirs(save_path, exist_ok=True)
            from PIL import Image
            for idx in range(batch_size):
                img = cropped_images[idx]
                np_img = (img.numpy() * 255).astype(np.uint8)
                if c == 1:
                    np_img = np_img[:, :, 0]
                    mode = "L"
                elif c == 3:
                    mode = "RGB"
                else:
                    mode = "RGBA"
                pil_img = Image.fromarray(np_img, mode=mode)
                pil_img.save(f"{save_path}/{filename}_{idx}.png")

        return (cropped_images,)


class ImageAspectRatioFixer:
    """
    Auto aspect ratio calculator based on the same principles
    as ImageAspectFixer (batch aware, tensor-safe).
    """

    ASPECT_CHOICES = [
        "21:9",
        "16:9",
        "4:3",
        "custom"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "aspect_ratio": (cls.ASPECT_CHOICES, {"default": "16:9"}),
                "custom_x": ("INT", {"default": 1, "min": 1}),
                "custom_y": ("INT", {"default": 1, "min": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("source_image", "target_width", "target_height")

    FUNCTION = "calculate"
    CATEGORY = "Stalkervr/Images"

    def parse_ratio(self, ratio_str, custom_x, custom_y):
        if ratio_str != "custom":
            x, y = ratio_str.split(":")
            return float(x), float(y)
        return float(custom_x), float(custom_y)

    def calculate(self, image, aspect_ratio, custom_x, custom_y):
        """
        image: torch.Tensor [B, H, W, C]
        """
        if not isinstance(image, torch.Tensor):
            raise ValueError("Expected IMAGE tensor")

        if image.dim() != 4:
            raise ValueError("IMAGE must be 4D: [B, H, W, C]")

        _, h, w, _ = image.shape

        is_vertical = h > w

        x, y = self.parse_ratio(aspect_ratio, custom_x, custom_y)

        if is_vertical:
            x, y = y, x

        target_ratio = x / y
        input_ratio = w / h

        if input_ratio > target_ratio:
            target_height = h
            target_width = int(h * target_ratio)
        else:
            target_width = w
            target_height = int(w / target_ratio)

        return (image, target_width, target_height)