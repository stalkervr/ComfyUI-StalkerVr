import os
import sys
import re
from datetime import datetime
from pathlib import Path
import torch
import time
import yaml

from .constants import CATEGORY_PREFIX


try:
    import folder_paths
    COMFY_OUTPUT_DIR = folder_paths.get_output_directory()
except Exception:
    COMFY_OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
    COMFY_OUTPUT_DIR = str(COMFY_OUTPUT_DIR.resolve())


class SaveTextFile:
    """
    SaveTextFile
    ------------
    Saves a string to a file with date formatting and sequential numbering.

    File name pattern: <base_name>_NNNNN.<ext>
    Example: 083818_SVI_24_00001.json

    Always uses 5-digit zero-padded numbering starting from 00001.
    Skips saving if input text is empty (only whitespace).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
                "file_path": ("STRING", {"multiline": False, "default": "logs/my_log"}),
                "extension": ([".txt", ".json", ".info", ".meta", ".log"], {"default": ".txt"}),
            }
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "save_text_file"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"

    def _format_date_in_path(self, path_template: str) -> str:
        now = datetime.now()
        def replace_match(match):
            fmt = match.group(1)
            py_fmt = (
                fmt.replace("yyyy", "%Y")
                .replace("MM", "%m")
                .replace("dd", "%d")
                .replace("HH", "%H")
                .replace("hh", "%H")
                .replace("mm", "%M")
                .replace("ss", "%S")
            )
            return now.strftime(py_fmt)

        return re.sub(r"%date:([^%]+)%", replace_match, path_template)

    def _get_next_numbered_filename(self, directory: str, base_name: str, extension: str) -> str:
        """
        Finds the next available filename with pattern: base_name_00001.ext, base_name_00002.ext, ...
        Always starts counting from 1.
        """
        # Ensure extension starts with dot
        if not extension.startswith("."):
            extension = "." + extension

        # Pattern to match: base_name_00001.ext, base_name_123.ext, etc.
        pattern = re.compile(rf"^{re.escape(base_name)}_(\d+){re.escape(extension)}$")

        existing_numbers = []
        try:
            for filename in os.listdir(directory):
                match = pattern.match(filename)
                if match:
                    num = int(match.group(1))
                    existing_numbers.append(num)
        except FileNotFoundError:
            pass  # Directory doesn't exist yet — no files

        next_num = max(existing_numbers, default=0) + 1
        numbered_name = f"{base_name}_{next_num:05d}{extension}"
        return numbered_name

    def save_text_file(self, text: str, file_path: str, extension: str):
        # Check for empty or whitespace-only text
        if not text or not text.strip():
            print("[SaveTextFile] Skipping save: input text is empty or contains only whitespace", file=sys.stderr)
            return {"ui": {}}

        try:
            if not extension.startswith("."):
                extension = "." + extension

            # Format date placeholders in the full path
            formatted_path = self._format_date_in_path(file_path)

            # Split into dir and base filename (without extension)
            dir_part = os.path.dirname(formatted_path)
            base_filename = os.path.basename(formatted_path)

            # If user provided extension in path, strip it
            if any(base_filename.endswith(ext) for ext in [".txt", ".json", ".info", ".meta", ".log"]):
                # Remove known extensions
                for ext in [".txt", ".json", ".info", ".meta", ".log"]:
                    if base_filename.endswith(ext):
                        base_filename = base_filename[:-len(ext)]
                        break

            # Full output directory
            output_dir = os.path.join(COMFY_OUTPUT_DIR, dir_part)
            os.makedirs(output_dir, exist_ok=True)

            # Generate next numbered filename
            final_filename = self._get_next_numbered_filename(output_dir, base_filename, extension)
            full_path = os.path.join(output_dir, final_filename)

            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"[SaveTextFile] Saved: {full_path}", file=sys.stderr)
            return {"ui": {}}

        except Exception as e:
            error_msg = f"[SaveTextFile] ERROR: {e}"
            print(error_msg, file=sys.stderr)
            return {"ui": {}}


class FormatDatePath:
    """
    FormatDatePath
    --------------
    Always returns current time — no caching.
    Uses IS_CHANGED = float('nan') to force re-execution.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template": ("STRING", {"multiline": False, "default": "WAN/%date:yyyy-MM-dd%/svi_test/%date:hhmmss%_SVI_24"}),
            }
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-execution on every run
        return float("nan")

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("formatted_path",)
    FUNCTION = "format_path"
    CATEGORY = "🎯 Stalkervr/IO"

    def format_path(self, template: str):
        now = datetime.now()

        def replace_match(match):
            fmt = match.group(1)
            py_fmt = (
                fmt.replace("yyyy", "%Y")
                   .replace("MM", "%m")
                   .replace("dd", "%d")
                   .replace("HH", "%H")
                   .replace("hh", "%H")
                   .replace("mm", "%M")
                   .replace("ss", "%S")
            )
            return now.strftime(py_fmt)

        try:
            formatted = re.sub(r"%date:([^%]+)%", replace_match, template)
            print(f"[FormatDatePath] Rendered at {now.strftime('%H:%M:%S')}: {formatted}", file=sys.stderr)
            return (formatted,)
        except Exception as e:
            error_str = f"[FormatDatePath ERROR] {e}"
            print(error_str, file=sys.stderr)
            return (error_str,)


