from ..config.config_manager import ConfigManager


class LogEntry:
    """Structured log object."""

    def __init__(self, node_class: str, title: str, details: dict, footer: str = None):
        self.node_class = node_class
        self.title = title
        self.details = details
        self.footer = footer


def _is_enabled(node_class: str) -> bool:
    """
    Whitelist-проверка логирования.
    Лог выводится ТОЛЬКО если класс явно включен в конфигурации:
        logging.node_class.<ClassName>: true
    Если значение false или класс отсутствует — лог подавляется.
    """
    config = ConfigManager()
    return bool(config.get(f"logging.node_class.{node_class}", False))


def log(entry: LogEntry):
    if not _is_enabled(entry.node_class):
        return

    print(f"🎯 [{entry.node_class}] {entry.title}")
    for key, value in entry.details.items():
        print(f"  {key}: {value}")
    if entry.footer:
        print(f"🎯 {entry.footer}")
    print()


def log_end(entry: LogEntry):
    if not _is_enabled(entry.node_class):
        return

    for key, value in entry.details.items():
        print(f"{key}: {value}")

    print(f"🎯 [{entry.node_class}] {entry.title}")
    print()


def log_start(entry: LogEntry):
    if not _is_enabled(entry.node_class):
        return

    print()
    print(f"🎯 [{entry.node_class}] {entry.title}")
    for key, value in entry.details.items():
        print(f"{key}: {value}")
