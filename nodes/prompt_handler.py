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


class ShotCameraAngle:
    """
    ShotCameraAngle
    ---------------
    Combines shot size and camera angle into a natural language description.

    - "none" in either field is treated as empty string
    - If both are "none" → returns empty string
    - If one is "none" → returns the other as-is
    - If both selected → returns "shot_size from camera_angle"
    """

    SHOT_SIZES = [
        "none",  # visual placeholder for empty
        "close-up shot",
        "medium shot",
        "full body shot",
        "wide shot",
        "long shot"
    ]

    CAMERA_ANGLES = [
        "none",  # visual placeholder for empty
        "front view",
        "side view",
        "three-quarter view",
        "rear view",
        "side-rear view",
        "bird's eye view",
        "worm's eye view",
        "dutch angle",
        "over-the-shoulder",
        "high angle",
        "low angle",
        "eye level"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "shot_size": (cls.SHOT_SIZES, {"default": "none"}),
                "camera_angle": (cls.CAMERA_ANGLES, {"default": "none"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("description",)
    FUNCTION = "build_description"
    CATEGORY = f"{CATEGORY_PREFIX}/Prompt"

    def build_description(self, shot_size: str, camera_angle: str) -> tuple[str]:
        # Convert "none" to empty string
        shot = "" if shot_size == "none" else shot_size.strip()
        angle = "" if camera_angle == "none" else camera_angle.strip()

        if not shot and not angle:
            return ("",)
        elif not shot:
            return (angle,)
        elif not angle:
            return (shot,)
        else:
            return (f"{shot} from {angle}",)


class NudePresetSelector:
    """
    NudePresetSelector
    ------------------
    Selects values from two predefined dictionaries: TOP and BOTTOM.
    Returns the values associated with the selected keys.
    """

    # Словарь описаний для верха (top)
    TOP = {
        "none": "",
        "без верха спереди": "topless, bare chest, detailed breast shape, natural semi saggy breasts, big erect nipples, areola fully visible",
        "без верха сзади": "backless, bare upper back, shoulder blades visible, skin texture, arched back",
        "без верха сбоку": "topless, bare chest in strict side profile, detailed breast silhouette, erect nipple visible from side, areola profile, natural gravity"
    }

    # Словарь описаний для низа (bottom)
    BOTTOM = {
        "none": "",
        "без низа спереди": "detailed vulva, open labia, open labia minora, exposed pubic area, frontal nudity, bare lower body, smooth skin texture",
        "без низа сзади": "rear nudity, bare buttocks, detailed buttocks, shaped glutes, smooth skin texture",
        "сзади наклонившись": "rear nudity, bare buttocks, visible anus, detailed buttocks, shaped glutes, smooth skin texture, hips tilted up",
        "сзади прогнувшись": "rear nudity, bare buttocks, visible anus, open labia, open labia minora, detailed buttocks, shaped glutes, smooth skin texture, arched back, hips elevated",
        "без низа сбоку": "side profile nudity, bare lower body in profile, detailed buttocks curve, visible pubic mound silhouette, smooth skin texture, natural leg alignment",
        "сзади секс": "rear nudity, bare buttocks, open labia, open labia minora, detailed buttocks, shaped glutes, smooth skin texture, arched back, hips elevated"
    }

    @classmethod
    def INPUT_TYPES(cls):
        top_keys = list(cls.TOP.keys())
        bottom_keys = list(cls.BOTTOM.keys())
        return {
            "required": {
                "top_describe": (top_keys, {"default": "none"}),
                "bottom_describe": (bottom_keys, {"default": "none"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("top_value", "bottom_value")
    FUNCTION = "select_values"
    CATEGORY = f"{CATEGORY_PREFIX}/Prompt"

    def select_values(self, top_describe: str, bottom_describe: str) -> tuple[str, str]:
        top_value = self.TOP.get(top_describe, "")
        bottom_value = self.BOTTOM.get(bottom_describe, "")
        return (top_value, bottom_value)