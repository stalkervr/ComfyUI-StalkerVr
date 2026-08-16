import os
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class FileNameExtractor:
    """
    Extracts the filename from a given file path.
    Optionally strips the file extension.
    Passes through the original path unchanged.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {
                    "default": "",
                    "tooltip": "Full file path to extract filename from"
                }),
                "strip_extension": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If True, returns filename without extension (e.g., 'model' instead of 'model.gguf')"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("file_name", "path_passthrough")
    FUNCTION = "extract"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def extract(self, path: str, strip_extension: bool = False):
        """
        Extracts the base filename from the path, optionally removing the extension.

        Args:
            path (str): The full file path.
            strip_extension (bool): Whether to remove the file extension.

        Returns:
            tuple[str, str]: (filename, original_path)
        """
        if not path or not isinstance(path, str):
            log(LogEntry(
                node_class="FileNameExtractor",
                title="Invalid input",
                details={"Reason": "Empty or non-string path provided"}
            ))
            return ("", path)

        # Получаем имя файла из пути
        full_name = os.path.basename(path.strip())

        # Если нужно убрать расширение
        if strip_extension and full_name:
            # splitext разделяет на (root, ext), нам нужен root
            file_name = os.path.splitext(full_name)[0]
        else:
            file_name = full_name

        log(LogEntry(
            node_class="FileNameExtractor",
            title="Filename extracted",
            details={
                "Original Path": path,
                "Extracted Name": file_name,
                "Extension Stripped": strip_extension
            }
        ))

        return (file_name, path)