class YAMLSavePrompt:
    """
    YAMLSavePrompt
    -------------------------
    Saves prompts to a structured YAML database with hierarchical organization.
    Supports person-name → type → group → sub_group → prompt structure.
    Stores both positive and negative prompts.
    Only saves when enabled (toggle switch).
    Cleans prompt text: removes extra whitespace and line breaks.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "positive_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "dynamicPrompts": False,
                    "tooltip": "Positive prompt text to save"
                }),
                "negative_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "dynamicPrompts": False,
                    "tooltip": "Negative prompt text to save"
                }),
                "save_enabled": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Enable/disable saving (only saves when enabled)"
                }),
                "file_path": ("STRING", {
                    "default": "./prompts_database.yaml",
                    "tooltip": "Path to the YAML database file"
                }),
                "person_name": ("STRING", {
                    "default": "Triksy",
                    "tooltip": "Person/author name for the prompt"
                }),
                "prompt_type": (["text-to-image", "image-to-video"], {
                    "default": "text-to-image",
                    "tooltip": "Type of prompt generation"
                }),
                "group_name": ("STRING", {
                    "default": "main",
                    "tooltip": "Group/category name for organizing prompts"
                }),
                "sub_group_name": ("STRING", {
                    "default": "",
                    "tooltip": "Sub-group name (optional, leave empty for no sub-group)"
                }),
                "prompt_name": ("STRING", {
                    "default": "My Prompt",
                    "tooltip": "Descriptive name for this specific prompt"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "save_prompt_database"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"
    OUTPUT_NODE = True

    def save_prompt_database(self, positive_prompt, negative_prompt, save_enabled, file_path,
                             person_name, prompt_type, group_name, sub_group_name, prompt_name):
        # Always return the original prompts (passthrough)
        result = (positive_prompt, negative_prompt)

        # Only save if enabled
        if not save_enabled:
            print(f"📝 [YAMLSavePrompt] Saving disabled - skipping")
            return result

        # Validate inputs
        if not positive_prompt.strip():
            print(f"⚠️ [YAMLSavePrompt] Warning: Empty positive prompt text - skipping save")
            return result

        if not all([file_path.strip(), person_name.strip(), group_name.strip(), prompt_name.strip()]):
            print(f"⚠️ [SYAMLSavePrompt] Warning: Missing required fields - skipping save")
            return result

        try:
            # Clean the prompt texts
            cleaned_positive = self._clean_prompt_text(positive_prompt)
            cleaned_negative = self._clean_prompt_text(negative_prompt)

            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Load existing database or create new one
            database = self._load_existing_database(file_path)

            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create new prompt entry with both positive and negative prompts
            new_prompt = {
                "date": timestamp,
                "name": prompt_name,
                "positive": cleaned_positive,
                "negative": cleaned_negative
            }

            # Navigate/create the hierarchical structure
            if person_name not in database:
                database[person_name] = {}

            if prompt_type not in database[person_name]:
                database[person_name][prompt_type] = {}

            if group_name not in database[person_name][prompt_type]:
                database[person_name][prompt_type][group_name] = {}

            # Handle subgroup logic
            group_dict = database[person_name][prompt_type][group_name]

            if sub_group_name.strip():
                # Use subgroup
                sub_group_key = sub_group_name.strip()
                if sub_group_key not in group_dict:
                    group_dict[sub_group_key] = []
                group_dict[sub_group_key].append(new_prompt)
                full_path = f"{person_name} → {prompt_type} → {group_name} → {sub_group_key}"
            else:
                # No subgroup, use group directly as list
                if isinstance(group_dict, dict):
                    # Convert dict to list if it was previously a dict (has subgroups)
                    group_dict["_prompts"] = group_dict.get("_prompts", [])
                    group_dict["_prompts"].append(new_prompt)
                    full_path = f"{person_name} → {prompt_type} → {group_name} (root)"
                else:
                    # Group is a list, append directly
                    if not isinstance(group_dict, list):
                        database[person_name][prompt_type][group_name] = []
                    database[person_name][prompt_type][group_name].append(new_prompt)
                    full_path = f"{person_name} → {prompt_type} → {group_name}"

            # Save back to file
            self._save_database(file_path, database)

            print(f"✅ [YAMLSavePrompt] Prompt saved successfully!")
            print(f"   File: {file_path}")
            print(f"   Path: {full_path}")
            print(f"   Name: {prompt_name}")
            print(f"   Date: {timestamp}")
            print(f"   Positive prompt length: {len(cleaned_positive)} characters")
            if cleaned_negative:
                print(f"   Negative prompt length: {len(cleaned_negative)} characters")

        except Exception as e:
            print(f"❌ [YAMLSavePrompt] Error saving prompt: {str(e)}")

        return result

    def _clean_prompt_text(self, text):
        """Clean prompt text: remove extra whitespace and line breaks, return single line"""
        if not text:
            return ""

        # Replace any whitespace (including newlines, tabs, multiple spaces) with single space
        cleaned = re.sub(r'\s+', ' ', text)

        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()

        return cleaned

    def _load_existing_database(self, file_path):
        """Load existing YAML database or return empty dict"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except yaml.YAMLError:
                # If file is corrupted, start fresh
                print(f"⚠️ [YAMLSavePrompt] Warning: Corrupted YAML file, starting fresh")
                return {}
        return {}

    def _save_database(self, file_path, database):
        """Save database to YAML file with proper formatting"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                database,
                f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False,
                width=1000  # Prevent line wrapping
            )


class YAMLLoadPrompt:
    """
    YAMLLoadPrompt
    -------------------------------
    Returns prompts as two LIST of STRING outputs for looping.
    Returns both positive and negative prompts as synchronized lists.
    Uses OUTPUT_IS_LIST = (True, True) to enable multiple outputs.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": "./prompts_database.yaml"}),
                "person_name": ("STRING", {"default": "Triksy"}),
                "prompt_type": (["text-to-image", "image-to-video"], {"default": "text-to-image"}),
                "group_name": ("STRING", {"default": "main"}),
                "sub_group_name": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE", "NEGATIVE")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "load_prompts_as_list"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_prompts_as_list(self, file_path, person_name, prompt_type, group_name, sub_group_name):
        positive_prompts = []
        negative_prompts = []

        try:
            if not file_path.strip() or not os.path.exists(file_path):
                return (positive_prompts, negative_prompts)

            with open(file_path, 'r', encoding='utf-8') as f:
                database = yaml.safe_load(f) or {}

            # Navigate hierarchy
            if (person_name not in database or
                    prompt_type not in database[person_name] or
                    group_name not in database[person_name][prompt_type]):
                return (positive_prompts, negative_prompts)

            group_data = database[person_name][prompt_type][group_name]

            # Collect both positive and negative prompts
            all_prompts = []

            if sub_group_name.strip():
                if isinstance(group_data, dict) and sub_group_name in group_data:
                    all_prompts = group_data[sub_group_name]
            else:
                if isinstance(group_data, list):
                    all_prompts = group_data
                elif isinstance(group_data, dict):
                    for sub_group_prompts in group_data.values():
                        all_prompts.extend(sub_group_prompts)

            # Extract positive and negative prompts synchronously
            for prompt_entry in all_prompts:
                positive = prompt_entry.get("positive", "")
                negative = prompt_entry.get("negative", "")
                positive_prompts.append(positive)
                negative_prompts.append(negative)

            print(f"✅ Loaded {len(positive_prompts)} prompt pairs as synchronized lists")

        except Exception as e:
            print(f"❌ Error: {str(e)}")

        return (positive_prompts, negative_prompts)  # Возвращаем два списка


