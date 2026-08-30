import json
import os
import hashlib

from ...common.constants import CATEGORY_PREFIX
from ...config.config_manager import ConfigManager
from ...common.logger import LogEntry, log_start, log_end


class LlamaPresetLoader:

    # ==================== ПРЕСЕТЫ (ИЗ КОНФИГУРАЦИИ) ====================
    @classmethod
    def get_presets_dirs(cls):
        raw = ConfigManager().get("llm.presets_path", "data/llm/presets")

        if isinstance(raw, str):
            raw = [raw]
        if not isinstance(raw, list):
            raw = ["data/llm/presets"]

        extension_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        dirs = []
        for path in raw:
            if not isinstance(path, str) or not path.strip():
                continue
            path = path.strip()
            if os.path.isabs(path):
                # Абсолютные пути НЕ создаем — они должны существовать (mounted volumes)
                presets_dir = path
            else:
                presets_dir = os.path.join(extension_root, path)
                try:
                    os.makedirs(presets_dir, exist_ok=True)
                except (PermissionError, OSError) as e:
                    print(f"[ComfyUI-StalkerVr] ⚠️ Cannot create presets dir {presets_dir}: {e}")
            if presets_dir not in dirs:
                dirs.append(presets_dir)

        return dirs

    @classmethod
    def get_preset_full_path(cls, rel_path):
        """
        Разрешает относительный путь в абсолютный.
        Проходит каталоги по порядку и возвращает первый существующий файл.
        """
        for presets_dir in cls.get_presets_dirs():
            full = os.path.join(presets_dir, rel_path)
            if os.path.exists(full):
                return full
        # Fallback: первый каталог из списка
        dirs = cls.get_presets_dirs()
        return os.path.join(dirs[0], rel_path) if dirs else rel_path

    @classmethod
    def get_preset_files(cls):
        """
        Рекурсивно сканирует ВСЕ каталоги шаблонов.
        Возвращает относительные пути всех .json файлов (без дубликатов).
        Приоритет: первый каталог в списке.
        """
        allowed_extensions = (".json",)
        files = []

        for presets_dir in cls.get_presets_dirs():
            if not os.path.isdir(presets_dir):
                continue
            for root, _, filenames in os.walk(presets_dir):
                for file_name in filenames:
                    if not file_name.lower().endswith(allowed_extensions):
                        continue
                    full_path = os.path.join(root, file_name)
                    relative_path = os.path.relpath(full_path, presets_dir)
                    relative_path = relative_path.replace("\\", "/")
                    if relative_path not in files:
                        files.append(relative_path)

        files.sort()
        return ["none"] + files
    # ==================== ПРЕСЕТЫ (ИЗ КОНФИГУРАЦИИ) ====================

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "preset_file": (cls.get_preset_files(), {}),
            }
        }

    RETURN_TYPES = (
        "FLOAT",
        "FLOAT",
        "INT",
        "FLOAT",
        "FLOAT",
        "FLOAT",
        "FLOAT",
    )

    RETURN_NAMES = (
        "temperature",
        "top_p",
        "top_k",
        "min_p",
        "repeat_penalty",
        "presence_penalty",
        "frequency_penalty",
    )

    FUNCTION = "load_preset"
    CATEGORY = f"{CATEGORY_PREFIX}/LLM"

    @classmethod
    def IS_CHANGED(cls, preset_file="none", **kwargs):
        """
        Отслеживание реальных изменений (без ложных перезапусков):
        - сменили шаблон в dropdown -> перезапуск (изменился вход)
        - отредактировали JSON на диске -> перезапуск (изменился хеш)
        - ничего не менялось -> кеш ComfyUI, цепочка НЕ перезапускается
        """
        if not preset_file or preset_file == "none":
            return "none"

        full_path = cls.get_preset_full_path(preset_file)
        if not os.path.exists(full_path):
            return f"missing:{preset_file}"

        h = hashlib.md5()
        with open(full_path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()

    def load_preset(self, preset_file):
        defaults = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "min_p": 0.05,
            "repeat_penalty": 1.1,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
        }

        if preset_file == "none":
            log_start(LogEntry(
                node_class="LlamaPresetLoader",
                title="START",
                details={"preset_file": "none (defaults)"}
            ))
            log_end(LogEntry(
                node_class="LlamaPresetLoader",
                title="DONE",
                details=defaults
            ))
            return (
                defaults["temperature"],
                defaults["top_p"],
                defaults["top_k"],
                defaults["min_p"],
                defaults["repeat_penalty"],
                defaults["presence_penalty"],
                defaults["frequency_penalty"],
            )

        full_path = self.get_preset_full_path(preset_file)

        if not os.path.exists(full_path):
            raise Exception(f"Preset file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as file:
            preset = json.load(file)

        loaded = {key: preset.get(key, defaults[key]) for key in defaults}

        log_start(LogEntry(
            node_class="LlamaPresetLoader",
            title="START",
            details={"preset_file": preset_file, "full_path": full_path}
        ))
        log_end(LogEntry(
            node_class="LlamaPresetLoader",
            title="DONE",
            details=loaded
        ))

        return (
            loaded["temperature"],
            loaded["top_p"],
            loaded["top_k"],
            loaded["min_p"],
            loaded["repeat_penalty"],
            loaded["presence_penalty"],
            loaded["frequency_penalty"],
        )