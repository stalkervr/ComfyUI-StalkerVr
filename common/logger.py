from ..config.config_manager import ConfigManager


class LogEntry:
    """Structured log object."""

    def __init__(self, node_class: str, title: str, details: dict, footer: str = None):
        self.node_class = node_class
        self.title = title
        self.details = details
        self.footer = footer


def log(entry: LogEntry):
    config = ConfigManager()
    if not config.get("logging.global_enabled", True):
        return
    if not config.get(f"logging.node_settings.{entry.node_class}", True):
        return

    print(f"🎯 [{entry.node_class}] {entry.title}")
    for key, value in entry.details.items():
        print(f"  {key}: {value}")
    if entry.footer:
        print(f"🎯 {entry.footer}")
    print()


def log_end(entry: LogEntry):
    config = ConfigManager()
    if not config.get("logging.global_enabled", True):
        return
    if not config.get(f"logging.node_settings.{entry.node_class}", True):
        return

    for key, value in entry.details.items():
        print(f"{key}: {value}")

    print(f"🎯 [{entry.node_class}] {entry.title}")
    print()


def log_start(entry: LogEntry):
    config = ConfigManager()
    if not config.get("logging.global_enabled", True):
        return
    if not config.get(f"logging.node_settings.{entry.node_class}", True):
        return

    print()
    print(f"🎯 [{entry.node_class}] {entry.title}")
    for key, value in entry.details.items():
        print(f"{key}: {value}")
