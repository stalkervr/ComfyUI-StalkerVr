## [Unreleased]

### ✨ Added - Wan 2.2 Ecosystem
- **Wan Video Lora CivitAI Downloader**: Fetches paired high/low noise LoRAs with auto-metadata generation and skip-if-exists caching.
- **Wan Video LoRA Pair Creator**: Converts existing LoRAs into structured Wan pairs with `lora.json` and overwrite protection.
- **Wan Video LoRA Pair Select**: Dropdown selector with chaining support, trigger word merging, and live UI metadata display.
- **Wan Video Enhance Motion Advanced KJ**: Motion amplification for `WANVIDIMAGE_EMBEDS` with PainterI2V algorithm and color drift protection.
- **Wan Video Enhance Motion Advanced**: Dual-output motion enhancement for `CONDITIONING`/`LATENT` designed for high/low noise dual-sampler workflows.

### 🛠 Added - Core Utilities & Workflow Tools
- **Logger**: Wildcard passthrough node with structured console logging, custom colors, and force-execution (`IS_CHANGED=NaN`).
- **Switch Any**: Lazy-evaluation conditional router that skips processing for unselected branches.
- **Calculate Frame Count**: Precise frame counter (`duration * fps + 1`) with bounded inputs and inline tooltips.
- **Current Date Time**: Real-time timestamp generator with cascading precision (auto-enables hours/minutes/seconds).
- **Config Manager & Constants**: Secure split-config system (`secrets.yaml` + `config.yaml`), centralized path registration, and shared category prefixes.
- **Custom Types Module**: Extracted `Everything` wildcard type for reusable cross-node compatibility.

### 🧩 Added - JSON Utilities
- **Json Builder**: Dynamic key-value construction with nested dot-notation support and JS-driven dynamic inputs.
- **Json Pair Input**: Smart input node with automatic type detection (JSON/Bool/Num/String) and wildcard passthrough.
- **Json Path Loader**: Batch directory scanner with sorting, limiting, and forced fresh-scan execution (`IS_CHANGED=random`).
- **Json Serialize / Deserialize Object**: Bidirectional batch conversion between Python objects and JSON strings with ComfyUI list output support.
- **Json Format / Minify**: Pretty-printing and compacting tools with configurable ASCII escaping, key sorting, and error fallback modes.
- **Json Field Value Extractor**: Precise value retrieval using dot notation with strict type preservation.
- **Json Field Remover**: Safe deletion of multiple fields by pipe-separated paths with graceful missing-key handling.
- **Json Field Replace Extend**: Dynamic field updates with smart casting, dot/array navigation, and optional value concatenation. Now accepts any data type via Wildcard input (strings, lists, dicts, numbers, booleans, null) with smart list concatenation in extend mode.
- **Json Prompt To Text Prompt**: Recursive flattener that converts JSON structures into clean, punctuated text prompts with newline toggling.

### 🔤 Added - String & Text Utilities
- **String Builder**: Dynamic text concatenation with configurable separators, newline injection, and JS-driven input scaling.
- **String Wrapper**: Prefix/suffix wrapping with intelligent whitespace handling and empty-segment filtering.
- **String Normalize**: Universal whitespace normalizer that collapses line breaks and multiple spaces into single delimiters.
- **Text SaveToFile**: Structured text saver with project-based paths, optional date folders, and dual write modes (unique numbered files or single-file append with custom separators).
- **Text LoadFromFile**: Reads text from a single file with support for splitting content into a list of strings via custom separators.
- **Text LoadFromDirectory**: Scans a folder for text files and loads content either as a per-file list or a flat merged list of all entries.
- **Text Find And Replace**: Advanced substitution tool supporting batch replacements via pipe separator and Regular Expressions.
- **Text Keyword Checker**: Scans text for specific keywords/phrases and returns a boolean flag for conditional workflow routing. Empty text is now treated as a valid input (returns `False`) instead of skipping execution.
- **Text Wrapper Batch**: Applies common prefix and suffix to every string in a batch, ideal for formatting prompt lists.

