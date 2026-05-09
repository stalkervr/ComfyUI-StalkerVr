# ComfyUI-StalkerVr

A versatile collection of custom nodes for ComfyUI, designed to streamline complex workflows and enhance productivity. This package provides a structured toolkit for asset management, model handling, and batch processing, featuring centralized configuration, secure API key management, and intelligent logging. Built with modularity in mind, it serves as a scalable foundation for efficient and maintainable ComfyUI workflows.

## 📦 Installation

### Method 1: Via ComfyUI-Manager (Recommended)
1. Open **ComfyUI-Manager** in your ComfyUI interface.
2. Click **Install via Git URL**.
3. Paste the repository URL: `https://github.com/stalkervr/ComfyUI-StalkerVr.git`
4. Click **Install** and restart ComfyUI.

### Method 2: Manual Installation
1. Open your terminal or command prompt.
2. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd path/to/ComfyUI/custom_nodes
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/stalkervr/ComfyUI-StalkerVr.git
   ```
4. Install dependencies:
   ```bash
   cd ComfyUI-StalkerVr
   pip install -r requirements.txt
   ```
5. Restart ComfyUI to apply changes.

---

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

---

### 📥 Wan Video Lora CivitAI Downloader

Automatically downloads paired Wan 2.2 LoRAs (High & Low noise) directly from CivitAI and prepares them for immediate use. Creates the correct folder structure and generates a valid `lora.json` metadata file for seamless integration with the loader node.

#### ✨ Key Features
- **Dual Platform Support:** Works with both `civitai.com` and `civitai.red` URLs.
- **Smart Caching:** The `Skip if Exists` toggle prevents redundant downloads and saves bandwidth.
- **Centralized Configuration:** Automatically reads the API key from `data/secrets.yaml` (can be overridden via node parameter).
- **Auto-Metadata Generation:** Creates `lora.json` with cleaned, deduplicated trigger words.
- **Structured Output:** Saves files to `models/loras/wan_loras/[subfolder]/[name]/`.

#### 📥 Input Parameters
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

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `status` | STRING | Execution summary (downloaded/skipped/failed counts). |
| `folder_path` | STRING | Absolute path to the created LoRA directory. |
| `trigger_words` | STRING | Cleaned trigger string for chaining into downstream nodes. |

#### 📁 Resulting File Structure
```text
models/loras/wan_loras/
└── [subfolder]/
    └── [lora_name]/
        ├── [lora_name]_High.safetensors
        ├── [lora_name]_Low.safetensors
        └── lora.json
```

---

### 🔹 Wan Video LoRA Pair Creator
Creates a paired Wan 2.2 LoRA folder from existing LoRAs in `models/loras/`. Copies selected high/low noise models, renames them to the expected format, and generates a matching `lora.json` for seamless integration with Wan loaders.

#### ✨ Key Features
- **Source Selection:** Dropdown lists populated from `models/loras/` for easy source LoRA selection.
- **Safe Copying:** Source files are copied, not moved—originals remain untouched.
- **Auto-Metadata:** Generates `lora.json` with cleaned, deduplicated trigger words and optional model page URL.
- **Overwrite Protection:** Skips creation if target files exist unless explicitly overridden.
- **Structured Output:** Saves to `models/loras/wan_loras/[subfolder]/[name]/` with consistent naming.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `model_page` | STRING | Optional URL to the model's page (saved to `lora.json` for reference). |
| `lora_name` | STRING | Name for the new folder and renamed files. |
| `high_noise_model` | COMBO | Source high noise LoRA from `models/loras/`. |
| `low_noise_model` | COMBO | Source low noise LoRA from `models/loras/`. |
| `trigger_words` | STRING | Comma-separated trigger words (auto-cleaned & deduplicated). |
| `subfolder` | STRING | Optional subfolder inside `wan_loras/` (e.g., `anime/style`). |
| `overwrite` | BOOLEAN | Replace existing files if target already exists (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `status` | STRING | Execution result: success, skipped, or error message. |
| `folder_path` | STRING | Absolute path to the created LoRA pair directory. |

#### 📁 Resulting File Structure
```text
models/loras/wan_loras/
└── [subfolder]/
    └── [lora_name]/
        ├── [lora_name]_High.safetensors
        ├── [lora_name]_Low.safetensors
        └── lora.json
