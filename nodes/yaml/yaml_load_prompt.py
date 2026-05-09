import os
import yaml
import traceback
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log

class YAMLLoadPrompt:
    """Loads prompts from a structured YAML database as synchronized positive/negative lists."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": "./prompts_database.yaml"}),
                "person_name": ("STRING", {"default": "Triksy"}),
                "prompt_type": (["text-to-image", "image-to-video"], {"default": "text-to-image"}),
                "group_name": ("STRING", {"default": "main"}),
            },
            "optional": {
                "sub_group_name": ("STRING", {"default": ""}),
                "prompt_name": ("STRING", {"default": "", "tooltip": "Optional: filter by specific prompt name"}),
                "limit": ("INT", {"default": 0, "min": 0, "max": 10000, "step": 1, "tooltip": "Max prompts to return (0=unlimited)"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("POSITIVE", "NEGATIVE")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "load_prompts_as_list"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def load_prompts_as_list(self, file_path, person_name, prompt_type, group_name, sub_group_name="", prompt_name="", limit=0):
        positive_prompts = []
        negative_prompts = []

        try:
            if not file_path.strip() or not os.path.exists(file_path):
                log(LogEntry(node_class="YAMLLoadPrompt", title="File not found", details={"Path": file_path}))
                return (positive_prompts, negative_prompts)

            with open(file_path, 'r', encoding='utf-8') as f:
                database = yaml.safe_load(f) or {}

            if (person_name not in database or
                prompt_type not in database[person_name] or
                group_name not in database[person_name][prompt_type]):
                log(LogEntry(node_class="YAMLLoadPrompt", title="Path not found", details={"Path": f"{person_name} > {prompt_type} > {group_name}"}))
                return (positive_prompts, negative_prompts)

            group_data = database[person_name][prompt_type][group_name]
            all_prompts = []

            if sub_group_name.strip():
                if isinstance(group_data, dict) and sub_group_name in group_data:
                    all_prompts = group_data[sub_group_name]
                else:
                    log(LogEntry(node_class="YAMLLoadPrompt", title="Sub-group not found", details={"Sub-group": sub_group_name}))
            else:
                if isinstance(group_data, list):
                    all_prompts = group_data
                elif isinstance(group_data, dict):
                    for sub_group_prompts in group_data.values():
                        all_prompts.extend(sub_group_prompts)

            if prompt_name.strip():
                log(LogEntry(node_class="YAMLLoadPrompt", title="Searching for prompt", details={"Name": prompt_name}))
                found = False
                for prompt_entry in all_prompts:
                    if prompt_entry.get("name", "") == prompt_name:
                        positive_prompts.append(prompt_entry.get("positive", ""))
                        negative_prompts.append(prompt_entry.get("negative", ""))
                        found = True
                        break

                if not found:
                    log(LogEntry(node_class="YAMLLoadPrompt", title="Prompt not found, returning all", details={"Name": prompt_name}))
                    for prompt_entry in all_prompts:
                        positive_prompts.append(prompt_entry.get("positive", ""))
                        negative_prompts.append(prompt_entry.get("negative", ""))
            else:
                for prompt_entry in all_prompts:
                    positive_prompts.append(prompt_entry.get("positive", ""))
                    negative_prompts.append(prompt_entry.get("negative", ""))

            total_loaded = len(positive_prompts)
            if limit > 0 and total_loaded > limit:
                positive_prompts = positive_prompts[:limit]
                negative_prompts = negative_prompts[:limit]
                log(LogEntry(node_class="YAMLLoadPrompt", title="Limit applied", details={"Original": total_loaded, "New": limit}))

            log(LogEntry(node_class="YAMLLoadPrompt", title="Prompts loaded", details={"Count": len(positive_prompts)}))

        except Exception as e:
            log(LogEntry(node_class="YAMLLoadPrompt", title="Error loading prompts", details={"Error": str(e)}))
            traceback.print_exc()

        return (positive_prompts, negative_prompts)