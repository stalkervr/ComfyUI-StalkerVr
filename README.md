# ComfyUI-StalkerVr

Advanced workflow tools for **Wan 2.2** video generation. This package provides a structured suite of nodes for downloading, managing, and applying paired LoRAs (High/Low noise), featuring centralized configuration, secure API key management, and batch processing capabilities.

## 📦 Installation

### Method 1: Via ComfyUI-Manager (Recommended)
1. Open **ComfyUI-Manager** in your ComfyUI interface.
2. Click **Install via Git URL**.
3. Paste the repository URL: `https://github.com/YOUR_USERNAME/ComfyUI-StalkerVr.git`
4. Click **Install** and restart ComfyUI.

### Method 2: Manual Installation
1. Open your terminal or command prompt.
2. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd path/to/ComfyUI/custom_nodes
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ComfyUI-StalkerVr.git
   ```
4. Install dependencies:
   ```bash
   cd ComfyUI-StalkerVr
   pip install -r requirements.txt
   ```
5. Restart ComfyUI to apply changes.

---

## 🔐 API Key Setup

1. Open the `data/` folder in this repository.
2. Rename `secrets.yaml.example` to `secrets.yaml`.
3. Open `secrets.yaml` and paste your API key:
   ```yaml
   civitai:
     api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxx"
   ```
4. (Optional) Edit `data/config.yaml` to control console logging:
   ```yaml
   logging:
     global_enabled: true
     node_settings:
       CivitAIWanLoraDownloader: true
       LoraLoaderExtended: true
       LoraLoaderExtendedBatch: true
   ```

> 🔒 `secrets.yaml` is automatically ignored by Git. Never commit real keys to the repository. Key resolution priority: Node Parameter → `secrets.yaml` → Public Config.

---

## 📥 CivitAI → Wan LoRA Downloader

Automatically downloads paired Wan 2.2 LoRAs (High & Low noise) directly from CivitAI and prepares them for immediate use. Creates the correct folder structure and generates a valid `lora.json` metadata file for seamless integration with the loader node.

### ✨ Key Features
- **Dual Platform Support:** Works with both `civitai.com` and `civitai.red` URLs.
- **Smart Caching:** The `Skip if Exists` toggle prevents redundant downloads and saves bandwidth.
- **Centralized Configuration:** Automatically reads the API key from `data/secrets.yaml` (can be overridden via node parameter).
- **Auto-Metadata Generation:** Creates `lora.json` with cleaned, deduplicated trigger words.
- **Structured Output:** Saves files to `models/loras/wan_loras/[subfolder]/[name]/`.

### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `model_page` | STRING | Optional URL to the model's CivitAI page (saved to JSON for reference). |
| `lora_name` | STRING | Name for the target folder and file prefix. |
| `high_url` | STRING | Direct API download URL for the High Noise model. |
| `low_url` | STRING | Direct API download URL for the Low Noise model. |
| `trigger_words` | STRING | Comma-separated trigger words (auto-cleaned & deduplicated). |
| `subfolder` | STRING | Optional path inside `wan_loras/` (e.g., `camera/motion`). |
| `civitai_api_key` | STRING | Optional override for the API key from `secrets.yaml`. |
| `skip_if_exists` | BOOLEAN | Skip download if files already exist (Default: `True`). |
| `enable_high` / `enable_low` | BOOLEAN | Toggle download for specific noise components. |

### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `status` | STRING | Execution summary (downloaded/skipped/failed counts). |
| `folder_path` | STRING | Absolute path to the created LoRA directory. |
| `trigger_words` | STRING | Cleaned trigger string for chaining into downstream nodes. |

### 📁 Resulting File Structure
```text
models/loras/wan_loras/
└── [subfolder]/
    └── [lora_name]/
        ├── [lora_name]_High.safetensors
        ├── [lora_name]_Low.safetensors
        └── lora.json
```

---

## 🔹 LoRA Loader Extended

Advanced single LoRA loader with enable/disable toggle, unified strength control, and automatic name chaining for workflow tracking.

### ✨ Key Features
- **Enable/Disable Toggle:** Dynamic workflow control without removing nodes.
- **Unified Strength:** Single slider applies to both MODEL and CLIP.
- **Name Chaining:** Automatic tracking of applied LoRAs via `NAME_STRING`.
- **Silent Bypass:** No console output when disabled or strength = 0.
- **Intelligent Caching:** Prevents redundant file loading.

### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | MODEL | Input model from previous nodes. |
| `clip` | CLIP | Input CLIP from previous nodes. |
| `lora_name` | COMBO | Dropdown list of available LoRAs. |
| `enable_lora` | BOOLEAN | Enable/disable LoRA application (Default: `True`). |
| `strength` | FLOAT | Unified strength for both MODEL and CLIP (-10.0 to 10.0). |
| `name_string` | STRING | Chain input: receives previous LoRA names. |

### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `MODEL` | MODEL | Model with LoRA applied (or bypassed). |
| `CLIP` | CLIP | CLIP with LoRA applied (or bypassed). |
| `NAME_STRING` | STRING | Combined list of all applied LoRA names (comma-separated). |

---

## 🔹 LoRA Loader Extended (Batch)

Process up to 5 LoRAs in a single node. Ideal for complex workflows requiring multiple style or character LoRAs simultaneously.

### ✨ Key Features
- **5 Independent Slots:** Individual enable toggles per LoRA.
- **Per-Slot Strength:** Separate control for each LoRA (unified for MODEL/CLIP).
- **Consolidated Output:** Single `NAME_STRING` combining all active slots.
- **Efficient Bypass:** Automatically skips disabled or zero-strength slots.

### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `model` / `clip` | MODEL / CLIP | Input model and CLIP. |
| `lora_name_1` to `5` | COMBO | 5 independent LoRA selectors. |
| `enable_1` to `5` | BOOLEAN | Individual slot toggles (Default: `True`). |
| `strength_1` to `5` | FLOAT | Per-slot strength control (-10.0 to 10.0). |
| `name_string` | STRING | Chain input from previous loaders. |

### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `MODEL` / `CLIP` | MODEL / CLIP | Model and CLIP with all active LoRAs applied. |
| `NAME_STRING` | STRING | Combined list of all applied LoRA names from all slots. |