import os
import re
from datetime import datetime
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class SaveTextFile:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "project_root": ("STRING", {
                    "multiline": False,
                    "default": "/home/stalkervr/AiProjects",
                    "tooltip": "Base directory for all projects"
                }),
                "folder_path": ("STRING", {
                    "multiline": False,
                    "default": "%date:yyyy-MM-dd%",
                    "tooltip": "Subfolder path. Supports %date:FORMAT% placeholders"
                }),
                "file_name": ("STRING", {
                    "multiline": False,
                    "default": "prompt_collection",
                    "tooltip": "Base filename. Supports %date:FORMAT% placeholders"
                }),
                "extension": ([".txt", ".json", ".info", ".meta", ".log"], {"default": ".txt"}),
            },
            "optional": {
                "text": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "forceInput": True,
                    "tooltip": "Text content to save"
                }),
                "use_numbering": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Always use sequential numbering, or fallback if file exists"
                }),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "save_text_file"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"

    def _format_date_in_path(self, path_template: str) -> str:
        """Replace %date:FORMAT% placeholders with current system time."""
        now = datetime.now()
        def replace_match(match):
            fmt = match.group(1)
            py_fmt = (fmt.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")
                      .replace("HH", "%H").replace("hh", "%H").replace("mm", "%M").replace("ss", "%S"))
            return now.strftime(py_fmt)
        return re.sub(r"%date:([^%]+)%", replace_match, path_template)

    def _get_next_numbered_filename(self, directory: str, base_name: str, extension: str) -> str:
        """Find next available filename with pattern: base_name_00001.ext."""
        if not extension.startswith("."): extension = "." + extension
        pattern = re.compile(rf"^{re.escape(base_name)}_(\d+){re.escape(extension)}$")
        existing_numbers = []
        try:
            for filename in os.listdir(directory):
                match = pattern.match(filename)
                if match: existing_numbers.append(int(match.group(1)))
        except FileNotFoundError: pass
        next_num = max(existing_numbers, default=0) + 1
        return f"{base_name}_{next_num:05d}{extension}"

    def _strip_existing_extension(self, filename: str) -> str:
        """Remove existing extension from filename if present."""
        for ext in [".txt", ".json", ".info", ".meta", ".log"]:
            if filename.endswith(ext): return filename[:-len(ext)]
        return filename

    def _file_exists(self, directory: str, base_name: str, extension: str) -> bool:
        """Check if exact filename exists in directory."""
        if not extension.startswith("."): extension = "." + extension
        return os.path.exists(os.path.join(directory, f"{base_name}{extension}"))

    def save_text_file(self, project_root, folder_path, file_name, extension, text="", use_numbering=False):
        if not file_name or not file_name.strip():
            raise ValueError("file_name is required and cannot be empty")

        if not text or not text.strip():
            log(LogEntry(node_class="SaveTextFile", title="Skipped save", details={"Reason": "Empty or whitespace-only text"}))
            return {"ui": {}}

        try:
            if not extension.startswith("."): extension = "." + extension

            formatted_root = self._format_date_in_path(project_root.strip())
            formatted_folder = self._format_date_in_path(folder_path.strip()) if folder_path else ""
            formatted_filename = self._format_date_in_path(file_name.strip())
            formatted_filename = self._strip_existing_extension(formatted_filename)

            output_dir = os.path.join(formatted_root, formatted_folder) if formatted_folder else formatted_root
            os.makedirs(output_dir, exist_ok=True)

            if use_numbering:
                final_filename = self._get_next_numbered_filename(output_dir, formatted_filename, extension)
                log(LogEntry(node_class="SaveTextFile", title="Numbering enabled", details={"Filename": final_filename}))
            else:
                if self._file_exists(output_dir, formatted_filename, extension):
                    final_filename = self._get_next_numbered_filename(output_dir, formatted_filename, extension)
                    log(LogEntry(node_class="SaveTextFile", title="Auto-numbering applied", details={"Filename": final_filename, "Reason": "File exists"}))
                else:
                    final_filename = f"{formatted_filename}{extension}"
                    log(LogEntry(node_class="SaveTextFile", title="Exact filename used", details={"Filename": final_filename}))

            full_path = os.path.join(output_dir, final_filename)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(text)

            log(LogEntry(node_class="SaveTextFile", title="File saved successfully", details={"Path": full_path}))
            return {"ui": {}}

        except Exception as e:
            log(LogEntry(node_class="SaveTextFile", title="Save failed", details={"Error": str(e)}))
            raise type(e)(f"Failed to save file: {e}")