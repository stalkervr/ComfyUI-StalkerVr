import torch
from PIL import Image, ImageOps
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log
from ...common.images import tensor2pil, pil2tensor

class ImageWatermark:
    """Adds image watermark with scaling, positioning, opacity, and rotation support."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"images": ("IMAGE",), "watermark": ("IMAGE",)},
            "optional": {
                "mask": ("MASK",),
                "position": (["top-left", "top-center", "top-right", "center-left", "center", "center-right", "bottom-left", "bottom-center", "bottom-right"], {"default": "bottom-right"}),
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

    def add_watermark(self, images, watermark, mask=None, position="bottom-right", margin_x=10, margin_y=10, scale_mode="percentage", scale_factor=0.2, opacity=100, rotation=0):
        if watermark is None or images is None:
            return (images,)

        batch_size = images.shape[0]
        wm_pil = tensor2pil(watermark).convert('RGBA')

        if mask is not None:
            mask_pil = tensor2pil(mask).resize(wm_pil.size)
            wm_pil.putalpha(ImageOps.invert(mask_pil.convert("L")))
        elif wm_pil.mode != "RGBA" or wm_pil.getbands()[-1] != 'A':
            wm_pil = wm_pil.convert("RGBA")
            wm_pil.putalpha(Image.new("L", wm_pil.size, 255))

        if rotation != 0:
            wm_pil = wm_pil.rotate(-rotation, expand=True)
        if opacity < 100:
            r, g, b, a = wm_pil.split()
            wm_pil.putalpha(a.point(lambda x: max(0, int(x * (opacity / 100)))))

        result = []
        for i in range(batch_size):
            img_pil = tensor2pil(images[i]).convert("RGBA")
            width, height = img_pil.size
            wm_scaled = self._scale_watermark(wm_pil, width, height, scale_mode, scale_factor)
            wm_w, wm_h = wm_scaled.size
            x, y = self._calculate_position(position, width, height, wm_w, wm_h, margin_x, margin_y)
            img_pil.paste(wm_scaled, (x, y), wm_scaled)
            result.append(pil2tensor(img_pil))

        log(LogEntry(node_class="ImageWatermark", title="Watermark applied", details={"Batch Size": batch_size}))
        return (torch.cat(result, dim=0),)

    def _scale_watermark(self, wm_pil, img_w, img_h, scale_mode, scale_factor):
        if scale_mode == "percentage":
            target = int(min(img_w, img_h) * scale_factor)
            return self._scale_to_size(wm_pil, target, target)
        elif scale_mode == "fixed":
            target = int(scale_factor * 1000)
            return self._scale_to_size(wm_pil, target, target)
        elif scale_mode == "fit_width":
            return self._scale_to_size(wm_pil, int(img_w * scale_factor), None)
        else:
            return self._scale_to_size(wm_pil, None, int(img_h * scale_factor))

    def _scale_to_size(self, img, target_width, target_height):
        orig_w, orig_h = img.size
        if target_width is None and target_height is None:
            return img
        ratio = min(target_width / orig_w, target_height / orig_h) if target_width and target_height else (target_width / orig_w if target_width else target_height / orig_h)
        return img.resize((max(1, int(orig_w * ratio)), max(1, int(orig_h * ratio))), Image.Resampling.LANCZOS)

    def _calculate_position(self, position, img_w, img_h, wm_w, wm_h, margin_x, margin_y):
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