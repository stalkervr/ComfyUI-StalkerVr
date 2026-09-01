import os
import re
from pathlib import Path
from datetime import datetime
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class TextSaveToFile:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "project_root": ("STRING", {
                    "multiline": False,
                    "default": "/home/stalkervr/AiProjects",
                    "tooltip": "Base directory for all projects"
                }),
                "project_name": ("STRING", {
                    "multiline": False,
                    "default": "Test",
                    "tooltip": "Name of the current project (creates subfolder)"
                }),
                "sub_folder_name": ("STRING", {
                    "multiline": False,
                    "default": "text",
                    "tooltip": "Content type folder: text, prompts, logs, etc."
                }),
                "file_name": ("STRING", {
                    "multiline": False,
                    "default": "prompt_collection",
                    "tooltip": "Base filename. Supports %date:FORMAT% placeholders"
                }),
                "use_date_folder": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Append current date (YYYY-MM-DD) to the path"
                }),
                "extension": ([".txt", ".json", ".info", ".meta", ".log"], {"default": ".txt"}),
                "append_mode": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If enabled, append text to a single file instead of creating new ones"
                }),
                "separator": ("STRING", {
                    "default": "\n--\n",
                    "tooltip": "Separator used between entries in append mode"
                }),
            },
            "optional": {
                "text": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "forceInput": True,
                    "tooltip": "Text content to save"
                }),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "save_text_file"
    CATEGORY = f"{CATEGORY_PREFIX}/Text"

    def _format_date_in_path(self, path_template: str) -> str:
        """Replace %date:FORMAT% placeholders with current system time."""
        now = datetime.now()

        def replace_match(match):
            fmt = match.group(1)
            py_fmt = (fmt.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")
                      .replace("HH", "%H").replace("hh", "%H").replace("mm", "%M").replace("ss", "%S"))
            return now.strftime(py_fmt)

        return re.sub(r"%date:([^%]+)%", replace_match, path_template)

    def _strip_existing_extension(self, filename: str) -> str:
        """Remove existing extension from filename if present."""
        for ext in [".txt", ".json", ".info", ".meta", ".log"]:
            if filename.endswith(ext): return filename[:-len(ext)]
        return filename

    def save_text_file(self, project_root, project_name, sub_folder_name, file_name,
                       use_date_folder, extension, append_mode, separator, text=""):
        if not file_name or not file_name.strip():
            raise ValueError("file_name is required and cannot be empty")

        if not text or not text.strip():
            log(LogEntry(node_class="SaveTextFile", title="Skipped save",
                         details={"Reason": "Empty or whitespace-only text"}))
            return {"ui": {}}

        try:
            if not extension.startswith("."): extension = "." + extension

            # Формируем базовый путь
            base_path = Path(project_root).expanduser().resolve()
            full_path_obj = base_path / project_name / sub_folder_name.strip()

            if use_date_folder:
                date_string = datetime.now().strftime("%Y-%m-%d")
                full_path_obj = full_path_obj / date_string

            # Применяем плейсхолдеры даты к имени файла
            formatted_filename = self._format_date_in_path(file_name.strip())
            formatted_filename = self._strip_existing_extension(formatted_filename)

            final_filename = f"{formatted_filename}{extension}"
            output_dir = str(full_path_obj)
            os.makedirs(output_dir, exist_ok=True)
            full_path = os.path.join(output_dir, final_filename)

            if append_mode:
                # Режим добавления в один файл
                mode = "a" if os.path.exists(full_path) else "w"
                with open(full_path, mode, encoding="utf-8") as f:
                    # Если файл уже существует и не пуст, добавляем разделитель перед новым текстом
                    if mode == "a" and os.path.getsize(full_path) > 0:
                        f.write(separator)
                    f.write(text)
                log(LogEntry(node_class="SaveTextFile", title="Appended to file", details={"Path": full_path}))
            else:
                # Режим создания уникальных файлов с нумерацией
                numbered_filename = self._get_next_numbered_filename(output_dir, formatted_filename, extension)
                full_path = os.path.join(output_dir, numbered_filename)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(text)
                log(LogEntry(node_class="SaveTextFile", title="Saved unique file",
                             details={"Filename": numbered_filename}))

            log(LogEntry(node_class="SaveTextFile", title="Operation completed", details={"Path": full_path}))
            return {"ui": {}}

        except Exception as e:
            log(LogEntry(node_class="SaveTextFile", title="Save failed", details={"Error": str(e)}))
            raise type(e)(f"Failed to save file: {e}")

    def _get_next_numbered_filename(self, directory: str, base_name: str, extension: str) -> str:
        """Find next available filename ensuring uniqueness against existing files."""
        if not extension.startswith("."): extension = "." + extension

        numbered_pattern = re.compile(rf"^{re.escape(base_name)}_(\d+){re.escape(extension)}$")
        exact_pattern = re.compile(rf"^{re.escape(base_name)}{re.escape(extension)}$")

        existing_numbers = []
        has_exact_match = False

        try:
            for filename in os.listdir(directory):
                if exact_pattern.match(filename):
                    has_exact_match = True
                else:
                    match = numbered_pattern.match(filename)
                    if match:
                        existing_numbers.append(int(match.group(1)))
        except FileNotFoundError:
            pass

        start_num = 1
        if existing_numbers:
            start_num = max(existing_numbers) + 1
        elif has_exact_match:
            start_num = 1

        return f"{base_name}_{start_num:05d}{extension}"