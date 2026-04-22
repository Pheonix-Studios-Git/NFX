"""Constants"""

import os
import platform

APP_NAME = "nfx"
VERSION = "0.1.0"
DEVELOPER = "Pheonix Studios"

SEPERATORS = [":", ";", "->", "-", "="]

SYSTEM = platform.system()

base_dir = ""
config_path = ""

if SYSTEM == "Windows":
    base_root = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
    base_dir = os.path.join(base_root, APP_NAME)
    config_path = os.path.join(base_dir, "config.json")
elif SYSTEM == "Darwin": # macOS
    base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    config_path = os.path.join(base_dir, "config.json")
else: # Linux / Unix
    base_root = os.getenv("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    base_dir = os.path.join(base_root, APP_NAME)
    config_path = os.path.join(os.path.expanduser("~"), ".config", "nfx", "config.json")

BASE_DIR_DEF = base_dir
CONFIG_PATH_DEF = config_path

INSTALL_DIR_DEF = os.path.join(BASE_DIR_DEF, "installs")
CACHE_DIR_DEF = os.path.join(BASE_DIR_DEF, "cache")
DOWNLOAD_DIR_DEF = os.path.join(BASE_DIR_DEF, "downloads")
