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
            # Batch of images [B, H, W, C]
            batch_size, h, w, c = image.shape
            single_image_mode = False
        elif image.ndim == 3:
            # Single image [H, W, C]
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
            if not single_image_mode:
                img = image[img_idx]
            else:
                img = image

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
                        if single_image_mode:
                            pil_img.save(f"{save_path}/{filename}_{row}_{col}.png")
                        else:
                            pil_img.save(f"{save_path}/{filename}_{img_idx}_{row}_{col}.png")

            batch_crops = torch.stack(crops, dim=0)
            all_crops.append(batch_crops)

        # Concatenate all crops from all images in the batch
        if single_image_mode:
            final_batch = all_crops[0]
        else:
            # When processing multiple images, concatenate their grids
            # The result will be [B*rows*cols, crop_H, crop_W, C]
            final_batch = torch.cat(all_crops, dim=0)

        return (final_batch,)

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


class ImageRatioResizer:
    """
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
    CATEGORY = "Stalkervr/Images"

    def resize_to_aspect_ratio(self, image, aspect_ratio, custom_x, custom_y):
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

        # Process each image in the batch
        if single_image_mode:
            # Process single image as before
            resized_img = self._center_crop_resize(image, target_width, target_height)
            return (resized_img, target_width, target_height)
        else:
            # Process batch of images
            resized_images = []
            for i in range(batch_size):
                img = image[i]
                resized_img = self._center_crop_resize(img, target_width, target_height)
                resized_images.append(resized_img)

            batch_result = torch.stack(resized_images, dim=0)
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