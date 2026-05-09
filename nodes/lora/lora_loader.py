import os
import folder_paths
import comfy.utils
import comfy.sd
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class LoraLoaderExtended:
    """
    Loads a single LoRA with enable toggle and name chaining.
    Uses centralized logging and config management.
    """

    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        file_list = folder_paths.get_filename_list("loras")
        file_list.insert(0, "None")
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_name": (file_list,),
                "enable_lora": ("BOOLEAN", {"default": True, "label": "Enable LoRA"}),
                "strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            },
            "optional": {
                "name_string": ("STRING", {"forceInput": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "NAME_STRING")
    FUNCTION = "load_lora"
    CATEGORY = f"{CATEGORY_PREFIX}/Loaders"

    def load_lora(self, model, clip, lora_name, enable_lora, strength, name_string=""):
        name_string = name_string or ""
        if not enable_lora or lora_name == "None" or strength == 0.0:
            return (model, clip, name_string)

        log(LogEntry(
            node_class="LoraLoaderExtended",
            title="Processing LoRA",
            details={"Name": lora_name, "Strength": f"{strength:.2f}", "Status": "Enabled"},
            footer="LoRA application completed"
        ))

        lora_path = folder_paths.get_full_path("loras", lora_name)
        lora = None
        if self.loaded_lora is not None and self.loaded_lora[0] == lora_path:
            lora = self.loaded_lora[1]
        else:
            self.loaded_lora = None

        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)

        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength, strength)
        current_name = os.path.splitext(lora_name)[0]
        combined = f"{name_string}, {current_name}" if name_string else current_name

        return (model_lora, clip_lora, combined)


class LoraLoaderExtendedBatch:
    """
    Loads up to 5 LoRAs in a single pass.
    Supports per-slot toggles, unified strength, and name chaining.
    """

    def __init__(self):
        self.loaded_loras = {}

    @classmethod
    def INPUT_TYPES(s):
        file_list = folder_paths.get_filename_list("loras")
        file_list.insert(0, "None")
        base_req = {"model": ("MODEL",), "clip": ("CLIP",)}
        for i in range(1, 6):
            base_req[f"lora_name_{i}"] = (file_list, {"tooltip": f"Slot {i} model"})
            base_req[f"enable_{i}"] = ("BOOLEAN", {"default": True, "label": f"Enable Slot {i}"})
            base_req[f"strength_{i}"] = ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01})
        return {
            "required": base_req,
            "optional": {
                "name_string": ("STRING", {"forceInput": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "NAME_STRING")
    FUNCTION = "load_loras"
    CATEGORY = f"{CATEGORY_PREFIX}/Loaders"

    def load_loras(self, model, clip, name_string="",
                   lora_name_1=None, enable_1=True, strength_1=1.0,
                   lora_name_2=None, enable_2=True, strength_2=1.0,
                   lora_name_3=None, enable_3=True, strength_3=1.0,
                   lora_name_4=None, enable_4=True, strength_4=1.0,
                   lora_name_5=None, enable_5=True, strength_5=1.0):

        name_string = name_string or ""
        slots = [
            (lora_name_1, enable_1, strength_1), (lora_name_2, enable_2, strength_2),
            (lora_name_3, enable_3, strength_3), (lora_name_4, enable_4, strength_4),
            (lora_name_5, enable_5, strength_5)
        ]

        for i, (l_name, en, st) in enumerate(slots, 1):
            if not en or l_name in ("None", None) or st == 0.0:
                continue

            log(LogEntry(
                node_class="LoraLoaderExtendedBatch",
                title=f"Processing Slot {i}",
                details={"Name": l_name, "Strength": f"{st:.2f}", "Status": "Enabled"},
                footer="Slot application completed"
            ))

            lora_path = folder_paths.get_full_path("loras", l_name)
            lora = self.loaded_loras.get(lora_path)
            if lora is None:
                lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
                self.loaded_loras[lora_path] = lora

            model, clip = comfy.sd.load_lora_for_models(model, clip, lora, st, st)
            current_name = os.path.splitext(l_name)[0]
            name_string = f"{name_string}, {current_name}" if name_string else current_name

        return (model, clip, name_string)