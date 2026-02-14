import os

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

from .nodes.image_process import (
    ImageGridCropper,
    ImageBatchCrop,
    ImageRatioResizer,
    SaveImageWithMetadata,
    LoadImageWithMetadata,
    LoadImagesWithMetadata
)

from .nodes.sting_process import (
    StringConcatenation,
    StringWrapper,
    StringListToString,
    StringCollector,
    StringBuilder
)

from .nodes.prompt_handler import (
    PromptPartJoin,
    WanVideoMultiPrompt
)

from .nodes.json_process import (
    JsonFieldValueExtractor,
    JsonRootListExtractor,
    JsonFieldRemover,
    JsonFieldReplaceAdvanced,
    JsonToString,
    JsonArraySplitter,
    JsonPromptToTextPromptConverter,
    JsonPathLoader,
    JsonSerializeObject,
    JsonDeserializeObject,
    JsonPairInput,
    JsonFormat,
    JsonMinify
)

from .nodes.batch_process import (
    LoopAny,
    ListItemExtractor,
    AnyCollector
)

from .nodes.utility import (
    LogValue,
    ConsoleLog,
    DebugConditioningStructure,
)

from .nodes.json_builder import (
    JsonBuilder
)

from .nodes.pipe import (
    PipeIn,
    PipeOut
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


NODE_CLASS_MAPPINGS = {
    "StringWrapper": StringWrapper,
    "StringListToString": StringListToString,
    "StringCollector": StringCollector,
    "StringConcatenation": StringConcatenation,
    "StringBuilder": StringBuilder,

    "PromptPartJoin": PromptPartJoin,
    "WanVideoMultiPrompt": WanVideoMultiPrompt,

    "ImageGridCropper": ImageGridCropper,
    "ImageBatchCrop": ImageBatchCrop,
    "ImageRatioResizer": ImageRatioResizer,
    "SaveImageWithMetadata": SaveImageWithMetadata,
    "LoadImageWithMetadata": LoadImageWithMetadata,
    "LoadImagesWithMetadata": LoadImagesWithMetadata,

    "JsonFieldValueExtractor": JsonFieldValueExtractor,
    "JsonRootListExtractor": JsonRootListExtractor,
    "JsonFieldRemover": JsonFieldRemover,
    "JsonFieldReplaceAdvanced": JsonFieldReplaceAdvanced,
    "JsonToString": JsonToString,
    "JsonArraySplitter": JsonArraySplitter,
    "JsonPromptToTextPromptConverter": JsonPromptToTextPromptConverter,
    "JsonPathLoader": JsonPathLoader,
    "JsonSerializeObject": JsonSerializeObject,
    "JsonDeserializeObject": JsonDeserializeObject,
    "JsonPairInput": JsonPairInput,
    "JsonBuilder": JsonBuilder,
    "JsonFormat": JsonFormat,
    "JsonMinify": JsonMinify,

    "LoopAny": LoopAny,
    "AnyCollector": AnyCollector,
    "ListItemExtractor": ListItemExtractor,

    "LogValue": LogValue,
    "ConsoleLog": ConsoleLog,
    "DebugConditioningStructure": DebugConditioningStructure,

    "SaveTextFile": SaveTextFile,
    "FormatDatePath": FormatDatePath,
    "YAMLSavePrompt": YAMLSavePrompt,
    "YAMLLoadPrompt": YAMLLoadPrompt,
    "CreateProjectStructure": CreateProjectStructure,

    "PipeIn": PipeIn,
    "PipeOut": PipeOut,

    "WanVideoEnhanceMotionAdvancedKJ": WanVideoEnhanceMotionAdvancedKJ,
    "WanVideoEnhanceMotionAdvanced": WanVideoEnhanceMotionAdvanced,
    "WanVideoEnhanceSVI": WanVideoEnhanceSVI,
    "WanVideoSVIProEmbeds_EnhancedMotion": WanVideoSVIProEmbeds_EnhancedMotion,

}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StringConcatenation": "🪛 String → Concatenation",
    "StringWrapper": "🪛 String → Wrapper",
    "StringListToString": "🪛 String → List To String",
    "StringCollector": "🪛 String → Collector",
    "StringBuilder": "🪛 String → Builder",

    "PromptPartJoin": "Prompt Part Join",
    "WanVideoMultiPrompt": "WanVideo Multi Prompt",

    "ImageGridCropper": "Image Grid Cropper",
    "ImageBatchCrop": "Image Batch Crop",
    "ImageRatioResizer": "🪛 Image → Ratio Resizer",
    "SaveImageWithMetadata": "🪛 Image → Save With Metadata",
    "LoadImageWithMetadata": "🪛 Image → Load With Metadata",
    "LoadImagesWithMetadata": "🪛 Image → Load Images With Metadata",

    "JsonFieldValueExtractor": "🪛 JSON → Field Value Extractor",
    "JsonRootListExtractor": "🪛 JSON → Root List Extractor",
    "JsonFieldRemover": "🪛 JSON → Field Remover",
    "JsonFieldReplaceAdvanced": "🪛 JSON → Field Add & Replace",
    "JsonToString": "🪛 JSON → To String",
    "JsonArraySplitter": "🪛 JSON → Split Array to List",
    "JsonPromptToTextPromptConverter": "🪛 JSON → To Text Prompt",
    "JsonPathLoader": "🪛 JSON → Path Loader",
    "JsonSerializeObject": "🪛 JSON → Serialize Object",
    "JsonDeserializeObject": "🪛 JSON → Deserialize Object",
    "JsonPairInput": "🪛 JSON → Pair Input",
    "JsonBuilder": "🪛 JSON → Builder",
    "JsonFormat": "🪛 JSON → Format",
    "JsonMinify": "🪛 JSON → Minify",

    "LoopAny": "🪛 Loop Any",
    "ListItemExtractor": "🪛 List Item Extractor",
    "AnyCollector": "🪛 Any Collector",

    "LogValue": "🪛 Log Value",
    "ConsoleLog": "🪛 Console Log",
    "DebugConditioningStructure": "🪛 Debug Conditioning Structure",

    "SaveTextFile": "🪛 Save Text File",
    "FormatDatePath": "🪛 Format Date Path",
    "YAMLSavePrompt": "🪛 YAML → Save Prompt",
    "YAMLLoadPrompt": "🪛 YAML → Load Prompt",
    "CreateProjectStructure": "🪛 Create Project Structure",

    "PipeIn": "🪛 Pipe In",
    "PipeOut": "🪛 Pipe Out",

    "WanVideoEnhanceMotionAdvancedKJ": "🪛 Enhance Motion KJ",
    "WanVideoEnhanceMotionAdvanced": "🪛 Enhance Motion",
    "WanVideoEnhanceSVI": "🪛 SVI Enhance",
    "WanVideoSVIProEmbeds_EnhancedMotion": "🪛 SVI ProEmbeds EnhancedMotion",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']