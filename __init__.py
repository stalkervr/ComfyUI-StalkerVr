import os

"""
ComfyUI-StalkerVr
A versatile collection of custom nodes for ComfyUI, designed to streamline complex workflows and enhance productivity.
This package provides a structured toolkit for asset management, model handling, and batch processing,
featuring centralized configuration, secure API key management, and intelligent logging.
Built with modularity in mind, it serves as a scalable foundation for efficient and maintainable ComfyUI workflows.
"""

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

from .nodes.lora_loader import (
    LoraLoaderExtended,
    LoraLoaderExtendedBatch
)

from .nodes.utils import (
    Logger,
    SwitchAny,
    CalculateFrameCount,
    CurrentDateTime
)

from .nodes.wan_video_lora_civitai_downloader import WanVideoLoraCivitAIDownloader
from .nodes.wan_video_lora_pair_creator import WanVideoLoraPairCreator
from .nodes.wan_video_enhance_motion_advanced_kj import WanVideoEnhanceMotionAdvancedKJ
from .nodes.wan_video_enhance_motion_advanced import WanVideoEnhanceMotionAdvanced
from .nodes.wan_video_lora_pair_select import WanVideoLoraPairSelect

from .nodes.json_field_value_extractor import JsonFieldValueExtractor
from .nodes.json_field_remover import JsonFieldRemover
from .nodes.json_field_replace_extend import JsonFieldReplaceExtend
from .nodes.json_prompt_to_text_prompt_converter import JsonPromptToTextPromptConverter
from .nodes.json_serialize_object import JsonSerializeObject
from .nodes.json_deserialize_object import JsonDeserializeObject
from .nodes.json_format import JsonFormat
from .nodes.json_minify import JsonMinify
from .nodes.json_path_loader import JsonPathLoader
from .nodes.json_builder import JsonBuilder
from .nodes.json_pair_input import JsonPairInput

NODE_CLASS_MAPPINGS = {
    "WanVideoLoraCivitAIDownloader": WanVideoLoraCivitAIDownloader,
    "WanVideoLoraPairCreator": WanVideoLoraPairCreator,
    "WanVideoEnhanceMotionAdvancedKJ": WanVideoEnhanceMotionAdvancedKJ,
    "WanVideoEnhanceMotionAdvanced": WanVideoEnhanceMotionAdvanced,
    "WanVideoLoraPairSelect": WanVideoLoraPairSelect,

    "LoraLoaderExtended": LoraLoaderExtended,
    "LoraLoaderExtendedBatch": LoraLoaderExtendedBatch,

    "Logger": Logger,
    "SwitchAny": SwitchAny,
    "CalculateFrameCount": CalculateFrameCount,
    "CurrentDateTime": CurrentDateTime,

    "JsonFieldValueExtractor": JsonFieldValueExtractor,
    "JsonFieldRemover": JsonFieldRemover,
    "JsonFieldReplaceExtend": JsonFieldReplaceExtend,
    "JsonPromptToTextPromptConverter": JsonPromptToTextPromptConverter,
    "JsonSerializeObject": JsonSerializeObject,
    "JsonDeserializeObject": JsonDeserializeObject,
    "JsonFormat": JsonFormat,
    "JsonMinify": JsonMinify,
    "JsonPathLoader": JsonPathLoader,
    "JsonBuilder": JsonBuilder,
    "JsonPairInput": JsonPairInput,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "WanVideoLoraCivitAIDownloader": "WanVideo LoraCivitAIDownloader",
    "WanVideoLoraPairCreator": "WanVideo LoraPairCreator",
    "WanVideoEnhanceMotionAdvancedKJ": "WanVideo EnhanceMotionAdvancedKJ",
    "WanVideoEnhanceMotionAdvanced": "WanVideo EnhanceMotionAdvanced",
    "WanVideoLoraPairSelect": "WanVideo LoraPairSelect",

    "LoraLoaderExtended": "LoRA Loader Extended",
    "LoraLoaderExtendedBatch": "LoRA Loader Extended (Batch)",

    "Logger": "Logger",
    "SwitchAny": "SwitchAny",
    "CalculateFrameCount": "CalculateFrameCount",
    "CurrentDateTime": "CurrentDateTime",

    "JsonFieldValueExtractor": "JSON FieldValueExtractor",
    "JsonFieldRemover": "JSON FieldRemover",
    "JsonFieldReplaceExtend": "JSON FieldReplaceExtend",
    "JsonPromptToTextPromptConverter": "JSON PromptToTextPromptConverter",
    "JsonSerializeObject": "JSON SerializeObject",
    "JsonDeserializeObject": "JSON DeserializeObject",
    "JsonFormat": "JSON Format",
    "JsonMinify": "JSON Minify",
    "JsonPathLoader": "JSON PathLoader",
    "JsonBuilder": "JSON Builder",
    "JsonPairInput": "JSON PairInput",
}


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]