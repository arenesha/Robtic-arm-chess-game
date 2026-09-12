import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_file: str = "config/settings.yaml"):
        self.config_file = Path(config_file)
        self.config = self.load_config()

    def load_config(self) -> dict:
        if not self.config_file.exists():
            logger.warning(f"Configuration file {self.config_file} not found. Using defaults.")
            return {}
            
        with open(self.config_file, 'r') as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as exc:
                logger.error(f"Error parsing YAML file: {exc}")
                return {}

    def get(self, section: str, key: str, default=None):
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        
    def save_config(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
