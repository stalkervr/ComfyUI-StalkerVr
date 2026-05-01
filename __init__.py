"""
ComfyUI-StalkerVr
A collection of advanced tools for Wan 2.2 video generation workflow.
Includes CivitAI downloader, batch LoRA loaders, and image utilities.
"""

# Import Core Utilities
from .nodes.config_manager import ConfigManager
from .nodes.logger import LogEntry, log

# Import Nodes
# We will add imports here as we refactor and add nodes
from .nodes.civitai_downloader import CivitAIWanLoraDownloader
from .nodes.lora_loader import LoraLoaderExtended, LoraLoaderExtendedBatch
# # from .nodes.image_size import ImageGetSize
#
# # Registration Dictionary
NODE_CLASS_MAPPINGS = {
    "CivitAIWanLoraDownloader": CivitAIWanLoraDownloader,
    "LoraLoaderExtended": LoraLoaderExtended,
    "LoraLoaderExtendedBatch": LoraLoaderExtendedBatch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitAIWanLoraDownloader": "CivitAI → Wan LoRA Downloader",
    "LoraLoaderExtended": "LoRA Loader Extended",
    "LoraLoaderExtendedBatch": "LoRA Loader Extended (Batch)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]