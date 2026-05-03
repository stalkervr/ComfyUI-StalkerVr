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
- **Json Field Replace Extend**: Dynamic field updates with smart casting, dot/array navigation, and optional value concatenation.
- **Json Prompt To Text Prompt**: Recursive flattener that converts JSON structures into clean, punctuated text prompts with newline toggling.

### 🔤 Added - String & Text Utilities
- **String Builder**: Dynamic text concatenation with configurable separators, newline injection, and JS-driven input scaling.
- **String Wrapper**: Prefix/suffix wrapping with intelligent whitespace handling and empty-segment filtering.
- **String Normalize**: Universal whitespace normalizer that collapses line breaks and multiple spaces into single delimiters.

### 🖼️ Added - Image Utilities
- **Image Grid Cropper**: Splits images into fixed-size grids with automatic edge padding, native batch processing, and optional sequential disk export.
- **Image Crop**: Margin-based cropping with optional bilinear size restoration and `[B, H, W, C]` batch support.
- **Image Ratio Resizer**: Aspect-ratio enforcement using cover-mode center cropping, auto-orientation detection, and preset/custom ratios.
- **Image Get Size**: Zero-overhead dimension extractor returning width, height, and configurable min/max resolution for dynamic routing.
- **Image Desired Resolution**: WAN/BiRefNet-optimized resizer with 16-pixel alignment, aspect-ratio preservation, and dimension-only fallback mode.
- **Images Load With Metadata**: Batch directory loader with universal format support, EXIF/PNG metadata extraction, alpha mask generation, and smart type conversion.
- **Image Load With Metadata**: Single-image loader with JS-driven global metadata cache that survives ComfyUI mask editor resets and clipspace temp files.
- **Image Save With Metadata**: High-reliability PNG archiver with embedded JSON metadata, workflow preservation, sequential numbering, and caption export.

### 📁 Added - IO & File Management Utilities
- **FormatDatePath**: Real-time path generator with custom `%date:FORMAT%` token parsing and forced workflow re-execution for dynamic timestamping.
- **FileSavePath**: Hierarchical path builder that auto-assembles `{root}/{project}/{type}/{date}/` structures for organized, date-partitioned output routing.
- **SaveTextFile**: Smart file saver with dynamic date placeholders, collision-safe sequential numbering, automatic extension management, and empty-input bypass.

### 📝 Documentation & Refactoring
- Complete `README.md` overhaul with installation, API key setup, and per-node specifications in standardized Markdown format.
- **Centralized Logging**: Replaced all `print()` statements with `LogEntry` across the entire node suite.
- **Type Safety & Fallbacks**: Added explicit type hints, safe parsing wrappers, and graceful degradation for all converters.
- All nodes now follow consistent architecture patterns, dynamic input handling, and ComfyUI best practices.