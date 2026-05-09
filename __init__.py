import os

"""
ComfyUI-StalkerVr
A versatile collection of custom nodes for ComfyUI, designed to streamline complex workflows and enhance productivity.
This package provides a structured toolkit for asset management, model handling, and batch processing,
featuring centralized configuration, secure API key management, and intelligent logging.
Built with modularity in mind, it serves as a scalable foundation for efficient and maintainable ComfyUI workflows.
"""

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

from .nodes.lora.lora_loader import (
    LoraLoaderExtended,
    LoraLoaderExtendedBatch
)

from .nodes.wan_video.wan_video_lora_civitai_downloader import WanVideoLoraCivitAIDownloader
from .nodes.wan_video.wan_video_lora_pair_creator import WanVideoLoraPairCreator
from .nodes.wan_video.wan_video_enhance_motion_advanced_kj import WanVideoEnhanceMotionAdvancedKJ
from .nodes.wan_video.wan_video_enhance_motion_advanced import WanVideoEnhanceMotionAdvanced
from .nodes.wan_video.wan_video_lora_pair_select import WanVideoLoraPairSelect
from .nodes.wan_video.wan_video_calculate_frame_count import CalculateFrameCount

from .nodes.json.json_field_value_extractor import JsonFieldValueExtractor
from .nodes.json.json_field_remover import JsonFieldRemover
from .nodes.json.json_field_replace_extend import JsonFieldReplaceExtend
from .nodes.json.json_prompt_to_text_prompt_converter import JsonPromptToTextPromptConverter
from .nodes.json.json_serialize_object import JsonSerializeObject
from .nodes.json.json_deserialize_object import JsonDeserializeObject
from .nodes.json.json_format import JsonFormat
from .nodes.json.json_minify import JsonMinify
from .nodes.json.json_path_loader import JsonPathLoader
from .nodes.json.json_builder import JsonBuilder
from .nodes.json.json_pair_input import JsonPairInput

from .nodes.string.string_builder import StringBuilder
from .nodes.string.string_wrapper import StringWrapper
from .nodes.string.string_normalize import StringNormalize

from .nodes.image.image_grid_cropper import ImageGridCropper
from .nodes.image.image_crop import ImageCropper
from .nodes.image.image_ratio_resizer import ImageRatioResizer
from .nodes.image.image_get_size import ImageGetSize
from .nodes.image.image_desired_resolution import ImageDesiredResolution

from .nodes.image.image_metadata_io import (
    ImagesLoadWithMetadata,
    ImageLoadWithMetadata,
    ImageSaveWithMetadata
)

from .nodes.yaml.yaml_save_prompt import YAMLSavePrompt
from .nodes.yaml.yaml_load_prompt import YAMLLoadPrompt

from .nodes.production.save_video_with_metadata import SaveVideoWithMetadata
from .nodes.production.generate_creation_time import GenerateCreationTime
from .nodes.production.text_watermark import TextWatermark
from .nodes.production.image_watermark import ImageWatermark

from .nodes.io.save_text_file import SaveTextFile

from .nodes.utils.logger import Logger
from .nodes.utils.switch_any import SwitchAny
from .nodes.utils.current_date_time import CurrentDateTime
from .nodes.utils.format_date_path import FormatDatePath
from .nodes.utils.file_save_path import FileSavePath


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

    "StringBuilder": StringBuilder,
    "StringWrapper": StringWrapper,
    "StringNormalize": StringNormalize,

    "ImageGridCropper": ImageGridCropper,
    "ImageCropper": ImageCropper,
    "ImageRatioResizer": ImageRatioResizer,
    "ImageGetSize": ImageGetSize,
    "ImageDesiredResolution": ImageDesiredResolution,

    "ImagesLoadWithMetadata": ImagesLoadWithMetadata,
    "ImageLoadWithMetadata": ImageLoadWithMetadata,
    "ImageSaveWithMetadata": ImageSaveWithMetadata,

    "FormatDatePath": FormatDatePath,
    "FileSavePath": FileSavePath,
    "SaveTextFile": SaveTextFile,

    "YAMLSavePrompt": YAMLSavePrompt,
    "YAMLLoadPrompt": YAMLLoadPrompt,

    "SaveVideoWithMetadata": SaveVideoWithMetadata,
    "GenerateCreationTime": GenerateCreationTime,
    "TextWatermark": TextWatermark,
    "ImageWatermark": ImageWatermark,
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

    "StringBuilder": "String Builder",
    "StringWrapper": "String Wrapper",
    "StringNormalize": "String Normalize",

    "ImageGridCropper": "Image GridCropper",
    "ImageCropper": "Image Cropper",
    "ImageRatioResizer": "Image RatioResizer",
    "ImageGetSize": "Image GetSize",
    "ImageDesiredResolution": "Image DesiredResolution",

    "ImagesLoadWithMetadata": "Images LoadWithMetadata",
    "ImageLoadWithMetadata": "Image LoadWithMetadata",
    "ImageSaveWithMetadata": "Image SaveWithMetadata",

    "FormatDatePath": "FormatDatePath",
    "FileSavePath": "FileSavePath",
    "SaveTextFile": "SaveTextFile",

    "YAMLSavePrompt": "YAML SavePrompt",
    "YAMLLoadPrompt": "YAML LoadPrompt",

    "SaveVideoWithMetadata": "SaveVideoWithMetadata",
    "GenerateCreationTime": "GenerateCreationTime",
    "TextWatermark": "TextWatermark",
    "ImageWatermark": "ImageWatermark",
}


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]