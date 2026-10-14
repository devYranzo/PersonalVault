from pathlib import Path

APP_NAME = "Personal Vault"
APP_VERSION = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"

PLUGIN_REGISTRY_FILE = DATA_DIR / "plugins.json"
