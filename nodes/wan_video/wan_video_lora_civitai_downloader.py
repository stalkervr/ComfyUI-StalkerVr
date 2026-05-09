import os
import json
import urllib.request
from ...common.constants import CATEGORY_PREFIX, WAN_LORAS_FULL_PATH
from ...config.config_manager import ConfigManager
from ...common.logger import LogEntry, log


class WanVideoLoraCivitAIDownloader:
    """
    Downloads Wan 2.2 LoRA pair (high/low noise) from CivitAI.
    Supports civitai.com and civitai.red with unified config management.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_page": ("STRING", {"default": "", "label": "Model Page URL",
                                          "tooltip": "URL to model page (saved to lora.json)"}),
                "lora_name": (
                "STRING", {"default": "Wan2.2 MyLora", "label": "LoRA Name", "tooltip": "Name for folder and files"}),
                "high_url": ("STRING", {"default": "", "multiline": True, "label": "High Noise URL",
                                        "tooltip": "API download URL for high_noise"}),
                "low_url": ("STRING", {"default": "", "multiline": True, "label": "Low Noise URL",
                                       "tooltip": "API download URL for low_noise"}),
                "trigger_words": ("STRING", {"default": "", "multiline": True, "label": "Trigger Words",
                                             "tooltip": "Comma-separated list"}),
                "subfolder": ("STRING", {"default": "", "label": "Subfolder Path", "tooltip": "e.g. 'camera/motion'"}),
            },
            "optional": {
                "civitai_api_key": (
                "STRING", {"default": "", "label": "API Key Override", "tooltip": "Override key from secrets.yaml"}),
                "skip_if_exists": ("BOOLEAN", {"default": True, "label": "Skip if Exists",
                                               "tooltip": "Skip download if files already present"}),
                "enable_high": ("BOOLEAN", {"default": True, "label": "Enable High"}),
                "enable_low": ("BOOLEAN", {"default": True, "label": "Enable Low"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "folder_path", "trigger_words")
    FUNCTION = "download_lora_pair"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"
    OUTPUT_NODE = True

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        sanitized = name.strip()
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            sanitized = sanitized.replace(char, '_')
        while '  ' in sanitized:
            sanitized = sanitized.replace('  ', ' ')
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        return sanitized.strip('_')

    @staticmethod
    def _parse_trigger_words(text: str) -> list:
        if not text or not text.strip():
            return []
        words = [w.strip() for w in text.split(",") if w.strip()]
        seen = set()
        result = []
        for w in words:
            key = w.lower()
            if key not in seen:
                seen.add(key)
                result.append(w)
        return result

    @staticmethod
    def _get_api_key(override_key: str = "") -> str:
        if override_key and override_key.strip():
            return override_key.strip()
        return ConfigManager().get("civitai.api_key", "")

    @staticmethod
    def _download_file(url: str, destination: str, api_key: str = None) -> bool:
        try:
            headers = {"User-Agent": "ComfyUI-StalkerVr/1.0"}
            if api_key and api_key.strip():
                headers["Authorization"] = f"Bearer {api_key.strip()}"

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=300) as response:
                total_size = response.headers.get('Content-Length')
                total_size = int(total_size) if total_size else None

                downloaded = 0
                with open(destination, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                return True
        except Exception:
            return False

    def download_lora_pair(self, lora_name, high_url, low_url, trigger_words, subfolder,
                           model_page="", civitai_api_key="", skip_if_exists=True,
                           enable_high=True, enable_low=True):

        lora_name = lora_name.strip()
        if not lora_name:
            return ("❌ Error: lora_name cannot be empty", "", "")

        clean_triggers = self._parse_trigger_words(trigger_words)
        safe_lora_name = self._sanitize_filename(lora_name)
        if not safe_lora_name:
            return ("❌ Error: Invalid characters in name", "", "")

        subfolder_clean = subfolder.strip().replace("\\", "/") if subfolder else ""
        target_folder = os.path.join(WAN_LORAS_FULL_PATH, subfolder_clean,
                                     safe_lora_name) if subfolder_clean else os.path.join(WAN_LORAS_FULL_PATH,
                                                                                          safe_lora_name)
        os.makedirs(target_folder, exist_ok=True)

        api_key = self._get_api_key(civitai_api_key)
        downloaded_files = []
        skipped_files = []
        errors = []

        def process_slot(url, filename_suffix, enable_flag):
            if not enable_flag or not url or not url.strip():
                return
            url = url.strip()
            filename = f"{safe_lora_name}_{filename_suffix}.safetensors"
            filepath = os.path.join(target_folder, filename)

            if skip_if_exists and os.path.exists(filepath):
                skipped_files.append(filename)
                downloaded_files.append(filename)
                return

            if self._download_file(url, filepath, api_key):
                downloaded_files.append(filename)
            else:
                errors.append(f"Failed {filename_suffix}")

        process_slot(high_url, "High", enable_high)
        process_slot(low_url, "Low", enable_low)

        if not downloaded_files:
            if not os.listdir(target_folder):
                os.rmdir(target_folder)
            error_msg = " | ".join(errors) if errors else "No files processed"
            return (f"❌ Error: {error_msg}", "", "")

        lora_config = {}
        if f"{safe_lora_name}_High.safetensors" in downloaded_files:
            lora_config["high_noise"] = f"{safe_lora_name}_High.safetensors"
        if f"{safe_lora_name}_Low.safetensors" in downloaded_files:
            lora_config["low_noise"] = f"{safe_lora_name}_Low.safetensors"

        lora_json = {
            "name": lora_name,
            "lora": lora_config,
            "trigger_words": clean_triggers
        }
        if model_page and model_page.strip():
            lora_json["model_page"] = model_page.strip()

        with open(os.path.join(target_folder, "lora.json"), 'w', encoding='utf-8') as f:
            json.dump(lora_json, f, indent=2, ensure_ascii=False)

        if downloaded_files:
            log(LogEntry(
                node_class="WanVideoLoraCivitAIDownloader",
                title=f"Downloaded: {safe_lora_name}",
                details={
                    "Files": f"{len(downloaded_files)} downloaded, {len(skipped_files)} skipped",
                    "Path": target_folder,
                    "Triggers": len(clean_triggers)
                },
                footer="lora.json created"
            ))

        parts = []
        if downloaded_files and not skipped_files:
            parts.append(f"✅ {len(downloaded_files)} downloaded")
        elif skipped_files:
            parts.append(f"⏭️ {len(skipped_files)} skipped")
        if errors:
            parts.append(f"❌ {len(errors)} failed")

        return (" | ".join(parts), target_folder, ", ".join(clean_triggers))