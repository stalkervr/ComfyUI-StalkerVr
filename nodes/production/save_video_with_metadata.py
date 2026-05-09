import subprocess
import tempfile
import numpy as np
import json
from pathlib import Path
from PIL import Image
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class SaveVideoWithMetadata:
    """Encodes image batch to MP4 with embedded metadata and optional cover image."""

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
                "title": ("STRING", {"default": ""}),
                "artist": ("STRING", {"default": ""}),
                "album": ("STRING", {"default": ""}),
                "comment": ("STRING", {"default": ""}),
                "genre": ("STRING", {"default": ""}),
                "creation_time": ("STRING", {"default": ""}),
                "copyright": ("STRING", {"default": ""}),
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

        log(LogEntry(
            node_class="SaveVideoWithMetadata",
            title="Starting video export",
            details={
                "Quality": quality,
                "Cover Image": cover_image is not None,
                "Output": str(video_path),
                "FPS": fps
            }
        ))

        # Prepare first frame for dimensions
        first_img = images[0].cpu().numpy()
        first_img = (first_img * 255.0).clip(0, 255).astype(np.uint8)
        if first_img.shape[2] == 4:
            first_img = first_img[:, :, :3]
        height, width = first_img.shape[:2]

        temp_video = video_path.with_suffix(".temp_raw.mp4")

        # FFmpeg encoding presets
        if quality == "lossless":
            crf, preset, pix_fmt, codec = "0", "ultrafast", "rgb24", "libx264rgb"
        elif quality == "high":
            crf, preset, pix_fmt, codec = "17", "slow", "yuv420p", "libx264"
        else:
            crf, preset, pix_fmt, codec = "23", "medium", "yuv420p", "libx264"

        cmd1 = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
            "-c:v", codec, "-crf", crf, "-preset", preset,
            "-pix_fmt", pix_fmt, "-movflags", "+faststart",
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

        # Embed metadata and cover
        cmd2 = ["ffmpeg", "-y", "-i", str(temp_video)]

        cover_temp = None
        if cover_image is not None and len(cover_image) > 0:
            try:
                img_tensor = cover_image[0]
                img_np = (img_tensor.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
                if img_np.shape[2] == 4:
                    img_np = img_np[:, :, :3]
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    cover_temp = Path(tmp.name)
                pil_img = Image.fromarray(img_np, mode="RGB")
                pil_img.save(cover_temp, "JPEG", quality=95)
                cmd2 += ["-i", str(cover_temp)]
            except Exception as e:
                log(LogEntry(node_class="SaveVideoWithMetadata", title="Cover image warning", details={"Error": str(e)}))

        def to_str(value):
            if value is None: return ""
            if isinstance(value, str): return value
            if isinstance(value, (int, float, bool)): return str(value)
            try: return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            except: return str(value)

        for key, value in [("title", title), ("artist", artist), ("album", album), ("comment", comment), ("genre", genre), ("creation_time", creation_time), ("copyright", copyright)]:
            s = to_str(value).strip()
            if s:
                cmd2 += ["-metadata", f"{key}={s}"]

        if cover_temp:
            cmd2 += ["-map", "0", "-map", "1", "-c", "copy", "-c:v:1", "mjpeg", "-disposition:v:1", "attached_pic"]
        else:
            cmd2 += ["-map", "0", "-c", "copy"]

        cmd2 += [str(video_path)]
        result = subprocess.run(cmd2, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        temp_video.unlink()
        if cover_temp and cover_temp.exists():
            cover_temp.unlink()

        log(LogEntry(node_class="SaveVideoWithMetadata", title="Video saved", details={"Path": str(video_path)}))
        return (str(video_path),)