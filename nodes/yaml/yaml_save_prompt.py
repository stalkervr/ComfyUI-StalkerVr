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
    Saves prompts to a structured YAML database.
    Supports saving single prompts or batches (lists) of prompts.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Принимаем STRING, но внутри будем проверять, не список ли это
                # В ComfyUI нет типа LIST для строк в required/optional напрямую без OUTPUT_IS_LIST у источника
                # Поэтому мы полагаемся на то, что если приходит список, он может быть обернут или передан как есть
                # Лучший способ для батча в ComfyUI — использовать ноду цикла.
                # Но если мы хотим поддержать прямой ввод списка (например, из кастомной ноды), делаем так:
                "positive_prompts": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "dynamicPrompts": False,
                    "tooltip": "Positive prompt(s). Can be a single string or a JSON list of strings."
                }),
                "negative_prompts": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "dynamicPrompts": False,
                    "tooltip": "Negative prompt(s). Can be a single string or a JSON list of strings."
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
                "base_prompt_name": ("STRING", {
                    "default": "My Prompt",
                    "tooltip": "Base name for prompts. Index will be appended if batch is saved."
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "save_prompt_database"
    CATEGORY = f"{CATEGORY_PREFIX}/IO"
    OUTPUT_NODE = True

    def save_prompt_database(self, positive_prompts, negative_prompts, save_enabled, file_path,
                             person_name, prompt_type, group_name, sub_group_name, base_prompt_name):

        # Если сохранение выключено, просто возвращаем входные данные как есть
        if not save_enabled:
            log(LogEntry(node_class="YAMLSavePrompt", title="Save skipped", details={"Reason": "Saving disabled"}))
            return (positive_prompts, negative_prompts)

        # Нормализация входов: превращаем всё в списки строк
        pos_list = self._normalize_to_list(positive_prompts)
        neg_list = self._normalize_to_list(negative_prompts)

        # Если списки разной длины, дополняем пустыми строками
        max_len = max(len(pos_list), len(neg_list))
        while len(pos_list) < max_len:
            pos_list.append("")
        while len(neg_list) < max_len:
            neg_list.append("")

        if not any(p.strip() for p in pos_list):
            log(LogEntry(node_class="YAMLSavePrompt", title="Save skipped",
                         details={"Reason": "All positive prompts are empty"}))
            return (positive_prompts, negative_prompts)

        if not all([file_path.strip(), person_name.strip(), group_name.strip(), base_prompt_name.strip()]):
            log(LogEntry(node_class="YAMLSavePrompt", title="Save skipped",
                         details={"Reason": "Missing required fields"}))
            return (positive_prompts, negative_prompts)

        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            database = self._load_existing_database(file_path)

            saved_count = 0
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for i, (pos, neg) in enumerate(zip(pos_list, neg_list)):
                if not pos.strip():
                    continue

                cleaned_positive = self._clean_prompt_text(pos)
                cleaned_negative = self._clean_prompt_text(neg)

                # Генерируем уникальное имя для каждого промпта в пакете
                prompt_name = f"{base_prompt_name}_{i + 1}" if len(pos_list) > 1 else base_prompt_name

                new_prompt = {
                    "date": timestamp,
                    "name": prompt_name,
                    "positive": cleaned_positive,
                    "negative": cleaned_negative
                }

                # Иерархическая структура
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
                else:
                    if isinstance(group_dict, dict):
                        group_dict["_prompts"] = group_dict.get("_prompts", [])
                        group_dict["_prompts"].append(new_prompt)
                    else:
                        if not isinstance(group_dict, list):
                            database[person_name][prompt_type][group_name] = []
                        database[person_name][prompt_type][group_name].append(new_prompt)

                saved_count += 1

            if saved_count > 0:
                self._save_database(file_path, database)
                log(LogEntry(
                    node_class="YAMLSavePrompt",
                    title="Prompts saved successfully",
                    details={
                        "File": file_path,
                        "Count": saved_count,
                        "Path": f"{person_name} → {prompt_type} → {group_name}" + (
                            f" → {sub_group_name}" if sub_group_name.strip() else ""),
                        "Date": timestamp
                    }
                ))
            else:
                log(LogEntry(node_class="YAMLSavePrompt", title="No valid prompts to save",
                             details={"Reason": "All inputs were empty or invalid"}))

        except Exception as e:
            log(LogEntry(node_class="YAMLSavePrompt", title="Save failed", details={"Error": str(e)}))
            import traceback
            traceback.print_exc()

        # Возвращаем исходные данные без изменений для пасстру
        return (positive_prompts, negative_prompts)

    def _normalize_to_list(self, data):
        """Converts input data to a list of strings."""
        if isinstance(data, list):
            return [str(item) for item in data]
        if isinstance(data, str):
            # Проверяем, не является ли строка JSON-списком
            if data.startswith("[") and data.endswith("]"):
                try:
                    import json
                    parsed = json.loads(data)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except json.JSONDecodeError:
                    pass
            # Если это просто одна строка (возможно, многострочная)
            # Разбиваем по двойному переносу строки, если похоже на список, иначе считаем одним элементом
            # Для надежности считаем одну строку одним элементом, если она не выглядит как явный список
            return [data]
        return [str(data)]

    def _clean_prompt_text(self, text):
        """Normalize whitespace and line breaks into a single line."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', str(text)).strip()

    def _load_existing_database(self, file_path):
        """Load existing YAML database or return empty dict on failure."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except yaml.YAMLError:
                log(LogEntry(node_class="YAMLSavePrompt", title="YAML load warning",
                             details={"Reason": "Corrupted file, starting fresh"}))
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