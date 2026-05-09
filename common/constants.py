import os
import folder_paths

# ─── Global Configuration ───────────────────────────────────────────────
# Category prefix used in all node definitions
CATEGORY_PREFIX = "🎯 Stalkervr"

# ─── Wan LoRA Folder Setup ───────────────────────────────────────────────
WAN_LORAS_KEY = "loras/wan_loras"
WAN_LORAS_FULL_PATH = os.path.join(folder_paths.models_dir, WAN_LORAS_KEY)

# Register custom folder with ComfyUI's path resolver (runs once on import)
if WAN_LORAS_KEY not in folder_paths.folder_names_and_paths:
    folder_paths.add_model_folder_path(
        WAN_LORAS_KEY,
        WAN_LORAS_FULL_PATH
    )

# Ensure the directory exists on disk
os.makedirs(WAN_LORAS_FULL_PATH, exist_ok=True)