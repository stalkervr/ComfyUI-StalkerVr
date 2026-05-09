import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont, ImageOps
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log
from ...common.fonts import get_system_font_names, load_font, BIDI_AVAILABLE

class TextWatermark:
    """Adds customizable text watermark with RTL support, auto-scaling, and precise positioning."""

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
            img_tensor = images[i].cpu()
            img_np = (img_tensor.numpy() * 255.0).clip(0, 255).astype(np.uint8)
            if img_np.shape[2] == 4:
                img_np = img_np[:, :, :3]
            pil_img = Image.fromarray(img_np, mode="RGB").convert("RGBA")
            width, height = pil_img.size

            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            fill_color = (255, 255, 255, int(255 * opacity))
            stroke_color = (0, 0, 0, int(255 * opacity * 0.5))

            # Calculate font size
            calculated_font_size = base_font_size
            if auto_scale:
                base_dim = {"width": width, "height": height, "diagonal": (width**2 + height**2)**0.5}.get(scale_reference, width)
                calculated_font_size = max(8, min(int(base_dim * auto_scale_factor), 200))

            font = load_font(font_name, calculated_font_size)

            # BiDi handling
            def is_rtl_text(s):
                return sum(1 for c in s if '\u0590' <= c <= '\uFEFF') > len(s) * 0.3

            is_rtl = force_rtl or (not BIDI_AVAILABLE and is_rtl_text(text))
            display_text = text
            if BIDI_AVAILABLE:
                from bidi.algorithm import get_display
                display_text = get_display(text)
            elif is_rtl:
                display_text = text[::-1]

            bbox = font.getbbox(display_text)
            offset_x, offset_y = -min(0, bbox[0]), -min(0, bbox[1])
            text_width = bbox[2] - bbox[0]
            text_height_for_positioning = bbox[3]

            if text_orientation == "vertical":
                canvas_w = int(text_width) + 20 + offset_x
                canvas_h = int(text_height_for_positioning) + 20 + offset_y
                text_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                text_draw.text((offset_x + 10, offset_y + 10), display_text, font=font, fill=fill_color, stroke_width=2, stroke_fill=stroke_color)
                try:
                    resample = Image.Resampling.BICUBIC
                except AttributeError:
                    resample = Image.BICUBIC
                rotated = text_img.rotate(90 if vertical_text_direction == "bottom-to-top" else -90, expand=True, resample=resample)
                rw, rh = rotated.size
                internal_padding = 10
                if text_horizontal_pos == "left":
                    x = margin_x - internal_padding if vertical_text_direction == "top-to-bottom" else margin_x - (internal_padding * 2)
                elif text_horizontal_pos == "center":
                    x = (width - rw) // 2
                else:
                    x = width - rw - margin_x + (internal_padding * 2 if vertical_text_direction == "top-to-bottom" else internal_padding)
                y = {"top": margin_y - internal_padding, "middle": (height - rh) // 2, "bottom": height - rh - margin_y + internal_padding}.get(text_vertical_pos, height - rh - margin_y + internal_padding)
                overlay.paste(rotated, (x, y), rotated)
            else:
                x = {"left": margin_x, "center": (width - text_width) // 2, "right": width - text_width - margin_x}.get(text_horizontal_pos, width - text_width - margin_x)
                y = {"top": margin_y - bbox[1], "middle": (height - text_height_for_positioning) // 2, "bottom": height - text_height_for_positioning - margin_y}.get(text_vertical_pos, height - text_height_for_positioning - margin_y)
                draw = ImageDraw.Draw(overlay)
                draw.text((x + offset_x, y + offset_y), display_text, font=font, fill=fill_color, stroke_width=2, stroke_fill=stroke_color)

            watermarked = Image.alpha_composite(pil_img, overlay).convert("RGB")
            result.append(torch.from_numpy(np.array(watermarked).astype(np.float32) / 255.0))

        log(LogEntry(node_class="TextWatermark", title="Watermark applied", details={"Batch Size": batch_size}))
        return (torch.stack(result, dim=0),)