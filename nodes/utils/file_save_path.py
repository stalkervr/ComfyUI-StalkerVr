from pathlib import Path
from datetime import datetime
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class FileSavePath:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "project_root": ("STRING", {
                    "default": "/home/stalkervr/AiProjects",
                    "multiline": False,
                    "tooltip": "Base directory for all projects"
                }),
                "project_name": ("STRING", {
                    "default": "Test",
                    "multiline": False,
                    "tooltip": "Name of the current project (creates subfolder)"
                }),
                "sub_folder_name": ("STRING", {
                    "default": "image",
                    "multiline": False,
                    "tooltip": "Content type folder: image, video, audio, etc."
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("save_path", "project_name")
    FUNCTION = "build_path"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"

    def build_path(self, project_root, project_name, sub_folder_name):
        log(LogEntry(
            node_class="FileSavePath",
            title="Building path",
            details={
                "Root": project_root,
                "Project": project_name,
                "Subfolder": sub_folder_name.strip()
            }
        ))
        try:
            base_path = Path(project_root).expanduser().resolve()
            full_path = base_path / project_name / sub_folder_name.strip()
            date_string = datetime.now().strftime("%Y-%m-%d")
            full_path = full_path / date_string
            path_str = str(full_path)

            log(LogEntry(
                node_class="FileSavePath",
                title="Path generated",
                details={"Final Path": path_str},
                footer="Returning save path and project name"
            ))
            return (path_str, project_name)

        except Exception as e:
            log(LogEntry(
                node_class="FileSavePath",
                title="Path build failed",
                details={"Error": str(e)}
            ))
            return (f"Error building path: {e}", project_name)