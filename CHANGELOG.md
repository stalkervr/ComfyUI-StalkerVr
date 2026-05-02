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

###  Documentation & Refactoring
- Complete `README.md` overhaul with installation, API key setup, and per-node specifications in standardized Markdown format.
- **Centralized Logging**: Replaced all `print()` statements with `LogEntry` across the entire node suite.
- **Type Safety & Fallbacks**: Added explicit type hints, safe parsing wrappers, and graceful degradation for all converters.
- All nodes now follow consistent architecture patterns, dynamic input handling, and ComfyUI best practices.