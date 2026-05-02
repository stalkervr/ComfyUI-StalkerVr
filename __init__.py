"""
ComfyUI-StalkerVr
A versatile collection of custom nodes for ComfyUI, designed to streamline complex workflows and enhance productivity.
This package provides a structured toolkit for asset management, model handling, and batch processing,
featuring centralized configuration, secure API key management, and intelligent logging.
Built with modularity in mind, it serves as a scalable foundation for efficient and maintainable ComfyUI workflows.
"""

from .nodes.wan_video_lora_civitai_downloader import (
    WanVideoLoraCivitAIDownloader
)
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
from .nodes.wan_video_lora_pair_creator import (
    WanVideoLoraPairCreator
)
from .nodes.wan_video_enhance_motion_advanced_kj import (
    WanVideoEnhanceMotionAdvancedKJ
)
from .nodes.wan_video_enhance_motion_advanced import (
    WanVideoEnhanceMotionAdvanced
)
from .nodes.wan_video_lora_pair_select import (
    WanVideoLoraPairSelect
)


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
}


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]