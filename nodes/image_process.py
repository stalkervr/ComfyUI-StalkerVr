import os
import torch
import numpy as np
import torch.nn.functional as F
import json
import re
import folder_paths

from PIL import Image, PngImagePlugin
from pathlib import Path
from .constants import CATEGORY_PREFIX


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
    CATEGORY = f"{CATEGORY_PREFIX}/Images"

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
    CATEGORY = f"{CATEGORY_PREFIX}/Images"

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
    CATEGORY = f"{CATEGORY_PREFIX}/Images"

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
    CATEGORY = f"{CATEGORY_PREFIX}/Images"

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


class SaveImageWithMetadata:
    """
    SaveImageWithMetadata
    --------------------
    Saves images as PNG with custom metadata embedded directly in PNG chunks.
    NO PREVIEW - simple and reliable saving to any path.
    Features:
    - Automatic sequential numbering (Triksy_00001.png)
    - Workflow saving toggle (save_workflow parameter)
    - Only counts PNG files for numbering (ignores txt/json/etc)
    - Works with ANY directory path (absolute or relative)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "save_directory": ("STRING", {
                    "default": "/home/stalkervr/AiProjects/Triksy/image/2026-02-11",
                    "tooltip": "Full directory path where PNG files will be saved"
                }),
                "filename_prefix": ("STRING", {
                    "default": "Triksy",
                    "tooltip": "Filename prefix. Format: {prefix}_{number:05d}.png"
                }),
                "save_workflow": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Save ComfyUI workflow in PNG metadata"
                }),
                "metadata_json": ("STRING", {
                    "default": '{"prompt_positive": "", "prompt_negative": "", "seed": ""}',
                    "multiline": False,
                    "dynamicPrompts": False,
                    "tooltip": "JSON with metadata to embed in PNG (key-value pairs)"
                }),
                "compression_level": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9,
                    "step": 1,
                    "tooltip": "PNG compression level (0=fastest, 9=best compression)"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "saved_paths")
    FUNCTION = "save_images_with_metadata"
    CATEGORY = f"{CATEGORY_PREFIX}/Images"
    OUTPUT_NODE = True

    def save_images_with_metadata(self, images, save_directory, filename_prefix, save_workflow,
                                  metadata_json, compression_level=6, prompt=None, extra_pnginfo=None):
        # Validate inputs
        save_directory = save_directory.strip()
        filename_prefix = filename_prefix.strip()

        if not save_directory:
            raise ValueError("❌ Save directory cannot be empty")
        if not filename_prefix:
            raise ValueError("❌ Filename prefix cannot be empty")

        # Parse metadata JSON
        try:
            metadata_dict = json.loads(metadata_json)
            if not isinstance(metadata_dict, dict):
                raise ValueError("Metadata must be a JSON object")
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Invalid JSON format: {str(e)}")

        # Ensure directory exists
        output_dir = Path(save_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find next available number based on existing PNG files ONLY
        next_number = self._get_next_number(output_dir, filename_prefix)

        # Process batch of images (ComfyUI format: [B, H, W, C])
        saved_paths = []

        for i in range(images.shape[0]):
            # Generate filename with sequential numbering
            current_number = next_number + i
            filename = f"{filename_prefix}_{current_number:05d}.png"
            save_path = output_dir / filename

            # Convert tensor to PIL Image
            img_tensor = images[i]
            img_np = img_tensor.cpu().numpy()
            img_np = (img_np * 255.0).clip(0, 255).astype(np.uint8)
            img_pil = Image.fromarray(img_np, mode="RGB")

            # Create PNG metadata container
            pnginfo = PngImagePlugin.PngInfo()

            # Add standard ComfyUI metadata (workflow, etc.) if enabled
            if save_workflow and extra_pnginfo is not None:
                for x in extra_pnginfo:
                    pnginfo.add_text(x, json.dumps(extra_pnginfo[x]))

            # Add custom metadata with proper chunk selection
            for key, value in metadata_dict.items():
                key_str = str(key)
                value_str = str(value)

                # Validate key length (PNG spec: max 79 bytes for tEXt/iTXt keys)
                if len(key_str.encode('latin-1', errors='ignore')) > 79:
                    print(f"⚠️ [SaveImageWithMetadata] Key '{key_str}' too long (>79 bytes), truncating")
                    key_str = key_str.encode('latin-1', errors='ignore')[:79].decode('latin-1', errors='ignore')

                # Choose chunk type based on value size and content
                if len(value_str) > 1024:
                    # Large values → zTXt (compressed text)
                    pnginfo.add_ztxt(key_str, value_str)
                elif any(ord(c) > 127 for c in value_str):
                    # UTF-8 content → iTXt (international text)
                    pnginfo.add_itxt(key_str, value_str, lang="", tkey="")
                else:
                    # Simple ASCII → tEXt (plain text)
                    pnginfo.add_text(key_str, value_str)

            # Save image with metadata
            img_pil.save(
                save_path,
                format="PNG",
                pnginfo=pnginfo,
                compress_level=compression_level
            )
            saved_paths.append(str(save_path))

            print(f"✅ [SaveImageWithMetadata] Saved: {save_path.name}")

        # Return images and saved paths (comma-separated for batch)
        saved_paths_str = ", ".join(saved_paths) if len(saved_paths) > 1 else saved_paths[0]

        print(f"   Total images saved: {len(saved_paths)}")
        print(f"   Workflow saved: {'YES' if save_workflow else 'NO'}")
        print(f"   Metadata keys: {list(metadata_dict.keys())}")

        return (images, saved_paths_str)

    def _get_next_number(self, directory, prefix):
        """
        Find the next available sequential number based on existing PNG files.
        Only considers files matching pattern: {prefix}_XXXXX.png
        Ignores all other file types (txt, json, jpg, etc.)
        """
        pattern = re.compile(rf'^{re.escape(prefix)}_(\d{{5}})\.png$', re.IGNORECASE)
        max_number = 0

        try:
            for entry in directory.iterdir():
                if entry.is_file() and entry.suffix.lower() == '.png':
                    match = pattern.match(entry.name)
                    if match:
                        number = int(match.group(1))
                        max_number = max(max_number, number)
        except Exception as e:
            print(f"⚠️ [SaveImageWithMetadata] Error scanning directory: {str(e)}")

        return max_number + 1


class LoadImageWithMetadata:
    """
    LoadImageWithMetadata
    --------------------
    Loads PNG images WITH metadata preservation.
    Returns image tensor + extracted metadata.
    Compatible with standard ComfyUI image workflows.
    """

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
            },
            "optional": {
                "extract_key": ("STRING", {
                    "default": "",
                    "tooltip": "Optional: extract specific metadata key (leave empty for all metadata)"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "metadata_json", "metadata_value")
    FUNCTION = "load_image"
    CATEGORY = f"{CATEGORY_PREFIX}/Images"

    def load_image(self, image, extract_key=""):
        # Get full path to image file
        image_path = folder_paths.get_annotated_filepath(image)

        # Validate file
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"❌ File not found: {image_path}")

        if not image_path.lower().endswith('.png'):
            print(f"⚠️ [LoadImageWithMetadata] Warning: Non-PNG file '{image_path}' - metadata extraction may fail")

        # Load image with PIL (preserves metadata)
        img = Image.open(image_path)

        # Extract metadata FIRST (before any conversions)
        metadata = self._extract_png_metadata(img)
        metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
        metadata_value = metadata.get(extract_key.strip(), "") if extract_key.strip() else ""

        # Convert to ComfyUI format
        output_images = []
        output_masks = []

        for i in range(img.n_frames):
            img.seek(i)
            frame = img.convert("RGB")
            image_np = np.array(frame).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_np)[None,]
            output_images.append(image_tensor)

            # Extract mask if available (RGBA images)
            if img.mode == 'RGBA':
                mask_np = np.array(img.getchannel('A')).astype(np.float32) / 255.0
                mask_tensor = torch.from_numpy(mask_np)[None,]
                output_masks.append(mask_tensor)
            else:
                output_masks.append(torch.zeros((64, 64), dtype=torch.float32))

        # Combine frames if multiple
        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        # Log results
        print(f"✅ [LoadImageWithMetadata] Loaded: {os.path.basename(image_path)}")
        print(f"   Size: {img.width}x{img.height} ({img.mode})")
        print(f"   Metadata keys: {list(metadata.keys())}")
        if extract_key.strip():
            preview = metadata_value[:80] + "..." if len(metadata_value) > 80 else metadata_value
            print(f"   Key '{extract_key}': {preview}")

        return (output_image, output_mask, metadata_json, metadata_value)

    def _extract_png_metadata(self, img):
        """Extract all text chunks from PNG image"""
        metadata = {}

        # Method 1: img.text (Pillow >= 9.1.0)
        if hasattr(img, 'text') and isinstance(img.text, dict):
            for k, v in img.text.items():
                if isinstance(v, str):
                    metadata[k] = v

        # Method 2: img.info fallback
        if hasattr(img, 'info') and isinstance(img.info, dict):
            for k, v in img.info.items():
                if isinstance(v, str) and k not in ['dpi', 'gamma', 'transparency', 'aspect']:
                    metadata[k] = v

        return metadata

    @classmethod
    def IS_CHANGED(cls, image, extract_key=""):
        image_path = folder_paths.get_annotated_filepath(image)
        try:
            m = os.path.getmtime(image_path)
            return m
        except Exception:
            return 0.0

    @classmethod
    def VALIDATE_INPUTS(cls, image, extract_key=""):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True


class LoadImagesWithMetadata:
    """
    LoadImagesWithMetadata
    ----------------------
    Loads ALL PNG images from a specified directory and extracts embedded metadata.
    Output structure matches your UI screenshot:
    - image (LIST[IMAGE])
    - mask (LIST[MASK])
    - metadata_json (LIST[STRING])
    - metadata_value (LIST[STRING])
    All outputs are true lists (OUTPUT_IS_LIST = (True, True, True, True))
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": "/home/stalkervr/AiProjects/Triksy/image/2026-02-11",
                    "tooltip": "Directory path containing PNG files to load"
                }),
                "sort_by": (["name", "date", "none"], {
                    "default": "name",
                    "tooltip": "How to sort loaded images"
                }),
            },
            "optional": {
                "extract_key": ("STRING", {
                    "default": "",
                    "tooltip": "Extract specific metadata key from all images"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "metadata_json", "metadata_value")
    FUNCTION = "load_images_with_metadata"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"
    OUTPUT_IS_LIST = (True, True, True, True)  # ← Все выходы — списки!

    def load_images_with_metadata(self, directory_path, sort_by="name", extract_key=""):
        # Validate directory
        directory_path = directory_path.strip()
        if not directory_path:
            raise ValueError("❌ Directory path cannot be empty")

        directory = Path(directory_path)
        if not directory.exists():
            print(f"⚠️ [LoadImagesWithMetadata] Directory not found: {directory_path}")
            return ([], [], [], [])

        # Find ALL PNG files in directory
        png_files = []
        for entry in directory.iterdir():
            if entry.is_file() and entry.suffix.lower() == '.png':
                png_files.append(entry)

        if not png_files:
            print(f"⚠️ [LoadImagesWithMetadata] No PNG files found in directory")
            return ([], [], [], [])

        # Sort files
        if sort_by == "name":
            png_files.sort(key=lambda x: x.name)
        elif sort_by == "date":
            png_files.sort(key=lambda x: x.stat().st_mtime)
        # "none" - keep original order

        # Load images and extract metadata
        image_list = []
        mask_list = []
        metadata_json_list = []
        metadata_value_list = []

        for i, file_path in enumerate(png_files):
            try:
                # Load image with PIL (preserves metadata)
                img = Image.open(file_path)

                # Extract metadata
                metadata = self._extract_png_metadata(img)
                metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
                metadata_json_list.append(metadata_json)

                # Extract specific value if requested
                extracted_value = metadata.get(extract_key.strip(), "") if extract_key.strip() else ""
                metadata_value_list.append(extracted_value)

                # Convert to ComfyUI tensor format [B, H, W, C]
                if img.mode == 'RGBA':
                    # Separate alpha channel as mask
                    rgb_channels = img.split()[:3]
                    alpha_channel = img.split()[3]
                    img_rgb = Image.merge('RGB', rgb_channels)
                    mask_np = np.array(alpha_channel).astype(np.float32) / 255.0
                    mask_tensor = torch.from_numpy(mask_np)[None,]
                    mask_list.append(mask_tensor)
                else:
                    # No alpha channel - create empty mask
                    w, h = img.size
                    mask_np = np.zeros((h, w), dtype=np.float32)
                    mask_tensor = torch.from_numpy(mask_np)[None,]
                    mask_list.append(mask_tensor)

                # Convert RGB to tensor
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                img_np = np.array(img).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np)[None,]  # Add batch dimension
                image_list.append(img_tensor)

                print(f"✅ [LoadImagesWithMetadata] Loaded: {file_path.name}")

            except Exception as e:
                print(f"❌ [LoadImagesWithMetadata] Error loading {file_path.name}: {str(e)}")
                # Skip problematic files, continue with others
                continue

        if not image_list:
            print(f"⚠️ [LoadImagesWithMetadata] No valid images loaded")
            return ([], [], [], [])

        print(f"✅ [LoadImagesWithMetadata] Successfully loaded {len(image_list)} images with metadata")
        return (image_list, mask_list, metadata_json_list, metadata_value_list)

    def _extract_png_metadata(self, img):
        """Extract all text chunks from PNG image"""
        metadata = {}

        # Method 1: img.text (Pillow >= 9.1.0)
        if hasattr(img, 'text') and isinstance(img.text, dict):
            for k, v in img.text.items():
                if isinstance(v, str):
                    metadata[k] = v

        # Method 2: img.info fallback
        if hasattr(img, 'info') and isinstance(img.info, dict):
            for k, v in img.info.items():
                if isinstance(v, str) and k not in ['dpi', 'gamma', 'transparency']:
                    metadata[k] = v

        return metadata