### 🖼️ Added - Image Utilities
- **Image Grid Cropper**: Splits images into fixed-size grids with automatic edge padding, native batch processing, and optional sequential disk export.
- **Image Crop**: Margin-based cropping with optional bilinear size restoration and `[B, H, W, C]` batch support.
- **Image Ratio Resizer**: Aspect-ratio enforcement using cover-mode center cropping, auto-orientation detection, and preset/custom ratios.
- **Image Get Size**: Zero-overhead dimension extractor with optional image input, returning width, height, resolution, and the original image for chaining.
- **Image Desired Resolution**: WAN/BiRefNet-optimized resizer with 16-pixel alignment, aspect-ratio preservation, and dimension-only fallback mode.
- **Images Load With Metadata**: Batch directory loader with universal format support, EXIF/PNG metadata extraction, alpha mask generation, smart type conversion, and configurable image count limit.
- **Image Load With Metadata**: Single-image loader with direct file metadata extraction ensuring data accuracy on every execution.
- **Image Save With Metadata**: High-reliability PNG archiver with embedded JSON metadata, workflow preservation, sequential numbering, caption export toggle, and compression control.
- **Image Resolution Calculator**: Calculates optimal dimensions from megapixels and aspect ratio with pixel alignment; includes a raw `aspect_ratio` string output and a new `prev_aspect_ratio` input for chaining multiple calculators with priority: `custom_ratio` → `prev_aspect_ratio` → `preset`.

###  Added - IO & File Management Utilities
- **FormatDatePath**: Real-time path generator with custom `%date:FORMAT%` token parsing and forced workflow re-execution for dynamic timestamping.
- **FileSavePath**: Hierarchical path builder with optional date partitioning toggle. Assembles `{root}/{project}/{type}/` and appends `{YYYY-MM-DD}` only if enabled.

###  Added - LoRA Management Utilities
- **Lora Select**: Pure container-based LoRA selector that packs file data and strength parameters without modifying models. Supports chainable architecture via `prev_lora` input. Now focused solely on data packing — name strings and logging moved to apply nodes.
- **Lora Select Batch**: Batch LoRA selector with 5 independent slots (name/strength/enable each). Merges all selected LoRAs into a single container chain, fully compatible with `LoraSelect` chaining.
- **Lora Apply**: Pure technical applier that injects pre-configured LoRA containers into Model/CLIP pairs. Uses base-model caching to prevent duplicate application. Now features structured `log_start`/`log_end` reporting and a new `applied_loras` output (list of `name | strength` strings) for metadata tracking.
- **Lora Apply Model Only**: New node that applies LoRA chains to MODEL only without touching CLIP. Ideal for workflows with separate text-encoder handling. Includes the same structured logging and `applied_loras` output.

### 📜 Added - YAML Prompt Utilities
- **YAML Save Prompt**: Saves positive/negative prompts to a hierarchical YAML database with person/type/group/sub-group nesting, toggle-controlled writing, whitespace normalization, and corruption-safe fallback.
- **YAML Load Prompt**: Loads synchronized positive/negative prompt lists from YAML with hierarchical path resolution, optional name filtering, result limiting, and force-refresh execution for real-time database reads.

### 🧩 Added - Production & Watermark Utilities
- **Save Video With Metadata**: Encodes image batches to MP4 with embedded standard metadata tags and optional cover image attachment. Supports lossless/high/medium quality presets, FFmpeg fast-start optimization, and dynamic tag injection.
- **Generate Creation Time**: Produces validated ISO-formatted timestamps for video metadata. Supports real-time generation or custom input with strict format checking and forced refresh execution.
- **Text Watermark**: Adds customizable text overlays with automatic RTL language support, dimension-based auto-scaling, and precise 3×3 positioning. Features horizontal/vertical orientation, BiDi algorithm integration, and adjustable opacity/stroke rendering.
- **Image Watermark**: Overlays image watermarks with multiple scaling modes (`percentage`, `fixed`, `fit_width`, `fit_height`), 9-point grid positioning, rotation, and opacity control. Supports external alpha masks and native batch processing.

### 🤖 Added - LLM & Vision-Language Utilities
- **LlamaCppTextGenerator**: Local GGUF-based vision-language text generator with full process isolation — each generation runs in a dedicated subprocess, protecting ComfyUI from C++ crashes (SIGABRT, CUDA errors). Features:
  - Multi-directory model search via `llm.models_path` config (list of absolute/relative paths) with recursive scanning.
  - Automatic mmproj (vision projector) detection from the main model's folder (priority: `mmproj` → `vision` → `clip`); mmproj files are hidden from the model dropdown.
  - Multi-directory system prompt loading via `llm.system_prompts_path` config (list of absolute/relative paths) with recursive scanning and first-match priority.
  - VRAM management via `kv_cache_type` (`f16`/`q8_0`/`q4_0`) and `flash_attn` to solve SWA-cache issues in Gemma and similar architectures.
  - New `metadata` output: JSON structure `{instructions, request, response}` ready for embedding into image/video metadata.
  - `used_handler` log line revealing the actual handler when `handler_type=auto`.
  - Version-agnostic handler initialization (tries both `mmproj_path` and `clip_model_path` for old/new llama-cpp-python).
  - Auto-handler detection (Qwen3-VL, Qwen3.5, Gemma4, LLaVA 1.5/1.6, MiniCPM), file-based system prompt management, `