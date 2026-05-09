import json
import os
import random
import traceback
from pathlib import Path
from ...common.constants import CATEGORY_PREFIX
from ...common.types import Everything
from ...common.logger import LogEntry, log

class JsonPathLoader:
    """
    JsonPathLoader
    --------------
    Loads all JSON files from a folder.
    Cache is disabled - folder is rescanned on every execution.
    Supports file sorting and quantity limits.
    Dynamically infers output type.
    """

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return random.random()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"multiline": False, "default": ""}),
            },
            "optional": {
                "sort_by": (
                    ["name", "name_desc", "created", "created_desc", "modified", "modified_desc", "size", "size_desc"], {
                        "default": "name",
                        "label": "Sort By",
                        "tooltip": "Sort files by: name, created date, modified date, or size (ascending or descending)"
                    }),
                "limit": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 1,
                    "label": "File Limit",
                    "tooltip": "Max number of files to load (0 = unlimited)"
                }),
            },
        }

    RETURN_TYPES = (Everything("*"),)
    RETURN_NAMES = ("output",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "load"
    CATEGORY = f"{CATEGORY_PREFIX}/JSON"

    def _sort_files(self, files, sort_by):
        if sort_by == "name":
            return sorted(files, key=lambda f: f.name.lower())
        elif sort_by == "name_desc":
            return sorted(files, key=lambda f: f.name.lower(), reverse=True)
        elif sort_by == "created":
            return sorted(files, key=lambda f: f.stat().st_ctime)
        elif sort_by == "created_desc":
            return sorted(files, key=lambda f: f.stat().st_ctime, reverse=True)
        elif sort_by == "modified":
            return sorted(files, key=lambda f: f.stat().st_mtime)
        elif sort_by == "modified_desc":
            return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
        elif sort_by == "size":
            return sorted(files, key=lambda f: f.stat().st_size)
        elif sort_by == "size_desc":
            return sorted(files, key=lambda f: f.stat().st_size, reverse=True)
        else:
            return sorted(files, key=lambda f: f.name.lower())

    def _infer_return_type(self, items):
        if not items:
            return (Everything("*"),)

        all_int = all(isinstance(v, int) and not isinstance(v, bool) for v in items)
        all_float = all(isinstance(v, float) for v in items)
        all_str = all(isinstance(v, str) for v in items)

        if all_int:
            return ("INT",)
        elif all_float:
            return ("FLOAT",)
        elif all_str:
            return ("STRING",)
        else:
            return (Everything("*"),)

    def load(self, folder_path, sort_by="name", limit=0):
        log(LogEntry(
            node_class="JsonPathLoader",
            title="Scan started",
            details={"Path": folder_path, "Sort": sort_by, "Limit": "unlimited" if limit == 0 else limit}
        ))

        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            log(LogEntry(
                node_class="JsonPathLoader",
                title="Invalid path",
                details={"Path": folder_path},
                footer="Returning empty list"
            ))
            self.RETURN_TYPES = (Everything("*"),)
            return ([],)

        json_files = list(folder.glob("*.json"))
        log(LogEntry(
            node_class="JsonPathLoader",
            title="Files found",
            details={"Count": len(json_files)}
        ))

        sorted_files = self._sort_files(json_files, sort_by)
        log(LogEntry(
            node_class="JsonPathLoader",
            title="Sorting applied",
            details={"Criteria": sort_by}
        ))

        if limit > 0:
            sorted_files = sorted_files[:limit]
            log(LogEntry(
                node_class="JsonPathLoader",
                title="Limit applied",
                details={"Files processed": len(sorted_files)}
            ))

        output_list = []

        for file in sorted_files:
            try:
                size_kb = round(os.path.getsize(file) / 1024, 2)
                log(LogEntry(
                    node_class="JsonPathLoader",
                    title="Processing file",
                    details={"File": file.name, "Size KB": size_kb}
                ))

                raw_text = file.read_text(encoding="utf-8")
                log(LogEntry(
                    node_class="JsonPathLoader",
                    title="File read",
                    details={"Chars": len(raw_text)}
                ))

                parsed = json.loads(raw_text)
                formatted = json.dumps(parsed, ensure_ascii=False, indent=4)
                output_list.append(formatted)
                log(LogEntry(
                    node_class="JsonPathLoader",
                    title="Loaded successfully",
                    details={"File": file.name}
                ))

            except Exception as e:
                log(LogEntry(
                    node_class="JsonPathLoader",
                    title="File error",
                    details={"File": file.name, "Error": str(e)},
                    footer="Traceback logged to console"
                ))
                traceback.print_exc()

        log(LogEntry(
            node_class="JsonPathLoader",
            title="Scan completed",
            details={"Total loaded": len(output_list)},
            footer="Returning output list"
        ))

        self.RETURN_TYPES = self._infer_return_type(output_list)
        return (output_list,)