import os
from pathlib import Path
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class TextLoadFromDirectory:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": "",
                    "tooltip": "Path to the directory containing text files"
                }),
                "extension": ([".txt", ".json", ".info", ".meta", ".log"], {"default": ".txt"}),
                "mode": (["single", "split"], {
                    "default": "single",
                    "tooltip": "Single: one string per file. Split: divide all content by separator into a flat list."
                }),
                "sort_by": (["name", "date"], {
                    "default": "name",
                    "tooltip": "Sort order for processing files"
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
    FUNCTION = "load_texts"
    CATEGORY = f"{CATEGORY_PREFIX}/Text"
    OUTPUT_IS_LIST = (True,)

    def load_texts(self, directory_path, extension, mode="single", sort_by="name", separator="\n--\n"):
        if not directory_path or not directory_path.strip():
            raise ValueError("Directory path is required")

        dir_path = Path(directory_path).expanduser().resolve()
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")

        # Поиск файлов
        files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() == extension.lower()]

        if not files:
            log(LogEntry(node_class="TextLoadFromDirectory", title="No files found",
                         details={"Path": str(dir_path), "Ext": extension}))
            return ([],)

        # Сортировка
        if sort_by == "name":
            files.sort(key=lambda x: x.name)
        elif sort_by == "date":
            files.sort(key=lambda x: x.stat().st_mtime)

        final_list = []

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if mode == "split":
                    # Разбиваем содержимое файла и добавляем части в общий список
                    if separator:
                        parts = content.split(separator)
                        # Добавляем только непустые части, если нужно, или все подряд
                        final_list.extend(parts)
                    else:
                        final_list.append(content)
                else:
                    # Режим single: добавляем содержимое файла как один элемент
                    final_list.append(content)

            except Exception as e:
                log(LogEntry(node_class="TextLoadFromDirectory", title="Skipped file",
                             details={"File": file_path.name, "Error": str(e)}))
                continue

        log(LogEntry(
            node_class="TextLoadFromDirectory",
            title="Loaded files",
            details={"Count": len(files), "Mode": mode, "Total Items": len(final_list)}
        ))

        return (final_list,)