class CreateProjectStructure:
    """
    CreateProjectStructure
    ---------------------
    Creates standardized project directory paths for generative AI workflows.
    ONLY generates paths - directories are created on first save by other nodes.
    Uses current date for date-based subdirectories.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "projects_root_path": ("STRING", {
                    "default": "/home/stalkervr/AiProjects",
                    "tooltip": "Root directory where all projects are stored"
                }),
                "project_name": ("STRING", {
                    "default": "MyProject",
                    "tooltip": "Name of the specific project"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "image_dataset", "video_dataset", "image_test", "image_edit", "image",
        "video_test", "video", "promptdb", "project_name"
    )
    FUNCTION = "create_project_paths"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"

    def create_project_paths(self, projects_root_path, project_name):
        # Validate inputs
        if not projects_root_path.strip() or not project_name.strip():
            raise ValueError("❌ Both projects_root_path and project_name must be provided")

        # Clean inputs
        projects_root_path = projects_root_path.strip()
        project_name_clean = project_name.strip()

        # Create project root path (don't create directory yet)
        project_root = os.path.join(projects_root_path, project_name_clean)

        # Get current date for date-based directories
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Define all directory paths (only paths, no directory creation)
        directories = {
            "image_dataset": os.path.join(project_root, "dataset", "image", current_date),
            "video_dataset": os.path.join(project_root, "dataset", "video", current_date),
            "image_test": os.path.join(project_root, "image", "test", current_date),
            "image_edit": os.path.join(project_root, "image", "edit", current_date),  # NEW!
            "image": os.path.join(project_root, "image", current_date),
            "video_test": os.path.join(project_root, "video", "test", current_date),
            "video": os.path.join(project_root, "video", current_date),
            # Special case: promptdb.yaml file path (not directory)
            "promptdb": os.path.join(project_root, "promptdb.yaml")
        }

        # Log paths (for debugging)
        print(f"📁 [CreateProjectStructure] Project paths generated:")
        print(f"   Project root: {project_root}")
        print(f"   Date: {current_date}")
        print(f"   Prompt DB file: {directories['promptdb']}")

        # Return directory paths as strings + original project name
        return (
            directories["image_dataset"],
            directories["video_dataset"],
            directories["image_test"],
            directories["image_edit"],  # Moved to position 4 (after image_test)
            directories["image"],
            directories["video_test"],
            directories["video"],
            directories["promptdb"],  # This is now a .yaml file path
            project_name  # Return original project name as-is
        )