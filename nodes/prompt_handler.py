from .constants import (
    CATEGORY_PREFIX
)


class PromptPartJoin:
    """Node to combine 6 multiline text fields into a single STRING output."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "camera_shot": ("STRING", {"multiline": True, "default": "close-up shot from above view"}),
                "main_character": ("STRING", {"multiline": True, "default": "slender woman 20-yo"}),
                "pose_action": ("STRING", {"multiline": True, "default": "siting on a flor"}),
                "clovers_style": ("STRING", {"multiline": True, "default": "naked nude"}),
                "advance_character": ("STRING", {"multiline": True, "default": "pale white skin"}),
                "env_photo_style": ("STRING", {"multiline": True, "default": "goth style dark art"}),
            },
            "optional": {
                "separator": ("STRING", {"default": ", "}),
                "newline": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("POSITIVE",)
    FUNCTION = "combine_texts"
    CATEGORY = f"{CATEGORY_PREFIX}/Prompt"

    def combine_texts(
            self,
            camera_shot,
            main_character,
            pose_action,
            clovers_style,
            advance_character,
            env_photo_style,
            separator=", ",
            newline=False
    ):
        parts = [
            camera_shot,
            main_character,
            pose_action,
            clovers_style,
            advance_character,
            env_photo_style,
        ]

        if newline:
            separator += "\n\n"

        combined = separator.join(parts)
        return (combined,)

class WanVideoMultiPrompt:
    """Node to split text by newline, wrap each block with prefix/suffix, and return final string split | and block count."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_text": ("STRING", {"multiline": False, "default": ""}),
                "prefix": ("STRING", {"multiline": False, "default": ""}),
                "suffix": ("STRING", {"multiline": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("split_prompt", "prompt_count")
    FUNCTION = "process_text"
    CATEGORY = f"{CATEGORY_PREFIX}/Prompt"

    def process_text(self, input_text, prefix, suffix):
        separator = "\n"
        lines = [line.strip() for line in input_text.splitlines() if line.strip()]
        processed_lines = [f"{prefix}{line}{suffix}{'|'}" for line in lines]
        final_text = separator.join(processed_lines)
        if final_text:
            final_text = final_text[:-1]
        count = len(processed_lines)
        return (final_text, count)