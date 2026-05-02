feat: add Wan 2.2 ecosystem nodes and core workflow utilities

- Introduce LoRA management suite (Downloader, Creator, Pair Select)
- Add motion enhancement nodes (Embeds & Conditioning variants)
- Implement Logger, Switch Any, Frame Counter, and Date/Time tools
- Centralize configuration, constants, and custom types
- Overhaul README.md with structured node documentation
- Enforce English logging, error handling, and type safety

## 📝 CHANGELOG.md

## [Unreleased]
###  Added - Wan 2.2 Ecosystem
- **CivitAI → Wan LoRA Downloader**: Fetches paired high/low noise LoRAs with auto-metadata generation and skip-if-exists caching.
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

### 📝 Documentation
- Complete `README.md` overhaul with installation, API key setup, and per-node specifications in standardized Markdown format.
- All nodes now use centralized logging, English error messages, and consistent type hints.