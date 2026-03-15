import os

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

from .nodes.image_process import (
    ImageGridCropper,
    ImageBatchCrop,
    ImageRatioResizer,
    ImageGetSize,
    DesiredResolution,
    SaveImageWithMetadata,
    LoadImageWithMetadata,
    LoadImagesWithMetadata
)

from .nodes.sting_process import (
    StringWrapper,
    StringListToString,
    StringCollector,
    StringBuilder,
    NormalizeString
)

from .nodes.prompt_handler import (
    PromptPartJoin,
    WanVideoMultiPrompt,
    ShotCameraAngle,
    NudePresetSelector
)

from .nodes.json_process import (
    JsonRootListExtractor,
    JsonFieldRemover,
    JsonFieldReplaceAdvanced,
    JsonArraySplitter,
    JsonPromptToTextPromptConverter,
    JsonPathLoader,
    JsonSerializeObject,
    JsonDeserializeObject,
    JsonFormat,
    JsonMinify,
    JsonPairInput,
    JsonFieldValueExtractor
)

from .nodes.batch_process import (
    LoopAny,
    ListItemExtractor,
    AnyCollector
)

from .nodes.utility import (
    Logger,
    SwitchAny,
    CalculateFrameCount
)

from .nodes.json_builder import (
    JsonBuilder
)

from .nodes.file_process import (
    SaveTextFile,
    FormatDatePath,
    YAMLSavePrompt,
    YAMLLoadPrompt,
    CreateProjectStructure
)

from .nodes.wan_video_enhance import (
    WanVideoEnhanceMotionAdvancedKJ,
    WanVideoEnhanceMotionAdvanced,
    WanVideoEnhanceSVI,
    WanVideoSVIProEmbeds_EnhancedMotion
)

from .nodes.production import (
    SaveVideoWithMetadata,
    GenerateCreationTime,
    TextWatermark,
    ImageWatermark
)


