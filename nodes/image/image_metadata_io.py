import os
import torch
import numpy as np
import json
import re
import folder_paths

from PIL import Image, ImageOps, PngImagePlugin
from pathlib import Path
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

from aiohttp import web
from server import PromptServer

_METADATA_CACHE = {}


@PromptServer.instance.routes.post("/stalker/metadata_cache")
async def cache_latest_metadata(request):
    try:
        data = await request.json()
        filename = data.get("filename")
        if not filename:
            return web.json_response({"error": "no filename"}, status=400)

        image_path = folder_paths.get_annotated_filepath(filename)
        if not os.path.exists(image_path):
            return web.json_response({"error": "file not found"}, status=404)

        with Image.open(image_path) as img:
            raw_meta = _extract_png_metadata_static(img)
            parsed_meta = _parse_metadata_static(raw_meta)
            global _METADATA_CACHE
            _METADATA_CACHE = parsed_meta

        log(LogEntry(node_class="MetadataCache", title="Updated latest metadata", details={"Filename": filename}))
        return web.json_response({"status": "success"})
    except Exception as e:
        log(LogEntry(node_class="MetadataCache", title="Cache update error", details={"Error": str(e)}))
        return web.json_response({"error": str(e)}, status=500)


def _extract_png_metadata_static(img):
    metadata = {}
    if hasattr(img, 'text') and isinstance(img.text, dict):
        for k, v in img.text.items():
            if isinstance(v, str): metadata[k] = v
    if hasattr(img, 'info') and isinstance(img.info, dict):
        for k, v in img.info.items():
            if isinstance(v, str) and k not in ['dpi', 'gamma', 'transparency', 'aspect']:
                metadata[k] = v
    return metadata


def _parse_metadata_static(raw_metadata):
    if "comfy_metadata" in raw_metadata:
        try:
            parsed = json.loads(raw_metadata["comfy_metadata"])
            if isinstance(parsed, dict): return parsed
        except (json.JSONDecodeError, TypeError) as e:
            log(LogEntry(node_class="ImageLoadWithMetadata", title="Error parsing comfy_metadata",
                         details={"Error": str(e)}))

    legacy_metadata = {}
    for key, value in raw_metadata.items():
        if key == "comfy_metadata": continue
        legacy_metadata[key] = _smart_convert_value_static(value)
    return legacy_metadata


def _smart_convert_value_static(value):
    if not isinstance(value, str): return value
    val = value.strip()
    if not val: return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        pass
    if val.lower() in ('true', 'false'): return val.lower() == 'true'
    if val.lower() in ('null', 'none'): return None
    if re.match(r'^-?\d+\.?\d*$', val):
        try:
            return int(val) if '.' not in val else float(val)
        except (ValueError, OverflowError):
            pass
    return val