```

---

### 🔹 Wan Video Enhance Motion Advanced KJ
Applies motion amplification with color drift protection to `image_embeds` from WanVideoImageToVideoEncode. Uses the PainterI2V algorithm with advanced color correction to enhance dynamic movement while preserving visual fidelity.

#### ✨ Key Features
- **Motion Amplification:** Increases temporal dynamics by scaling frame-to-frame differences (factor 1.0–1.5).
- **Color Drift Protection:** Automatically detects and corrects channel-wise color shifts to maintain consistency.
- **Brightness Stabilization:** Prevents unwanted darkening/brightening during motion enhancement.
- **Safe Latent Clamping:** Keeps values within WanVideo's expected range ([-6, 6]) to avoid artifacts.
- **Zero Overhead Bypass:** Returns input unchanged when `motion_amplitude = 1.0`.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `image_embeds` | WANVIDIMAGE_EMBEDS | Input embeddings from WanVideoImageToVideoEncode. |
| `motion_amplitude` | FLOAT | Amplification factor: 1.0 = disabled, >1.0 = more dynamic (range: 1.0–1.5). |
| `color_protect` | BOOLEAN | Enable automatic color drift correction (Default: `True`). |
| `correct_strength` | FLOAT | Strength of color correction (0.0 = none, 0.3 = strong; Default: `0.05`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `enhanced_image_embeds` | WANVIDIMAGE_EMBEDS | Modified embeddings with amplified motion and protected colors. |

#### ⚠️ Requirements
- Requires at least **2 frames** in the input sequence.
- Designed for use **after** `WanVideoImageToVideoEncode` and **before** the Wan sampler.
- GPU memory usage increases slightly due to tensor cloning and device transfers.

---

### 🔹 Wan Video Enhance Motion Advanced
Advanced motion enhancement with color drift protection for `CONDITIONING`/`LATENT` inputs. Outputs both enhanced and original conditioning sets for dual-sampler workflows (high/low noise branching). Based on PainterI2VAdvanced logic with adaptive color correction.

#### ✨ Key Features
- **Dual Output Design:** Returns enhanced + original conditioning for parallel high/low noise sampling.
- **Motion Amplification:** Scales temporal differences in latent space (factor 1.0–2.0) for more dynamic motion.
- **Color Drift Protection:** Auto-detects and corrects channel-wise color shifts to preserve visual fidelity.
- **Brightness Stabilization:** Prevents unwanted exposure changes during enhancement.
- **Format Agnostic:** Handles both tuple and list conditioning formats used by ComfyUI.
- **Zero Overhead Bypass:** Returns inputs unchanged when `motion_amplitude = 1.0`.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `positive` | CONDITIONING | Positive conditioning from text/image encoder. |
| `negative` | CONDITIONING | Negative conditioning for guidance. |
| `latent` | LATENT | Input latent with 5D shape `[B, C, T, H, W]`. |
| `vae` | VAE | VAE model (required for dimension inference). |
| `motion_amplitude` | FLOAT | Amplification factor: 1.0 = disabled, >1.0 = more dynamic (range: 1.0–2.0). |
| `color_protect` | BOOLEAN | Enable automatic color drift correction (Default: `True`). |
| `correct_strength` | FLOAT | Strength of color correction (0.0 = none, 0.3 = strong; Default: `0.05`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `high_positive` | CONDITIONING | Enhanced positive conditioning for high-noise sampler. |
| `high_negative` | CONDITIONING | Enhanced negative conditioning for high-noise sampler. |
| `low_positive` | CONDITIONING | Original positive conditioning for low-noise sampler. |
| `low_negative` | CONDITIONING | Original negative conditioning for low-noise sampler. |
| `latent` | LATENT | Unmodified input latent (passthrough). |

#### ⚠️ Requirements
- Requires `concat_latent_image` parameter in positive conditioning (set by `WanVideoImageToVideoEncode`).
- Input latent must be 5D: `[Batch, Channels, Time, Height, Width]`.
- Designed for use **before** dual KSampler nodes in Wan 2.2 workflows.

---

### 🔹 Wan Video LoRA Pair Select
Loads Wan 2.2 LoRA pair metadata from structured folders and returns chained `WANVIDLORA` lists. Supports `[none]` passthrough, automatic trigger word merging, and real-time UI metadata display for workflow transparency.

#### ✨ Key Features
- **Auto-Discovery:** Scans `models/loras/wan_loras/` for folders containing valid `lora.json`.
- **Chaining Support:** Seamlessly chains multiple pairs via `prev_high_lora` / `prev_low_lora` inputs.
- **Smart Passthrough:** Selecting `[none]` bypasses processing and forwards previous inputs unchanged.
- **Trigger Merging:** Automatically deduplicates and combines trigger words across chained nodes.
- **UI Metadata Panel:** Displays live folder status, availability, and merged triggers in the ComfyUI interface.
- **Granular Control:** Independent enable/strength toggles for high and low noise components.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `lora_folder` | COMBO | Dropdown of valid Wan LoRA folders + `[none]` option. |
| `high_strength` | FLOAT | Strength for high noise LoRA (range: -1000.0 to 1000.0). |
| `enable_high` | BOOLEAN | Toggle high noise LoRA application (Default: `True`). |
| `low_strength` | FLOAT | Strength for low noise LoRA (range: -1000.0 to 1000.0). |
| `enable_low` | BOOLEAN | Toggle low noise LoRA application (Default: `True`). |
| `prev_high_lora` | WANVIDLORA | Chained high noise LoRA list from upstream nodes. |
| `prev_low_lora` | WANVIDLORA | Chained low noise LoRA list from upstream nodes. |
| `prev_trigger_words` | STRING | Chained trigger words string from upstream nodes. |
| `blocks` | SELECTEDBLOCKS | Optional block/layer selection for fine-tuned application. |
| `low_mem_load` | BOOLEAN | Enable low VRAM loading mode (Default: `False`). |
| `merge_loras` | BOOLEAN | Merge LoRAs directly into model weights (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `high_lora` | WANVIDLORA | List of high noise LoRA configs ready for loader. |
| `low_lora` | WANVIDLORA | List of low noise LoRA configs ready for loader. |
| `trigger_words` | STRING | Deduplicated, merged trigger string for downstream use. |

---

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

---

---

### 🔹 Current Date Time
Returns the current date and time as a formatted string (YYYYMMDD base). Supports cascading precision toggles where enabling seconds automatically enables minutes and hours. Forces execution on every queue cycle for real-time timestamps.

#### ✨ Key Features
- **Real-Time Execution:** Uses `IS_CHANGED = NaN` to generate fresh timestamps on every workflow run.
- **Cascading Precision:** Automatically enables lower units (e.g., seconds → minutes + hours) to maintain valid format structure.
- **Base Format:** Always starts with `YYYYMMDD` for sortable, unambiguous date strings.
- **Zero-Input Design:** Operates independently without requiring upstream connections.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `include_hours` | BOOLEAN | Append hours (HH) to the timestamp (Default: `False`). |
| `include_minutes` | BOOLEAN | Append minutes (MM). Auto-enables hours if toggled (Default: `False`). |
| `include_seconds` | BOOLEAN | Append seconds (SS). Auto-enables hours & minutes if toggled (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `date_time` | STRING | Formatted timestamp string (e.g., `20260401`, `20260401090534`). |

---

### 🔹 Calculate Frame Count
Computes total frame count for video generation using the formula: `frames = (duration_seconds × fps) + 1`. The +1 offset ensures the starting frame (frame 0) is included in the count.

#### ✨ Key Features
- **Precise Calculation:** Uses integer math for exact frame counts without floating-point errors.
- **Bounded Inputs:** Enforces sensible ranges for duration (1–300s) and fps (12–60) to prevent invalid workflows.
- **Tooltip Guidance:** Inline help text explains each parameter directly in the ComfyUI interface.
- **Zero Dependencies:** Pure logic node with no external libraries or side effects.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `duration_seconds` | INT | Video duration in seconds (range: 1–300, step: 1). |
| `fps` | INT | Frames per second (range: 12–60, step: 4). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `frame_count` | INT | Total number of frames including the starting frame (frame 0). |

---

### 🔹 Switch Any
Conditional routing node with lazy evaluation. Passes through the selected input (`on_true` or `on_false`) based on a boolean condition, evaluating only the active branch to save computation.

#### ✨ Key Features
- **Lazy Evaluation:** Skips processing for the unselected branch, improving workflow performance.
- **Wildcard Support:** Accepts any data type via `*` connectors for maximum flexibility.
- **Zero Overhead Passthrough:** Directly routes selected data without modification or copying.
- **Dynamic Branching:** Ideal for conditional workflows, model swapping, or feature toggles.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `condition` | BOOLEAN | Toggle to select output branch (Default: `False` → `on_false`). |
| `on_true` | * | Wildcard input routed when condition is `True`. |
| `on_false` | * | Wildcard input routed when condition is `False`. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `passthrough` | * | Direct output from the selected branch (`on_true` or `on_false`). |

---

### 🔹 Logger
Enhanced console logger with passthrough functionality, structured log output, and customizable console colors. Accepts wildcard inputs and formats pipeline data for debugging and tracking.

#### ✨ Key Features
- **Wildcard Input:** Accepts any ComfyUI data type via `*` connector.
- **Passthrough Mode:** Outputs the exact same value unchanged for seamless pipeline integration.
- **Custom Console Colors:** Choose from 8 terminal colors for better visual tracking in workflows.
- **Structured Logging:** Generates clean, readable log strings with type and value inspection.
- **Configurable Output:** Toggle console printing on/off without breaking the workflow.
- **Force Execution:** Runs on every queue cycle (`IS_CHANGED = NaN`) for real-time debugging.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `any_value` | * | Wildcard input: accepts any data type (tensors, dicts, strings, etc.). |
| `checkpoint_name` | STRING | Custom label for the log entry (Default: `default`). |
| `text_color` | COMBO | Console text color: `default`, `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, `white`. |
| `console` | BOOLEAN | Enable/disable console output (Default: `True`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `passthrough` | * | Exact copy of the input value, unchanged. |
| `log_string` | STRING | Formatted log string containing checkpoint name, type, and value (clean, no ANSI codes). |

---

---

### 🔹 Json Field Value Extractor
Extracts a specific field value from a JSON string using dot notation, preserving the original data type. Includes a passthrough output for seamless pipeline chaining.

#### ✨ Key Features
- **Dot Notation Support:** Navigate nested JSON objects using `parent.child.key` syntax.
- **Type Preservation:** Returns values as their native Python types (string, number, list, dict, etc.) for direct use in downstream nodes.
- **Exact Passthrough:** Outputs the original JSON string unchanged to prevent data loss in complex workflows.
- **Graceful Fallback:** Returns `None` on missing keys or invalid JSON without breaking the workflow.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `json_string` | STRING | Valid JSON string to parse. |
| `key` | STRING | Target field path using dot notation (e.g., `info.city`). |

####  Outputs
| Output | Type | Description |
|--------|------|-------------|
| `value` | * | Extracted value in its original type, or `None` if not found. |
| `json_passthrough` | STRING | Exact copy of the input JSON string for chaining. |

---

### 🔹 Json Field Remover
Removes specified fields from a JSON string using dot-notation paths. Supports multiple paths separated by `|` and returns a cleanly formatted JSON string.

#### ✨ Key Features
- **Multi-Path Support:** Remove multiple fields in a single pass using `|` delimiter.
- **Dot Notation Navigation:** Safely traverse nested JSON objects to target specific keys.
- **Safe Deletion:** Gracefully handles missing paths without throwing errors or breaking the workflow.
- **Auto-Formatting:** Outputs a properly indented, human-readable JSON string.

#### 📥 Input Parameters
| Parameter | Type | Description                                                       |
|-----------|------|-------------------------------------------------------------------|
| `json_string` | STRING | Valid JSON string to process.                                     |
| `key` | STRING | Dot-notation paths to remove, separated by `|` (e.g., `path.to.field1 | path.to.field2`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `json_string` | STRING | Modified JSON string with specified fields removed and formatted with indentation. |

---

### 🔹 Json Field Replace Extend
Adds or replaces a field in a JSON string using dot-notation paths. Supports array indexing, automatic type casting, and optional value extension for string concatenation workflows.

####  Key Features
- **Dot & Array Notation:** Navigate and modify nested objects or arrays using paths like `parent.child` or `arr.0.id`.
- **Smart Type Casting:** Automatically converts input strings to `int`, `float`, `bool`, `null`, or valid JSON objects before assignment.
- **Value Extension:** When enabled, prepends new values to existing strings (`new_value, old_value`) instead of overwriting.
- **Safe Fallback Parsing:** Gracefully handles Python `repr()`-style dictionary strings if standard JSON parsing fails.
- **Silent Bypass:** Skips processing and returns the original JSON if the value field is empty.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `json_string` | STRING | Valid JSON string or dictionary-like structure to modify. |
| `key` | STRING | Dot-notation target path (e.g., `settings.theme` or `users.0.name`). |
| `value` | STRING | Value to assign. Auto-casts to native types or JSON structures. |
| `extend_value` | BOOLEAN | If `True`, prepends value to existing string instead of replacing (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `json_string` | STRING | Modified JSON string with updated/added fields, formatted with indentation. |

---

### 🔹 Json Prompt To Text Prompt Converter
Converts a JSON object into a plain text prompt by extracting only values, ignoring keys. Automatically formats strings and lists with proper punctuation, filters empty data, and supports single-line or newline output.

####  Key Features
- **Value-Only Extraction:** Strips JSON keys, preserving only semantic values for clean prompt generation.
- **Auto-Punctuation:** Appends periods to strings and comma-separates list items, ending with a period.
- **Null/Empty Filtering:** Silently skips `null`, empty strings, and empty lists to prevent prompt pollution.
- **Recursive Flattening:** Handles deeply nested dictionaries and arrays without losing data structure context.
- **Flexible Formatting:** Toggle between space-separated or newline-separated output for multi-line prompts.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `json_string` | STRING | Valid JSON object to parse. |
| `new_line` | BOOLEAN | Join extracted values with newlines instead of spaces (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `prompt` | STRING | Extracted values formatted as a continuous text prompt. |

---

### 🔹 Json Serialize Object
Serializes single Python objects or lists of objects into JSON strings. Designed for batch processing in ComfyUI workflows, converting arbitrary data structures (dicts, lists, primitives) into a standardized string format.

#### ✨ Key Features
- **Wildcard Input:** Accepts any Python object type via `*` connector.
- **Batch Processing:** Automatically wraps single objects into a list; handles pre-existing lists natively.
- **ComfyUI List Output:** Uses `OUTPUT_IS_LIST` to return a batch of JSON strings compatible with downstream nodes.
- **Safe Fallback:** Replaces unserializable objects with an empty string instead of breaking the workflow.
- **Unicode Support:** Preserves non-ASCII characters in output strings.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `input_data` | * | Single object or list of objects to serialize. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `output` | * | List of JSON strings, one per input item. |

---

### 🔹 Json Deserialize Object
Deserializes single JSON strings or lists of strings back into native Python objects. Designed for batch processing in ComfyUI workflows, converting standardized JSON strings back into dictionaries, lists, or primitives.

#### ✨ Key Features
- **Wildcard Input:** Accepts any input type, automatically routing strings or lists of strings.
- **Batch Processing:** Wraps single strings into a list; processes pre-existing lists natively.
- **ComfyUI List Output:** Uses `OUTPUT_IS_LIST` to return a batch of Python objects for downstream nodes.
- **Safe Fallback:** Replaces invalid or non-string inputs with `None` instead of breaking the workflow.
- **Error Isolation:** Handles malformed JSON per-item, preserving valid objects in the batch.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `input_data` | * | Single JSON string or list of JSON strings to deserialize. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `output` | * | List of deserialized Python objects (dicts, lists, primitives, or `None` on error). |

---

### 🔹 Json Format
Takes a JSON string (formatted or minified) and outputs a pretty-printed version. Useful for human-readable logging, debugging, or file saving.

#### ✨ Key Features
- **Auto-Formatting:** Converts minified or irregular JSON into a clean, indented structure.
- **Configurable Output:** Toggle ASCII escaping and key sorting for consistent serialization.
- **Graceful Error Handling:** Returns the original string or a clear error message based on workflow needs.
- **Silent Bypass:** Safely handles empty inputs without throwing exceptions.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `json_string` | STRING | Valid JSON string to format. |
| `ensure_ascii` | BOOLEAN | Escape non-ASCII characters to `\uXXXX` sequences (Default: `False`). |
| `sort_keys` | BOOLEAN | Sort dictionary keys alphabetically (Default: `False`). |
| `on_error_return_original` | BOOLEAN | Return original string on parse failure instead of an error message (Default: `True`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `pretty_json` | STRING | Formatted JSON string with 4-space indentation. |

---

### 🔹 Json Minify
Takes a pretty-printed JSON string and outputs a minified (compact) version. Removes all unnecessary whitespace, newlines, and indentation for efficient storage or transmission.

#### ✨ Key Features
- **Compact Serialization:** Strips all formatting to produce the smallest possible valid JSON string.
- **Configurable Output:** Toggle ASCII escaping and key sorting for consistent, deterministic minification.
- **Graceful Error Handling:** Returns the original string or a clear error message based on workflow needs.
- **Silent Bypass:** Safely handles empty inputs without throwing exceptions.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `json_string` | STRING | Valid JSON string to minify. |
| `ensure_ascii` | BOOLEAN | Escape non-ASCII characters to `\uXXXX` sequences (Default: `False`). |
| `sort_keys` | BOOLEAN | Sort dictionary keys alphabetically (Default: `False`). |
| `on_error_return_original` | BOOLEAN | Return original string on parse failure instead of an error message (Default: `True`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `minified_json` | STRING | Compact JSON string with all whitespace removed. |

---

### 🔹 Json Path Loader
Loads all JSON files from a specified folder. Forces re-execution to ensure fresh scans, supports sorting, limiting, and automatic output type inference.

#### ✨ Key Features
- **Fresh Scans:** `IS_CHANGED` uses a random seed to force re-execution, ensuring newly added files are always detected.
- **Flexible Sorting:** Sort files by name, creation date, modification date, or size (ascending/descending).
- **Batch Limit:** Control the number of files loaded to prevent memory overload.
- **Type Inference:** Automatically detects if loaded content is `INT`, `FLOAT`, `STRING`, or mixed, adjusting the output type accordingly.
- **Formatted Output:** Parses and re-dumps JSON with 4-space indentation for readability.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `folder_path` | STRING | Absolute or relative path to the folder containing JSON files. |
| `sort_by` | COMBO | Sorting criteria: `name`, `created`, `modified`, `size` (with `_desc` variants). |
| `limit` | INT | Maximum number of files to load. `0` loads all files (Default: `0`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `output` | * | List of formatted JSON strings. Type adapts based on content (INT/FLOAT/STRING/*). |

---

### 🔹 Json Builder
Builds a JSON object from dynamic key-value pairs. Supports nested keys via dot notation, automatically skips empty fields, and outputs a cleanly formatted JSON string.

#### ✨ Key Features
- **Dynamic Pair Input:** Configurable number of key/value slots (1–100) via a single slider.
- **Nested Key Support:** Use dot notation (e.g., `user.profile.name`) to create nested JSON structures.
- **Empty Field Filtering:** Automatically ignores empty keys or values to keep output clean.
- **Formatted Output:** Returns a pretty-printed JSON string ready for downstream nodes or file saving.

#### 📥 Input Parameters
| Parameter                | Type | Description                                           |
|--------------------------|------|-------------------------------------------------------|
| `num_pairs`              | INT | Number of key-value pairs to process (range: 1–100).  |
| `key_1` to `key_100`     | STRING | Field names. Supports dot notation for nesting.       |
| `value_1` to `value_100` | STRING | Field values. Empty values are automatically skipped. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `json_output` | STRING | Formatted JSON string containing all valid key-value pairs. |

---

### 🔹 Json Pair Input
Creates a key-value pair with automatic type detection. Accepts any input type via wildcard, attempts to parse strings as JSON/numbers/booleans, and falls back to plain text if conversion fails.

#### ✨ Key Features
- **Wildcard Input:** Accepts any ComfyUI data type or raw string.
- **Smart Type Conversion:** Automatically converts strings to `int`, `float`, `bool`, `None`, or complex JSON structures.
- **Safe Fallback:** Returns the original string if type detection fails, preventing workflow breaks.
- **Disconnected Input Handling:** Treats unconnected or empty value slots as `None`.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | STRING | Field name for the JSON pair. |
| `value` | * | Field value. Supports auto-conversion from string or direct passthrough. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `key` | STRING | Normalized string key. |
| `value` | * | Converted value in its detected native type, or `None` if empty/unconnected. |

---

---

### 🔹 String Builder
Concatenates multiple string inputs with a configurable separator. Supports optional newline injection for multi-line prompt construction.

#### ✨ Key Features
- **Dynamic Input Count:** Adjustable number of string slots (0–100) via `num_inputs` slider.
- **Flexible Separator:** Custom delimiter between segments (space, comma, custom text).
- **Newline Mode:** Injects line breaks while preserving separator formatting for structured prompts.
- **Type Safety:** Automatically converts all inputs to strings before concatenation.

#### 📥 Input Parameters
| Parameter | Type | Description                                                       |
|-----------|------|-------------------------------------------------------------------|
| `num_inputs` | INT | Number of string slots to process (range: 2–100).                 |
| `separator` | STRING | Delimiter inserted between each string segment (Default: `" "`).  |
| `newline` | BOOLEAN | Enable newline injection after each separator (Default: `False`). |
| `string_1` to `string_N` | STRING | Dynamic string inputs added based on `num_inputs`.                |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `STRING` | STRING | Final concatenated result with applied separator and newline logic. |

---

### 🔹 String Wrapper
Wraps input text with configurable prefix and suffix strings. Automatically trims whitespace and intelligently skips empty segments to produce clean, concatenated output.

#### ✨ Key Features
- **Smart Concatenation:** Joins non-empty parts with single spaces, avoiding double-spacing.
- **Whitespace Normalization:** Automatically strips leading/trailing whitespace from all inputs.
- **Empty Segment Handling:** Silently ignores empty prefix/suffix to prevent awkward spacing.
- **Simple Interface:** Three straightforward inputs for predictable text composition.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `prefix` | STRING | Optional text to prepend (trimmed, skipped if empty). |
| `input_text` | STRING | Main text content to wrap (trimmed). |
| `suffix` | STRING | Optional text to append (trimmed, skipped if empty). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `STRING` | STRING | Combined result: `prefix + input_text + suffix` with intelligent spacing. |

---

### 🔹 String Normalize
Cleans text input by removing line breaks and collapsing multiple whitespace characters into a single space. Ideal for sanitizing prompts, JSON values, or any user-generated text.

#### ✨ Key Features
- **Universal Input:** Accepts any data type via wildcard connector, auto-converting to string.
- **Whitespace Collapsing:** Replaces all whitespace sequences (`\n`, `\r`, `\t`, multiple spaces) with a single space.
- **Trimming:** Automatically removes leading and trailing whitespace from the result.
- **Safe Fallback:** Handles `None` or empty inputs gracefully without errors.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `string` | * | Input text or any value to normalize (auto-converted to string). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `normalized_string` | STRING | Cleaned text with single-space separators and no leading/trailing whitespace. |

---

---

### 🔹 Image Grid Cropper
Splits images or image batches into a grid of fixed-size crops. Automatically pads edge crops to maintain uniform dimensions, and optionally saves results directly to disk.

#### ✨ Key Features
- **Batch & Single Support:** Handles both `[B, H, W, C]` and `[H, W, C]` tensor formats seamlessly.
- **Automatic Padding:** Edge crops smaller than the target size are zero-padded to ensure uniform output.
- **Optional Disk Export:** Saves each crop as a PNG file with customizable naming patterns.
- **Channel Agnostic:** Supports grayscale (1), RGB (3), and RGBA (4) images.
- **Deterministic Output:** Returns a stacked batch of crops ready for downstream processing.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | IMAGE | Input image tensor or batch of tensors. |
| `rows` | INT | Number of grid rows (Default: `2`). |
| `cols` | INT | Number of grid columns (Default: `2`). |
| `block_width` | INT | Target crop width in pixels (Default: `256`). |
| `block_height` | INT | Target crop height in pixels (Default: `256`). |
| `save_path` | STRING | Directory path for saving cropped images. |
| `filename` | STRING | Base filename for saved crops (e.g., `crop`). |
| `save_to_folder` | BOOLEAN | Enable/disable disk saving (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `images` | IMAGE | Batch tensor containing all cropped regions `[rows*cols, H, W, C]`. |

---

### 🔹 Image Cropper
Crops images from a batch using explicit margin offsets (left, right, top, bottom). Supports optional size restoration via bilinear interpolation and direct disk export.

#### ✨ Key Features
- **Margin-Based Cropping:** Precise control over crop boundaries from all four sides.
- **Size Restoration:** Optionally resizes cropped regions back to original dimensions using bilinear interpolation.
- **Batch Processing:** Handles `[B, H, W, C]` tensors natively.
- **Disk Export:** Saves each cropped frame as a PNG with sequential indexing.
- **Channel Agnostic:** Supports grayscale (1), RGB (3), and RGBA (4) images.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `images` | IMAGE | Input batch tensor `[B, H, W, C]`. |
| `left` | INT | Pixels to crop from the left edge (Default: `0`). |
| `right` | INT | Pixels to crop from the right edge (Default: `0`). |
| `top` | INT | Pixels to crop from the top edge (Default: `0`). |
| `bottom` | INT | Pixels to crop from the bottom edge (Default: `0`). |
| `restore_size` | BOOLEAN | Resize cropped output back to original `H x W` (Default: `False`). |
| `save_path` | STRING | Directory path for saving cropped images. |
| `filename` | STRING | Base filename for saved crops (e.g., `crop`). |
| `save_to_folder` | BOOLEAN | Enable/disable disk saving (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `cropped_images` | IMAGE | Cropped (and optionally resized) batch tensor. |

---

### 🔹 Image Ratio Resizer
Resizes images to a specific aspect ratio while maintaining original proportions. Uses a "cover" strategy with center cropping to achieve the target ratio without distortion or padding.

#### ✨ Key Features
- **Smart Orientation Detection:** Automatically swaps landscape ratios to portrait equivalents when processing vertical images.
- **Cover-Mode Resizing:** Scales image to fully cover target dimensions, then center-crops for clean composition.
- **Batch Support:** Handles both single `[H, W, C]` and batch `[B, H, W, C]` tensors.
- **Preset & Custom Ratios:** Choose from common aspect ratios or define custom `x:y` values.
- **Dimension Output:** Returns final width/height integers for downstream node coordination.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | IMAGE | Input image tensor or batch. |
| `aspect_ratio` | COMBO | Target ratio preset or `custom` (Default: `16:9 (Landscape)`). |
| `custom_x` | INT | Custom ratio width component (used only if `aspect_ratio == "custom"`). |
| `custom_y` | INT | Custom ratio height component (used only if `aspect_ratio == "custom"`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `resized_image` | IMAGE | Image cropped/resized to exact target aspect ratio. |
| `width` | INT | Final output width in pixels. |
| `height` | INT | Final output height in pixels. |

---

### 🔹 Image Get Size
Extracts width, height, and resolution from an input image tensor. Useful for dynamic workflow branching based on image dimensions.

#### ✨ Key Features
- **Batch-Aware:** Correctly reads dimensions from ComfyUI's `[B, H, W, C]` tensor format.
- **Flexible Resolution:** Toggle between minimum or maximum side length for adaptive workflows.
- **Triple Output:** Returns width, height, and selected resolution in a single call.
- **Zero Overhead:** Pure metadata extraction with no image copying or processing.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | IMAGE | Input image tensor (single or batch). |
| `use_min_side` | BOOLEAN | If `True`, returns `min(width, height)` as resolution; else `max()` (Default: `True`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `width` | INT | Image width in pixels. |
| `height` | INT | Image height in pixels. |
| `resolution` | INT | Selected side length (`min` or `max`) for conditional logic. |

---

### 🔹 Image Desired Resolution
Crops and resizes images to match target aspect ratios for BiRefNet/WAN pipelines. Supports optional image input for dimension-only calculation mode.

#### ✨ Key Features
- **Optional Image Input:** Returns computed dimensions even without an image connected, enabling dynamic resolution planning.
- **Aspect Ratio Presets:** Supports common ratios (21:9, 16:9, 4:3, 3:2, 1:1) with automatic orientation handling.
- **Center Crop Strategy:** Crops to target ratio before resizing to preserve composition and avoid distortion.
- **16-Pixel Alignment:** All output dimensions are rounded up to multiples of 16 for model compatibility.
- **Batch Processing:** Handles `[B, H, W, C]` tensors natively.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | IMAGE | Optional input image tensor. If omitted, only dimensions are computed. |
| `min_side` | INT | Minimum side length in pixels (range: 360–1440, step: 16). |
| `aspect_ratio` | COMBO | Target aspect ratio preset (Default: `16:9`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `image` | IMAGE | Resized image tensor, or `None` if no input was provided. |
| `width` | INT | Final output width (aligned to 16px). |
| `height` | INT | Final output height (aligned to 16px). |

---

### 🔹 Images Load With Metadata
Batch loads all supported images from a directory, extracting embedded metadata and alpha masks. Returns true lists for seamless pipeline iteration.

#### ✨ Key Features
- **Universal Format Support:** PNG, JPG, JPEG, WEBP, BMP, TIFF.
- **Metadata Extraction:** Reads PNG text chunks, EXIF data, and `comfy_metadata` JSON blobs.
- **Smart Type Conversion:** Automatically restores native Python types from string values.
- **Alpha Handling:** Extracts transparency as inverted ComfyUI-compatible masks.
- **Flexible Sorting:** By name, modification date, or filesystem order.
- **Key Filtering:** Extract specific metadata fields across the entire batch.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `directory_path` | STRING | Path to image directory. |
| `sort_by` | COMBO | `name`, `date`, or `none`. |
| `extract_key` | STRING | Optional dot-notation key to extract separately. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `image` | IMAGE | List of image tensors `[B, H, W, C]`. |
| `mask` | MASK | List of alpha masks or empty tensors. |
| `metadata_json` | STRING | Full metadata JSON per image. |
| `metadata_value` | STRING | Extracted value for `extract_key` (or empty). |

---

### 🔹 Image Load With Metadata
Loads a single uploaded image with global metadata caching. Designed to survive mask editor resets and maintain prompt/metadata context across sessions.

#### ✨ Key Features
- **Global JS Cache:** Automatically updates metadata on file selection via ComfyUI extension.
- **Mask Editor Safe:** Retains cached metadata even when ComfyUI generates temp clipspace files.
- **Nested Key Support:** Extract deep values using dot notation (e.g., `settings.model.seed`).
- **Fallback Parsing:** Reads metadata directly from file if cache is empty.
- **Standard Output:** Compatible with all native ComfyUI image/mask pipelines.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `image` | COMBO | Dropdown of uploaded images in `input/` directory. |
| `extract_key` | STRING | Optional dot-notation key to extract. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `image` | IMAGE | Loaded image tensor `[1, H, W, C]`. |
| `mask` | MASK | Alpha channel mask or empty tensor. |
| `metadata_json` | STRING | Complete metadata JSON. |
| `metadata_value` | STRING | Extracted nested value or empty string. |

---

### 🔹 Image Save With Metadata
Saves images as PNG with embedded custom metadata, workflow data, and optional captions. No preview overhead; optimized for reliable batch archiving.

#### ✨ Key Features
- **Metadata Embedding:** Stores JSON in PNG `tEXt`/`zTXt`/`iTXt` chunks automatically.
- **Workflow Preservation:** Optionally saves full ComfyUI generation graph.
- **Sequential Numbering:** Auto-increments filenames based on existing PNGs only.
- **Caption Export:** Saves matching `.txt` files for prompt tracking.
- **Compression Control:** Adjustable PNG compression level (0–9).
- **Universal Paths:** Supports absolute/relative directories; auto-creates missing folders.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `images` | IMAGE | Input image batch. |
| `save_directory` | STRING | Target output path. |
| `filename_prefix` | STRING | Prefix for sequential naming. |
| `save_workflow` | BOOLEAN | Embed ComfyUI workflow JSON (Default: `True`). |
| `metadata_json` | STRING | Custom metadata to embed. |
| `compression_level` | INT | PNG compression 0–9 (Default: `4`). |
| `captions` | STRING | Optional text for `.txt` export. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `images` | IMAGE | Passthrough of input images. |
| `saved_paths` | STRING | Comma-separated list of saved file paths. |

---

---

### 🔹 Format Date Path
Generates a dynamic file path by replacing custom date/time tokens with the current system time. Forces re-execution on every run to ensure timestamps are always up-to-date.

#### ✨ Key Features
- **Real-Time Generation:** Uses `IS_CHANGED = NaN` to guarantee fresh paths on every workflow execution.
- **Custom Token Syntax:** Supports `%date:yyyy-MM-dd%`, `%date:hhmmss%`, and standard Python `strftime` formats.
- **Automatic Mapping:** Converts common UI tokens (`yyyy`, `MM`, `dd`, `HH`, `hh`, `mm`, `ss`) to Python `strftime` codes.
- **Error Fallback:** Returns a clear error string if template parsing fails, preventing workflow crashes.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `template` | STRING | Path string containing `%date:...%` placeholders. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `formatted_path` | STRING | Fully resolved path with current date/time inserted. |

---

### 🔹 File Save Path
Constructs a structured absolute path for saving files based on project root, name, content type, and current date. Ideal for organizing generative outputs in a consistent, date-partitioned directory tree.

#### ✨ Key Features
- **Hierarchical Path Building:** Automatically assembles `{root}/{project}/{type}/{YYYY-MM-DD}/`.
- **System Expansion:** Resolves `~` and relative paths to absolute system paths via `expanduser().resolve()`.
- **Auto-Date Partitioning:** Appends current date to keep outputs organized chronologically.
- **Project Tracking:** Returns both the full path and the project name for downstream routing.
- **Safe Fallback:** Returns a clear error string on path construction failure without breaking the workflow.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_root` | STRING | Base directory for all projects (supports `~` expansion). |
| `project_name` | STRING | Subfolder name for the current project. |
| `sub_folder_name` | STRING | Content type folder (e.g., `image`, `video`, `audio`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `save_path` | STRING | Complete absolute path ending with today's date. |
| `project_name` | STRING | Passthrough of the input project name. |

---

### 🔹 Save Text File
Saves text content to disk with dynamic date formatting, sequential numbering, and automatic collision handling. Designed for logging prompts, metadata, and workflow outputs.

#### ✨ Key Features
- **Date Placeholders:** Use `%date:yyyy-MM-dd%` or `%date:hhmmss%` in paths/filenames for real-time stamping.
- **Smart Numbering:** Toggle between forced sequential numbering (`_00001`) or fallback numbering only when a file exists.
- **Auto-Collision Avoidance:** Never overwrites existing files; automatically appends next available index.
- **Extension Management:** Strips accidental double extensions and supports `.txt`, `.json`, `.info`, `.meta`, `.log`.
- **Empty Input Guard:** Silently skips saving if input text is empty or contains only whitespace.
- **Force Execution:** `IS_CHANGED = NaN` ensures timestamps and file checks run on every workflow trigger.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_root` | STRING | Base directory for all outputs (supports `~` expansion). |
| `folder_path` | STRING | Subfolder path with optional `%date:...%` placeholders. |
| `file_name` | STRING | Base filename with optional `%date:...%` placeholders. |
| `extension` | COMBO | File extension (`.txt`, `.json`, `.info`, `.meta`, `.log`). |
| `text` | STRING | Content to write to the file. |
| `use_numbering` | BOOLEAN | Force `_NNNNN` suffix, or use only when file exists (Default: `False`). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| *(None)* | - | `OUTPUT_NODE` only. File is written directly to disk. |

---

---

### 🔹 YAML Save Prompt
Saves positive and negative prompts into a hierarchically organized YAML database. Supports person → type → group → sub-group nesting with automatic whitespace normalization and toggle-controlled saving.

#### ✨ Key Features
- **Hierarchical Storage:** Organizes prompts by `person_name → prompt_type → group_name → [sub_group]`.
- **Toggle Protection:** Only writes to disk when `save_enabled` is `True`.
- **Auto-Cleaning:** Flattens multiline inputs into single-line strings with normalized spacing.
- **Safe Append Logic:** Loads existing database, appends new entry, and preserves YAML structure.
- **Corruption Fallback:** Automatically resets to an empty database if the target YAML file is malformed.
- **Passthrough Outputs:** Returns original prompts unchanged for downstream node chaining.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `positive_prompt` | STRING | Main prompt text to save. |
| `negative_prompt` | STRING | Negative prompt text to save. |
| `save_enabled` | BOOLEAN | Master switch to trigger disk write (Default: `False`). |
| `file_path` | STRING | Target YAML database path (supports relative/absolute). |
| `person_name` | STRING | Top-level author/project key. |
| `prompt_type` | COMBO | `text-to-image` or `image-to-video`. |
| `group_name` | STRING | Category name for grouping related prompts. |
| `sub_group_name` | STRING | Optional sub-category (leave empty to store at group root). |
| `prompt_name` | STRING | Descriptive label for the specific prompt entry. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `positive_prompt` | STRING | Passthrough of the original positive prompt. |
| `negative_prompt` | STRING | Passthrough of the original negative prompt. |

---

### 🔹 YAML Load Prompt
Loads prompts from a hierarchical YAML database as synchronized lists of positive and negative strings. Designed for seamless iteration with `OUTPUT_IS_LIST` and ComfyUI loop nodes.

#### ✨ Key Features
- **Synchronized List Output:** Returns matching positive/negative pairs via `OUTPUT_IS_LIST = (True, True)`.
- **Targeted Filtering:** Optionally filter by `prompt_name` for precise retrieval.
- **Limit Control:** Cap the number of returned prompts to prevent workflow overload.
- **Hierarchical Navigation:** Resolves `person → type → group → [sub_group]` paths automatically.
- **Force Refresh:** `IS_CHANGED = NaN` ensures database is re-read on every execution.
- **Graceful Fallback:** Returns empty lists if file/path is missing or malformed, never breaking the graph.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | STRING | Path to the YAML prompts database. |
| `person_name` | STRING | Top-level author/project key. |
| `prompt_type` | COMBO | `text-to-image` or `image-to-video`. |
| `group_name` | STRING | Category/group name within the hierarchy. |
| `sub_group_name` | STRING | Optional sub-category (leave empty to load entire group). |
| `prompt_name` | STRING | Optional exact match filter for a specific prompt. |
| `limit` | INT | Maximum number of prompt pairs to return (`0` = unlimited). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `POSITIVE` | STRING | List of positive prompt strings. |
| `NEGATIVE` | STRING | List of negative prompt strings (synchronized with positive). |

---

---

### 🔹 Save Video With Metadata
Encodes image batches to MP4 with embedded metadata (title, artist, genre, etc.) and optional cover image. Uses FFmpeg with quality presets for lossless, high, or medium output.

#### ✨ Key Features
- **Quality Presets:** `lossless` (CRF 0), `high` (CRF 17), `medium` (CRF 23) with matching FFmpeg presets.
- **Metadata Embedding:** Supports standard MP4 tags via `-metadata` flags.
- **Cover Image:** Attaches thumbnail as `attached_pic` disposition.
- **Fast Start:** `-movflags +faststart` for web streaming compatibility.
- **Force Execution:** `IS_CHANGED = NaN` ensures re-encoding on every run.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `images` | IMAGE | Input batch `[B, H, W, C]`. |
| `output_path` | STRING | Target directory for MP4 file. |
| `filename` | STRING | Output filename (without extension). |
| `fps` | FLOAT | Frames per second (12–60). |
| `quality` | COMBO | `lossless`, `high`, or `medium`. |
| `cover_image` | IMAGE | Optional thumbnail for embedding. |
| `title`/`artist`/`album`/etc. | STRING | Standard MP4 metadata fields. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `video_path` | STRING | Absolute path to saved MP4 file. |

---

### 🔹 Generate Creation Time
Produces ISO-formatted timestamps for video metadata. Supports current time or custom input with validation.

#### ✨ Key Features
- **Real-Time or Custom:** Toggle between `now()` and user-defined datetime.
- **Format Validation:** Ensures `YYYY-MM-DD HH:MM:SS` structure for custom values.
- **Force Refresh:** `IS_CHANGED = NaN` guarantees fresh timestamp on every execution.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `use_current_time` | BOOLEAN | Use `datetime.now()` if `True` (Default: `True`). |
| `custom_datetime` | STRING | Manual timestamp in `YYYY-MM-DD HH:MM:SS` format. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `creation_time` | STRING | Formatted timestamp string. |

---

### 🔹 Text Watermark
Adds customizable text overlays with RTL language support, auto-scaling, and precise positioning controls.

#### ✨ Key Features
- **RTL Support:** Automatic BiDi handling for Arabic/Hebrew via `python-bidi` (fallback to manual reversal).
- **Auto-Scaling:** Font size adapts to image dimensions (`width`, `height`, or `diagonal` reference).
- **Flexible Layout:** Horizontal/vertical orientation, 3×3 positioning grid, margin offsets.
- **Visual Polish:** White text with black stroke, adjustable opacity, anti-aliased rendering.
- **Batch Processing:** Applies watermark to entire image sequence in one pass.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `images` | IMAGE | Input batch. |
| `text` | STRING | Watermark content. |
| `font_name` | COMBO | System font selector. |
| `base_font_size` | INT | Starting font size (8–500). |
| `auto_scale` | BOOLEAN | Enable dynamic sizing (Default: `True`). |
| `auto_scale_factor` | FLOAT | Scale ratio relative to reference dimension (0.005–0.1). |
| `scale_reference` | COMBO | `width`, `height`, or `diagonal`. |
| `text_orientation` | COMBO | `horizontal` or `vertical`. |
| `text_vertical_pos` / `text_horizontal_pos` | COMBO | 3-position selectors for alignment. |
| `vertical_text_direction` | COMBO | `top-to-bottom` or `bottom-to-top` for vertical mode. |
| `opacity` | FLOAT | Text transparency (0.0–1.0). |
| `margin_x` / `margin_y` | INT | Offset from edges (-500 to 500). |
| `force_rtl` | BOOLEAN | Override auto-detection for RTL languages. |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `watermarked_images` | IMAGE | Batch with applied watermark. |

---

### 🔹 Image Watermark
Overlays image watermarks with scaling modes, positioning presets, opacity control, and rotation.

#### ✨ Key Features
- **Scaling Modes:** `percentage` (relative to min dimension), `fixed`, `fit_width`, `fit_height`.
- **Positioning:** 3×3 grid with independent X/Y margin offsets.
- **Alpha Handling:** Supports transparency via alpha channel or external mask input.
- **Rotation & Opacity:** Apply angle (-180° to 180°) and transparency (0–100%) independently.
- **Batch Processing:** Applies watermark to entire sequence efficiently.

#### 📥 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `images` | IMAGE | Input batch. |
| `watermark` | IMAGE | Watermark image (any size). |
| `mask` | MASK | Optional alpha mask for watermark transparency. |
| `position` | COMBO | 9-position grid preset. |
| `margin_x` / `margin_y` | INT | Offset from edges (-500 to 500). |
| `scale_mode` | COMBO | `percentage`, `fixed`, `fit_width`, or `fit_height`. |
| `scale_factor` | FLOAT | Scale value (interpretation depends on `scale_mode`). |
| `opacity` | FLOAT | Watermark transparency (0–100). |
| `rotation` | INT | Rotation angle (-180° to 180°). |

#### 📤 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `watermarked_images` | IMAGE | Batch with applied image watermark. |

