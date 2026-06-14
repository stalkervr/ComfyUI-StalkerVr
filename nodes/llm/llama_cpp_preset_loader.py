import json
import os

from ...common.constants import CATEGORY_PREFIX
from ...config.config_manager import ConfigManager


class LlamaPresetLoader:

    @staticmethod
    def get_presets_dir():

        extension_root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                ".."
            )
        )

        path = ConfigManager().get(
            "llm.presets_path",
            "data/llm/presets"
        )

        presets_dir = os.path.join(
            extension_root,
            path
        )

        os.makedirs(
            presets_dir,
            exist_ok=True
        )

        return presets_dir

    @classmethod
    def get_preset_files(cls):

        presets_dir = cls.get_presets_dir()

        allowed_extensions = (
            ".json",
        )

        files = []

        for root, _, filenames in os.walk(presets_dir):

            for file_name in filenames:

                if not file_name.lower().endswith(
                    allowed_extensions
                ):
                    continue

                full_path = os.path.join(
                    root,
                    file_name
                )

                relative_path = os.path.relpath(
                    full_path,
                    presets_dir
                )

                relative_path = relative_path.replace(
                    "\\",
                    "/"
                )

                files.append(relative_path)

        files.sort()

        return ["none"] + files

    @classmethod
    def INPUT_TYPES(cls):

        return {
            "required": {

                "preset_file": (
                    cls.get_preset_files(),
                    {}
                ),
            }
        }

    RETURN_TYPES = (
        "INT",  # max_tokens
        "INT",  # context_length
        "INT",  # gpu_layers
        "FLOAT",   # temperature
        "FLOAT",   # top_p
        "INT",     # top_k
        "FLOAT",   # min_p
        "FLOAT",   # repeat_penalty
        "FLOAT",   # presence_penalty
        "FLOAT",   # frequency_penalty

        # "BOOLEAN", # enable_thinking
    )

    RETURN_NAMES = (
        "max_tokens",
        "context_length",
        "gpu_layers",
        "temperature",
        "top_p",
        "top_k",
        "min_p",
        "repeat_penalty",
        "presence_penalty",
        "frequency_penalty",

        # "enable_thinking",
    )

    FUNCTION = "load_preset"
    CATEGORY = f"{CATEGORY_PREFIX}/LLM"

    def load_preset(self, preset_file):

        defaults = {
            "max_tokens": 1024,
            "context_length": 4096,
            "gpu_layers": -1,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "min_p": 0.05,
            "repeat_penalty": 1.1,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            # "enable_thinking": False,
        }

        if preset_file == "none":

            return (
                defaults["max_tokens"],
                defaults["context_length"],
                defaults["gpu_layers"],
                defaults["temperature"],
                defaults["top_p"],
                defaults["top_k"],
                defaults["min_p"],
                defaults["repeat_penalty"],
                defaults["presence_penalty"],
                defaults["frequency_penalty"],

                # defaults["enable_thinking"],
            )

        presets_dir = self.get_presets_dir()

        full_path = os.path.join(
            presets_dir,
            preset_file
        )

        if not os.path.exists(full_path):

            raise Exception(
                f"Preset file not found: {full_path}"
            )

        with open(
            full_path,
            "r",
            encoding="utf-8"
        ) as file:

            preset = json.load(file)

        return (
            preset.get(
                "max_tokens",
                defaults["max_tokens"]
            ),

            preset.get(
                "context_length",
                defaults["context_length"]
            ),

            preset.get(
                "gpu_layers",
                defaults["gpu_layers"]
            ),
            preset.get(
                "temperature",
                defaults["temperature"]
            ),

            preset.get(
                "top_p",
                defaults["top_p"]
            ),

            preset.get(
                "top_k",
                defaults["top_k"]
            ),

            preset.get(
                "min_p",
                defaults["min_p"]
            ),

            preset.get(
                "repeat_penalty",
                defaults["repeat_penalty"]
            ),

            preset.get(
                "presence_penalty",
                defaults["presence_penalty"]
            ),

            preset.get(
                "frequency_penalty",
                defaults["frequency_penalty"]
            ),

            # preset.get(
            #     "enable_thinking",
            #     defaults["enable_thinking"]
            # ),
        )