class ImagesLoadWithMetadata:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {"default": "", "tooltip": "Directory path containing image files"}),
                "sort_by": (["name", "date", "none"], {"default": "name", "tooltip": "Sort order"}),
            },
            "optional": {
                "extract_key": ("STRING", {"default": "", "tooltip": "Extract specific metadata key"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "metadata_json", "metadata_value")
    FUNCTION = "load_images_with_metadata"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"
    OUTPUT_IS_LIST = (True, True, True, True)

    def load_images_with_metadata(self, directory_path, sort_by="name", extract_key=""):
        directory_path = directory_path.strip()
        if not directory_path:
            raise ValueError("Directory path cannot be empty")

        directory = Path(directory_path)
        if not directory.exists():
            return ([], [], [], [])

        supported_ext = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}
        image_files = [e for e in directory.iterdir() if e.is_file() and e.suffix.lower() in supported_ext]
        if not image_files:
            return ([], [], [], [])

        if sort_by == "name":
            image_files.sort(key=lambda x: x.name)
        elif sort_by == "date":
            image_files.sort(key=lambda x: x.stat().st_mtime)

        image_list, mask_list, meta_json_list, meta_val_list = [], [], [], []

        for file_path in image_files:
            try:
                img = Image.open(file_path)
                img = ImageOps.exif_transpose(img)

                raw_meta = self._extract_image_metadata(img)
                metadata = self._parse_metadata(raw_meta)
                meta_json_list.append(json.dumps(metadata, ensure_ascii=False, indent=2))

                extracted = metadata.get(extract_key.strip(), "") if extract_key.strip() else ""
                meta_val_list.append(extracted)

                if 'A' in img.getbands():
                    alpha = np.array(img.getchannel('A')).astype(np.float32) / 255.0
                    mask_list.append((1.0 - torch.from_numpy(alpha)).unsqueeze(0))
                else:
                    mask_list.append(torch.zeros((img.size[1], img.size[0]), dtype=torch.float32).unsqueeze(0))

                img_rgb = img.convert('RGB')
                img_np = np.array(img_rgb).astype(np.float32) / 255.0
                image_list.append(torch.from_numpy(img_np).unsqueeze(0))

                log(LogEntry(node_class="ImagesLoadWithMetadata", title="Loaded", details={"File": file_path.name}))
            except Exception as e:
                log(LogEntry(node_class="ImagesLoadWithMetadata", title="Skipped",
                             details={"File": file_path.name, "Error": str(e)}))
                continue

        return (image_list, mask_list, meta_json_list, meta_val_list)

    def _extract_image_metadata(self, img):
        metadata = {}
        if hasattr(img, 'text') and isinstance(img.text, dict):
            for k, v in img.text.items():
                if isinstance(v, str): metadata[k] = v
        if hasattr(img, 'info') and isinstance(img.info, dict):
            for k, v in img.info.items():
                if isinstance(v, str) and k not in ['dpi', 'gamma', 'transparency', 'aspect']:
                    metadata[k] = v
        if hasattr(img, '_getexif') and callable(img._getexif):
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    if isinstance(value, (str, int, float)) and len(str(value)) < 1000:
                        metadata[f"exif_{tag}"] = str(value)
        return metadata

    def _parse_metadata(self, raw_metadata):
        return _parse_metadata_static(raw_metadata)

    def _smart_convert_value(self, value):
        return _smart_convert_value_static(value)


class ImageLoadWithMetadata:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {"image": (sorted(files), {"image_upload": True})},
            "optional": {"extract_key": ("STRING", {"default": ""})}
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "metadata_json", "metadata_value")
    FUNCTION = "load_image"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"

    def load_image(self, image, extract_key=""):
        image_path = folder_paths.get_annotated_filepath(image)
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"File not found: {image_path}")

        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)

        final_metadata = _METADATA_CACHE.copy()
        if not final_metadata:
            try:
                final_metadata = self._parse_metadata(self._extract_png_metadata(img))
            except Exception as e:
                log(LogEntry(node_class="ImageLoadWithMetadata", title="Fallback metadata failed",
                             details={"Error": str(e)}))
                final_metadata = {}

        frame = img.convert("RGB")
        image_tensor = torch.from_numpy(np.array(frame).astype(np.float32) / 255.0)[None,]

        if 'A' in img.getbands():
            mask_np = np.array(img.getchannel('A')).astype(np.float32) / 255.0
            mask_tensor = (1.0 - torch.from_numpy(mask_np)).unsqueeze(0)
        else:
            mask_tensor = torch.zeros((frame.size[1], frame.size[0]), dtype=torch.float32).unsqueeze(0)

        metadata_json = json.dumps(final_metadata, ensure_ascii=False, indent=2)
        metadata_value = ""

        if extract_key.strip():
            current = final_metadata
            for part in extract_key.strip().split("."):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    current = None
                    break
            if current is not None:
                metadata_value = json.dumps(current, ensure_ascii=False, indent=2) if isinstance(current, (dict, list)) else str(current)

        log(LogEntry(node_class="ImageLoadWithMetadata", title="Loaded",
                     details={"File": image, "Size": f"{img.width}x{img.height}", "Mode": img.mode}))
        return (image_tensor, mask_tensor, metadata_json, metadata_value)

    def _extract_png_metadata(self, img):
        return _extract_png_metadata_static(img)

    def _parse_metadata(self, raw_metadata):
        return _parse_metadata_static(raw_metadata)

    @classmethod
    def VALIDATE_INPUTS(cls, image, extract_key=""):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True


