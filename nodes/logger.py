from .config_manager import ConfigManager


class LogEntry:
    """Structured log object."""

    def __init__(self, node_class: str, title: str, details: dict, footer: str = None):
        self.node_class = node_class
        self.title = title
        self.details = details
        self.footer = footer


def log(entry: LogEntry):
    """Prints log only if enabled in config."""
    config = ConfigManager()

    # 1. Global switch
    if not config.get("logging.global_enabled", True):
        return

    # 2. Class-specific switch
    if not config.get(f"logging.node_settings.{entry.node_class}", True):
        return

    # 3. Formatted output
    print(f"🎯 [{entry.node_class}] {entry.title}")
    for key, value in entry.details.items():
        print(f"  {key}: {value}")
    if entry.footer:
        print(f"🎯 {entry.footer}")
    print()  # Empty line for readability