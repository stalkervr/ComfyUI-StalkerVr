import os
import json
import shutil
import folder_paths
from .constants import CATEGORY_PREFIX, WAN_LORAS_FULL_PATH
from .logger import LogEntry, log

class WanVideoLoraPairCreator:
    """
    WanVideoLoraPairCreator
    -----------------------
    Creates a paired Wan 2.2 LoRA folder from existing LoRAs in models/loras.
    Copies selected high/low noise models, renames them, and generates lora.json.
    """

    @classmethod
    def INPUT_TYPES(s):
        all_loras = folder_paths.get_filename_list("loras")
        lora_list = sorted([f for f in all_loras if f.lower().endswith(".safetensors")])

        return {
            "required": {
                "model_page": ("STRING", {"default": "", "multiline": False, "label": "Model Page URL", "tooltip": "Optional URL to model page (saved to lora.json)"}),
                "lora_name": ("STRING", {"default": "Wan2.2_NewPair", "label": "LoRA Name", "tooltip": "Name for new folder and files"}),
                "high_noise_model": (lora_list, {"tooltip": "Select source high noise LoRA from models/loras"}),
                "low_noise_model": (lora_list, {"tooltip": "Select source low noise LoRA from models/loras"}),
                "trigger_words": ("STRING", {"default": "", "multiline": True, "label": "Trigger Words", "tooltip": "Comma-separated trigger words"}),
                "subfolder": ("STRING", {"default": "", "label": "Subfolder Path", "tooltip": "Optional subfolder (e.g., 'anime/style')"}),
            },
            "optional": {
                "overwrite": ("BOOLEAN", {"default": False, "label": "Overwrite Existing", "tooltip": "Replace files if they already exist"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("status", "folder_path")
    FUNCTION = "create_pair"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"
    OUTPUT_NODE = True

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Remove/replace characters invalid for filesystem."""
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
        """Parse comma-separated trigger words, clean whitespace, remove duplicates."""
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

    def create_pair(self, model_page, lora_name, high_noise_model, low_noise_model,
                    trigger_words, subfolder, overwrite=False):
        # 1. Validate & sanitize inputs
        safe_name = self._sanitize_filename(lora_name)
        if not safe_name:
            return ("❌ Error: Invalid LoRA name", "")

        sub_clean = subfolder.strip().replace("\\", "/") if subfolder else ""

        # 2. Resolve absolute source paths
        try:
            src_high = folder_paths.get_full_path("loras", high_noise_model)
            src_low = folder_paths.get_full_path("loras", low_noise_model)
        except Exception as e:
            return (f"❌ Error resolving source paths: {e}", "")

        if not src_high or not os.path.exists(src_high):
            return (f"❌ High noise source not found: {high_noise_model}", "")
        if not src_low or not os.path.exists(src_low):
            return (f"❌ Low noise source not found: {low_noise_model}", "")

        # 3. Build target paths
        target_dir = os.path.join(WAN_LORAS_FULL_PATH, sub_clean, safe_name) if sub_clean else os.path.join(WAN_LORAS_FULL_PATH, safe_name)
        tgt_high = os.path.join(target_dir, f"{safe_name}_High.safetensors")
        tgt_low = os.path.join(target_dir, f"{safe_name}_Low.safetensors")
        json_path = os.path.join(target_dir, "lora.json")

        # 4. Check overwrite protection
        if not overwrite and (os.path.exists(tgt_high) or os.path.exists(tgt_low) or os.path.exists(json_path)):
            log(LogEntry(
                node_class="WanVideoLoraPairCreator",
                title="Skipped: Target exists",
                details={"Name": safe_name, "Path": target_dir},
                footer="Enable 'overwrite' to replace"
            ))
            return ("⚠️ Skipped: Target files already exist. Enable 'overwrite' to replace.", target_dir)

        # 5. Create directory & copy files
        try:
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(src_high, tgt_high)
            shutil.copy2(src_low, tgt_low)
        except Exception as e:
            log(LogEntry(
                node_class="WanVideoLoraPairCreator",
                title="File operation failed",
                details={"Error": str(e)},
                footer="Copy aborted"
            ))
            return (f"❌ File operation failed: {e}", "")

        # 6. Generate lora.json
        triggers = self._parse_trigger_words(trigger_words)
        lora_data = {
            "name": lora_name.strip(),
            "lora": {
                "high_noise": f"{safe_name}_High.safetensors",
                "low_noise": f"{safe_name}_Low.safetensors"
            },
            "trigger_words": triggers
        }

        model_page_clean = model_page.strip() if model_page else ""
        if model_page_clean:
            lora_data["model_page"] = model_page_clean

        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(lora_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(LogEntry(
                node_class="WanVideoLoraPairCreator",
                title="JSON write failed",
                details={"Error": str(e)},
                footer="Files created, metadata missing"
            ))
            return (f"⚠️ Created files but failed to write lora.json: {e}", target_dir)

        # 7. Success
        log(LogEntry(
            node_class="WanVideoLoraPairCreator",
            title=f"Created pair: {safe_name}",
            details={
                "Files": f"{safe_name}_High.safetensors, {safe_name}_Low.safetensors",
                "Path": target_dir,
                "Triggers": len(triggers)
            },
            footer="lora.json generated"
        ))

        return (f"✅ Created pair: {safe_name}", target_dir)