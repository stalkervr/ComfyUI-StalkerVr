import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class YAMLSavePrompt:
    """
    YAMLSavePrompt
    -------------------------
    Saves prompts to a structured YAML database with hierarchical organization.
    Supports person-name → type → group → sub_group → prompt structure.
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
                    "tooltip": "Enable/disable saving"
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
                    "tooltip": "Sub-group name (optional)"
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

        result = (positive_prompt, negative_prompt)

        if not save_enabled:
            log(LogEntry(node_class="YAMLSavePrompt", title="Save skipped", details={"Reason": "Saving disabled"}))
            return result

        if not positive_prompt.strip():
            log(LogEntry(node_class="YAMLSavePrompt", title="Save skipped", details={"Reason": "Empty positive prompt"}))
            return result

        if not all([file_path.strip(), person_name.strip(), group_name.strip(), prompt_name.strip()]):
            log(LogEntry(node_class="YAMLSavePrompt", title="Save skipped", details={"Reason": "Missing required fields"}))
            return result

        try:
            cleaned_positive = self._clean_prompt_text(positive_prompt)
            cleaned_negative = self._clean_prompt_text(negative_prompt)

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            database = self._load_existing_database(file_path)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            new_prompt = {
                "date": timestamp,
                "name": prompt_name,
                "positive": cleaned_positive,
                "negative": cleaned_negative
            }

            if person_name not in database:
                database[person_name] = {}
            if prompt_type not in database[person_name]:
                database[person_name][prompt_type] = {}
            if group_name not in database[person_name][prompt_type]:
                database[person_name][prompt_type][group_name] = {}

            group_dict = database[person_name][prompt_type][group_name]

            if sub_group_name.strip():
                sub_group_key = sub_group_name.strip()
                if sub_group_key not in group_dict:
                    group_dict[sub_group_key] = []
                group_dict[sub_group_key].append(new_prompt)
                full_path = f"{person_name} → {prompt_type} → {group_name} → {sub_group_key}"
            else:
                if isinstance(group_dict, dict):
                    group_dict["_prompts"] = group_dict.get("_prompts", [])
                    group_dict["_prompts"].append(new_prompt)
                    full_path = f"{person_name} → {prompt_type} → {group_name} (root)"
                else:
                    if not isinstance(group_dict, list):
                        database[person_name][prompt_type][group_name] = []
                    database[person_name][prompt_type][group_name].append(new_prompt)
                    full_path = f"{person_name} → {prompt_type} → {group_name}"

            self._save_database(file_path, database)

            log(LogEntry(
                node_class="YAMLSavePrompt",
                title="Prompt saved successfully",
                details={
                    "File": file_path,
                    "Path": full_path,
                    "Name": prompt_name,
                    "Date": timestamp,
                    "Positive Length": len(cleaned_positive),
                    "Negative Length": len(cleaned_negative) if cleaned_negative else 0
                }
            ))

        except Exception as e:
            log(LogEntry(node_class="YAMLSavePrompt", title="Save failed", details={"Error": str(e)}))

        return result

    def _clean_prompt_text(self, text):
        """Normalize whitespace and line breaks into a single line."""
        if not text: return ""
        return re.sub(r'\s+', ' ', text).strip()

    def _load_existing_database(self, file_path):
        """Load existing YAML database or return empty dict on failure."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except yaml.YAMLError:
                log(LogEntry(node_class="YAMLSavePrompt", title="YAML load warning", details={"Reason": "Corrupted file, starting fresh"}))
                return {}
        return {}

    def _save_database(self, file_path, database):
        """Save database to YAML with proper formatting."""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                database, f,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False,
                width=1000
            )