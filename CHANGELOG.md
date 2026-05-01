# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Centralized ConfigManager for public/private settings separation.
- Structured Logger with per-node toggle support.
- `CivitAIWanLoraDownloader`: Downloads Wan 2.2 LoRA pairs with skip-if-exists.
- `LoraLoaderExtended`: Single LoRA loader with enable toggle and name chaining.
- `LoraLoaderExtendedBatch`: Batch loader for up to 5 LoRAs simultaneously.
- `secrets.yaml.example` template for secure API key management.

### Changed
- Migrated all console logging to the new centralized logger.
- Removed hardcoded prints and debug comments from node logic.

### Fixed
- API key loading priority (Parameter > secrets.yaml > public config).