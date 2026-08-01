import os
from pathlib import Path
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class TextLoadFromFile:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "Absolute or relative path to the text file"
                }),
                "mode": (["single", "split"], {
                    "default": "single",
                    "tooltip": "Single: read whole file. Split: divide by separator into a list."
                }),
            },
            "optional": {
                "separator": ("STRING", {
                    "default": "\n--\n",
                    "tooltip": "Delimiter used to split text in 'split' mode"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "load_text"
    CATEGORY = f"{CATEGORY_PREFIX}/Text"
    OUTPUT_IS_LIST = (True,)  # Всегда возвращаем список для совместимости с batch-нодами

    def load_text(self, file_path, mode="single", separator="\n--\n"):
        if not file_path or not file_path.strip():
            raise ValueError("File path is required")

        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        supported_ext = {'.txt', '.json', '.info', '.meta', '.log'}
        if path.suffix.lower() not in supported_ext:
            raise ValueError(f"Unsupported extension: {path.suffix}. Supported: {supported_ext}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            log(LogEntry(
                node_class="TextLoadFromFile",
                title="File loaded",
                details={"Path": str(path), "Size": len(content)}
            ))

            if mode == "split":
                if not separator:
                    # Если разделитель пустой, возвращаем список из одного элемента
                    result_list = [content]
                else:
                    # Разбиваем текст и убираем пустые элементы в начале/конце если нужно
                    parts = content.split(separator)
                    # Опционально: можно убрать пустые строки, если они не нужны
                    # result_list = [p for p in parts if p.strip()]
                    result_list = parts

                log(LogEntry(
                    node_class="TextLoadFromFile",
                    title="Split mode",
                    details={"Parts count": len(result_list)}
                ))
                return (result_list,)
            else:
                # В режиме single тоже возвращаем список из одного элемента для consistency
                return ([content],)

        except Exception as e:
            log(LogEntry(node_class="TextLoadFromFile", title="Load failed", details={"Error": str(e)}))
            raise type(e)(f"Failed to load file: {e}")