import configparser
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_path: str = "config/config.ini"):
        self.config = configparser.ConfigParser()
        self.config_path = Path(config_path)
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            self.config.read(self.config_path)
        else:
            self._create_default_config()

    def _create_default_config(self) -> None:
        """Create default configuration."""
        self.config["IDENTIFICATION"] = {"USER_AGENT": "UCI Search Engine Crawler/1.0"}
        self.config["CONNECTION"] = {"HOST": "localhost", "PORT": "8000"}
        self.config["CRAWLER"] = {
            "SEEDURL": "https://www.ics.uci.edu/",
            "POLITENESS": "1.0",
        }
        self.config["LOCAL PROPERTIES"] = {
            "SAVE_FILE": "crawler_state.db",
            "THREADCOUNT": "4",
        }
        self.save()

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            self.config.write(f)

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        """Set a configuration value."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self.save()

    def get_section(self, section: str) -> Dict[str, str]:
        """Get all values in a section."""
        if not self.config.has_section(section):
            return {}
        return dict(self.config[section])
