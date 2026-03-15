import subprocess
import tempfile
import numpy as np
import json
import cv2
import datetime
import torch
import os
import sys


from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
from pathlib import Path


from .utils import get_system_font_names, find_font_path, load_font, BIDI_AVAILABLE
from .utils import tensor2pil, pil2tensor
from .constants import CATEGORY_PREFIX


class Everything(str):
    """Wildcard type marker."""
    def __ne__(self, __value: object) -> bool:
        return False


class SaveVideoWithMetadata:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "output_path": ("STRING", {"default": "./output/"}),
                "filename": ("STRING", {"default": "final_video"}),
                "fps": ("FLOAT", {"default": 24.0, "min": 12.0, "max": 60.0, "step": 1.0}),
                "quality": (["lossless", "high", "medium"], {"default": "lossless"}),
            },
            "optional": {
                "cover_image": ("IMAGE",),
                "title": (Everything("*"), {"default": ""}),
                "artist": (Everything("*"), {"default": ""}),
                "album": (Everything("*"), {"default": ""}),
                "comment": (Everything("*"), {"default": ""}),
                "genre": (Everything("*"), {"default": ""}),
                "creation_time": (Everything("*"), {"default": ""}),
                "copyright": (Everything("*"), {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "save_and_embed"
    CATEGORY = f"{CATEGORY_PREFIX}/Production"
    OUTPUT_NODE = True

    def save_and_embed(self, images, output_path, filename, fps, quality, cover_image=None, title="", artist="", album="", comment="", genre="", creation_time="", copyright="", **kwargs):
        output_dir = Path(output_path).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        video_path = output_dir / f"{filename}.mp4"

        print(f"\n{'='*60}")
        print(f"📹 SaveVideoWithMetadata - Starting")
        print(f"Quality mode: {quality}")
        print(f"Cover image: {'Yes' if cover_image is not None else 'No'}")
        print(f"Output: {video_path}")
        print(f"FPS: {fps}")

        # --- Step 1: Record raw video ---
        first_img = images[0].cpu().numpy()
        first_img = (first_img * 255.0).clip(0, 255).astype(np.uint8)
        if first_img.shape[2] == 4:
            first_img = first_img[:, :, :3]
        height, width = first_img.shape[:2]

        temp_video = video_path.with_suffix(".temp_raw.mp4")

        if quality == "lossless":
            crf = "0"
            preset = "ultrafast"
            pix_fmt = "rgb24"
            codec = "libx264rgb"
        elif quality == "high":
            crf = "17"
            preset = "slow"
            pix_fmt = "yuv420p"
            codec = "libx264"
        else:  # medium
            crf = "23"
            preset = "medium"
            pix_fmt = "yuv420p"
            codec = "libx264"

        cmd1 = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
            "-c:v", codec,
            "-crf", crf,
            "-preset", preset,
            "-pix_fmt", pix_fmt,
            "-movflags", "+faststart",
            str(temp_video)
        ]

        proc = subprocess.Popen(cmd1, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        for i in range(images.shape[0]):
            img = images[i].cpu().numpy()
            img = (img * 255.0).clip(0, 255).astype(np.uint8)
            if img.shape[2] == 4:
                img = img[:, :, :3]
            proc.stdin.write(img.tobytes())
        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Recording failed: {stderr.decode()}")

        # --- Step 2: Embed metadata + cover ---
        cmd2 = ["ffmpeg", "-y", "-i", str(temp_video)]

        cover_temp = None
        if cover_image is not None and len(cover_image) > 0:
            try:
                img_tensor = cover_image[0]
                img_np = img_tensor.cpu().numpy()
                img_np = (img_np * 255.0).clip(0, 255).astype(np.uint8)
                if img_np.shape[2] == 4:
                    img_np = img_np[:, :, :3]
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    cover_temp = Path(tmp.name)
                pil_img = Image.fromarray(img_np, mode="RGB")
                pil_img.save(cover_temp, "JPEG", quality=95)
                cmd2 += ["-i", str(cover_temp)]
                print(f"✅ Cover image prepared: {cover_temp}")
            except Exception as e:
                print(f"⚠️ Failed to process cover image: {e}")

        def to_str(value):
            if value is None:
                return ""
            if isinstance(value, str):
                return value
            if isinstance(value, (int, float, bool)):
                return str(value)
            try:
                return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            except:
                return str(value)

        for key, value in [
            ("title", title),
            ("artist", artist),
            ("album", album),
            ("comment", comment),
            ("genre", genre),
            ("creation_time", creation_time),
            ("copyright", copyright),
        ]:
            s = to_str(value).strip()
            if s:
                cmd2 += ["-metadata", f"{key}={s}"]
                print(f"✅ Adding meta: {key}={s}")

        if cover_temp:
            cmd2 += [
                "-map", "0",
                "-map", "1",
                "-c", "copy",
                "-c:v:1", "mjpeg",
                "-disposition:v:1", "attached_pic"
            ]
        else:
            cmd2 += ["-map", "0", "-c", "copy"]

        cmd2 += [str(video_path)]

        result = subprocess.run(cmd2, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        temp_video.unlink()
        if cover_temp and cover_temp.exists():
            cover_temp.unlink()

        print(f"✅ Video saved: {video_path}")
        return (str(video_path),)


class GenerateCreationTime:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "use_current_time": ("BOOLEAN", {"default": True}),
                "custom_datetime": ("STRING", {"default": "2026-03-11 15:30:00"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("creation_time",)
    FUNCTION = "generate"
    CATEGORY = f"{CATEGORY_PREFIX}/Production"
    OUTPUT_NODE = True

    def generate(self, use_current_time=True, custom_datetime=""):
        if use_current_time:
            creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            creation_time = custom_datetime.strip()

            if creation_time:
                try:
                    datetime.datetime.strptime(creation_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError("Custom datetime must be in format: YYYY-MM-DD HH:MM:SS")

        return (creation_time,)


class TextWatermark:
    """
    Add customizable text watermark to images with auto-scaling support.
    Supports horizontal and vertical text orientation, RTL languages,
    smart font sizing, and precise margin control.
    """

    @classmethod
    def INPUT_TYPES(cls):
        font_names = get_system_font_names()
        return {
            "required": {"images": ("IMAGE",), "text": ("STRING", {"default": "© 2026 AI Art Studio"})},
            "optional": {
                "font_name": (font_names, {"default": font_names[0] if font_names else "Arial"}),
                "base_font_size": ("INT", {"default": 38, "min": 8, "max": 500}),
                "auto_scale": ("BOOLEAN", {"default": True}),
                "auto_scale_factor": ("FLOAT", {"default": 0.02, "min": 0.005, "max": 0.1, "step": 0.001}),
                "scale_reference": (["width", "height", "diagonal"], {"default": "width"}),
                "text_orientation": (["horizontal", "vertical"], {"default": "horizontal"}),
                "text_vertical_pos": (["top", "middle", "bottom"], {"default": "bottom"}),
                "text_horizontal_pos": (["left", "center", "right"], {"default": "right"}),
                "vertical_text_direction": (["top-to-bottom", "bottom-to-top"], {"default": "top-to-bottom"}),
                "opacity": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.01}),
                "margin_x": ("INT", {"default": 10, "min": -500, "max": 500}),
                "margin_y": ("INT", {"default": 10, "min": -500, "max": 500}),
                "force_rtl": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("watermarked_images",)
    FUNCTION = "add_watermark"
    CATEGORY = f"{CATEGORY_PREFIX}/Production"
    OUTPUT_NODE = False

    def add_watermark(self, images, text="", font_name="Arial", base_font_size=38, auto_scale=True,
                      auto_scale_factor=0.02, scale_reference="width", text_orientation="horizontal",
                      text_vertical_pos="bottom", text_horizontal_pos="right", vertical_text_direction="top-to-bottom",
                      opacity=0.7, margin_x=10, margin_y=10, force_rtl=False):
        if not text or not text.strip():
            return (images,)

        batch_size = images.shape[0]
        result = []

        for i in range(batch_size):
            # Prepare image
            img_tensor = images[i].cpu()
            img_np = (img_tensor.numpy() * 255.0).clip(0, 255).astype(np.uint8)
            if img_np.shape[2] == 4:
                img_np = img_np[:, :, :3]
            pil_img = Image.fromarray(img_np, mode="RGB").convert("RGBA")
            width, height = pil_img.size

            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            fill_color = (255, 255, 255, int(255 * opacity))
            stroke_color = (0, 0, 0, int(255 * opacity * 0.5))

            # Calculate font size (auto-scaling)
            calculated_font_size = base_font_size
            if auto_scale:
                if scale_reference == "width":
                    base_dim = width
                elif scale_reference == "height":
                    base_dim = height
                else:
                    base_dim = (width ** 2 + height ** 2) ** 0.5
                calculated_font_size = max(8, min(int(base_dim * auto_scale_factor), 200))

            font = load_font(font_name, calculated_font_size)

            # BiDi processing for RTL languages
            def is_rtl_text(s):
                return sum(1 for c in s if '\u0590' <= c <= '\uFEFF') > len(s) * 0.3

            is_rtl = force_rtl or (not BIDI_AVAILABLE and is_rtl_text(text))
            display_text = text
            if BIDI_AVAILABLE:
                from bidi.algorithm import get_display
                display_text = get_display(text)
            elif is_rtl:
                display_text = text[::-1]

            # Calculate bbox with negative coordinates handling
            bbox = font.getbbox(display_text)
            offset_x = -min(0, bbox[0])
            offset_y = -min(0, bbox[1])
            text_width = bbox[2] - bbox[0]

            # bbox[3] = full height from baseline to bottom (for positioning)
            text_height_for_positioning = bbox[3]

            if text_orientation == "vertical":
                # === VERTICAL TEXT ===
                # Create temporary canvas with padding for stroke and offset
                canvas_width = int(text_width) + 20 + offset_x
                canvas_height = int(text_height_for_positioning) + 20 + offset_y
                text_img = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                text_draw.text((offset_x + 10, offset_y + 10), display_text, font=font,
                               fill=fill_color, stroke_width=2, stroke_fill=stroke_color)

                # Rotate with expand=True to preserve all text
                try:
                    resample = Image.Resampling.BICUBIC
                except AttributeError:
                    resample = Image.BICUBIC

                if vertical_text_direction == "bottom-to-top":
                    rotated = text_img.rotate(90, expand=True, resample=resample)
                else:
                    rotated = text_img.rotate(-90, expand=True, resample=resample)

                rw, rh = rotated.size

                # Compensate internal padding (10px) for positioning
                internal_padding = 10

                # Horizontal position
                if text_horizontal_pos == "left":
                    # Different compensation for different rotation directions
                    if vertical_text_direction == "top-to-bottom":
                        x = margin_x - internal_padding
                    else:  # bottom-to-top
                        x = margin_x - (internal_padding * 2)
                elif text_horizontal_pos == "center":
                    x = (width - rw) // 2
                else:  # right
                    if vertical_text_direction == "top-to-bottom":
                        x = width - rw - margin_x + (internal_padding * 2)
                    else:
                        x = width - rw - margin_x + internal_padding

                # Vertical position
                if text_vertical_pos == "top":
                    y = margin_y - internal_padding
                elif text_vertical_pos == "middle":
                    y = (height - rh) // 2
                else:  # bottom
                    y = height - rh - margin_y + internal_padding

                overlay.paste(rotated, (x, y), rotated)

            else:
                # === HORIZONTAL TEXT ===
                # Horizontal positioning
                if text_horizontal_pos == "left":
                    x = margin_x
                elif text_horizontal_pos == "center":
                    x = (width - text_width) // 2
                else:  # right
                    x = width - text_width - margin_x

                # Vertical positioning
                if text_vertical_pos == "top":
                    # Compensate ascent (bbox[1]) for precise top alignment
                    y = margin_y - bbox[1]
                elif text_vertical_pos == "middle":
                    y = (height - text_height_for_positioning) // 2
                else:  # bottom
                    y = height - text_height_for_positioning - margin_y

                # Draw text with offset to handle negative bbox coordinates
                draw = ImageDraw.Draw(overlay)
                draw.text((x + offset_x, y + offset_y), display_text, font=font,
                          fill=fill_color, stroke_width=2, stroke_fill=stroke_color)

            # Compose result
            watermarked = Image.alpha_composite(pil_img, overlay)
            watermarked_rgb = watermarked.convert("RGB")
            result.append(torch.from_numpy(np.array(watermarked_rgb).astype(np.float32) / 255.0))

        output = torch.stack(result, dim=0)
        return (output,)


class ImageWatermark:
    """Add image watermark."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "watermark": ("IMAGE",),
            },
            "optional": {
                "mask": ("MASK",),
                "position": ([
                                 "top-left", "top-center", "top-right",
                                 "center-left", "center", "center-right",
                                 "bottom-left", "bottom-center", "bottom-right"
                             ], {"default": "bottom-right"}),
                "margin_x": ("INT", {"default": 10, "min": -500, "max": 500}),
                "margin_y": ("INT", {"default": 10, "min": -500, "max": 500}),
                "scale_mode": (["percentage", "fixed", "fit_width", "fit_height"], {"default": "percentage"}),
                "scale_factor": ("FLOAT", {"default": 0.2, "min": 0.01, "max": 1.0, "step": 0.01}),
                "opacity": ("FLOAT", {"default": 100, "min": 0, "max": 100, "step": 5}),
                "rotation": ("INT", {"default": 0, "min": -180, "max": 180, "step": 5}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("watermarked_images",)
    FUNCTION = "add_watermark"
    CATEGORY = f"{CATEGORY_PREFIX}/Production"
    OUTPUT_NODE = False

    def add_watermark(self, images, watermark, mask=None, position="bottom-right", margin_x=10, margin_y=10,
                      scale_mode="percentage", scale_factor=0.2, opacity=100, rotation=0):
        if watermark is None or images is None:
            return (images,)

        batch_size = images.shape[0]
        wm_pil = tensor2pil(watermark)
        wm_pil = wm_pil.convert('RGBA')

        if mask is not None:
            mask_pil = tensor2pil(mask)
            mask_pil = mask_pil.resize(wm_pil.size)
            wm_pil.putalpha(ImageOps.invert(mask_pil.convert("L")))
        else:
            if wm_pil.mode != "RGBA":
                wm_pil = wm_pil.convert("RGBA")
            if wm_pil.getbands()[-1] != 'A':
                wm_pil.putalpha(Image.new("L", wm_pil.size, 255))

        if rotation != 0:
            wm_pil = wm_pil.rotate(-rotation, expand=True)

        if opacity < 100:
            r, g, b, a = wm_pil.split()
            a = a.point(lambda x: max(0, int(x * (opacity / 100))))
            wm_pil.putalpha(a)

        result = []

        for i in range(batch_size):
            img_pil = tensor2pil(images[i])

            if img_pil.mode != "RGBA":
                img_pil = img_pil.convert("RGBA")

            width, height = img_pil.size
            wm_scaled = self._scale_watermark(wm_pil, width, height, scale_mode, scale_factor)
            wm_w, wm_h = wm_scaled.size
            x, y = self._calculate_position(position, width, height, wm_w, wm_h, margin_x, margin_y)
            img_pil.paste(wm_scaled, (x, y), wm_scaled)
            result.append(pil2tensor(img_pil))

        output = torch.cat(result, dim=0)
        return (output,)

    def _scale_watermark(self, wm_pil, img_w, img_h, scale_mode, scale_factor):
        """Scale watermark based on mode."""
        if scale_mode == "percentage":
            base_dim = min(img_w, img_h)
            target_size = int(base_dim * scale_factor)
            return self._scale_to_size(wm_pil, target_size, target_size)
        elif scale_mode == "fixed":
            target_size = int(scale_factor * 1000)
            return self._scale_to_size(wm_pil, target_size, target_size)
        elif scale_mode == "fit_width":
            target_width = int(img_w * scale_factor)
            return self._scale_to_size(wm_pil, target_width, None)
        else:
            target_height = int(img_h * scale_factor)
            return self._scale_to_size(wm_pil, None, target_height)

    def _scale_to_size(self, img, target_width, target_height):
        """Scale preserving aspect ratio."""
        orig_w, orig_h = img.size

        if target_width is None and target_height is None:
            return img

        if target_width and target_height:
            ratio = min(target_width / orig_w, target_height / orig_h)
        elif target_width:
            ratio = target_width / orig_w
        else:
            ratio = target_height / orig_h

        new_w = max(1, int(orig_w * ratio))
        new_h = max(1, int(orig_h * ratio))

        return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def _calculate_position(self, position, img_w, img_h, wm_w, wm_h, margin_x, margin_y):
        """Calculate position."""
        pos_map = {
            "top-left": (margin_x, margin_y),
            "top-center": ((img_w - wm_w) // 2, margin_y),
            "top-right": (img_w - wm_w - margin_x, margin_y),
            "center-left": (margin_x, (img_h - wm_h) // 2),
            "center": ((img_w - wm_w) // 2, (img_h - wm_h) // 2),
            "center-right": (img_w - wm_w - margin_x, (img_h - wm_h) // 2),
            "bottom-left": (margin_x, img_h - wm_h - margin_y),
            "bottom-center": ((img_w - wm_w) // 2, img_h - wm_h - margin_y),
            "bottom-right": (img_w - wm_w - margin_x, img_h - wm_h - margin_y),
        }
        return pos_map.get(position, (img_w - wm_w - margin_x, img_h - wm_h - margin_y))
