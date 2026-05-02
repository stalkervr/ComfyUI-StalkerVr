import os
import json
from .constants import CATEGORY_PREFIX, WAN_LORAS_FULL_PATH
from .logger import LogEntry, log

try:
    from comfy.server import PromptServer
except ImportError:
    PromptServer = None


class WanVideoLoraPairSelect:
    """
    WanVideoLoraPairSelect
    ----------------------
    Loads Wan 2.2 LoRA pair metadata from structured folders and returns chained WANVIDLORA lists.
    Supports [none] passthrough, trigger word merging, and UI metadata display.
    """

    @classmethod
    def INPUT_TYPES(cls):
        lora_folders = cls._get_valid_lora_folders()
        return {
            "required": {
                "lora_folder": (lora_folders, {
                    "tooltip": "Select Wan 2.2 LoRA pair folder. Use [none] to pass through prev_* values."}),
                "high_strength": ("FLOAT", {"default": 1.0, "min": -1000.0, "max": 1000.0, "step": 0.0001,
                                            "tooltip": "High noise LoRA strength"}),
                "enable_high": ("BOOLEAN", {"default": True, "label": "Enable High Noise",
                                            "tooltip": "Enable/disable high noise LoRA"}),
                "low_strength": ("FLOAT", {"default": 1.0, "min": -1000.0, "max": 1000.0, "step": 0.0001,
                                           "tooltip": "Low noise LoRA strength"}),
                "enable_low": (
                "BOOLEAN", {"default": True, "label": "Enable Low Noise", "tooltip": "Enable/disable low noise LoRA"}),
            },
            "optional": {
                "prev_high_lora": ("WANVIDLORA", {"default": None, "tooltip": "Chain high noise LoRAs"}),
                "prev_low_lora": ("WANVIDLORA", {"default": None, "tooltip": "Chain low noise LoRAs"}),
                "prev_trigger_words": ("STRING", {"forceInput": True}),
                "blocks": ("SELECTEDBLOCKS",),
                "low_mem_load": ("BOOLEAN", {"default": False, "tooltip": "Load LoRA with less VRAM"}),
                "merge_loras": ("BOOLEAN", {"default": False, "tooltip": "Merge LoRAs into model"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("WANVIDLORA", "WANVIDLORA", "STRING")
    RETURN_NAMES = ("high_lora", "low_lora", "trigger_words")
    FUNCTION = "select_lora_pair"
    CATEGORY = f"{CATEGORY_PREFIX}/WanVideo"

    @classmethod
    def _get_valid_lora_folders(cls):
        """Scan wan_loras directory for folders containing valid lora.json."""
        valid_folders = []
        if os.path.exists(WAN_LORAS_FULL_PATH):
            for root, dirs, files in os.walk(WAN_LORAS_FULL_PATH):
                if "lora.json" not in files:
                    continue

                json_path = os.path.join(root, "lora.json")
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    lora_config = metadata.get("lora", {})
                    has_high = "high_noise" in lora_config or "high" in lora_config
                    has_low = "low_noise" in lora_config or "low" in lora_config

                    if not has_high and not has_low:
                        continue

                    rel_path = os.path.relpath(root, WAN_LORAS_FULL_PATH)
                    if rel_path == ".":
                        continue

                    valid_folders.append(rel_path.replace("\\", "/"))
                except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                    continue

        valid_folders.sort()
        return ["[none]"] + valid_folders

    @classmethod
    def _merge_trigger_words(cls, prev_words: str, new_words: list) -> str:
        """Merge and deduplicate trigger words while preserving order."""
        prev_list = [w.strip() for w in prev_words.split(",") if w.strip()] if prev_words else []
        seen = set()
        merged = []
        for word in prev_list + new_words:
            word_lower = word.lower()
            if word_lower not in seen:
                seen.add(word_lower)
                merged.append(word)
        return ", ".join(merged)

    def select_lora_pair(self, lora_folder, high_strength, enable_high, low_strength, enable_low,
                         unique_id, blocks=None, prev_high_lora=None, prev_low_lora=None,
                         prev_trigger_words=None, low_mem_load=False, merge_loras=True):

        # Passthrough mode
        if lora_folder == "[none]":
            log(LogEntry(
                node_class="WanVideoLoraPairSelect",
                title="Passthrough mode",
                details={"Folder": "[none]"},
                footer="Returning prev_* inputs unchanged"
            ))
            high_out = prev_high_lora if prev_high_lora is not None else []
            low_out = prev_low_lora if prev_low_lora is not None else []
            trigger_out = prev_trigger_words or ""
            return (high_out, low_out, trigger_out)

        if blocks is None:
            blocks = {}
        if not merge_loras:
            low_mem_load = False

        folder_path = os.path.join(WAN_LORAS_FULL_PATH, lora_folder.replace("/", os.sep))
        json_path = os.path.join(folder_path, "lora.json")

        # Load and normalize metadata
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_metadata = json.load(f)

            metadata = {}
            for key, value in raw_metadata.items():
                clean_key = key.strip()
                if isinstance(value, str):
                    metadata[clean_key] = value.strip()
                elif isinstance(value, dict):
                    clean_dict = {}
                    for k, v in value.items():
                        k_clean = k.strip()
                        if k_clean in ("high", "high_noise"):
                            clean_dict["high_noise"] = v.strip() if isinstance(v, str) else v
                        elif k_clean in ("low", "low_noise"):
                            clean_dict["low_noise"] = v.strip() if isinstance(v, str) else v
                        else:
                            clean_dict[k_clean] = v.strip() if isinstance(v, str) else v
                    metadata[clean_key] = clean_dict
                elif isinstance(value, list):
                    metadata[clean_key] = [item.strip() if isinstance(item, str) else item for item in value]
                else:
                    metadata[clean_key] = value
        except Exception as e:
            log(LogEntry(
                node_class="WanVideoLoraPairSelect",
                title="Failed to load lora.json",
                details={"Folder": lora_folder, "Error": str(e)},
                footer="Returning empty outputs"
            ))
            return ([], [], f"Error: {e}")

        lora_name = metadata.get("name", os.path.basename(lora_folder))
        lora_config = metadata.get("lora", {})
        high_filename = lora_config.get("high_noise")
        low_filename = lora_config.get("low_noise")
        trigger_words = metadata.get("trigger_words", [])

        high_path = os.path.join(folder_path, high_filename) if high_filename else None
        low_path = os.path.join(folder_path, low_filename) if low_filename else None
        high_exists = high_path and os.path.exists(high_path)
        low_exists = low_path and os.path.exists(low_path)

        if not high_exists and not low_exists:
            log(LogEntry(
                node_class="WanVideoLoraPairSelect",
                title="No valid LoRA files found",
                details={"Folder": lora_folder},
                footer="Returning empty outputs"
            ))
            return ([], [], "Error: No valid LoRA files found")

        def build_lora_dict(path, name, strength, blocks_dict, low_mem, merge):
            return {
                "path": path,
                "strength": round(strength, 4) if isinstance(strength, (int, float)) else strength,
                "name": name,
                "blocks": blocks_dict.get("selected_blocks", {}),
                "layer_filter": blocks_dict.get("layer_filter", ""),
                "low_mem_load": low_mem,
                "merge_loras": merge,
            }

        # Build high noise list
        high_loras = []
        high_str = round(high_strength, 4) if isinstance(high_strength, (int, float)) else high_strength
        high_was_used = False

        if enable_high and high_exists and isinstance(high_str, (int, float)) and high_str != 0.0:
            if prev_high_lora:
                high_loras.extend(prev_high_lora)
            high_rel_name = f"wan_loras/{lora_folder}/{os.path.splitext(high_filename)[0]}"
            high_loras.append(build_lora_dict(high_path, high_rel_name, high_str, blocks, low_mem_load, merge_loras))
            high_was_used = True
        elif prev_high_lora:
            high_loras.extend(prev_high_lora)

        # Build low noise list
        low_loras = []
        low_str = round(low_strength, 4) if isinstance(low_strength, (int, float)) else low_strength
        low_was_used = False

        if enable_low and low_exists and isinstance(low_str, (int, float)) and low_str != 0.0:
            if prev_low_lora:
                low_loras.extend(prev_low_lora)
            low_rel_name = f"wan_loras/{lora_folder}/{os.path.splitext(low_filename)[0]}"
            low_loras.append(build_lora_dict(low_path, low_rel_name, low_str, blocks, low_mem_load, merge_loras))
            low_was_used = True
        elif prev_low_lora:
            low_loras.extend(prev_low_lora)

        # Merge trigger words
        prev_words = prev_trigger_words or ""
        merged_triggers = self._merge_trigger_words(prev_words, trigger_words) if (
                    high_was_used or low_was_used) else prev_words

        # UI Metadata display (optional, safe fallback)
        if unique_id and PromptServer is not None:
            try:
                metadata_rows = ""
                for key, value in metadata.items():
                    if key in ("lora", "trigger_words"):
                        continue
                    if isinstance(value, dict):
                        formatted_value = "<pre>" + "\n".join([f"{k}: {v}" for k, v in value.items()]) + "</pre>"
                    elif isinstance(value, (list, tuple)):
                        formatted_value = "<pre>" + "\n".join([str(item) for item in value]) + "</pre>"
                    else:
                        formatted_value = str(value)
                    metadata_rows += f"<tr><td><b>{key}</b></td><td>{formatted_value}</td></tr>"

                raw_triggers_str = ", ".join(trigger_words) if trigger_words else "<i>empty</i>"
                metadata_rows += f"<tr><td><b>📄 Raw Trigger Words (JSON)</b></td><td>{raw_triggers_str}</td></tr>"
                metadata_rows += f"<tr><td><b>🔗 Merged Trigger Words (Output)</b></td><td>{merged_triggers if merged_triggers else '<i>empty</i>'}</td></tr>"

                availability = f"High: {'✅' if high_exists else '❌'}, Low: {'✅' if low_exists else '❌'}"
                status = f"High: {'✅' if high_was_used else '❌'}, Low: {'✅' if low_was_used else '❌'}"

                PromptServer.instance.send_progress_text(
                    f"<details>"
                    f"<summary><b>{lora_name}</b> <small>({lora_folder})</small></summary>"
                    f"<table border='0' cellpadding='3' style='font-size:12px'>"
                    f"<tr><td colspan='2'><small>Available: {availability}</small></td></tr>"
                    f"<tr><td colspan='2'><small>Active: {status}</small></td></tr>"
                    f"{metadata_rows}"
                    f"</table>"
                    f"</details>",
                    unique_id
                )
            except Exception:
                pass

        log(LogEntry(
            node_class="WanVideoLoraPairSelect",
            title=f"Loaded pair: {lora_name}",
            details={
                "Folder": lora_folder,
                "High Active": high_was_used,
                "Low Active": low_was_used,
                "Triggers Merged": len(merged_triggers.split(", ")) if merged_triggers else 0
            },
            footer="Ready for WanVideoLoraLoader"
        ))

        return (high_loras, low_loras, merged_triggers)