class ImageSaveWithMetadata:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "save_directory": ("STRING", {"default": "", "tooltip": "Output directory path"}),
                "filename_prefix": ("STRING", {"default": "output", "tooltip": "Filename prefix"}),
                "save_workflow": ("BOOLEAN", {"default": True, "tooltip": "Embed ComfyUI workflow"}),
                "metadata_json": ("STRING", {"default": "{}", "multiline": False, "dynamicPrompts": False}),
                "compression_level": ("INT", {"default": 0, "min": 0, "max": 9, "step": 1}),
            },
            "optional": {"captions": ("STRING", {"forceInput": True})},
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "saved_paths")
    FUNCTION = "save_images_with_metadata"
    CATEGORY = f"{CATEGORY_PREFIX}/Image"
    OUTPUT_NODE = True

    def save_images_with_metadata(self, images, save_directory, filename_prefix, save_workflow,
                                  metadata_json, compression_level=4, captions="", prompt=None, extra_pnginfo=None):
        save_directory = save_directory.strip()
        filename_prefix = filename_prefix.strip()
        if not save_directory: raise ValueError("Directory cannot be empty")
        if not filename_prefix: raise ValueError("Prefix cannot be empty")

        metadata_dict = {}
        try:
            parsed = json.loads(metadata_json.strip())
            if isinstance(parsed, dict): metadata_dict = parsed
        except json.JSONDecodeError:
            pass

        output_dir = Path(save_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        next_number = self._get_next_number(output_dir, filename_prefix)

        saved_paths = []
        has_captions = bool(captions.strip())

        for i in range(images.shape[0]):
            idx = next_number + i
            filename = f"{filename_prefix}_{idx:05d}.png"
            save_path = output_dir / filename

            img_np = (images[i].cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
            if img_np.shape[2] == 4:
                img_pil = Image.fromarray(img_np, mode="RGBA")
            elif img_np.shape[2] == 3:
                img_pil = Image.fromarray(img_np, mode="RGB")
            else:
                raise ValueError(f"Unsupported channels: {img_np.shape[2]}")

            pnginfo = PngImagePlugin.PngInfo()
            if save_workflow and extra_pnginfo:
                for k, v in extra_pnginfo.items():
                    pnginfo.add_text(k, json.dumps(v))

            if metadata_dict:
                meta_str = json.dumps(metadata_dict, ensure_ascii=False, separators=(',', ':'))
                key = "comfy_metadata" if len("comfy_metadata") <= 79 else "metadata"
                if len(meta_str) > 1024:
                    (pnginfo.add_ztxt if hasattr(pnginfo, 'add_ztxt') else pnginfo.add_text)(key, meta_str)
                elif any(ord(c) > 127 for c in meta_str):
                    (pnginfo.add_itxt if hasattr(pnginfo, 'add_itxt') else pnginfo.add_text)(key, meta_str, lang="", tkey="")
                else:
                    pnginfo.add_text(key, meta_str)

            img_pil.save(save_path, format="PNG", pnginfo=pnginfo, compress_level=compression_level)
            saved_paths.append(str(save_path))

            if has_captions:
                try:
                    with open(output_dir / f"{filename_prefix}_{idx:05d}.txt", 'w', encoding='utf-8') as f:
                        f.write(captions.strip())
                except Exception:
                    pass

        log(LogEntry(node_class="ImageSaveWithMetadata", title="Saved",
                     details={"Count": len(saved_paths), "Path": str(output_dir)}))
        return (images, ", ".join(saved_paths) if len(saved_paths) > 1 else saved_paths[0])

    def _get_next_number(self, directory, prefix):
        pattern = re.compile(rf'^{re.escape(prefix)}_(\d{{5}})\.png$', re.IGNORECASE)
        max_num = 0
        try:
            for entry in directory.iterdir():
                if entry.is_file() and entry.suffix.lower() == '.png':
                    match = pattern.match(entry.name)
                    if match: max_num = max(max_num, int(match.group(1)))
        except Exception:
            pass
        return max_num + 1