NODE_CLASS_MAPPINGS = {
    "StringWrapper": StringWrapper,
    "StringListToString": StringListToString,
    "StringCollector": StringCollector,
    "StringBuilder": StringBuilder,
    "NormalizeString": NormalizeString,

    "PromptPartJoin": PromptPartJoin,
    "WanVideoMultiPrompt": WanVideoMultiPrompt,
    "ShotCameraAngle": ShotCameraAngle,
    "NudePresetSelector": NudePresetSelector,

    "ImageGridCropper": ImageGridCropper,
    "ImageBatchCrop": ImageBatchCrop,
    "ImageRatioResizer": ImageRatioResizer,
    "ImageGetSize": ImageGetSize,
    "DesiredResolution": DesiredResolution,
    "SaveImageWithMetadata": SaveImageWithMetadata,
    "LoadImageWithMetadata": LoadImageWithMetadata,
    "LoadImagesWithMetadata": LoadImagesWithMetadata,

    "JsonRootListExtractor": JsonRootListExtractor,
    "JsonFieldRemover": JsonFieldRemover,
    "JsonFieldReplaceAdvanced": JsonFieldReplaceAdvanced,
    "JsonArraySplitter": JsonArraySplitter,
    "JsonPromptToTextPromptConverter": JsonPromptToTextPromptConverter,
    "JsonPathLoader": JsonPathLoader,
    "JsonSerializeObject": JsonSerializeObject,
    "JsonDeserializeObject": JsonDeserializeObject,
    "JsonBuilder": JsonBuilder,
    "JsonFormat": JsonFormat,
    "JsonMinify": JsonMinify,
    "JsonPairInput": JsonPairInput,
    "JsonFieldValueExtractor": JsonFieldValueExtractor,

    "LoopAny": LoopAny,
    "AnyCollector": AnyCollector,
    "ListItemExtractor": ListItemExtractor,

    "Logger": Logger,
    "SwitchAny": SwitchAny,
    "CalculateFrameCount": CalculateFrameCount,

    "SaveTextFile": SaveTextFile,
    "FormatDatePath": FormatDatePath,
    "YAMLSavePrompt": YAMLSavePrompt,
    "YAMLLoadPrompt": YAMLLoadPrompt,
    "CreateProjectStructure": CreateProjectStructure,

    "WanVideoEnhanceMotionAdvancedKJ": WanVideoEnhanceMotionAdvancedKJ,
    "WanVideoEnhanceMotionAdvanced": WanVideoEnhanceMotionAdvanced,
    "WanVideoEnhanceSVI": WanVideoEnhanceSVI,
    "WanVideoSVIProEmbeds_EnhancedMotion": WanVideoSVIProEmbeds_EnhancedMotion,

    "SaveVideoWithMetadata": SaveVideoWithMetadata,
    "GenerateCreationTime": GenerateCreationTime,
    "TextWatermark": TextWatermark,
    "ImageWatermark": ImageWatermark,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "StringWrapper": "🪛 String → Wrapper",
    "StringListToString": "🪛 String → List To String",
    "StringCollector": "🪛 String → Collector",
    "StringBuilder": "🪛 String → Builder",
    "NormalizeString": "🪛 String → Normalize String",

    "PromptPartJoin": "Prompt Part Join",
    "WanVideoMultiPrompt": "WanVideo Multi Prompt",
    "ShotCameraAngle": "Shot Camera Angle",
    "NudePresetSelector": "Nude Preset Selector",

    "ImageGridCropper": "🪛 Image → Grid Cropper",
    "ImageBatchCrop": "🪛 Image → Batch Crop",
    "ImageRatioResizer": "🪛 Image → Ratio Resizer",
    "ImageGetSize": "🪛 Image → Get Size",
    "DesiredResolution": "🪛 Image → Desired Resolution",
    "SaveImageWithMetadata": "🪛 Image → Save With Metadata",
    "LoadImageWithMetadata": "🪛 Image → Load With Metadata",
    "LoadImagesWithMetadata": "🪛 Images → Load With Metadata",

    "JsonRootListExtractor": "🪛 JSON → Root List Extractor",
    "JsonFieldRemover": "🪛 JSON → Field Remover",
    "JsonFieldReplaceAdvanced": "🪛 JSON → Field Add & Replace",
    "JsonArraySplitter": "🪛 JSON → Split Array to List",
    "JsonPromptToTextPromptConverter": "🪛 JSON → To Text Prompt",
    "JsonPathLoader": "🪛 JSON → Path Loader",
    "JsonSerializeObject": "🪛 JSON → Serialize Object",
    "JsonDeserializeObject": "🪛 JSON → Deserialize Object",
    "JsonBuilder": "🪛 JSON → Builder",
    "JsonFormat": "🪛 JSON → Format",
    "JsonMinify": "🪛 JSON → Minify",
    "JsonFieldValueExtractor": "🪛 JSON → Field Value Extractor",
    "JsonPairInput": "🪛 JSON → Pair Input",

    "LoopAny": "🪛 Loop Any",
    "ListItemExtractor": "🪛 List Item Extractor",
    "AnyCollector": "🪛 Any Collector",

    "Logger": "🪛 Logger",
    "SwitchAny": "🪛 Switch",
    "CalculateFrameCount": "🪛 Calculate Frame Count",

    "SaveTextFile": "🪛 Save Text File",
    "FormatDatePath": "🪛 Format Date Path",
    "YAMLSavePrompt": "🪛 YAML → Save Prompt",
    "YAMLLoadPrompt": "🪛 YAML → Load Prompt",
    "CreateProjectStructure": "🪛 Create Project Structure",

    "WanVideoEnhanceMotionAdvancedKJ": "🪛 Enhance Motion KJ",
    "WanVideoEnhanceMotionAdvanced": "🪛 Enhance Motion",
    "WanVideoEnhanceSVI": "🪛 SVI Enhance",
    "WanVideoSVIProEmbeds_EnhancedMotion": "🪛 SVI ProEmbeds EnhancedMotion",

    "SaveVideoWithMetadata": "🪛 Save Video With Metadata",
    "GenerateCreationTime": "🪛 Generate Creation Time",
    "TextWatermark": "🪛 Text Watermark",
    "ImageWatermark": "🪛 Image Watermark",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']