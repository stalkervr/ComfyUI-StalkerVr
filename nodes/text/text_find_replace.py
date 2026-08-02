import re
from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class TextFindAndReplace:
    """
    Finds and replaces specific words or phrases in the input text.
    Supports single replacement or multiple replacements using a separator.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "The source text to process"
                }),
                "find_text": ("STRING", {
                    "default": "",
                    "tooltip": "Text or phrase to find. For multiple items, separate with '|'"
                }),
                "replace_text": ("STRING", {
                    "default": "",
                    "tooltip": "Text to replace with. For multiple items, separate with '|' matching the find list"
                }),
                "use_regex": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If True, treat 'find_text' as Regular Expressions"
                }),
                "case_sensitive": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If True, matching is case-sensitive"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result_text",)
    FUNCTION = "replace"
    CATEGORY = f"{CATEGORY_PREFIX}/Utils"
    DESCRIPTION = """
    Finds and replaces specific words or phrases in the input text.
    Supports single replacement or multiple replacements using a separator.
    """

    def replace(self, text: str, find_text: str, replace_text: str, use_regex: bool = False,
                case_sensitive: bool = False):
        """
        Performs find and replace operations on the input text.

        Args:
            text (str): Source text.
            find_text (str): Target string(s) to find. Separated by '|' for multiple.
            replace_text (str): Replacement string(s). Separated by '|' for multiple.
            use_regex (bool): Use Regular Expressions for finding.
            case_sensitive (bool): Case-sensitive matching.

        Returns:
            tuple[str]: The modified text.
        """
        if not text:
            return (text,)

        # Разбиваем списки поиска и замены по разделителю '|'
        find_list = [f.strip() for f in find_text.split('|') if f.strip()]
        replace_list = [r.strip() for r in replace_text.split('|')]

        # Если замен меньше, чем поисков, дополняем пустыми строками (удаление)
        # Если замен больше, лишние игнорируем
        while len(replace_list) < len(find_list):
            replace_list.append("")

        result_text = text
        replacements_made = 0

        for i, target in enumerate(find_list):
            if not target:
                continue

            replacement = replace_list[i] if i < len(replace_list) else ""

            flags = 0 if case_sensitive else re.IGNORECASE

            try:
                if use_regex:
                    # Для регулярных выражений компилируем паттерн с флагами
                    pattern = re.compile(target, flags)
                    new_text, count = pattern.subn(replacement, result_text)
                else:
                    # Для обычного текста используем str.replace или re.escape для безопасности
                    if case_sensitive:
                        new_text = result_text.replace(target, replacement)
                    else:
                        # Для нечувствительного к регистру обычного текста используем regex с экранированием
                        escaped_target = re.escape(target)
                        pattern = re.compile(escaped_target, flags)
                        new_text, count = pattern.subn(replacement, result_text)

                if new_text != result_text:
                    replacements_made += count
                    result_text = new_text

            except re.error as e:
                log(LogEntry(
                    node_class="TextFindAndReplace",
                    title="Regex Error",
                    details={"Pattern": target, "Error": str(e)}
                ))
                # В случае ошибки регулярных выражений пропускаем этот паттерн
                continue

        log(LogEntry(
            node_class="TextFindAndReplace",
            title="Replacement completed",
            details={
                "Replacements Made": replacements_made,
                "Patterns Used": len(find_list),
                "Use Regex": use_regex,
                "Case Sensitive": case_sensitive
            }
        ))

        return (result_text,)