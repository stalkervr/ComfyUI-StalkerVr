import os

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

from .image_process import (
    ImageGridCropper,
    ImageBatchCrop,
    ImageAspectRatioFixer,
)

from .sting_process import (
    StringConcatenation,
    StringWrapper,
    StringListToString,
    StringCollector,
    StringBuilder
)

from .prompt_handler import (
    PromptPartJoin,
    WanVideoMultiPrompt
)

from .json_process import (
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
    JsonPairInput
)

from .batch_process import (
    LoopAny,
    ListItemExtractor,
    AnyCollector
)

from .utility import (
    LogValue
)

from .json_builder import (
    JsonBuilder
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
    "ImageAspectRatioFixer": ImageAspectRatioFixer,

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

    "LoopAny": LoopAny,
    "AnyCollector": AnyCollector,
    "ListItemExtractor": ListItemExtractor,

    "LogValue": LogValue,
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
    "ImageAspectRatioFixer": "Image Aspect Ratio Fixer",

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

    "LoopAny": "🪛 Loop Any",
    "ListItemExtractor": "🪛 List Item Extractor",
    "AnyCollector": "🪛 Any Collector",

    "LogValue": "🪛 Log Value",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']