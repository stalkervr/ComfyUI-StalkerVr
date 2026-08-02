from ...common.constants import CATEGORY_PREFIX
from ...common.logger import LogEntry, log


class TextKeywordChecker:
    """
    Checks if the input text contains any of the specified keywords or phrases.
    Keywords are separated by '|' (pipe) character.
    Returns a boolean flag and the original text unchanged.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "The text to check for keywords"
                }),
                "keywords": ("STRING", {
                    "multiline": True,
                    "default": "bad|nsfw|error",
                    "tooltip": "Keywords or phrases to search for, separated by '|'"
                }),
                "case_sensitive": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "If True, matching is case-sensitive. If False, ignores case."
                }),
            }
        }

    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("text_passthrough", "is_found")
    FUNCTION = "check_keywords"
    CATEGORY = f"{CATEGORY_PREFIX}/Text"
    DESCRIPTION = """
    Checks if the input text contains any of the specified keywords or phrases.
    Keywords are separated by '|' (pipe) character.
    Returns a boolean flag and the original text unchanged.
    """

    def check_keywords(self, text: str, keywords: str, case_sensitive: bool = False):
        """
        Checks if any of the keywords exist in the text.

        Args:
            text (str): The source text.
            keywords (str): Pipe-separated list of keywords/phrases.
            case_sensitive (bool): Whether to perform case-sensitive matching.

        Returns:
            tuple[bool, str]: (is_found, original_text)
        """
        # Если текст или ключевые слова пустые
        if not text or not keywords:
            log(LogEntry(
                node_class="TextKeywordChecker",
                title="Check skipped",
                details={"Reason": "Empty text or keywords"}
            ))
            return (False, text)

        # Разбиваем строку ключевых слов по разделителю '|'
        # strip() убирает пробелы вокруг каждого ключевого слова
        keyword_list = [k.strip() for k in keywords.split('|') if k.strip()]

        if not keyword_list:
            return (False, text)

        # Подготовка текста для поиска
        search_text = text if case_sensitive else text.lower()

        is_found = False
        matched_keyword = None

        for kw in keyword_list:
            # Приводим ключевое слово к нужному регистру
            search_kw = kw if case_sensitive else kw.lower()

            if search_kw in search_text:
                is_found = True
                matched_keyword = kw
                break  # Нашли хотя бы одно совпадение, выходим из цикла

        log(LogEntry(
            node_class="TextKeywordChecker",
            title="Keyword check completed",
            details={
                "Found": is_found,
                "Matched Keyword": matched_keyword if is_found else "None",
                "Case Sensitive": case_sensitive,
                "Total Keywords Checked": len(keyword_list)
            }
        ))

        return (text, is_found)